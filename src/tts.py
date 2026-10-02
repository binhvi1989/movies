# -*- coding: utf-8 -*-
"""Tạo giọng thuyết minh tiếng Việt (offline) bằng Piper VITS qua sherpa-onnx.

Cách dùng:
    python3 src/tts.py --voice vais1000 --out build/voice_vais1000
    python3 src/tts.py --voice vivos    --out build/voice_vivos

Kết quả: mỗi câu thuyết minh một file WAV + `lines.json` (thời lượng từng câu).
Các mô hình giọng được tải về thư mục `models/` (xem scripts/download_models.sh).
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
    # tên -> (thư mục mô hình, tên file onnx, speaker id, tốc độ)
    "vais1000": ("vits-piper-vi_VN-vais1000-medium", "vi_VN-vais1000-medium", 0, 0.88),
    "vivos": ("vits-piper-vi_VN-vivos-x_low", "vi_VN-vivos-x_low", 4, 1.0),
    "25hours": ("vits-piper-vi_VN-25hours_single-low", "vi_VN-25hours_single-low", 0, 0.92),
}

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


def trim_silence(x, sr, thresh=0.01, pad=0.08):
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="vais1000", choices=list(VOICES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed", type=float, default=None)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    tts, sid, speed = load_tts(args.voice)
    if args.speed:
        speed = args.speed
    meta = []
    for s in SCENES:
        for i, line in enumerate(s["lines"]):
            a = tts.generate(speakable(line), sid=sid, speed=speed)
            x = np.asarray(a.samples, dtype=np.float32)
            x = trim_silence(x, a.sample_rate)
            # chuẩn hoá biên độ
            peak = float(np.max(np.abs(x))) or 1.0
            x = x * (0.85 / peak)
            fn = f"{s['id']}_{i:02d}.wav"
            sf.write(os.path.join(args.out, fn), x, a.sample_rate)
            meta.append(dict(scene=s["id"], idx=i, text=line, file=fn, dur=len(x) / a.sample_rate, sr=a.sample_rate))
            print(f"{fn}: {len(x) / a.sample_rate:5.2f}s  {line}")
    json.dump(meta, open(os.path.join(args.out, "lines.json"), "w"), ensure_ascii=False, indent=1)
    total = sum(m["dur"] for m in meta)
    print(f"Tổng thời lượng thuyết minh: {total:.1f}s ({len(meta)} câu)")


if __name__ == "__main__":
    main()
