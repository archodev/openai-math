"""Synthesize narration with Kokoro and compute cue timings.

    /opt/venv/bin/python tools/build_audio.py [scene_id ...]

Reads narration/script.py (SCENES) and narration/lexicon.py (LEXICON), writes
    build/audio/<id>.wav       24 kHz mono narration for the scene
    build/timing/<id>.json     {"duration", "cues", "lines"}
Inline cue markers look like {name}; their time is measured by synthesizing
the text prefix up to the marker (same voice/speed) and measuring its length.
All syntheses are cached in build/cache/tts, so edits only re-synthesize what
changed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import multiprocessing as mp
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

VIDEO = Path(__file__).resolve().parents[1]
CACHE = VIDEO / "build" / "cache" / "tts"
SR = 24000
VOICE = "af_heart"
SPEED = 1.1
HEAD = 0.35         # silence before first line of a scene
TAIL = 0.55         # silence after last line
GAP = 0.30          # default pause between lines
CUE_LEAD = 0.04     # cues fire slightly before the word


def load(name):
    spec = importlib.util.spec_from_file_location(name, VIDEO / "narration" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LEX = load("lexicon").LEXICON
_LEX_RE = None


def apply_lexicon(text):
    """Replace words with misaki inline phoneme links: [word](/phonemes/)."""
    global _LEX_RE
    if not LEX:
        return text
    if _LEX_RE is None:
        keys = sorted(LEX, key=len, reverse=True)
        _LEX_RE = re.compile(r"(?<![\w\[])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w\]])")
    return _LEX_RE.sub(lambda m: f"[{m.group(1)}](/{LEX[m.group(1)]}/)", text)


def spoken(text):
    """Normalise display-ish punctuation for TTS."""
    t = text.replace("—", ", ").replace("–", "-").replace("…", "...")
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ------------------------------------------------------------------ synthesis worker
_tts = None


def _init():
    global _tts
    sys.path.insert(0, "/opt/kokoro")
    import tts as T  # /opt/kokoro/tts.py
    _tts = T


def _key(text, voice, speed):
    return hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:20]


def synth_cached(args):
    text, voice, speed = args
    CACHE.mkdir(parents=True, exist_ok=True)
    k = _key(text, voice, speed)
    f = CACHE / f"{k}.npy"
    if f.exists():
        return text, np.load(f)
    if _tts is None:
        _init()
    ph = _tts.phonemize(apply_lexicon(spoken(text)))
    samples, sr = _tts.kokoro().create(ph, voice=voice, speed=speed, is_phonemes=True)
    assert sr == SR
    a = trim(np.asarray(samples, dtype=np.float32))
    np.save(f, a)
    (CACHE / f"{k}.txt").write_text(f"{text}\n{ph}\n")
    return text, a


def trim(a, keep=0.03, db=-42):
    if len(a) == 0:
        return a
    win = int(0.01 * SR)
    n = len(a) // win
    if n == 0:
        return a
    rms = np.sqrt(np.mean(a[: n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    thr = rms.max() * 10 ** (db / 20)
    idx = np.where(rms > thr)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] * win - int(keep * SR))
    e = min(len(a), (idx[-1] + 1) * win + int(keep * SR))
    return a[s:e]


# ------------------------------------------------------------------ script parsing
CUE_RE = re.compile(r"\{([A-Za-z0-9_]+)\}")


def parse_line(line):
    if isinstance(line, str):
        line = {"text": line}
    raw = line["text"]
    cues, clean, last = [], "", 0
    for m in CUE_RE.finditer(raw):
        clean += raw[last:m.start()]
        cues.append((m.group(1), len(clean)))
        last = m.end()
    clean += raw[last:]
    # collapse double spaces created by markers
    clean2, mapping = "", []
    for i, ch in enumerate(clean):
        if ch == " " and clean2.endswith(" "):
            mapping.append(len(clean2))
            continue
        mapping.append(len(clean2))
        clean2 += ch
    mapping.append(len(clean2))
    cues = [(n, mapping[p]) for n, p in cues]
    return {
        "text": clean2.strip(),
        "cues": cues,
        "pause": line.get("pause", GAP),
        "speed": line.get("speed", SPEED),
        "voice": line.get("voice", VOICE),
        "lead": clean2[: len(clean2) - len(clean2.lstrip())],
    }


def prefix_of(text, pos):
    p = text[:pos].rstrip()
    # strip trailing punctuation-only remainder
    return p


def build(scenes, only=None, procs=4):
    jobs = set()
    parsed = {}
    for sc in scenes:
        if only and sc["id"] not in only:
            continue
        lines = [parse_line(l) for l in sc["lines"]]
        parsed[sc["id"]] = lines
        for ln in lines:
            t = ln["text"]
            jobs.add((t, ln["voice"], ln["speed"]))
            off = len(ln["lead"])
            for _, pos in ln["cues"]:
                pre = prefix_of(ln["text"], max(0, pos - off))
                if pre and pre != t:
                    jobs.add((pre, ln["voice"], ln["speed"]))
    todo = [j for j in jobs if not (CACHE / f"{_key(*j)}.npy").exists()]
    print(f"[tts] {len(jobs)} syntheses, {len(todo)} new")
    results = {}
    if todo:
        with mp.get_context("spawn").Pool(procs, initializer=_init) as pool:
            for i, (text, a) in enumerate(pool.imap_unordered(synth_cached, todo)):
                if (i + 1) % 20 == 0:
                    print(f"[tts]   {i + 1}/{len(todo)}")
    for j in jobs:
        results[j] = np.load(CACHE / f"{_key(*j)}.npy")

    (VIDEO / "build" / "audio").mkdir(parents=True, exist_ok=True)
    (VIDEO / "build" / "timing").mkdir(parents=True, exist_ok=True)
    summary = []
    for sc in scenes:
        if sc["id"] not in parsed:
            continue
        lines = parsed[sc["id"]]
        head = sc.get("head", HEAD)
        tail = sc.get("tail", TAIL)
        t = head
        chunks = [np.zeros(int(head * SR), np.float32)]
        cues, info = {}, []
        for i, ln in enumerate(lines):
            a = results[(ln["text"], ln["voice"], ln["speed"])]
            dur = len(a) / SR
            cues[f"L{i}"] = round(t, 3)
            off = len(ln["lead"])
            for name, pos in ln["cues"]:
                pre = prefix_of(ln["text"], max(0, pos - off))
                if not pre:
                    ct = t
                elif pre == ln["text"]:
                    ct = t + dur
                else:
                    pa = results[(pre, ln["voice"], ln["speed"])]
                    ct = t + min(dur, max(0.0, len(pa) / SR - CUE_LEAD))
                if name in cues:
                    raise SystemExit(f"duplicate cue {name} in {sc['id']}")
                cues[name] = round(ct, 3)
            chunks.append(a)
            t += dur
            cues[f"L{i}_end"] = round(t, 3)
            info.append({"text": ln["text"], "start": round(cues[f'L{i}'], 3), "end": round(t, 3)})
            pause = ln["pause"] if i < len(lines) - 1 else tail
            chunks.append(np.zeros(int(pause * SR), np.float32))
            t += pause
        audio = np.concatenate(chunks)
        total = len(audio) / SR
        sf.write(VIDEO / "build" / "audio" / f"{sc['id']}.wav", audio, SR, subtype="FLOAT")
        timing = {"duration": round(total, 3), "cues": cues, "lines": info}
        (VIDEO / "build" / "timing" / f"{sc['id']}.json").write_text(json.dumps(timing, indent=1))
        summary.append((sc["id"], total, sum(len(l["text"].split()) for l in lines)))
    tot = sum(s[1] for s in summary)
    for sid, d, w in summary:
        print(f"  {sid:28s} {d:6.1f}s  {w:4d} words")
    print(f"[tts] total {tot:.1f}s = {tot / 60:.2f} min")


if __name__ == "__main__":
    script = load("script")
    only = set(sys.argv[1:]) or None
    build(script.SCENES, only)
