"""Procedural ambient music bed (no samples, fully reproducible).

    /opt/venv/bin/python tools/music.py <seconds> <out.wav>

Slow pad chords (additive sines with gentle detune and long envelopes), a sparse
bell motif, soft sub, all through a simple feedback-delay-network reverb.
Designed to sit ~20 dB under narration; deliberately calm and consonant.
"""
import sys

import numpy as np
import soundfile as sf

SR = 48000
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# D major-ish, gently moving: Dmaj9, Bm9, Gmaj7(9), Asus2 / Em9, Gmaj7, Bm7, A6sus
PROG = [
    [50, 57, 62, 64, 66, 69],   # D  A  D  E  F# A
    [47, 54, 61, 62, 66, 69],   # B  F# C# D F# A
    [43, 50, 57, 59, 62, 66],   # G  D  A  B  D  F#
    [45, 52, 57, 59, 64, 69],   # A  E  A  B  E  A
    [40, 47, 54, 59, 62, 66],   # E  B  F# B  D  F#
    [43, 50, 54, 59, 62, 69],   # G  D  F# B  D  A
    [47, 54, 57, 62, 66, 69],   # B  F# A  D  F# A
    [45, 52, 57, 61, 64, 66],   # A  E  A  C# E  F#
]
CHORD_LEN = 9.6  # seconds per chord


def env(n, a, r):
    e = np.ones(n)
    ai, ri = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    e[:ai] = np.sin(np.linspace(0, np.pi / 2, ai)) ** 2
    e[-ri:] *= np.cos(np.linspace(0, np.pi / 2, ri)) ** 2
    return e


def pad_voice(freq, n, detune_cents=5):
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for k, (amp, mult) in enumerate([(1.0, 1), (0.28, 2), (0.10, 3), (0.04, 4)]):
        for side, d in ((0, -detune_cents), (1, detune_cents)):
            f = freq * mult * 2 ** (d / 1200)
            ph = rng.uniform(0, 2 * np.pi)
            vib = 1 + 0.0015 * np.sin(2 * np.pi * 0.17 * t + ph)
            out[:, side] += amp * np.sin(2 * np.pi * f * t * vib + ph)
    return out


def bell(freq, n):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for amp, ratio, dec in [(1, 1, 2.2), (0.35, 2.0, 1.4), (0.15, 3.01, 0.8), (0.06, 4.2, 0.5)]:
        s += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / dec)
    att = np.minimum(1, t / 0.008)
    return s * att


def main(total, path):
    n = int(total * SR)
    mix = np.zeros((n, 2))
    nchords = int(np.ceil(total / CHORD_LEN)) + 1
    for c in range(nchords):
        chord = PROG[c % len(PROG)]
        start = int(c * CHORD_LEN * SR)
        ln = int((CHORD_LEN + 3.5) * SR)        # overlap for crossfade
        if start >= n:
            break
        ln = min(ln, n - start)
        e = env(ln, 2.8, 3.4)[:, None]
        for j, note in enumerate(chord):
            amp = 0.075 if j == 0 else 0.05
            mix[start:start + ln] += amp * e * pad_voice(midi(note), ln)
        # soft sub
        t = np.arange(ln) / SR
        mix[start:start + ln] += (0.06 * e[:, 0] * np.sin(2 * np.pi * midi(chord[0] - 12) * t))[:, None]
        # sparse bell motif: 2-3 notes per chord from the upper voices, an octave up
        for k in range(rng.integers(2, 4)):
            note = chord[rng.integers(2, len(chord))] + 12
            at = start + int(rng.uniform(0.6, CHORD_LEN - 1.0) * SR)
            bl = min(int(4 * SR), n - at)
            if bl <= 0:
                continue
            b = 0.035 * bell(midi(note), bl)
            pan = rng.uniform(0.25, 0.75)
            mix[at:at + bl, 0] += b * (1 - pan)
            mix[at:at + bl, 1] += b * pan
    # gentle global fade in/out
    mix *= env(n, 3.0, 6.0)[:, None]
    # one-pole lowpass to soften
    a = np.exp(-2 * np.pi * 5000 / SR)
    for ch in range(2):
        from scipy.signal import lfilter
        mix[:, ch] = lfilter([1 - a], [1, -a], mix[:, ch])
    mix = fdn_reverb_fast(mix)
    peak = np.abs(mix).max()
    mix *= 0.5 / peak
    sf.write(path, mix.astype(np.float32), SR)
    print(f"wrote {path} {total:.1f}s peak-normalised to -6 dBFS")


def fdn_reverb_fast(x, seconds=3.4, mix=0.4):
    """Convolution reverb with a synthetic decaying-noise impulse (fast via FFT)."""
    from scipy.signal import fftconvolve
    L = int(seconds * SR)
    t = np.arange(L) / SR
    ir = np.zeros((L, 2))
    for ch in range(2):
        noise = rng.standard_normal(L)
        # darker tail: smooth noise progressively
        ir[:, ch] = noise * np.exp(-6.9 * t / seconds)
    from scipy.signal import lfilter
    a = np.exp(-2 * np.pi * 2500 / SR)
    ir = lfilter([1 - a], [1, -a], ir, axis=0)
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    wet = np.stack([fftconvolve(x[:, ch], ir[:, ch])[: len(x)] for ch in range(2)], axis=1)
    wet *= np.abs(x).max() / (np.abs(wet).max() + 1e-9)
    return (1 - mix) * x + mix * wet


if __name__ == "__main__":
    main(float(sys.argv[1]), sys.argv[2])
