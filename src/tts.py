# -*- coding: utf-8 -*-
"""Tạo giọng thuyết minh và lồng tiếng từng nhân vật (offline, Piper VITS qua sherpa-onnx).

    python3 src/tts.py --voice vais1000 --out build/vais1000/voice

Mỗi nhân vật dùng cùng mô hình giọng nhưng được đổi cao độ (pitch) và tốc độ:
    - sinh âm thanh chậm hơn p lần, rồi phát nhanh lên p lần -> cao độ tăng p lần, nhịp nói giữ nguyên.
Giọng "all" (cả nhà) là ba giọng cao độ khác nhau chồng lên nhau.
Kết quả: mỗi câu một file WAV + lines.json (ai nói, lời, thời lượng).
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
from story import SCENES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models")

VOICES = {
    # tên -> (thư mục mô hình, tên file onnx, speaker id, tốc độ nền)
    "vais1000": ("vits-piper-vi_VN-vais1000-medium", "vi_VN-vais1000-medium", 0, 0.88),
    "vivos": ("vits-piper-vi_VN-vivos-x_low", "vi_VN-vivos-x_low", 4, 1.0),
    "25hours": ("vits-piper-vi_VN-25hours_single-low", "vi_VN-25hours_single-low", 0, 0.92),
}

# Giọng từng nhân vật: (hệ số cao độ, hệ số tốc độ so với tốc độ nền)
CHARACTER_VOICES = {
    "nar": (1.00, 1.00),
    "ma": (0.92, 1.00),
    "kaka": (1.08, 1.05),
    "puka": (1.24, 1.00),
    "moon": (1.14, 0.97),
    "sam": (1.20, 1.03),
    "lu": (1.45, 1.20),
}
ALL_VOICES = [(1.08, 1.02), (1.18, 1.02), (1.24, 1.02)]

# Tên nhân vật viết theo cách đọc tiếng Việt để máy đọc đúng
READ_AS = [
    (r"\bKaka\b", "Ca ca"),
    (r"\bPuka\b", "Bu ca"),
    (r"\bMoon\b", "Mun"),
    (r"\bSam\b", "Sam"),
    (r"\bLu\b", "Lu"),
]


def speakable(text):
    for pat, rep in READ_AS:
        text = re.sub(pat, rep, text)
    return text


def load_tts(voice):
    import sherpa_onnx

    folder, model, sid, speed = VOICES[voice]
    d = os.path.join(MODELS, folder)
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=os.path.join(d, f"{model}.onnx"),
                tokens=os.path.join(d, "tokens.txt"),
                data_dir=os.path.join(d, "espeak-ng-data"),
            ),
            num_threads=4,
        )
    )
    return sherpa_onnx.OfflineTts(cfg), sid, speed


def trim_silence(x, sr, thresh=0.01, pad=0.06):
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def pitch_shift(x, p):
    """Phát nhanh lên p lần (cao độ tăng p lần, ngắn lại p lần)."""
    if abs(p - 1.0) < 1e-3:
        return x
    n = int(len(x) / p)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def synth(tts, sid, base_speed, text, who):
    text = speakable(text)
    if who == "all":
        parts = []
        for p, sp in ALL_VOICES:
            a = tts.generate(text, sid=sid, speed=base_speed * sp / p)
            parts.append(pitch_shift(np.asarray(a.samples, dtype=np.float32), p))
        n = max(len(q) for q in parts)
        x = np.zeros(n, dtype=np.float32)
        for k, q in enumerate(parts):
            off = k * int(0.015 * a.sample_rate)  # lệch nhẹ cho giống nhiều người nói
            m = min(len(q), n - off)
            x[off:off + m] += q[:m] / len(parts)
        return x, a.sample_rate
    p, sp = CHARACTER_VOICES[who]
    a = tts.generate(text, sid=sid, speed=base_speed * sp / p)
    return pitch_shift(np.asarray(a.samples, dtype=np.float32), p), a.sample_rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="vais1000", choices=list(VOICES))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    tts, sid, base_speed = load_tts(args.voice)
    meta = []
    for s in SCENES:
        for i, line in enumerate(s["lines"]):
            x, sr = synth(tts, sid, base_speed, line["text"], line["who"])
            x = trim_silence(x, sr)
            peak = float(np.max(np.abs(x))) or 1.0
            x = x * (0.85 / peak)
            fn = f"{s['id']}_{i:02d}.wav"
            sf.write(os.path.join(args.out, fn), x, sr)
            meta.append(dict(scene=s["id"], idx=i, who=line["who"], key=line["key"], text=line["text"], file=fn, dur=len(x) / sr, sr=sr))
            print(f"{fn}: {len(x) / sr:5.2f}s  [{line['who']}] {line['text']}")
    json.dump(meta, open(os.path.join(args.out, "lines.json"), "w"), ensure_ascii=False, indent=1)
    total = sum(m["dur"] for m in meta)
    print(f"Tổng thời lượng lời: {total:.1f}s ({len(meta)} câu)")


if __name__ == "__main__":
    main()
