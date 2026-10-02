# Bàn giao công việc – phim hoạt hình "Nhà Mình Vui Trung Thu"

Repo: `binhvi1989/movies`, nhánh `claude/nice-albattani-meimmt` (mọi thứ đã commit và push).

## Trạng thái hiện tại

- Phim hoàn chỉnh dài 3:54, 1280x720, 24fps: `output/nam_anh_em_nha_minh_vais1000.mp4` (47 MB) và bản nén nhẹ
  `output/nam_anh_em_nha_minh_vais1000_nhe.mp4` (21 MB, dùng để gửi qua chat).
- Nhân vật là đúng 7 chân dung người dùng cung cấp (`assets/refs/`), tách nền thành `assets/cutouts/`, rồi dựng
  thành rối khớp (đầu, thân, 2 tay, 2 chân) với tay chân vung khi đi, tư thế theo lời thoại, mắt chớp, khẩu hình.
- Kịch bản 14 cảnh, 98 câu, mỗi nhân vật một giọng (cùng mô hình, đổi cao độ), người dẫn chuyện, phụ đề màu.
- Toàn bộ dựng offline: Python + Pillow + numpy + sherpa-onnx (Piper VITS) + ffmpeg. Không dùng dịch vụ mạng.

## Lịch sử các phiên bản đã làm

1. Nhân vật vẽ thủ công bằng Pillow, thuyết minh một giọng (~3 phút).
2. Lồng tiếng từng nhân vật, kịch bản nhiều hành động hơn.
3. Người dùng gửi 7 chân dung + tính cách mới (thêm Muội, Eric) -> tách nền, nhân vật cắt dán 2.5D, kịch bản Trung thu múa lân.
4. (hiện tại) Rối khớp: tay chân/mặt/miệng cử động, thêm trò gây cười.

## Cách dựng lại

```bash
pip install -r requirements.txt       # cần ffmpeg sẵn trong máy
scripts/download_models.sh            # tải mô hình giọng từ GitHub releases của sherpa-onnx (~100 MB)
python3 src/cutout.py                 # chỉ khi đổi ảnh trong assets/refs
./build.sh                            # ~6-8 phút với 4 CPU -> output/nam_anh_em_nha_minh_vais1000.mp4
```

Xem nhanh khung hình mẫu từng cảnh (không mã hoá video): `python3 src/render.py --timeline build/vais1000/timeline.json --preview build/preview`

Thử tư thế rối: `python3 src/puppet.py` (xuất ảnh vào thư mục scratchpad; sửa đường dẫn trong `__main__` nếu cần).

## Sửa ở đâu

| Muốn đổi | Sửa file |
|----------|----------|
| Lời thoại, thứ tự cảnh, ai nói | `src/story.py` (mỗi câu có khoá `key` để biên đạo bám theo) |
| Chuyển động, tư thế, đạo cụ, hiệu ứng từng cảnh | `src/scenes.py` (hàm `sc_<tên cảnh>`; dùng `kid()`, `walk()`, `jump()`, `.set("pose", [...])`) |
| Tư thế mới, khớp, vị trí mắt/miệng | `src/puppet.py` (bảng `RIGS` toạ độ tỉ lệ 0..1, bảng `POSES` góc tay) |
| Giọng từng nhân vật (cao độ, tốc độ) | `src/tts.py` bảng `CHARACTER_VOICES`; cách đọc tên trong `READ_AS` |
| Nhạc nền, hiệu ứng âm thanh | `src/audio.py` (`music_loop`, `sfx`) |
| Phông nền | `src/backgrounds.py` |
| Đạo cụ vẽ (đầu lân, trống, quạt, lồng đèn, bánh, râu...) | `src/characters.py` hàm `prop()` |
| Khoảng nghỉ giữa câu, kéo dài cuối cảnh | `src/timeline.py` |

## Hạn chế đã biết / việc có thể làm tiếp

- Không có phần mềm 3D thật: chuyển động là rối khớp 2.5D. Muốn 3D thật phải làm ngoài (Blender) với mô hình riêng.
- Giọng đọc: mô hình offline `vais1000` rõ nhất nhưng không chắc là giọng miền Nam; mô hình `vivos` (kho ghi âm TP.HCM)
  nghe kém rõ. Tên "Puka", "Kaka" máy đọc chưa chuẩn (đã thay cách đọc "Bu ca", "Ca ca").
- Tay Kaka trong ảnh gốc khoanh trước ngực nên được dựng lại thành tay buông; chỗ áo bị tay che được vá lại, còn hơi lộ dải màu.
- Kích thước MP4 chất lượng cao vượt giới hạn gửi tệp của chat (khoảng 25-30 MB); dùng bản `_nhe` để gửi.
- Ý tưởng tiếp: thêm nháy mắt theo nhịp nhạc, mí mắt/lông mày biểu cảm, tay cầm đạo cụ bám theo bàn tay thật,
  chuyển cảnh mượt (crossfade), nhạc nền riêng cho đoạn múa lân.
