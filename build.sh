#!/usr/bin/env bash
# Dựng toàn bộ phim: thuyết minh -> mốc thời gian -> khung hình -> âm thanh -> MP4.
#   ./build.sh            (giọng mặc định: vais1000)
#   ./build.sh vivos      (giọng VIVOS, kho giọng miền Nam, chất lượng thấp hơn)
set -euo pipefail
cd "$(dirname "$0")"
VOICE="${1:-vais1000}"
B="build/$VOICE"
mkdir -p "$B" output
echo "== 1/5 Thuyết minh ($VOICE)"
python3 src/tts.py --voice "$VOICE" --out "$B/voice" | tail -1
echo "== 2/5 Mốc thời gian"
python3 src/timeline.py "$B/voice" "$B/timeline.json" | tail -1
echo "== 3/5 Dựng khung hình"
python3 src/render.py --timeline "$B/timeline.json" --out "$B/segs" --jobs "${JOBS:-4}"
echo "== 4/5 Âm thanh"
python3 src/audio.py --timeline "$B/timeline.json" --voice-dir "$B/voice" --out "$B/audio.wav"
echo "== 5/5 Ghép phim"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$B/segs/list.txt" -i "$B/audio.wav" \
  -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart "output/nam_anh_em_nha_minh_${VOICE}.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "output/nam_anh_em_nha_minh_${VOICE}.mp4" | xargs printf "Xong: output/nam_anh_em_nha_minh_${VOICE}.mp4 (%.1fs)\n"
