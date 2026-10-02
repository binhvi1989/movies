# -*- coding: utf-8 -*-
"""Vẽ các nhân vật hoạt hình (Kaka, Puka, Moon, Sam, Lu) bằng Pillow.

Mỗi nhân vật được vẽ ở độ phân giải gấp đôi (SS = 2) rồi thu nhỏ để có nét mượt.
Hàm `sprite()` trả về ảnh RGBA, điểm neo là *giữa bàn chân* (đáy ảnh, giữa ảnh).
"""
import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw

SS = 2  # supersampling
OUT = (40, 30, 30)  # màu viền
LW = 5  # độ dày viền (ở tỉ lệ 1x)

# ---------------------------------------------------------------- màu sắc
SKIN = {"tan": (242, 196, 160), "light": (250, 214, 184)}
HAIR_BLACK = (38, 30, 32)
HAIR_DARK = (55, 42, 40)

SPECS = {
    "puka": dict(
        skin=SKIN["tan"], hair="messy", hair_color=HAIR_BLACK, height=0.80,
        shirt=(247, 170, 190), shirt_style="puka", shorts=(247, 170, 190), shorts_len=0.55,
        sleeve="wide", girl=True, cheeks=True,
    ),
    "kaka": dict(
        skin=SKIN["tan"], hair="boy", hair_color=HAIR_BLACK, height=0.90,
        shirt=(150, 142, 138), shirt_style="kaka", shorts=(140, 132, 128), shorts_len=0.70,
        sleeve="normal", girl=False, cheeks=False,
    ),
    "moon": dict(
        skin=SKIN["light"], hair="ponytail", hair_color=HAIR_DARK, height=1.00,
        shirt=(252, 232, 232), shirt_style="moon", shorts=(252, 232, 232), shorts_len=0.5,
        sleeve="none", girl=True, cheeks=True,
    ),
    "sam": dict(
        skin=SKIN["tan"], hair="long", hair_color=HAIR_BLACK, height=0.95,
        shirt=(246, 110, 170), shirt_style="sam", shorts=(246, 110, 170), shorts_len=0.6,
        sleeve="puff", girl=True, cheeks=True,
    ),
}

# kích thước cơ sở (đơn vị px ở tỉ lệ 1x, nhân vật cao ~ 5 R)
R = 58  # bán kính đầu


def _ell(d, cx, cy, rx, ry, fill, outline=OUT, w=LW):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline, width=w * SS if outline else 0)


def _rrect(d, box, r, fill, outline=OUT, w=LW):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w * SS if outline else 0)


def _poly(d, pts, fill, outline=OUT, w=LW):
    d.polygon(pts, fill=fill)
    if outline:
        d.line(list(pts) + [pts[0]], fill=outline, width=w * SS, joint="curve")


def _limb(d, p0, p1, thick, fill, outline=OUT):
    """Chi (tay/chân) dạng ống bo tròn hai đầu."""
    x0, y0 = p0
    x1, y1 = p1
    if outline:
        d.line([p0, p1], fill=outline, width=int(thick + 2 * LW * SS))
        for (x, y) in (p0, p1):
            r = (thick + 2 * LW * SS) / 2
            d.ellipse([x - r, y - r, x + r, y + r], fill=outline)
    d.line([p0, p1], fill=fill, width=int(thick))
    for (x, y) in (p0, p1):
        r = thick / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def _darken(c, f=0.75):
    return tuple(int(v * f) for v in c)


def _lighten(c, f=0.25):
    return tuple(int(v + (255 - v) * f) for v in c)


# ------------------------------------------------------------- khuôn mặt
def _face(d, cx, cy, r, spec, expr, look=0.0):
    """Vẽ mắt, miệng, má, lông mày. expr: smile|grin|laugh|talk|pout|sad|wide|sleepy|wink|angry|smirk|o"""
    eye_y = cy + r * 0.05
    ex = r * 0.38
    er = r * 0.17
    ox = look * r * 0.06
    eyes = expr
    # --- mắt
    for side in (-1, 1):
        x = cx + side * ex
        if expr in ("laugh", "wink" if side == 1 else "", "sleepy_closed"):
            # mắt cười cong
            d.arc([x - er * 1.1, eye_y - er, x + er * 1.1, eye_y + er * 0.9], 200, 340, fill=OUT, width=LW * SS)
        elif expr == "sleepy":
            d.ellipse([x - er, eye_y - er, x + er, eye_y + er], fill=(255, 255, 255), outline=OUT, width=LW * SS)
            d.ellipse([x - er * 0.5 + ox, eye_y - er * 0.1, x + er * 0.5 + ox, eye_y + er * 0.9], fill=OUT)
            d.rectangle([x - er - 2, eye_y - er - 2, x + er + 2, eye_y - er * 0.15], fill=spec["skin"])
            d.line([x - er, eye_y - er * 0.15, x + er, eye_y - er * 0.15], fill=OUT, width=LW * SS)
        elif expr == "wide":
            d.ellipse([x - er * 1.3, eye_y - er * 1.4, x + er * 1.3, eye_y + er * 1.3], fill=(255, 255, 255), outline=OUT, width=LW * SS)
            d.ellipse([x - er * 0.7 + ox, eye_y - er * 0.7, x + er * 0.7 + ox, eye_y + er * 0.7], fill=OUT)
            d.ellipse([x - er * 0.15 + ox, eye_y - er * 0.5, x + er * 0.25 + ox, eye_y - er * 0.1], fill=(255, 255, 255))
        else:
            d.ellipse([x - er, eye_y - er * 1.1, x + er, eye_y + er * 1.1], fill=(255, 255, 255), outline=OUT, width=LW * SS)
            d.ellipse([x - er * 0.6 + ox, eye_y - er * 0.55, x + er * 0.6 + ox, eye_y + er * 0.7], fill=OUT)
            d.ellipse([x - er * 0.1 + ox, eye_y - er * 0.45, x + er * 0.3 + ox, eye_y - er * 0.05], fill=(255, 255, 255))
    # --- lông mày
    by = eye_y - er * 1.9
    bw = er * 1.2
    if expr == "angry" or expr == "grin":
        for side in (-1, 1):
            x = cx + side * ex
            d.line([x - side * bw, by - er * 0.1, x + side * bw * 0.2, by + er * 0.5], fill=OUT, width=LW * SS)
    elif expr == "smirk":
        d.line([cx - ex - bw, by + er * 0.3, cx - ex + bw * 0.3, by - er * 0.6], fill=OUT, width=LW * SS)
        d.line([cx + ex - bw * 0.3, by + er * 0.1, cx + ex + bw, by + er * 0.3], fill=OUT, width=LW * SS)
    elif expr in ("sad", "pout"):
        for side in (-1, 1):
            x = cx + side * ex
            d.line([x - side * bw * 0.2, by - er * 0.2, x + side * bw, by + er * 0.4], fill=OUT, width=LW * SS)
    elif expr == "wide":
        for side in (-1, 1):
            x = cx + side * ex
            d.arc([x - bw, by - er * 0.9, x + bw, by + er * 0.6], 200, 340, fill=OUT, width=LW * SS)
    # --- má hồng
    if spec.get("cheeks") or expr in ("laugh", "grin"):
        for side in (-1, 1):
            x = cx + side * r * 0.62
            d.ellipse([x - r * 0.13, cy + r * 0.32, x + r * 0.13, cy + r * 0.48], fill=(250, 170, 170))
    # --- miệng
    my = cy + r * 0.5
    mw = r * 0.28
    if expr in ("smile", "sleepy", "wink"):
        d.arc([cx - mw, my - mw * 0.9, cx + mw, my + mw * 0.5], 15, 165, fill=OUT, width=LW * SS)
    elif expr == "smirk":
        d.arc([cx - mw * 1.2, my - mw * 0.6, cx + mw * 0.6, my + mw * 0.5], 20, 150, fill=OUT, width=LW * SS)
    elif expr == "grin":
        d.rounded_rectangle([cx - mw * 1.3, my - mw * 0.4, cx + mw * 1.3, my + mw * 0.55], radius=int(mw * 0.4),
                            fill=(255, 255, 255), outline=OUT, width=LW * SS)
        for i in range(1, 6):
            x = cx - mw * 1.3 + i * mw * 2.6 / 6
            d.line([x, my - mw * 0.4, x, my + mw * 0.55], fill=OUT, width=max(2, LW * SS // 2))
        d.line([cx - mw * 1.3, my + mw * 0.08, cx + mw * 1.3, my + mw * 0.08], fill=OUT, width=max(2, LW * SS // 2))
    elif expr in ("laugh", "talk"):
        h = mw * (1.3 if expr == "laugh" else 0.9)
        d.chord([cx - mw * 1.1, my - h * 0.7, cx + mw * 1.1, my + h], 0, 180, fill=(120, 40, 50), outline=OUT, width=LW * SS)
        d.chord([cx - mw * 0.7, my + h * 0.25, cx + mw * 0.7, my + h * 1.0], 180, 360, fill=(240, 110, 120))
    elif expr == "o" or expr == "wide":
        d.ellipse([cx - mw * 0.55, my - mw * 0.5, cx + mw * 0.55, my + mw * 0.7], fill=(120, 40, 50), outline=OUT, width=LW * SS)
    elif expr in ("pout", "angry"):
        d.arc([cx - mw, my, cx + mw, my + mw * 1.4], 200, 340, fill=OUT, width=LW * SS)
    elif expr == "sad":
        d.arc([cx - mw, my, cx + mw, my + mw * 1.4], 200, 340, fill=OUT, width=LW * SS)
        # giọt nước mắt
        d.ellipse([cx + ex + er * 0.6, eye_y + er * 1.2, cx + ex + er * 1.2, eye_y + er * 2.2], fill=(140, 200, 250), outline=OUT, width=max(2, LW * SS // 2))
    else:
        d.line([cx - mw * 0.7, my, cx + mw * 0.7, my], fill=OUT, width=LW * SS)


# ------------------------------------------------------------------- tóc
def _hair_back(d, cx, cy, r, spec):
    hc = spec["hair_color"]
    st = spec["hair"]
    if st == "messy":
        _ell(d, cx, cy - r * 0.05, r * 1.08, r * 1.08, hc)
        rnd = random.Random(7)
        for i in range(10):
            a = math.radians(200 + i * 14 + rnd.uniform(-5, 5))
            L = r * rnd.uniform(1.15, 1.45)
            x0, y0 = cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9
            x1, y1 = cx + math.cos(a) * L, cy + math.sin(a) * L - r * 0.1
            _limb(d, (x0, y0), (x1, y1), r * 0.16, hc)
        # tóc buộc lệch hai bên
        _ell(d, cx - r * 1.05, cy + r * 0.55, r * 0.26, r * 0.42, hc)
        _ell(d, cx + r * 1.05, cy + r * 0.5, r * 0.26, r * 0.42, hc)
    elif st == "boy":
        _ell(d, cx, cy - r * 0.08, r * 1.06, r * 1.04, hc)
    elif st == "ponytail":
        _ell(d, cx, cy - r * 0.05, r * 1.06, r * 1.06, hc)
        # đuôi tóc sau lưng (bên phải)
        _limb(d, (cx + r * 0.7, cy + r * 0.2), (cx + r * 0.95, cy + r * 1.7), r * 0.42, hc)
        _ell(d, cx + r * 0.95, cy + r * 1.75, r * 0.3, r * 0.3, hc)
    elif st == "long":
        _ell(d, cx, cy - r * 0.05, r * 1.08, r * 1.08, hc)
        # tóc dài hai bên xuống vai
        _rrect(d, [cx - r * 1.12, cy - r * 0.2, cx - r * 0.55, cy + r * 1.9], int(r * 0.3), hc)
        _rrect(d, [cx + r * 0.55, cy - r * 0.2, cx + r * 1.12, cy + r * 1.9], int(r * 0.3), hc)


def _hair_front(d, cx, cy, r, spec):
    hc = spec["hair_color"]
    st = spec["hair"]
    top = cy - r
    if st == "messy":
        # mái lởm chởm che trán
        pts = [(cx - r * 1.02, cy - r * 0.15)]
        rnd = random.Random(3)
        n = 9
        for i in range(n + 1):
            x = cx - r * 1.0 + i * (2.0 * r / n)
            y = cy - r * 0.05 + rnd.uniform(-0.22, 0.22) * r
            pts.append((x, y))
        pts += [(cx + r * 1.02, cy - r * 0.15), (cx + r * 0.9, top - r * 0.05), (cx, top - r * 0.12), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)
        # kẹp sao vàng
        _ell(d, cx + r * 0.55, cy - r * 0.55, r * 0.09, r * 0.09, (255, 210, 60), outline=OUT, w=2)
    elif st == "boy":
        pts = [(cx - r * 1.0, cy - r * 0.35), (cx - r * 0.7, cy - r * 0.55), (cx - r * 0.3, cy - r * 0.4),
               (cx + r * 0.05, cy - r * 0.62), (cx + r * 0.45, cy - r * 0.38), (cx + r * 0.8, cy - r * 0.72),
               (cx + r * 1.0, cy - r * 0.3), (cx + r * 0.9, top - r * 0.05), (cx, top - r * 0.1), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)
    elif st == "ponytail":
        # tóc vuốt ngược, chẻ nhẹ: chỉ để lộ trán cao
        pts = [(cx - r * 1.02, cy - r * 0.3), (cx - r * 0.6, cy - r * 0.78), (cx, cy - r * 0.88),
               (cx + r * 0.6, cy - r * 0.78), (cx + r * 1.02, cy - r * 0.3), (cx + r * 0.9, top - r * 0.05),
               (cx, top - r * 0.1), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)
    elif st == "long":
        pts = [(cx - r * 1.04, cy - r * 0.1), (cx - r * 0.75, cy - r * 0.35), (cx - r * 0.35, cy - r * 0.2),
               (cx - r * 0.1, cy - r * 0.75), (cx + r * 0.3, cy - r * 0.3), (cx + r * 0.75, cy - r * 0.4),
               (cx + r * 1.04, cy - r * 0.1), (cx + r * 0.9, top - r * 0.05), (cx, top - r * 0.1), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)


# ---------------------------------------------------------------- trang phục
def _shirt_print(d, spec, box):
    """Hoa văn áo. box = (x0,y0,x1,y1) phần thân áo."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = x1 - x0, y1 - y0
    st = spec["shirt_style"]
    rnd = random.Random(11)
    if st == "puka":
        # bé gái đeo kính + chữ THINGW
        hr = w * 0.13
        hy = cy - h * 0.12
        _ell(d, cx, hy, hr * 1.25, hr * 1.15, HAIR_BLACK, w=2)
        _ell(d, cx, hy + hr * 0.15, hr, hr * 0.95, (250, 225, 200), w=2)
        for s in (-1, 1):
            d.ellipse([cx + s * hr * 0.45 - hr * 0.3, hy + hr * 0.05, cx + s * hr * 0.45 + hr * 0.3, hy + hr * 0.6], outline=OUT, width=2 * SS)
            d.ellipse([cx + s * hr * 0.45 - hr * 0.1, hy + hr * 0.25, cx + s * hr * 0.45 + hr * 0.1, hy + hr * 0.42], fill=OUT)
        d.arc([cx - hr * 0.25, hy + hr * 0.4, cx + hr * 0.25, hy + hr * 0.8], 10, 170, fill=OUT, width=2 * SS)
        _text(d, (cx, cy + h * 0.27), "THINGW", int(w * 0.17), (30, 30, 30), bold=True)
    elif st == "kaka":
        # áo loang màu đá + khóa kéo vai + chữ UMO
        for _ in range(26):
            px, py = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
            rr = rnd.uniform(w * 0.05, w * 0.16)
            c = _darken(spec["shirt"], rnd.uniform(0.7, 0.9)) if rnd.random() < 0.6 else _lighten(spec["shirt"], 0.25)
            d.ellipse([px - rr, py - rr * 0.6, px + rr, py + rr * 0.6], fill=c)
        _text(d, (cx, cy - h * 0.02), "UMO", int(w * 0.24), (245, 245, 245), bold=True)
    elif st == "moon":
        # họa tiết hoa nhỏ
        cols = [(250, 190, 90), (240, 120, 140), (150, 200, 90), (120, 170, 240)]
        for _ in range(28):
            px, py = rnd.uniform(x0 + w * 0.08, x1 - w * 0.08), rnd.uniform(y0 + h * 0.2, y1 - h * 0.08)
            c = rnd.choice(cols)
            rr = w * 0.03
            for k in range(5):
                a = k * 2 * math.pi / 5
                d.ellipse([px + math.cos(a) * rr - rr * 0.6, py + math.sin(a) * rr - rr * 0.6, px + math.cos(a) * rr + rr * 0.6, py + math.sin(a) * rr + rr * 0.6], fill=c)
            d.ellipse([px - rr * 0.5, py - rr * 0.5, px + rr * 0.5, py + rr * 0.5], fill=(255, 240, 150))
        # bèo ngực
        yy = y0 + h * 0.22
        d.line([(x0 + w * 0.12 + i * w * 0.76 / 12, yy + (i % 2) * h * 0.04) for i in range(13)], fill=(230, 150, 170), width=3 * SS, joint="curve")
    elif st == "sam":
        # mặt hoạt hình nhỏ trên nền hồng
        cols = [(255, 255, 255), (110, 190, 250), (255, 230, 90), (60, 60, 70), (160, 230, 120)]
        for _ in range(22):
            px, py = rnd.uniform(x0 + w * 0.1, x1 - w * 0.1), rnd.uniform(y0 + h * 0.12, y1 - h * 0.1)
            rr = w * 0.055
            c = rnd.choice(cols)
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=c, outline=_darken(c, 0.6), width=max(1, SS))
            ec = (30, 30, 30) if c != (60, 60, 70) else (255, 255, 255)
            d.ellipse([px - rr * 0.45, py - rr * 0.25, px - rr * 0.15, py + rr * 0.05], fill=ec)
            d.ellipse([px + rr * 0.15, py - rr * 0.25, px + rr * 0.45, py + rr * 0.05], fill=ec)
        # túi bèo
        for s in (-1, 1):
            px = cx + s * w * 0.27
            py = y1 - h * 0.22
            _rrect(d, [px - w * 0.14, py - h * 0.1, px + w * 0.14, py + h * 0.12], int(w * 0.04), spec["shirt"], w=2)
            d.line([(px - w * 0.14 + i * w * 0.28 / 8, py - h * 0.1 + (i % 2) * h * 0.03) for i in range(9)], fill=(255, 255, 255), width=3 * SS, joint="curve")


_FONT_CACHE = {}


def _font(size, bold=True):
    key = (size, bold)
    if key not in _FONT_CACHE:
        from PIL import ImageFont
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        _FONT_CACHE[key] = ImageFont.truetype(path, max(6, int(size)))
    return _FONT_CACHE[key]


def _text(d, pos, s, size, fill, bold=True):
    f = _font(size, bold)
    d.text(pos, s, font=f, fill=fill, anchor="mm")


# ------------------------------------------------------------------ nhân vật
POSES = ("stand", "walk", "cheer", "claws", "crossed", "hold", "sit", "point", "hug", "monkey", "lie", "pull")
EXPRS = ("smile", "grin", "laugh", "talk", "pout", "sad", "wide", "sleepy", "wink", "angry", "smirk", "o", "flat")


@lru_cache(maxsize=4096)
def sprite(name, pose="stand", expr="smile", phase=0.0, flip=False, look=0.0):
    """Trả về ảnh RGBA nhân vật ở tỉ lệ 1x, neo giữa bàn chân (đáy, giữa)."""
    spec = SPECS[name]
    r = R * SS
    hf = spec["height"]
    # kích thước canvas (2x)
    W, H = int(r * 5.0), int(r * 6.2)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W / 2
    foot_y = H - r * 0.1
    leg_len = r * 1.35 * hf
    body_h = r * 1.55 * hf
    hip_y = foot_y - leg_len
    shoulder_y = hip_y - body_h
    head_cy = shoulder_y - r * 0.95
    body_w = r * 1.35 if spec["shirt_style"] in ("puka", "kaka") else r * 1.15
    skin = spec["skin"]
    leg_th = r * 0.42
    arm_th = r * 0.36

    sitting = pose in ("sit", "lie")
    if sitting:
        # ngồi: chân gập về trước, mông ở foot_y - r*0.6
        hip_y = foot_y - r * 0.75
        shoulder_y = hip_y - body_h
        head_cy = shoulder_y - r * 0.95

    # ----- tóc sau
    _hair_back(d, cx, head_cy, r, spec)

    # ----- chân
    sw = 0.0
    if pose == "walk":
        sw = math.sin(phase * 2 * math.pi)
    if sitting:
        for s in (-1, 1):
            kx = cx + s * r * 0.35
            _limb(d, (kx, hip_y), (kx + s * r * 0.15, foot_y - r * 0.5), leg_th, skin)
            _limb(d, (kx + s * r * 0.15, foot_y - r * 0.5), (kx + s * r * 0.3, foot_y - r * 0.15), leg_th, skin)
            # bàn chân
            _ell(d, kx + s * r * 0.45, foot_y - r * 0.05, r * 0.27, r * 0.17, skin)
    else:
        for s in (-1, 1):
            kx = cx + s * r * 0.32
            dx = s * sw * r * 0.35 if pose == "walk" else 0
            lift = (max(0, s * sw) * r * 0.25) if pose == "walk" else 0
            if pose == "monkey":
                dx = s * r * 0.35
                lift = r * 0.1 if s > 0 else 0
            _limb(d, (kx, hip_y), (kx + dx, foot_y - r * 0.12 - lift), leg_th, skin)
            _ell(d, kx + dx, foot_y - r * 0.1 - lift, r * 0.3, r * 0.17, skin)

    # ----- quần short
    sl = spec["shorts_len"]
    q_top = hip_y - r * 0.25
    q_bot = hip_y + r * (0.3 + 0.5 * sl)
    if sitting:
        q_bot = hip_y + r * 0.45
    _rrect(d, [cx - body_w * 0.62, q_top, cx + body_w * 0.62, q_bot], int(r * 0.2), spec["shorts"])
    if spec["shirt_style"] == "kaka":
        _text(d, (cx + body_w * 0.15, q_bot - r * 0.3), "STREET", int(r * 0.17), (70, 70, 70))
    if spec["shirt_style"] == "moon" or spec["shirt_style"] == "sam":
        # bèo ống quần
        d.line([(cx - body_w * 0.6 + i * body_w * 1.2 / 10, q_bot + (i % 2) * r * 0.06) for i in range(11)], fill=_darken(spec["shorts"], 0.85), width=3 * SS, joint="curve")

    # ----- thân áo
    sh_w = body_w
    bx0, by0, bx1, by1 = cx - sh_w * 0.65, shoulder_y - r * 0.1, cx + sh_w * 0.65, hip_y + r * 0.22
    if spec["shirt_style"] == "puka":
        by1 = hip_y + r * 0.4  # áo rộng dài
        bx0, bx1 = cx - sh_w * 0.72, cx + sh_w * 0.72
    _rrect(d, [bx0, by0, bx1, by1], int(r * 0.28), spec["shirt"])
    _shirt_print(d, spec, (bx0, by0, bx1, by1))
    # cổ áo
    d.chord([cx - r * 0.38, by0 - r * 0.18, cx + r * 0.38, by0 + r * 0.22], 0, 180, fill=skin, outline=OUT, width=LW * SS)
    if spec["shirt_style"] == "sam":
        # hàng nút
        for i in range(3):
            _ell(d, cx, by0 + r * 0.35 + i * r * 0.22, r * 0.06, r * 0.06, (255, 240, 240), w=2)
    if spec["shirt_style"] == "moon":
        # dây chuyền
        d.arc([cx - r * 0.22, by0 - r * 0.1, cx + r * 0.22, by0 + r * 0.22], 10, 170, fill=(230, 200, 120), width=2 * SS)

    # ----- tay
    sh_y = shoulder_y + r * 0.12
    def arm(side, elbow, hand, hand_item=None):
        sx = cx + side * sh_w * 0.55
        # tay áo
        if spec["sleeve"] != "none":
            sl_len = r * 0.55 if spec["sleeve"] == "wide" else r * 0.42
            ex_, ey_ = elbow
            ux, uy = ex_ - sx, ey_ - sh_y
            L = math.hypot(ux, uy) or 1
            ux, uy = ux / L, uy / L
            th = arm_th * (1.9 if spec["sleeve"] == "wide" else 1.6)
            if spec["sleeve"] == "puff":
                _ell(d, sx + ux * r * 0.18, sh_y + uy * r * 0.18, r * 0.27, r * 0.27, spec["shirt"])
            else:
                _limb(d, (sx, sh_y), (sx + ux * sl_len, sh_y + uy * sl_len), th, spec["shirt"])
        _limb(d, (sx, sh_y), elbow, arm_th, skin)
        _limb(d, elbow, hand, arm_th, skin)
        # vai áo đè lên
        if spec["sleeve"] != "none":
            sl_len = r * 0.55 if spec["sleeve"] == "wide" else r * 0.42
            ex_, ey_ = elbow
            ux, uy = ex_ - sx, ey_ - sh_y
            L = math.hypot(ux, uy) or 1
            ux, uy = ux / L, uy / L
            th = arm_th * (1.9 if spec["sleeve"] == "wide" else 1.6)
            if spec["sleeve"] == "puff":
                _ell(d, sx + ux * r * 0.18, sh_y + uy * r * 0.18, r * 0.27, r * 0.27, spec["shirt"])
            else:
                _limb(d, (sx, sh_y), (sx + ux * sl_len, sh_y + uy * sl_len), th, spec["shirt"])
            if spec["shirt_style"] == "kaka":
                # khóa kéo bạc trên vai
                d.line([(sx - side * r * 0.1, sh_y - r * 0.28), (sx + ux * r * 0.45, sh_y + uy * r * 0.45 - r * 0.1)], fill=(215, 215, 220), width=3 * SS)
                d.line([(sx - side * r * 0.1, sh_y - r * 0.28), (sx + ux * r * 0.45, sh_y + uy * r * 0.45 - r * 0.1)], fill=(120, 120, 125), width=1 * SS)
        hx, hy = hand
        _ell(d, hx, hy, r * 0.24, r * 0.24, skin)

    if pose == "stand" or pose == "walk":
        for s in (-1, 1):
            swing = (math.sin(phase * 2 * math.pi) * s * r * 0.35) if pose == "walk" else 0
            arm(s, (cx + s * sh_w * 0.72 + swing * 0.5, sh_y + r * 0.7), (cx + s * sh_w * 0.78 + swing, sh_y + r * 1.35))
    elif pose == "cheer":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.95, sh_y - r * 0.3), (cx + s * sh_w * 1.05, sh_y - r * 1.05))
    elif pose == "claws":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 1.0, sh_y + r * 0.35), (cx + s * sh_w * 1.15, sh_y - r * 0.35))
    elif pose == "crossed":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.8, sh_y + r * 0.75), (cx - s * sh_w * 0.45, sh_y + r * 0.7))
    elif pose == "hold":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.8, sh_y + r * 0.6), (cx + s * sh_w * 0.3, sh_y + r * 0.95))
    elif pose == "sit":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.75, sh_y + r * 0.6), (cx + s * sh_w * 0.55, sh_y + r * 1.15))
    elif pose == "lie":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.8, sh_y + r * 0.5), (cx + s * sh_w * 0.35, sh_y + r * 0.9))
    elif pose == "point":
        arm(-1, (cx - sh_w * 0.72, sh_y + r * 0.7), (cx - sh_w * 0.78, sh_y + r * 1.35))
        arm(1, (cx + sh_w * 1.0, sh_y + r * 0.2), (cx + sh_w * 1.7, sh_y - r * 0.1))
    elif pose == "hug":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.95, sh_y + r * 0.3), (cx + s * sh_w * 1.35, sh_y + r * 0.5))
    elif pose == "monkey":
        arm(-1, (cx - sh_w * 1.05, sh_y + r * 0.6), (cx - sh_w * 1.2, sh_y + r * 1.4))
        arm(1, (cx + sh_w * 1.0, sh_y - r * 0.2), (cx + sh_w * 0.6, sh_y - r * 0.9))
    elif pose == "pull":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.6 + sh_w * 0.4, sh_y + r * 0.5), (cx + sh_w * 1.15, sh_y + r * 0.6))

    # ----- đầu
    _ell(d, cx, head_cy, r, r * 0.98, skin)
    # tai
    for s in (-1, 1):
        _ell(d, cx + s * r * 0.98, head_cy + r * 0.12, r * 0.16, r * 0.2, skin)
    _face(d, cx, head_cy, r, spec, expr, look)
    _hair_front(d, cx, head_cy, r, spec)

    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img = img.resize((W // SS, H // SS), Image.LANCZOS)
    return img


# ------------------------------------------------------------------ cún Lu
LU_BROWN = (150, 92, 55)
LU_DARK = (110, 65, 38)


def _curls(d, cx, cy, rx, ry, color, seed=1, n=26, k=0.3):
    rnd = random.Random(seed)
    _ell(d, cx, cy, rx, ry, color)
    for i in range(n):
        a = i * 2 * math.pi / n
        px, py = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        rr = rx * k * rnd.uniform(0.7, 1.2)
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=color, outline=OUT, width=LW * SS)
    _ell(d, cx, cy, rx, ry, color, outline=None)
    # vài vòng xoăn bên trong
    for i in range(n // 2):
        px, py = cx + rnd.uniform(-rx * 0.7, rx * 0.7), cy + rnd.uniform(-ry * 0.7, ry * 0.7)
        rr = rx * 0.14
        d.arc([px - rr, py - rr, px + rr, py + rr], rnd.uniform(0, 360), rnd.uniform(0, 360) + 200, fill=LU_DARK, width=2 * SS)


@lru_cache(maxsize=512)
def lu(pose="sit", expr="smile", phase=0.0, flip=False, item=None):
    """Cún Lu: pose sit|run|stand|lie ; item None|teddy."""
    r = R * SS * 0.62
    W, H = int(r * 6.5), int(r * 4.8)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W / 2
    foot_y = H - r * 0.1
    if pose == "sit":
        body_cx, body_cy = cx, foot_y - r * 1.25
        _curls(d, body_cx, body_cy, r * 1.3, r * 1.25, LU_BROWN, seed=2)
        # chân trước
        for s in (-1, 1):
            _limb(d, (body_cx + s * r * 0.45, body_cy + r * 0.5), (body_cx + s * r * 0.55, foot_y - r * 0.2), r * 0.45, LU_BROWN)
            _ell(d, body_cx + s * r * 0.6, foot_y - r * 0.15, r * 0.35, r * 0.22, LU_BROWN)
        head_cx, head_cy = cx, foot_y - r * 3.0
    elif pose == "lie":
        body_cx, body_cy = cx, foot_y - r * 0.75
        _curls(d, body_cx, body_cy, r * 1.9, r * 0.8, LU_BROWN, seed=2)
        for s in (-1, 1):
            _ell(d, body_cx + s * r * 1.4, foot_y - r * 0.25, r * 0.4, r * 0.25, LU_BROWN)
        head_cx, head_cy = cx - r * 1.7, foot_y - r * 1.5
    else:  # run / stand
        sw = math.sin(phase * 2 * math.pi) if pose == "run" else 0
        body_cx, body_cy = cx, foot_y - r * 1.45
        _curls(d, body_cx, body_cy, r * 1.7, r * 0.95, LU_BROWN, seed=2)
        for i, s in enumerate((-1, 1)):
            for j, f in enumerate((-1, 1)):
                px = body_cx + f * r * 1.0
                dx = sw * r * 0.45 * (1 if (i + j) % 2 else -1)
                _limb(d, (px, body_cy + r * 0.4), (px + dx, foot_y - r * 0.2), r * 0.42, LU_BROWN)
                _ell(d, px + dx, foot_y - r * 0.15, r * 0.3, r * 0.2, LU_BROWN)
        head_cx, head_cy = cx - r * 1.9, foot_y - r * 2.6
        # đuôi
        _ell(d, body_cx + r * 1.85, body_cy - r * 0.6 - sw * r * 0.2, r * 0.35, r * 0.35, LU_BROWN)
    if pose == "sit":
        _ell(d, body_cx + r * 1.2, body_cy + r * 0.3, r * 0.35, r * 0.35, LU_BROWN)
    # đầu
    _curls(d, head_cx, head_cy, r * 1.05, r * 0.95, LU_BROWN, seed=5, n=18, k=0.28)
    # tai rũ
    for s in (-1, 1):
        _curls(d, head_cx + s * r * 1.05, head_cy + r * 0.45, r * 0.42, r * 0.75, LU_BROWN, seed=8 + s, n=10, k=0.35)
    # mõm
    _ell(d, head_cx, head_cy + r * 0.45, r * 0.55, r * 0.42, (175, 120, 80))
    _ell(d, head_cx, head_cy + r * 0.3, r * 0.22, r * 0.17, (30, 25, 25))
    # mắt
    for s in (-1, 1):
        ex = head_cx + s * r * 0.42
        ey = head_cy - r * 0.15
        if expr == "laugh":
            d.arc([ex - r * 0.18, ey - r * 0.15, ex + r * 0.18, ey + r * 0.15], 200, 340, fill=OUT, width=LW * SS)
        else:
            _ell(d, ex, ey, r * 0.17, r * 0.17, (255, 255, 255), w=2)
            _ell(d, ex + r * 0.03, ey + r * 0.02, r * 0.1, r * 0.1, OUT, outline=None)
    # miệng / lưỡi
    my = head_cy + r * 0.62
    if item == "teddy":
        teddy(d, head_cx + r * 0.1, my + r * 0.3, r * 0.75)
    elif expr in ("laugh", "tongue"):
        d.chord([head_cx - r * 0.3, my - r * 0.1, head_cx + r * 0.3, my + r * 0.35], 0, 180, fill=(120, 40, 50), outline=OUT, width=2 * SS)
        _ell(d, head_cx, my + r * 0.35, r * 0.14, r * 0.22, (250, 120, 140), w=2)
    else:
        d.arc([head_cx - r * 0.25, my - r * 0.2, head_cx + r * 0.25, my + r * 0.1], 0, 180, fill=OUT, width=2 * SS)
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img.resize((W // SS, H // SS), Image.LANCZOS)


# ------------------------------------------------------------------- đạo cụ
def teddy(d, cx, cy, r):
    """Gấu bông nâu nhạt có nơ đỏ, tâm ở giữa thân."""
    c = (205, 160, 110)
    c2 = (235, 205, 165)
    for s in (-1, 1):
        _ell(d, cx + s * r * 0.55, cy - r * 0.95, r * 0.25, r * 0.25, c, w=3)
    _ell(d, cx, cy - r * 0.7, r * 0.6, r * 0.55, c, w=3)
    _ell(d, cx, cy + r * 0.15, r * 0.6, r * 0.7, c, w=3)
    _ell(d, cx, cy + r * 0.25, r * 0.35, r * 0.42, c2, outline=None)
    for s in (-1, 1):
        _ell(d, cx + s * r * 0.65, cy + r * 0.1, r * 0.2, r * 0.2, c, w=3)
        _ell(d, cx + s * r * 0.4, cy + r * 0.75, r * 0.25, r * 0.22, c, w=3)
        _ell(d, cx + s * r * 0.22, cy - r * 0.78, r * 0.06, r * 0.06, OUT, outline=None)
    _ell(d, cx, cy - r * 0.55, r * 0.22, r * 0.18, c2, outline=None)
    _ell(d, cx, cy - r * 0.62, r * 0.09, r * 0.07, OUT, outline=None)
    # nơ
    _poly(d, [(cx - r * 0.4, cy - r * 0.3), (cx - r * 0.05, cy - r * 0.15), (cx - r * 0.4, cy)], (220, 50, 60), w=2)
    _poly(d, [(cx + r * 0.4, cy - r * 0.3), (cx + r * 0.05, cy - r * 0.15), (cx + r * 0.4, cy)], (220, 50, 60), w=2)


@lru_cache(maxsize=16)
def prop(kind):
    """Đạo cụ nhỏ dạng ảnh RGBA (1x), neo ở giữa đáy."""
    r = R * SS
    if kind == "teddy":
        W, H = int(r * 1.6), int(r * 2.2)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        teddy(ImageDraw.Draw(img), W / 2, H * 0.5, r * 0.62)
    elif kind == "book":
        W, H = int(r * 1.4), int(r * 1.0)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rrect(d, [r * 0.05, r * 0.15, W - r * 0.05, H - r * 0.05], int(r * 0.08), (90, 140, 220), w=3)
        _rrect(d, [r * 0.15, r * 0.05, W - r * 0.15, H - r * 0.15], int(r * 0.08), (255, 250, 235), w=3)
        d.line([W / 2, r * 0.08, W / 2, H - r * 0.15], fill=OUT, width=2 * SS)
        for i in range(3):
            y = r * 0.3 + i * r * 0.18
            d.line([r * 0.28, y, W / 2 - r * 0.1, y], fill=(150, 150, 150), width=2 * SS)
            d.line([W / 2 + r * 0.1, y, W - r * 0.28, y], fill=(150, 150, 150), width=2 * SS)
    elif kind == "backpack":
        W, H = int(r * 1.1), int(r * 1.3)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rrect(d, [r * 0.1, r * 0.1, W - r * 0.1, H - r * 0.05], int(r * 0.25), (240, 90, 80), w=3)
        _rrect(d, [r * 0.25, r * 0.6, W - r * 0.25, H - r * 0.2], int(r * 0.12), (255, 200, 80), w=3)
        d.arc([r * 0.3, -r * 0.1, W - r * 0.3, r * 0.35], 180, 360, fill=OUT, width=3 * SS)
    elif kind == "blanket":
        W, H = int(r * 2.6), int(r * 1.4)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rrect(d, [r * 0.05, r * 0.05, W - r * 0.05, H - r * 0.05], int(r * 0.5), (120, 170, 240), w=4)
        for i in range(5):
            d.ellipse([r * 0.3 + i * r * 0.45, H * 0.35, r * 0.6 + i * r * 0.45, H * 0.35 + r * 0.3], fill=(255, 255, 255))
    elif kind == "zzz":
        W, H = int(r * 1.5), int(r * 1.2)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _text(d, (W * 0.3, H * 0.75), "z", int(r * 0.35), (90, 110, 200))
        _text(d, (W * 0.55, H * 0.5), "Z", int(r * 0.5), (90, 110, 200))
        _text(d, (W * 0.8, H * 0.22), "Z", int(r * 0.65), (90, 110, 200))
    else:
        raise ValueError(kind)
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


if __name__ == "__main__":
    # bảng nhân vật để xem thử
    canvas = Image.new("RGB", (1500, 520), (245, 240, 230))
    x = 40
    for n, pose, ex in (("kaka", "crossed", "smirk"), ("puka", "claws", "grin"), ("moon", "hold", "smile"), ("sam", "stand", "laugh")):
        s = sprite(n, pose, ex)
        canvas.paste(s, (x, 500 - s.height), s)
        x += s.width - 60
    l = lu("sit", "smile")
    canvas.paste(l, (x, 500 - l.height), l)
    x += l.width
    l = lu("run", "laugh", 0.25, item="teddy")
    canvas.paste(l, (x - 40, 500 - l.height), l)
    for i, k in enumerate(("teddy", "book", "backpack", "blanket", "zzz")):
        p = prop(k)
        canvas.paste(p, (40 + i * 110, 10), p)
    canvas.save("/tmp/claude-0/-home-user-movies/4eb93384-7854-5b1d-b894-3192c5ee23bc/scratchpad/characters_test.png")
    print("ok")
