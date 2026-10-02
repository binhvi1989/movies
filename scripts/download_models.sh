#!/usr/bin/env bash
# Tải các mô hình giọng đọc tiếng Việt (Piper VITS, chạy offline qua sherpa-onnx) vào thư mục models/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p models
BASE="https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models"
for m in vits-piper-vi_VN-vais1000-medium vits-piper-vi_VN-vivos-x_low; do
  if [ ! -d "models/$m" ]; then
    echo "Tải $m ..."
    curl -sS -L -o "models/$m.tar.bz2" "$BASE/$m.tar.bz2"
    tar xjf "models/$m.tar.bz2" -C models && rm "models/$m.tar.bz2"
  fi
done
echo "Xong. Mô hình nằm trong models/"
