# Năm Anh Em Nhà Mình

Phim hoạt hình ngắn (~3 phút) cho trẻ em về tình anh em trong gia đình, có thuyết minh tiếng Việt
và phụ đề. Toàn bộ hình ảnh, chuyển động, nhạc nền và hiệu ứng âm thanh được dựng bằng mã nguồn
trong thư mục này (Python + Pillow + ffmpeg), giọng đọc tạo offline bằng mô hình Piper VITS.

## Nhân vật

| Tên | Vai vế | Tính cách | Tạo hình |
|-----|--------|-----------|----------|
| **Kaka** | anh Hai, lớn nhất nhà | ham chơi, hài hước, lì lợm, thương em | tóc ngắn, áo xám loang đá có khóa kéo ở vai, quần short xám |
| **Puka** | chị Ba | bướng bỉnh, nghịch ngợm, lười đi học | tóc rối bù, áo thun hồng in hình bé đeo kính và chữ THINGW |
| **Moon** | em (nhưng lớn tuổi nhất nhà) | ham học, thích chăm các em | tóc cột đuôi ngựa, bộ đồ bông sát nách màu kem hồng |
| **Sam** | em Út | điệu đà, nghịch ngợm, lười học, hài hước | tóc dài, bộ đồ ngủ hồng in mặt hoạt hình, túi bèo |
| **Lu** | cún cưng | biếng ăn, ham chơi, hay chạy theo anh chị | poodle lông xoăn màu nâu |

## Kết quả

- `output/nam_anh_em_nha_minh_vais1000.mp4` – bản chính (giọng rõ nhất, mô hình `vais1000`, chất lượng medium).
- `output/nam_anh_em_nha_minh_vivos.mp4` – bản thay thế dùng giọng huấn luyện từ kho **VIVOS**
  (ghi âm tại TP. HCM, giọng miền Nam) nhưng mô hình chỉ ở mức x_low nên nghe kém rõ hơn.

Hai bản chỉ khác giọng đọc; hình ảnh, kịch bản, phụ đề giống nhau. Kịch bản được viết bằng
từ ngữ miền Nam (ba má, hông, nha, dữ lắm, thiệt hông…).

## Cấu trúc

```
src/story.py        kịch bản: 14 cảnh, 46 câu thuyết minh
src/characters.py   vẽ 5 nhân vật (nhiều tư thế / biểu cảm) và đạo cụ
src/backgrounds.py  5 phông nền: trước nhà (chiều/tối), hành lang kệ giày, phòng khách sofa xanh, phòng ngủ
src/anim.py         bộ máy keyframe, bong bóng thoại, chữ hiệu ứng, phụ đề, camera
src/scenes.py       biên đạo từng cảnh (ai đi đâu, làm gì, nói gì, hiệu ứng gì)
src/tts.py          tạo giọng thuyết minh offline (sherpa-onnx + Piper)
src/timeline.py     tính mốc thời gian theo độ dài từng câu
src/render.py       dựng khung hình 1280x720 @ 24fps, mã hoá H.264
src/audio.py        ghép thuyết minh + nhạc nền tự tổng hợp + hiệu ứng (gâu gâu, bịch, ting…)
build.sh            chạy toàn bộ quy trình
scripts/download_models.sh  tải mô hình giọng đọc
```

## Dựng lại phim

```bash
pip install -r requirements.txt       # cần sẵn ffmpeg
scripts/download_models.sh            # tải mô hình giọng (~100 MB)
./build.sh                            # -> output/nam_anh_em_nha_minh_vais1000.mp4
./build.sh vivos                      # -> bản giọng VIVOS
```

Xem nhanh khung hình mẫu của từng cảnh (không mã hoá video):

```bash
python3 src/render.py --timeline build/vais1000/timeline.json --preview build/preview
```

Muốn đổi lời thoại, sửa `src/story.py`; muốn đổi chuyển động, sửa `src/scenes.py`;
muốn đổi giọng/tốc độ đọc, sửa bảng `VOICES` trong `src/tts.py`.
