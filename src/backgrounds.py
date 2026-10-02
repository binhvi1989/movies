# -*- coding: utf-8 -*-
"""Các phông nền (background) của phim, vẽ bằng Pillow ở tỉ lệ 2x rồi thu nhỏ."""
import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
SS = 2
OUT = (60, 45, 45)


def _grad(img, top, bottom, y0=0, y1=None):
    """Tô dải màu dọc từ top -> bottom vào vùng [y0,y1)."""
    d = ImageDraw.Draw(img)
    y1 = img.height if y1 is None else y1
    n = max(1, y1 - y0)
    for y in range(y0, y1):
        f = (y - y0) / n
        c = tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3))
        d.line([0, y, img.width, y], fill=c)


def _wood_floor(d, w, y0, y1, base=(178, 98, 62), seed=1):
    """Sàn gỗ màu nâu đỏ với vân gỗ và khe ván."""
    rnd = random.Random(seed)
    d.rectangle([0, y0, w, y1], fill=base)
    plank_h = (y1 - y0) / 7
    for i in range(7):
        y = y0 + i * plank_h
        shade = rnd.uniform(0.9, 1.08)
        c = tuple(min(255, int(v * shade)) for v in base)
        d.rectangle([0, y, w, y + plank_h], fill=c)
        # vân gỗ
        for _ in range(6):
            x0 = rnd.uniform(-200, w)
            yy = y + rnd.uniform(plank_h * 0.15, plank_h * 0.85)
            d.line([x0, yy, x0 + rnd.uniform(200, 600), yy + rnd.uniform(-4, 4)], fill=tuple(int(v * 0.85) for v in c), width=2)
        d.line([0, y, w, y], fill=tuple(int(v * 0.7) for v in base), width=3)
        # khe ngang so le
        off = rnd.uniform(0, w)
        for k in range(4):
            x = (off + k * w / 3.2) % w
            d.line([x, y, x, y + plank_h], fill=tuple(int(v * 0.7) for v in base), width=3)


def _shutter_wall(d, x0, x1, y0, y1, base=(226, 222, 210)):
    """Tường/cửa cuốn kim loại màu kem, gân dọc."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    rib = 34
    x = x0
    dark = tuple(int(v * 0.86) for v in base)
    light = tuple(min(255, int(v * 1.05)) for v in base)
    while x < x1:
        d.rectangle([x, y0, x + rib * 0.45, y1], fill=light)
        d.line([x + rib * 0.5, y0, x + rib * 0.5, y1], fill=dark, width=5)
        x += rib


def _accordion_gate(d, x0, x1, y0, y1, color=(190, 185, 170)):
    """Cửa xếp kéo kim loại dạng lưới chéo."""
    dark = tuple(int(v * 0.75) for v in color)
    step = 50
    for x in range(int(x0), int(x1), step):
        d.line([x, y0, x + step, y1 * 0.0 + y0 + (y1 - y0)], fill=dark, width=5)
        d.line([x + step, y0, x, y1], fill=dark, width=5)
    for x in range(int(x0), int(x1) + 1, step):
        d.line([x, y0, x, y1], fill=color, width=8)


def _shoe_rack(d, x, y, w, h, seed=3):
    """Kệ giày 4 tầng với giày dép nhiều màu."""
    rnd = random.Random(seed)
    frame = (120, 125, 130)
    for s in (0, 1):
        d.rectangle([x + s * (w - 14), y, x + s * (w - 14) + 14, y + h], fill=frame, outline=OUT, width=3)
    tiers = 4
    th = h / tiers
    cols = [(60, 60, 70), (230, 230, 230), (40, 70, 150), (220, 60, 70), (250, 200, 80), (100, 160, 90), (255, 140, 180), (120, 120, 120)]
    for i in range(tiers):
        yy = y + i * th + th * 0.85
        d.rectangle([x, yy, x + w, yy + 10], fill=frame, outline=OUT, width=3)
        # giày
        n = 3
        for k in range(n):
            sx = x + 20 + k * (w - 40) / n
            c = rnd.choice(cols)
            sw = (w - 40) / n - 14
            d.rounded_rectangle([sx, yy - th * 0.42, sx + sw, yy - 2], radius=14, fill=c, outline=OUT, width=3)
            d.rounded_rectangle([sx + sw * 0.1, yy - th * 0.42, sx + sw * 0.75, yy - th * 0.22], radius=10, fill=tuple(min(255, int(v * 1.2) + 20) for v in c), outline=OUT, width=2)


def _coat_hooks(d, x, y, w):
    """Móc treo đồ bằng gỗ với áo khoác và mũ bảo hiểm hồng."""
    wood = (190, 140, 80)
    d.rectangle([x, y, x + w, y + 16], fill=wood, outline=OUT, width=3)
    for i in range(4):
        hx = x + 30 + i * (w - 60) / 3
        d.polygon([(hx - 20, y + 16), (hx + 20, y + 16), (hx, y + 60)], fill=wood, outline=OUT)
    # áo khoác vàng nhạt
    hx = x + 30
    d.rounded_rectangle([hx - 45, y + 50, hx + 45, y + 330], radius=30, fill=(245, 235, 180), outline=OUT, width=3)
    # túi nilon trắng
    hx = x + 30 + (w - 60) / 3
    d.ellipse([hx - 55, y + 60, hx + 55, y + 260], fill=(240, 240, 245), outline=OUT, width=3)
    d.ellipse([hx - 30, y + 90, hx + 25, y + 180], fill=(250, 120, 140))
    # mũ bảo hiểm hồng
    hx = x + 30 + 2 * (w - 60) / 3
    d.pieslice([hx - 60, y + 60, hx + 60, y + 190], 180, 360, fill=(250, 160, 190), outline=OUT, width=3)
    d.rectangle([hx - 60, y + 125, hx + 60, y + 140], fill=(250, 160, 190), outline=OUT, width=3)
    # áo khoác đen sọc
    hx = x + 30 + 3 * (w - 60) / 3
    d.rounded_rectangle([hx - 50, y + 50, hx + 50, y + 320], radius=30, fill=(45, 45, 55), outline=OUT, width=3)
    for k in range(6):
        d.line([hx - 50, y + 90 + k * 36, hx + 50, y + 90 + k * 36], fill=(220, 220, 220), width=6)


def _wall_panel(d, w, y0, y1):
    """Ốp tường gỗ nâu đỏ (phòng khách)."""
    base = (190, 110, 60)
    d.rectangle([0, y0, w, y1], fill=base)
    rnd = random.Random(9)
    for _ in range(60):
        x = rnd.uniform(0, w)
        yy = rnd.uniform(y0, y1)
        d.line([x, yy, x + rnd.uniform(-20, 20), yy + rnd.uniform(60, 200)], fill=(170, 95, 50), width=3)
    d.rectangle([0, y0, w, y0 + 20], fill=(160, 85, 45), outline=OUT, width=3)


def _sofa(d, x, y, w, h, color=(28, 120, 80)):
    """Ghế sofa xanh lá, nệm vuông."""
    dark = tuple(int(v * 0.75) for v in color)
    light = tuple(min(255, int(v * 1.15)) for v in color)
    # lưng ghế
    d.rounded_rectangle([x, y, x + w, y + h * 0.55], radius=30, fill=color, outline=OUT, width=4)
    for k in range(1, 3):
        d.line([x + w * k / 3, y + 15, x + w * k / 3, y + h * 0.5], fill=dark, width=5)
    # nệm ngồi
    d.rounded_rectangle([x - 20, y + h * 0.5, x + w + 20, y + h], radius=30, fill=light, outline=OUT, width=4)
    for k in range(1, 3):
        d.line([x + w * k / 3, y + h * 0.55, x + w * k / 3, y + h * 0.95], fill=dark, width=5)
    d.line([x - 10, y + h * 0.72, x + w + 10, y + h * 0.72], fill=dark, width=4)


def _coffee_table(d, x, y, w, h):
    wood = (165, 85, 40)
    top = (200, 120, 60)
    d.polygon([(x, y), (x + w, y), (x + w * 1.1, y + h * 0.35), (x - w * 0.1, y + h * 0.35)], fill=top, outline=OUT)
    d.rectangle([x - w * 0.1, y + h * 0.35, x + w * 1.1, y + h * 0.55], fill=wood, outline=OUT, width=3)
    d.rectangle([x - w * 0.02, y + h * 0.55, x + w * 0.06, y + h], fill=wood, outline=OUT, width=3)
    d.rectangle([x + w * 0.94, y + h * 0.55, x + w * 1.02, y + h], fill=wood, outline=OUT, width=3)
    # viền vàng
    d.polygon([(x + w * 0.08, y + h * 0.05), (x + w * 0.92, y + h * 0.05), (x + w * 1.0, y + h * 0.3), (x, y + h * 0.3)], outline=(240, 200, 110))


def _tree(d, x, y, s, leaf=(60, 130, 70)):
    d.rectangle([x - s * 0.08, y - s * 0.6, x + s * 0.08, y], fill=(110, 70, 40), outline=OUT, width=3)
    for (dx, dy, r) in ((0, -0.9, 0.42), (-0.3, -0.7, 0.32), (0.3, -0.72, 0.33), (0, -0.55, 0.3)):
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s], fill=leaf, outline=OUT, width=3)


def _house_front(d, x, y, w, h, night=False):
    """Mặt tiền nhà: mái tôn, tường kem, cửa xếp mở, ánh đèn ấm bên trong."""
    wall = (225, 222, 210)
    d.rectangle([x, y, x + w, y + h], fill=wall, outline=OUT, width=4)
    # mái tôn
    d.polygon([(x - 30, y), (x + w + 30, y), (x + w + 10, y - h * 0.18), (x - 10, y - h * 0.18)], fill=(160, 165, 170), outline=OUT)
    for k in range(1, 14):
        xx = x - 10 + k * (w + 20) / 14
        d.line([xx, y - h * 0.18 + 4, xx + 14, y - 3], fill=(120, 125, 130), width=4)
    # cửa chính (mở) thấy bên trong sáng
    dx0, dx1 = x + w * 0.3, x + w * 0.7
    inner = (255, 235, 170) if night else (250, 240, 215)
    d.rectangle([dx0, y + h * 0.15, dx1, y + h], fill=inner, outline=OUT, width=4)
    _wood_floor(d, 0, y + h * 0.78, y + h, seed=4) if False else None
    d.rectangle([dx0 + 4, y + h * 0.78, dx1 - 4, y + h - 4], fill=(178, 98, 62))
    # cửa xếp hai bên
    _accordion_gate(d, x + w * 0.05, dx0, y + h * 0.15, y + h)
    _accordion_gate(d, dx1, x + w * 0.95, y + h * 0.15, y + h)
    # bảng số nhà
    d.rectangle([x + w * 0.45, y + h * 0.04, x + w * 0.55, y + h * 0.12], fill=(40, 90, 170), outline=OUT, width=3)


@lru_cache(maxsize=8)
def background(kind):
    img = Image.new("RGB", (W * SS, H * SS))
    d = ImageDraw.Draw(img)
    w, h = W * SS, H * SS
    if kind in ("exterior", "exterior_night"):
        night = kind == "exterior_night"
        if night:
            _grad(img, (20, 25, 70), (70, 50, 110), 0, int(h * 0.62))
            rnd = random.Random(2)
            for _ in range(80):
                x, y = rnd.uniform(0, w), rnd.uniform(0, h * 0.45)
                r = rnd.uniform(2, 5)
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
            d.ellipse([w * 0.78, h * 0.08, w * 0.78 + 160, h * 0.08 + 160], fill=(255, 245, 200), outline=OUT, width=4)
            d.ellipse([w * 0.78 + 40, h * 0.08 - 20, w * 0.78 + 190, h * 0.08 + 130], fill=(20, 25, 70))
        else:
            _grad(img, (250, 150, 90), (255, 215, 150), 0, int(h * 0.62))
            d.ellipse([w * 0.12, h * 0.22, w * 0.12 + 170, h * 0.22 + 170], fill=(255, 240, 180), outline=(250, 200, 120), width=6)
            for cx, cy, r in ((w * 0.3, h * 0.12, 90), (w * 0.37, h * 0.1, 120), (w * 0.44, h * 0.13, 80), (w * 0.62, h * 0.2, 70), (w * 0.67, h * 0.18, 95)):
                d.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], fill=(255, 235, 215))
        # nhà hàng xóm xa
        far = (90, 80, 120) if night else (190, 160, 175)
        for i, (x0, hh) in enumerate(((0, 0.25), (w * 0.1, 0.32), (w * 0.75, 0.3), (w * 0.9, 0.22))):
            d.rectangle([x0, h * 0.62 - h * hh, x0 + w * 0.14, h * 0.62], fill=far, outline=OUT, width=3)
            for r in range(2):
                for c in range(2):
                    wx = x0 + w * 0.03 + c * w * 0.06
                    wy = h * 0.62 - h * hh + h * 0.05 + r * h * 0.09
                    d.rectangle([wx, wy, wx + w * 0.035, wy + h * 0.05], fill=(255, 230, 140) if night else (220, 235, 250), outline=OUT, width=2)
        # đường
        d.rectangle([0, h * 0.62, w, h], fill=(95, 95, 105) if night else (130, 130, 140))
        d.rectangle([0, h * 0.62, w, h * 0.66], fill=(170, 170, 160) if not night else (120, 120, 120), outline=OUT, width=3)
        for k in range(8):
            d.rectangle([k * w / 8 + 20, h * 0.85, k * w / 8 + w / 16, h * 0.87], fill=(240, 230, 150))
        # nhà chính
        _house_front(d, w * 0.27, h * 0.2, w * 0.46, h * 0.42, night)
        _tree(d, w * 0.14, h * 0.63, 260)
        _tree(d, w * 0.86, h * 0.63, 220)
        # đèn đường
        d.rectangle([w * 0.8 - 8, h * 0.25, w * 0.8 + 8, h * 0.64], fill=(80, 80, 90), outline=OUT, width=2)
        d.ellipse([w * 0.8 - 40, h * 0.2, w * 0.8 + 40, h * 0.28], fill=(255, 240, 170), outline=OUT, width=3)
        if night:
            glow = Image.new("RGB", img.size, (0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gd.ellipse([w * 0.8 - 300, h * 0.2 - 100, w * 0.8 + 300, h * 0.75], fill=(60, 55, 20))
            glow = glow.filter(ImageFilter.GaussianBlur(80))
            img = Image.blend(img, Image.eval(img, lambda v: v), 0)
            from PIL import ImageChops
            img = ImageChops.add(img, glow)
    elif kind == "hall":
        # trần/tường: cửa cuốn kem gân dọc, bên trái cửa mở ra ngoài
        _shutter_wall(d, 0, w, 0, h * 0.72)
        # khung cửa mở nhìn ra đường buổi chiều
        d.rectangle([w * 0.03, h * 0.08, w * 0.3, h * 0.72], fill=(120, 110, 150), outline=OUT, width=6)
        _grad(img, (250, 160, 100), (255, 220, 170), int(h * 0.08), int(h * 0.42))
        d.rectangle([0, int(h * 0.08), int(w * 0.03) - 1, int(h * 0.42)], fill=(226, 222, 210))
        d.rectangle([int(w * 0.3) + 1, int(h * 0.08), w, int(h * 0.42)], fill=(226, 222, 210))
        _shutter_wall(d, 0, w * 0.03, 0, h * 0.72)
        _shutter_wall(d, w * 0.3, w, 0, h * 0.72)
        d.rectangle([w * 0.03, h * 0.42, w * 0.3, h * 0.72], fill=(130, 130, 140))
        _tree(d, w * 0.1, h * 0.46, 150)
        _tree(d, w * 0.24, h * 0.45, 120)
        d.rectangle([w * 0.03, h * 0.08, w * 0.3, h * 0.72], outline=OUT, width=6)
        _accordion_gate(d, w * 0.03, w * 0.12, h * 0.08, h * 0.72)
        # trần tôn
        d.rectangle([0, 0, w, h * 0.06], fill=(180, 185, 190), outline=OUT, width=3)
        for k in range(1, 30):
            d.line([k * w / 30, 0, k * w / 30, h * 0.06], fill=(140, 145, 150), width=3)
        _wood_floor(d, w, h * 0.72, h)
        _coat_hooks(d, w * 0.72, h * 0.12, w * 0.24)
        _shoe_rack(d, w * 0.76, h * 0.42, w * 0.2, h * 0.31)
        # vài đôi dép trên sàn gần cửa
        rnd = random.Random(5)
        for k in range(6):
            sx = w * 0.04 + k * w * 0.045
            sy = h * 0.72 + rnd.uniform(10, 50)
            c = rnd.choice([(60, 60, 70), (230, 230, 230), (40, 70, 150), (220, 60, 70), (100, 160, 90)])
            d.rounded_rectangle([sx, sy, sx + 44, sy + 24], radius=10, fill=c, outline=OUT, width=3)
    elif kind == "living":
        # tường trên kem, ốp gỗ dưới, sofa xanh, bàn gỗ
        _grad(img, (245, 242, 232), (236, 230, 215), 0, int(h * 0.34))
        for k in range(0, w, 60):
            d.line([k, 0, k, h * 0.34], fill=(232, 228, 216), width=2)
        _wall_panel(d, w, h * 0.34, h * 0.68)
        _wood_floor(d, w, h * 0.68, h)
        _sofa(d, w * 0.08, h * 0.44, w * 0.5, h * 0.4)
        _coffee_table(d, w * 0.66, h * 0.6, w * 0.26, h * 0.28)
        # khung tranh nhỏ
        d.rectangle([w * 0.75, h * 0.08, w * 0.9, h * 0.26], fill=(80, 60, 50), outline=OUT, width=4)
        d.rectangle([w * 0.765, h * 0.095, w * 0.885, h * 0.245], fill=(150, 200, 240))
        d.ellipse([w * 0.78, h * 0.11, w * 0.81, h * 0.14], fill=(255, 230, 120))
        d.polygon([(w * 0.765, h * 0.245), (w * 0.82, h * 0.16), (w * 0.885, h * 0.245)], fill=(90, 150, 90))
    elif kind == "bedroom":
        _grad(img, (200, 225, 250), (225, 238, 252), 0, int(h * 0.66))
        # cửa sổ
        d.rectangle([w * 0.6, h * 0.1, w * 0.86, h * 0.45], fill=(255, 225, 160), outline=OUT, width=5)
        d.line([w * 0.73, h * 0.1, w * 0.73, h * 0.45], fill=OUT, width=5)
        d.line([w * 0.6, h * 0.27, w * 0.86, h * 0.27], fill=OUT, width=5)
        d.ellipse([w * 0.63, h * 0.13, w * 0.70, h * 0.23], fill=(255, 250, 200))
        d.rectangle([w * 0.58, h * 0.07, w * 0.64, h * 0.47], fill=(250, 170, 190), outline=OUT, width=3)
        d.rectangle([w * 0.84, h * 0.07, w * 0.9, h * 0.47], fill=(250, 170, 190), outline=OUT, width=3)
        # tủ đồ
        d.rectangle([w * 0.9, h * 0.15, w * 0.995, h * 0.66], fill=(200, 150, 100), outline=OUT, width=4)
        d.line([w * 0.9475, h * 0.17, w * 0.9475, h * 0.64], fill=OUT, width=3)
        _wood_floor(d, w, h * 0.66, h)
        # giường
        bx, by, bw, bh = w * 0.1, h * 0.46, w * 0.42, h * 0.26
        d.rectangle([bx - 20, by - h * 0.14, bx + 10, by + bh], fill=(140, 95, 60), outline=OUT, width=4)  # đầu giường
        d.rectangle([bx, by, bx + bw, by + bh], fill=(255, 250, 240), outline=OUT, width=4)
        d.rounded_rectangle([bx + 20, by + 30, bx + bw - 10, by + bh - 10], radius=30, fill=(120, 170, 240), outline=OUT, width=4)
        for k in range(5):
            d.ellipse([bx + 60 + k * 70, by + 70, bx + 95 + k * 70, by + 105], fill=(255, 255, 255))
        d.rounded_rectangle([bx + 15, by - 20, bx + 130, by + 40], radius=20, fill=(255, 255, 255), outline=OUT, width=4)
        # chân giường (khoảng trống gầm giường)
        d.rectangle([bx, by + bh, bx + bw, by + bh + 40], fill=(120, 80, 50), outline=OUT, width=4)
        # thảm tròn
        d.ellipse([w * 0.55, h * 0.74, w * 0.9, h * 0.95], fill=(240, 200, 120), outline=OUT, width=4)
        d.ellipse([w * 0.6, h * 0.77, w * 0.85, h * 0.92], fill=(250, 225, 160), outline=OUT, width=3)
    else:
        raise ValueError(kind)
    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    import os
    out = "/tmp/claude-0/-home-user-movies/4eb93384-7854-5b1d-b894-3192c5ee23bc/scratchpad"
    sheet = Image.new("RGB", (W * 2, H * 3))
    for i, k in enumerate(("exterior", "hall", "living", "bedroom", "exterior_night")):
        sheet.paste(background(k), ((i % 2) * W, (i // 2) * H))
    sheet.resize((W, int(H * 1.5))).save(os.path.join(out, "bg_test.png"))
    print("ok")
