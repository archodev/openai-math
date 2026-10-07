"""Assemble the final video.

    /opt/venv/bin/python tools/assemble.py [--video-dir build/final] [--out out/four-thousand-problems.mp4]

* concatenates the rendered scene videos in script order (re-encodes once, H.264),
* lays each scene's narration WAV at that scene's actual start time,
* adds the procedural music bed, ducked under the voice,
* loudness-normalises to about -15 LUFS,
* writes subtitles (.srt) and YouTube chapter timestamps (.txt).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

VIDEO = Path(__file__).resolve().parents[1]
SR = 48000


def load_script():
    spec = importlib.util.spec_from_file_location("script", VIDEO / "narration" / "script.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.SCENES


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                          "-show_entries", "stream=nb_read_packets,r_frame_rate", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"][0]
    num, den = map(int, st["r_frame_rate"].split("/"))
    return int(st["nb_read_packets"]) * den / num


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_caption(text, start, end, max_chars=84):
    """Split a narration line into caption chunks (<= 2 lines of 42 chars),
    timing proportional to characters."""
    words = text.split()
    chunks, cur = [], []
    for w in words:
        if len(" ".join(cur + [w])) > max_chars and cur:
            chunks.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
        if cur and cur[-1][-1:] in ".?!" and len(" ".join(cur)) > 40:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    total = sum(len(c) for c in chunks)
    out, t = [], start
    for c in chunks:
        d = (end - start) * len(c) / total
        out.append((t, t + d, "\n".join(textwrap.wrap(c, 44))))
        t += d
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-dir", default=str(VIDEO / "build" / "final"))
    ap.add_argument("--out", default=str(VIDEO / "out" / "four-thousand-problems.mp4"))
    ap.add_argument("--music-db", type=float, default=-24.0, help="music level under voice (dB rel. full)")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--crf", default="18")
    ap.add_argument("--preset", default="slow")
    a = ap.parse_args()

    scenes = load_script()
    vdir = Path(a.video_dir)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = VIDEO / "build" / "assemble"
    work.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- timeline
    starts, durs, missing = [], [], []
    t = 0.0
    for sc in scenes:
        p = vdir / f"{sc['id']}.mp4"
        if not p.exists():
            missing.append(sc["id"])
            continue
        d = probe_duration(p)
        timing = json.loads((VIDEO / "build" / "timing" / f"{sc['id']}.json").read_text())
        if abs(d - timing["duration"]) > 0.1:
            print(f"  ! {sc['id']}: video {d:.2f}s vs narration {timing['duration']:.2f}s")
        starts.append((sc["id"], t))
        durs.append(d)
        t += d
    if missing:
        print("missing scene videos:", missing)
        sys.exit(1)
    total = t
    print(f"timeline: {len(starts)} scenes, {total:.1f}s = {total / 60:.2f} min")

    # ---------------------------------------------------------------- video concat
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{(vdir / f'{sid}.mp4').resolve()}'\n" for sid, _ in starts))
    vid = work / "video.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:v", "libx264", "-preset", a.preset, "-crf", a.crf, "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-an", str(vid)], check=True)

    # ---------------------------------------------------------------- narration track
    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n, np.float32)
    for sid, st in starts:
        a24, sr = sf.read(VIDEO / "build" / "audio" / f"{sid}.wav", dtype="float32")
        a48 = resample_poly(a24, 2, 1).astype(np.float32) if sr == 24000 else a24
        i = int(round(st * SR))
        voice[i:i + len(a48)] += a48[: n - i]
    # gentle voice polish: high-pass 70 Hz, slight presence lift is skipped (keep it natural)
    from scipy.signal import butter, sosfilt
    voice = sosfilt(butter(2, 70, "hp", fs=SR, output="sos"), voice).astype(np.float32)
    peak = np.abs(voice).max()
    voice *= 0.89 / max(peak, 1e-6)

    mix = np.stack([voice, voice], axis=1)
    if not a.no_music:
        mpath = work / "music.wav"
        subprocess.run([sys.executable, str(VIDEO / "tools" / "music.py"), f"{total + 1:.2f}", str(mpath)], check=True)
        music, msr = sf.read(mpath, dtype="float32")
        assert msr == SR
        music = music[:n]
        if len(music) < n:
            music = np.pad(music, ((0, n - len(music)), (0, 0)))
        # high-pass the bed a bit so it does not mask the voice fundamentals
        music = sosfilt(butter(2, 110, "hp", fs=SR, output="sos"), music, axis=0)
        # ducking envelope from voice activity
        win = int(0.02 * SR)
        m = len(voice) // win
        rms = np.sqrt(np.mean(voice[: m * win].reshape(m, win) ** 2, axis=1) + 1e-12)
        active = (rms > 0.01).astype(float)
        # attack fast (60 ms), release slow (700 ms)
        env = np.zeros_like(active)
        a_c, r_c = np.exp(-1 / (0.06 / 0.02)), np.exp(-1 / (0.7 / 0.02))
        e = 0.0
        for k, v in enumerate(active):
            c = a_c if v > e else r_c
            e = c * e + (1 - c) * v
            env[k] = e
        env = np.repeat(env, win)
        env = np.pad(env, (0, n - len(env)), mode="edge")
        lo = 10 ** (a.music_db / 20)          # under voice
        hi = 10 ** ((a.music_db + 7) / 20)    # in gaps
        gain = hi + (lo - hi) * env
        mrms = np.sqrt(np.mean(music ** 2)) + 1e-9
        music = music / mrms * 0.1            # normalise bed to ~-20 dBFS rms before gain
        mix += music * gain[:, None] * 1.0
    wav = work / "mix.wav"
    sf.write(wav, mix, SR, subtype="FLOAT")
    norm = work / "mix_norm.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-af",
                    "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", str(SR), str(norm)], check=True)

    # ---------------------------------------------------------------- mux
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(vid), "-i", str(norm),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("wrote", out)

    # ---------------------------------------------------------------- subtitles + chapters
    srt, idx = [], 1
    chapters = ["0:00 Intro"]
    for sid, st in starts:
        timing = json.loads((VIDEO / "build" / "timing" / f"{sid}.json").read_text())
        for ln in timing["lines"]:
            for s0, s1, txt in split_caption(ln["text"], st + ln["start"], st + ln["end"]):
                srt.append(f"{idx}\n{srt_time(s0)} --> {srt_time(s1)}\n{txt}\n")
                idx += 1
        if sid.endswith("_card"):
            title = timing["lines"][0]["text"].split(":")[0].split(". ", 1)[-1].strip()
            mm, ss = divmod(int(st), 60)
            chapters.append(f"{mm}:{ss:02d} {title}")
        if sid == "s99_outro":
            mm, ss = divmod(int(st), 60)
            chapters.append(f"{mm}:{ss:02d} Outro")
    out.with_suffix(".srt").write_text("\n".join(srt))
    out.with_name(out.stem + "-chapters.txt").write_text("\n".join(chapters) + "\n")
    print("wrote subtitles and chapters")


if __name__ == "__main__":
    main()
