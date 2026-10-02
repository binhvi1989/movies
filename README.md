# Nhà Mình Vui Trung Thu

Phim hoạt hình ngắn (~4 phút) cho trẻ em về một gia đình sáu anh em và chú cún Lu chuẩn bị múa lân
Trung thu. Nhân vật là **đúng chân dung do người dùng cung cấp** (assets/refs), được tách nền (assets/cutouts)
rồi dựng thành **rối khớp** (src/puppet.py): đầu, thân, hai tay, hai chân tách riêng với khớp xoay ở cổ, vai, hông;
tay chân tự vung khi đi, tay giơ/vẫy/che mặt theo tư thế, mắt chớp, miệng mở theo lời nói, đầu nghiêng, bóng đổ mềm,
camera phóng gần. Chuyển động có chiều sâu kiểu 2.5D (không phải mô hình 3D thật).
Có người dẫn chuyện, lồng tiếng riêng từng nhân vật (giọng nam/nữ phân biệt bằng cao độ), biểu cảm vẽ thêm
(khóc, giận, toát mồ hôi, tim, nốt nhạc) và phụ đề màu theo người nói. Toàn bộ dựng offline bằng Python + Pillow + ffmpeg.

## Nhân vật

| Tên | Vai vế | Tính cách |
|-----|--------|-----------|
| **Kaka** | anh Hai | nghịch ngợm, siêu lì, mê múa lân, cầm đầu lân |
| **Puka** | chị Ba | nghịch ngợm, siêu quậy |
| **Moon** | em (lớn tuổi nhất nhà) | ham học, lo cho cả đám, đánh trống |
| **Sam** | chị Tư | siêu lì, điệu đà, nhí nhảnh, làm đuôi lân |
| **Muội** | chị Năm | thích ăn, giành đồ chơi, hay chọc Eric |
| **Eric** | em Út | siêu quậy, mít ướt, làm Ông Địa |
| **Lu** | cún cưng | ham chơi, biếng ăn, hay đòi đi theo |

## Lồng tiếng

Tất cả giọng sinh từ cùng một mô hình, rồi đổi cao độ và nhịp nói cho từng nhân vật
(bảng `CHARACTER_VOICES` trong `src/tts.py`): Kaka hơi cao và lanh lợi, Puka the thé, Moon dịu,
Sam lí lắc, Lu "gâu gâu" cao vút, Má trầm hơn người dẫn chuyện; câu của "cả nhà" là ba giọng chồng lên nhau.
Bong bóng thoại và cử động miệng được render tự động cho người đang nói.

## Kết quả

- `output/nam_anh_em_nha_minh_vais1000.mp4` – bản chính (giọng rõ nhất, mô hình `vais1000`, chất lượng medium).
- `output/nam_anh_em_nha_minh_vivos.mp4` – bản thay thế dùng giọng huấn luyện từ kho **VIVOS**
  (ghi âm tại TP. HCM, giọng miền Nam) nhưng mô hình chỉ ở mức x_low nên nghe kém rõ hơn.

Hai bản chỉ khác giọng đọc; hình ảnh, kịch bản, phụ đề giống nhau. Kịch bản được viết bằng
từ ngữ miền Nam (ba má, hông, nha, dữ lắm, thiệt hông…).

## Cấu trúc

```
src/story.py        kịch bản: 14 cảnh, 98 câu (dẫn chuyện + thoại từng nhân vật, có khoá thời gian)
src/cutout.py       tách nền chân dung -> assets/cutouts (ước lượng nền bậc hai, lấp lỗ, mặt nạ hình dáng cho Lu)
src/characters.py   đạo cụ vẽ bằng Pillow (đầu lân, đuôi lân, trống, quạt, mặt nạ Ông Địa, lồng đèn, bánh trung thu...)
src/backgrounds.py  phông nền: trước nhà (chiều/tối), hành lang kệ giày, phòng khách sofa xanh, phòng ngủ, sân Trung thu
src/puppet.py       rối khớp từ chân dung: tách bộ phận bằng mặt nạ màu da, khớp xoay, tư thế (wave, cheer, lion, drum, fan, cry, hold...), chớp mắt, khẩu hình
src/anim.py         bộ máy keyframe, nhân vật rối + bóng đổ + biểu cảm, bong bóng thoại, phụ đề, camera
src/scenes.py       biên đạo 14 cảnh (giới thiệu, lên kế hoạch, tập lân, giành quạt, đêm Trung thu, kết) bám theo mốc câu thoại
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
python3 src/cutout.py                 # tách nền chân dung (chỉ cần khi đổi ảnh trong assets/refs)
./build.sh                            # -> output/nam_anh_em_nha_minh_vais1000.mp4
./build.sh vivos                      # -> bản giọng VIVOS
```

Xem nhanh khung hình mẫu của từng cảnh (không mã hoá video):

```bash
python3 src/render.py --timeline build/vais1000/timeline.json --preview build/preview
```

Muốn đổi lời thoại, sửa `src/story.py`; muốn đổi chuyển động, sửa `src/scenes.py`;
muốn đổi giọng/tốc độ đọc, sửa bảng `VOICES` trong `src/tts.py`.
