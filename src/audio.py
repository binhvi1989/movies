# -*- coding: utf-8 -*-
"""Ghép âm thanh: thuyết minh + nhạc nền tự tổng hợp + hiệu ứng âm thanh.

    python3 src/audio.py --timeline build/timeline.json --voice-dir build/voice_vais1000 --out build/audio.wav
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
import scenes  # noqa: E402

SR = 44100


# ------------------------------------------------------------------ tiện ích
def note(freq, dur, wave="sine", a=0.01, d=0.08, s=0.6, r=0.1, vol=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if wave == "sine":
        x = np.sin(2 * np.pi * freq * t)
    elif wave == "tri":
        x = 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1
    elif wave == "soft":  # sine + ít bội âm, giống đàn gỗ/ukulele
        x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) + 0.12 * np.sin(2 * np.pi * 3 * freq * t)
        x *= np.exp(-t * 3.0)
    elif wave == "pluck":
        x = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2 * freq * t) + 0.25 * np.sin(2 * np.pi * 3 * freq * t)
        x *= np.exp(-t * 5.0)
    else:
        raise ValueError(wave)
    env = np.ones(n)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    if na:
        env[:na] = np.linspace(0, 1, na)
    if nd:
        env[na:na + nd] = np.linspace(1, s, min(nd, max(0, n - na)))
    env[na + nd:] = s
    if nr and n > nr:
        env[-nr:] *= np.linspace(1, 0, nr)
    return x * env * vol


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, x, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n]


def lowpass_fast(x, cutoff=6000.0):
    """Lọc thông thấp bằng FFT (nhanh)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X * H, n=len(x))


# ------------------------------------------------------------------ nhạc nền
BPM = 112
BEAT = 60.0 / BPM

# hợp âm theo ô nhịp (C major): C F G C | Am F G C
CHORDS = [[60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67], [57, 60, 64], [65, 69, 72], [67, 71, 74], [60, 64, 67]]
BASS = [48, 53, 55, 48, 45, 53, 55, 48]
# giai điệu 8 ô nhịp, mỗi ô 8 nốt móc đơn (None = nghỉ), số = MIDI
MELODY = [
    [72, None, 76, None, 79, None, 76, 72],
    [77, None, 81, 77, 76, None, 74, None],
    [74, None, 79, None, 83, 79, 74, None],
    [72, None, 76, 79, 84, None, None, None],
    [69, None, 72, None, 76, None, 72, 69],
    [77, 76, 74, None, 77, None, 81, None],
    [79, None, 74, 71, 67, None, 71, 74],
    [72, None, None, None, 72, 76, 79, None],
]


def music_loop(with_drums=True, soft=False):
    bars = len(CHORDS)
    dur = bars * 4 * BEAT
    buf = np.zeros(int(dur * SR) + SR)
    for b in range(bars):
        t0 = b * 4 * BEAT
        # đệm hợp âm: gảy 8 nốt móc đơn kiểu ukulele
        for k in range(8):
            tt = t0 + k * BEAT / 2
            for j, m in enumerate(CHORDS[b]):
                vol = 0.12 if soft else 0.16
                place(buf, note(midi(m), BEAT * 0.9, "pluck", a=0.003, d=0.05, s=0.5, r=0.08, vol=vol * (1.0 if k % 2 == 0 else 0.6)), tt + j * 0.012)
        # bass
        for k in (0, 2):
            place(buf, note(midi(BASS[b]), BEAT * 1.6, "tri", a=0.005, d=0.1, s=0.5, r=0.15, vol=0.22), t0 + k * BEAT)
        if not soft:
            place(buf, note(midi(BASS[b] + 7), BEAT * 0.6, "tri", a=0.005, d=0.1, s=0.5, r=0.1, vol=0.14), t0 + 3 * BEAT)
        # giai điệu
        for k, m in enumerate(MELODY[b]):
            if m is None:
                continue
            # kéo dài nốt tới nốt tiếp theo
            ln = 1
            while k + ln < 8 and MELODY[b][k + ln] is None:
                ln += 1
            place(buf, note(midi(m), BEAT / 2 * ln * 0.95, "soft", a=0.01, d=0.1, s=0.7, r=0.08, vol=0.28 if not soft else 0.2), t0 + k * BEAT / 2)
        # trống nhẹ
        if with_drums and not soft:
            for k in range(8):
                tt = t0 + k * BEAT / 2
                n = int(0.03 * SR)
                hat = np.random.RandomState(k + b * 8).randn(n) * np.exp(-np.arange(n) / (0.004 * SR)) * (0.06 if k % 2 == 0 else 0.035)
                place(buf, hat, tt)
            for k in (0, 2):
                n = int(0.15 * SR)
                t = np.arange(n) / SR
                kick = np.sin(2 * np.pi * (40 + 80 * np.exp(-t * 30)) * t) * np.exp(-t * 18) * 0.5
                place(buf, kick, t0 + k * BEAT)
            for k in (1, 3):
                n = int(0.1 * SR)
                t = np.arange(n) / SR
                sn = (np.random.RandomState(99 + k).randn(n) * 0.25 + np.sin(2 * np.pi * 180 * t) * 0.3) * np.exp(-t * 35)
                place(buf, sn, t0 + k * BEAT)
    buf = lowpass_fast(buf[: int(dur * SR)], 7000)
    return buf


def music_track(total, timeline):
    full = music_loop(True)
    soft = music_loop(False, soft=True)
    n = int(total * SR)
    out = np.zeros(n)
    reps = n // len(full) + 2
    full_t = np.tile(full, reps)[:n]
    soft_t = np.tile(soft, reps)[:n]
    # chọn bản soft trong hai cảnh cuối, chuyển mượt
    w = np.zeros(n)
    for s in timeline["scenes"]:
        if s["id"] in ("13_ending", "14_outro"):
            i0, i1 = int(s["start"] * SR), int(s["end"] * SR)
            w[i0:i1] = 1.0
    w = moving_average(w, int(1.5 * SR))
    out = full_t * (1 - w) + soft_t * w
    return out


def moving_average(x, k):
    """Trung bình trượt cửa sổ k mẫu, tính bằng cộng dồn (O(n))."""
    c = np.cumsum(np.concatenate([[0.0], x]))
    n = len(x)
    i = np.arange(n)
    lo = np.maximum(i - k // 2, 0)
    hi = np.minimum(i + k - k // 2, n)
    return (c[hi] - c[lo]) / (hi - lo)


# ------------------------------------------------------------------ hiệu ứng
def sfx(kind, tts=None):
    t = lambda d: np.arange(int(d * SR)) / SR  # noqa: E731
    if kind == "pop":
        tt = t(0.12)
        return np.sin(2 * np.pi * (500 + 700 * tt / 0.12) * tt) * np.exp(-tt * 40) * 0.5
    if kind == "ding":
        tt = t(0.9)
        return (np.sin(2 * np.pi * 1318 * tt) + 0.4 * np.sin(2 * np.pi * 2637 * tt)) * np.exp(-tt * 5) * 0.3
    if kind == "boing":
        tt = t(0.4)
        f = 380 * np.exp(-tt * 4) + 120 + 25 * np.sin(2 * np.pi * 18 * tt)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6) * 0.45
    if kind == "swoosh":
        tt = t(0.35)
        x = np.random.RandomState(1).randn(len(tt))
        env = np.sin(np.pi * tt / 0.35) ** 2
        return lowpass_fast(x, 2500) * env * 0.35
    if kind == "bark":
        out = np.zeros(int(0.45 * SR))
        for k, t0 in enumerate((0.0, 0.2)):
            tt = t(0.13)
            f = 420 - 150 * tt / 0.13
            tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.random.RandomState(k).randn(len(tt)) * 0.5
            env = np.minimum(1, tt / 0.012) * np.exp(-tt * 20)
            place(out, lowpass_fast(tone * env, 1800) * 0.6, t0)
        return out
    if kind == "sparkle":
        out = np.zeros(int(0.7 * SR))
        for k, m in enumerate((84, 88, 91, 96)):
            place(out, note(midi(m), 0.35, "sine", a=0.005, d=0.05, s=0.6, r=0.2, vol=0.2), k * 0.09)
        return out
    if kind == "yawn":
        tt = t(0.8)
        f = 260 + 120 * np.sin(np.pi * tt / 0.8)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * 2 * np.cumsum(f) / SR)) * np.sin(np.pi * tt / 0.8) * 0.25
    if kind == "laugh":
        if tts is not None:
            a = tts.generate("Ha ha ha ha!", sid=0, speed=1.25)
            x = np.asarray(a.samples, dtype=np.float32)
            return resample(x, a.sample_rate) * 0.9
        out = np.zeros(int(0.9 * SR))
        for k in range(4):
            tt = t(0.14)
            tone = np.sin(2 * np.pi * (300 - 20 * k) * tt) * np.exp(-tt * 15)
            place(out, tone * 0.3, k * 0.2)
        return out
    raise ValueError(kind)


def resample(x, sr):
    if sr == SR:
        return x
    n = int(len(x) * SR / sr)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


# ------------------------------------------------------------------ ghép
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--voice-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--music", type=float, default=0.12, help="âm lượng nhạc nền")
    ap.add_argument("--no-laugh-tts", action="store_true")
    args = ap.parse_args()
    tl = json.load(open(args.timeline))
    total = tl["total"] + 0.5
    n = int(total * SR)
    narr = np.zeros(n)
    for s in tl["scenes"]:
        for ln in s["lines"]:
            x, sr = sf.read(os.path.join(args.voice_dir, ln["file"]), dtype="float32")
            if x.ndim > 1:
                x = x.mean(axis=1)
            place(narr, resample(x, sr), ln["start"])
    # hiệu ứng
    tts = None
    if not args.no_laugh_tts:
        try:
            from tts import load_tts
            tts, _, _ = load_tts("vais1000")
        except Exception as e:  # noqa: BLE001
            print("không dùng TTS cho tiếng cười:", e)
    fx = np.zeros(n)
    cache = {}
    for s in tl["scenes"]:
        built = scenes.build(s)
        for (rel, kind) in built.get("sfx", []):
            if kind not in cache:
                cache[kind] = sfx(kind, tts)
            place(fx, cache[kind], s["start"] + rel)
    # nhạc nền + ducking theo thuyết minh
    mus = music_track(total, tl)
    env = np.abs(narr)
    env = moving_average(env, int(0.25 * SR))
    duck = 1.0 - 0.6 * np.clip(env / 0.03, 0, 1)
    mus = mus * duck
    # chuẩn hoá nhạc về RMS mục tiêu
    rms = np.sqrt(np.mean(mus ** 2)) or 1
    mus = mus / rms * args.music * 0.5
    # fade in/out
    f = int(1.0 * SR)
    mus[:f] *= np.linspace(0, 1, f)
    mus[-f:] *= np.linspace(1, 0, f)
    mix = narr * 0.95 + fx * 0.55 + mus
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix = mix / peak * 0.98
    st = np.stack([mix, mix], axis=1)
    sf.write(args.out, st.astype(np.float32), SR, subtype="PCM_16")
    print(f"đã ghi {args.out}: {total:.1f}s, đỉnh {np.max(np.abs(mix)):.2f}")


if __name__ == "__main__":
    main()
