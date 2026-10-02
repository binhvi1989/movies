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

SKIN["dark"] = (205, 150, 110)
SKIN["pale"] = (252, 228, 210)

SPECS = {
    # Vẽ theo chân dung trong assets/refs/
    "kaka": dict(
        skin=SKIN["tan"], hair="kaka", hair_color=HAIR_BLACK, height=0.92, width=1.0, eyes="round",
        shirt=(165, 162, 160), shirt_style="kaka", shorts=(160, 157, 155), shorts_len=0.75,
        sleeve="normal", girl=False, cheeks=True,
    ),
    "puka": dict(
        skin=SKIN["tan"], hair="puka", hair_color=HAIR_BLACK, height=0.82, width=1.0, eyes="round",
        shirt=(247, 170, 190), shirt_style="puka", shorts=(247, 170, 190), shorts_len=0.55,
        sleeve="wide", girl=True, cheeks=True, earrings=(240, 200, 60),
    ),
    "moon": dict(
        skin=SKIN["dark"], hair="bun", hair_color=HAIR_BLACK, height=1.00, width=1.0, eyes="narrow",
        shirt=(252, 248, 238), shirt_style="moon", shorts=(252, 248, 238), shorts_len=0.5,
        sleeve="flutter", girl=True, cheeks=True, earrings=(250, 140, 180), necklace=(235, 200, 90),
    ),
    "sam": dict(
        skin=SKIN["tan"], hair="braid", hair_color=HAIR_BLACK, height=0.95, width=1.0, eyes="narrow",
        shirt=(250, 150, 200), shirt_style="sam", shorts=(250, 150, 200), shorts_len=0.6,
        sleeve="short", girl=True, cheeks=True, necklace=(220, 220, 230),
    ),
    "muoi": dict(
        skin=SKIN["pale"], hair="sidepony", hair_color=HAIR_BLACK, height=0.90, width=1.35, eyes="narrow",
        shirt=(252, 215, 225), shirt_style="muoi", shorts=(252, 215, 225), shorts_len=0.55,
        sleeve="none", girl=True, cheeks=True, necklace=(235, 200, 90), mole=True,
    ),
    "eric": dict(
        skin=SKIN["tan"], hair="buzz", hair_color=HAIR_BLACK, height=0.80, width=1.05, eyes="narrow",
        shirt=(90, 200, 215), shirt_style="eric", shorts=(90, 200, 215), shorts_len=0.6,
        sleeve="none", girl=False, cheeks=True, bigcheeks=True,
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
        elif spec.get("eyes") == "narrow":
            # mắt hí: hình hạnh nhân dẹt, mí trên đậm
            d.ellipse([x - er * 1.25, eye_y - er * 0.55, x + er * 1.25, eye_y + er * 0.55], fill=(255, 255, 255), outline=OUT, width=max(2, LW * SS // 2))
            d.ellipse([x - er * 0.5 + ox, eye_y - er * 0.5, x + er * 0.5 + ox, eye_y + er * 0.5], fill=(70, 45, 30))
            d.ellipse([x - er * 0.3 + ox, eye_y - er * 0.35, x + er * 0.3 + ox, eye_y + er * 0.35], fill=OUT)
            d.ellipse([x - er * 0.05 + ox, eye_y - er * 0.3, x + er * 0.2 + ox, eye_y - er * 0.05], fill=(255, 255, 255))
            d.arc([x - er * 1.3, eye_y - er * 0.7, x + er * 1.3, eye_y + er * 0.6], 195, 345, fill=OUT, width=LW * SS)
        else:
            d.ellipse([x - er, eye_y - er * 1.1, x + er, eye_y + er * 1.1], fill=(255, 255, 255), outline=OUT, width=LW * SS)
            d.ellipse([x - er * 0.6 + ox, eye_y - er * 0.55, x + er * 0.6 + ox, eye_y + er * 0.7], fill=(70, 45, 30))
            d.ellipse([x - er * 0.4 + ox, eye_y - er * 0.35, x + er * 0.4 + ox, eye_y + er * 0.55], fill=OUT)
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
    elif spec.get("eyes") == "narrow":
        for side in (-1, 1):
            x = cx + side * ex
            d.arc([x - bw * 0.9, by - er * 0.5, x + bw * 0.9, by + er * 0.7], 200, 340, fill=OUT, width=max(2, LW * SS // 2))
    # --- má hồng
    if spec.get("cheeks") or expr in ("laugh", "grin"):
        big = 1.6 if spec.get("bigcheeks") else 1.0
        for side in (-1, 1):
            x = cx + side * r * 0.62
            d.ellipse([x - r * 0.13 * big, cy + r * 0.32, x + r * 0.13 * big, cy + r * 0.48 + r * 0.06 * (big - 1)], fill=(250, 170, 170))
    if spec.get("mole"):
        d.ellipse([cx + r * 0.3, cy + r * 0.62, cx + r * 0.36, cy + r * 0.68], fill=OUT)
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
        _rrect(d, [cx - r * 1.12, cy - r * 0.2, cx - r * 0.55, cy + r * 1.9], int(r * 0.3), hc)
        _rrect(d, [cx + r * 0.55, cy - r * 0.2, cx + r * 1.12, cy + r * 1.9], int(r * 0.3), hc)
    elif st == "puka":
        # tóc dài ngang vai, đuôi lởm chởm, vài sợi dựng đứng
        _ell(d, cx, cy - r * 0.05, r * 1.1, r * 1.08, hc)
        for sd in (-1, 1):
            pts = [(cx + sd * r * 0.5, cy - r * 0.2), (cx + sd * r * 1.15, cy - r * 0.2)]
            n = 5
            for i in range(n + 1):
                xx = cx + sd * (r * 1.15 - i * r * 0.65 / n)
                yy = cy + r * (1.55 if i % 2 == 0 else 1.25)
                pts.append((xx, yy))
            _poly(d, pts, hc)
        rnd = random.Random(21)
        for i in range(6):
            a = math.radians(225 + i * 18 + rnd.uniform(-4, 4))
            x0, y0 = cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95
            x1, y1 = cx + math.cos(a) * r * 1.4, cy + math.sin(a) * r * 1.4
            d.line([(x0, y0), (x1, y1)], fill=hc, width=3 * SS)
    elif st == "kaka":
        _ell(d, cx, cy - r * 0.08, r * 1.06, r * 1.04, hc)
        rnd = random.Random(22)
        for i in range(5):
            a = math.radians(235 + i * 18 + rnd.uniform(-4, 4))
            x0, y0 = cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95
            x1, y1 = cx + math.cos(a) * r * 1.35, cy + math.sin(a) * r * 1.35
            d.line([(x0, y0), (x1, y1)], fill=hc, width=3 * SS)
    elif st == "bun":
        _ell(d, cx, cy - r * 0.05, r * 1.06, r * 1.06, hc)
        _ell(d, cx, cy - r * 1.12, r * 0.32, r * 0.28, hc)  # búi tóc cao
        for i in range(3):
            d.line([(cx - r * 0.2 + i * r * 0.2, cy - r * 1.35), (cx - r * 0.3 + i * r * 0.3, cy - r * 1.55)], fill=hc, width=2 * SS)
    elif st == "braid":
        _ell(d, cx, cy - r * 0.05, r * 1.06, r * 1.06, hc)
        # bím xoắn bên trái
        for i in range(5):
            _ell(d, cx - r * 1.0 + (i % 2) * r * 0.08, cy + r * 0.55 + i * r * 0.3, r * 0.2, r * 0.2, hc, w=3)
    elif st == "sidepony":
        _ell(d, cx, cy - r * 0.05, r * 1.06, r * 1.06, hc)
        # đuôi ngựa thấp bên phải
        _limb(d, (cx + r * 0.85, cy + r * 0.55), (cx + r * 1.35, cy + r * 1.3), r * 0.36, hc)
        _ell(d, cx + r * 1.38, cy + r * 1.35, r * 0.22, r * 0.22, hc)
    elif st == "buzz":
        _ell(d, cx, cy - r * 0.06, r * 1.04, r * 1.02, hc)


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
    elif st == "puka":
        # mái lởm chởm che trán, không che mắt
        pts = [(cx - r * 1.05, cy - r * 0.1)]
        rnd = random.Random(31)
        n = 11
        for i in range(n + 1):
            x = cx - r * 1.0 + i * (2.0 * r / n)
            y = cy - r * 0.2 + (0.16 if i % 2 == 0 else -0.08) * r + rnd.uniform(-0.04, 0.04) * r
            pts.append((x, y))
        pts += [(cx + r * 1.05, cy - r * 0.1), (cx + r * 0.9, top - r * 0.05), (cx, top - r * 0.12), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)
    elif st == "kaka":
        pts = [(cx - r * 1.0, cy - r * 0.3)]
        n = 9
        for i in range(n + 1):
            x = cx - r * 0.95 + i * (1.9 * r / n)
            y = cy - r * 0.42 + (0.22 if i % 2 == 0 else 0.0) * r
            pts.append((x, y))
        pts += [(cx + r * 1.0, cy - r * 0.3), (cx + r * 0.9, top - r * 0.05), (cx, top - r * 0.1), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)
    elif st in ("bun", "sidepony"):
        # tóc vuốt mượt rẽ ngôi giữa, trán cao
        pts = [(cx - r * 1.02, cy - r * 0.3), (cx - r * 0.55, cy - r * 0.72), (cx, cy - r * 0.6),
               (cx + r * 0.55, cy - r * 0.72), (cx + r * 1.02, cy - r * 0.3), (cx + r * 0.9, top - r * 0.05),
               (cx, top - r * 0.1), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)
        if st == "bun":
            d.line([(cx, cy - r * 0.6), (cx, cy - r * 1.0)], fill=(90, 75, 70), width=2 * SS)
    elif st == "braid":
        # tóc chải ngược, vài sợi lòa xòa
        pts = [(cx - r * 1.02, cy - r * 0.35), (cx - r * 0.5, cy - r * 0.8), (cx + r * 0.5, cy - r * 0.8),
               (cx + r * 1.02, cy - r * 0.35), (cx + r * 0.9, top - r * 0.05), (cx, top - r * 0.1), (cx - r * 0.9, top - r * 0.05)]
        _poly(d, pts, hc)
        d.line([(cx - r * 0.5, cy - r * 0.75), (cx - r * 0.75, cy - r * 0.1)], fill=hc, width=2 * SS)
        d.line([(cx + r * 0.55, cy - r * 0.75), (cx + r * 0.85, cy - r * 0.2)], fill=hc, width=2 * SS)
    elif st == "buzz":
        # tóc húi cua: viền tóc sát trán
        pts = [(cx - r * 1.0, cy - r * 0.35), (cx - r * 0.6, cy - r * 0.62), (cx, cy - r * 0.68),
               (cx + r * 0.6, cy - r * 0.62), (cx + r * 1.0, cy - r * 0.35), (cx + r * 0.9, top - r * 0.05),
               (cx, top - r * 0.1), (cx - r * 0.9, top - r * 0.05)]
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
        # kem chấm bi đen, nơ hồng, mặt gấu vàng
        for i in range(60):
            px, py = rnd.uniform(x0 + w * 0.05, x1 - w * 0.05), rnd.uniform(y0 + h * 0.12, y1 - h * 0.06)
            d.ellipse([px - 2 * SS, py - 2 * SS, px + 2 * SS, py + 2 * SS], fill=(50, 45, 45))
        for i in range(7):
            px, py = rnd.uniform(x0 + w * 0.12, x1 - w * 0.12), rnd.uniform(y0 + h * 0.18, y1 - h * 0.1)
            if i % 2 == 0:
                rr = w * 0.05
                _poly(d, [(px - rr, py - rr * 0.6), (px, py), (px - rr, py + rr * 0.6)], (240, 120, 170), w=1)
                _poly(d, [(px + rr, py - rr * 0.6), (px, py), (px + rr, py + rr * 0.6)], (240, 120, 170), w=1)
            else:
                rr = w * 0.045
                _ell(d, px, py, rr, rr * 0.9, (240, 180, 70), w=1)
                _ell(d, px - rr * 0.7, py - rr * 0.7, rr * 0.35, rr * 0.35, (240, 180, 70), w=1)
                _ell(d, px + rr * 0.7, py - rr * 0.7, rr * 0.35, rr * 0.35, (240, 180, 70), w=1)
                d.ellipse([px - rr * 0.1, py, px + rr * 0.1, py + rr * 0.2], fill=OUT)
        # đường bèo ngực
        yy = y0 + h * 0.3
        d.line([(x0 + w * 0.1 + i * w * 0.8 / 12, yy + (i % 2) * h * 0.03) for i in range(13)], fill=(200, 200, 200), width=2 * SS, joint="curve")
    elif st == "sam":
        # hồng caro chấm bi + mặt cười nhiều màu
        cell = w * 0.1
        xx = x0 + w * 0.05
        k = 0
        while xx < x1 - w * 0.05:
            yy = y0 + h * 0.1
            j = 0
            while yy < y1 - h * 0.05:
                if (k + j) % 2 == 0:
                    d.rectangle([xx, yy, xx + cell, yy + cell], fill=_darken(spec["shirt"], 0.92))
                yy += cell
                j += 1
            xx += cell
            k += 1
        cols = [(90, 170, 240), (250, 210, 70), (120, 200, 110), (255, 255, 255)]
        for i in range(9):
            px, py = rnd.uniform(x0 + w * 0.12, x1 - w * 0.12), rnd.uniform(y0 + h * 0.15, y1 - h * 0.1)
            rr = w * 0.05
            c = rnd.choice(cols)
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=c, outline=_darken(c, 0.7), width=max(1, SS))
            d.ellipse([px - rr * 0.45, py - rr * 0.3, px - rr * 0.2, py - rr * 0.05], fill=OUT)
            d.ellipse([px + rr * 0.2, py - rr * 0.3, px + rr * 0.45, py - rr * 0.05], fill=OUT)
            d.arc([px - rr * 0.4, py - rr * 0.1, px + rr * 0.4, py + rr * 0.5], 20, 160, fill=OUT, width=max(1, SS))
        # túi bèo
        for sgn in (-1, 1):
            px = cx + sgn * w * 0.27
            py = y1 - h * 0.22
            _rrect(d, [px - w * 0.13, py - h * 0.09, px + w * 0.13, py + h * 0.11], int(w * 0.03), spec["shirt"], w=2)
            d.line([(px - w * 0.13 + i * w * 0.26 / 8, py - h * 0.09 + (i % 2) * h * 0.025) for i in range(9)], fill=(255, 255, 255), width=2 * SS, joint="curve")
    elif st == "muoi":
        # hồng nhạt sọc dọc, in bé gái / hoa cam / thỏ trắng
        xx = x0 + w * 0.06
        while xx < x1 - w * 0.04:
            d.line([(xx, y0 + h * 0.1), (xx, y1 - h * 0.05)], fill=_darken(spec["shirt"], 0.93), width=2 * SS)
            xx += w * 0.08
        for i in range(10):
            px, py = rnd.uniform(x0 + w * 0.12, x1 - w * 0.12), rnd.uniform(y0 + h * 0.2, y1 - h * 0.1)
            kind = i % 3
            rr = w * 0.045
            if kind == 0:   # hoa cam
                for k in range(5):
                    a = k * 2 * math.pi / 5
                    d.ellipse([px + math.cos(a) * rr - rr * 0.55, py + math.sin(a) * rr - rr * 0.55, px + math.cos(a) * rr + rr * 0.55, py + math.sin(a) * rr + rr * 0.55], fill=(245, 150, 60))
                d.ellipse([px - rr * 0.4, py - rr * 0.4, px + rr * 0.4, py + rr * 0.4], fill=(255, 230, 120))
            elif kind == 1:  # thỏ trắng
                _ell(d, px, py, rr * 0.8, rr * 0.8, (255, 255, 255), w=1)
                _ell(d, px - rr * 0.4, py - rr * 1.1, rr * 0.25, rr * 0.6, (255, 255, 255), w=1)
                _ell(d, px + rr * 0.4, py - rr * 1.1, rr * 0.25, rr * 0.6, (255, 255, 255), w=1)
                d.ellipse([px - rr * 0.35, py - rr * 0.2, px - rr * 0.15, py], fill=OUT)
                d.ellipse([px + rr * 0.15, py - rr * 0.2, px + rr * 0.35, py], fill=OUT)
            else:           # bé gái váy hồng/xanh
                _ell(d, px, py - rr * 0.5, rr * 0.6, rr * 0.6, (250, 225, 190), w=1)
                _ell(d, px, py - rr * 0.8, rr * 0.65, rr * 0.4, (240, 200, 90), outline=None)
                _poly(d, [(px - rr * 0.7, py + rr * 0.9), (px + rr * 0.7, py + rr * 0.9), (px + rr * 0.3, py), (px - rr * 0.3, py)], (240, 110, 150) if i % 2 else (130, 200, 90), w=1)
        # cổ bèo hồng
        d.rounded_rectangle([x0 - w * 0.02, y0 + h * 0.02, x1 + w * 0.02, y0 + h * 0.16], radius=int(w * 0.05), fill=(252, 200, 215), outline=OUT, width=2 * SS)
    elif st == "eric":
        # sọc ngang xanh ngọc / vàng, viền caro đỏ, mặt gấu nâu & chó trắng
        band = h * 0.2
        yy = y0 + h * 0.08
        k = 0
        while yy < y1:
            c = (90, 200, 215) if k % 2 == 0 else (250, 205, 60)
            d.rectangle([x0, yy, x1, min(y1, yy + band)], fill=c)
            # viền caro đỏ-trắng
            if yy + band < y1:
                for i in range(int(w / (w * 0.06))):
                    cc = (230, 70, 70) if i % 2 == 0 else (255, 255, 255)
                    d.rectangle([x0 + i * w * 0.06, yy + band - h * 0.03, x0 + (i + 1) * w * 0.06, yy + band + h * 0.01], fill=cc)
            # mặt thú
            for i in range(3):
                px = x0 + w * (0.2 + i * 0.3)
                py = yy + band * 0.45
                rr = w * 0.055
                if (i + k) % 2 == 0:
                    _ell(d, px, py, rr, rr * 0.9, (170, 110, 60), w=1)
                    _ell(d, px - rr * 0.75, py - rr * 0.7, rr * 0.35, rr * 0.35, (170, 110, 60), w=1)
                    _ell(d, px + rr * 0.75, py - rr * 0.7, rr * 0.35, rr * 0.35, (170, 110, 60), w=1)
                    _ell(d, px, py + rr * 0.25, rr * 0.45, rr * 0.35, (235, 200, 160), outline=None)
                else:
                    _ell(d, px, py, rr, rr * 0.9, (255, 255, 255), w=1)
                    _ell(d, px + rr * 0.6, py - rr * 0.3, rr * 0.4, rr * 0.5, (170, 110, 60), outline=None)
                d.ellipse([px - rr * 0.4, py - rr * 0.25, px - rr * 0.2, py - rr * 0.05], fill=OUT)
                d.ellipse([px + rr * 0.2, py - rr * 0.25, px + rr * 0.4, py - rr * 0.05], fill=OUT)
                d.ellipse([px - rr * 0.1, py + rr * 0.15, px + rr * 0.1, py + rr * 0.3], fill=OUT)
            yy += band
            k += 1
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(w * 0.12), outline=OUT, width=LW * SS)


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
    W, H = int(r * 5.0), int(r * 6.4)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W / 2
    foot_y = H - r * 0.1
    leg_len = r * 1.35 * hf
    body_h = r * 1.55 * hf
    hip_y = foot_y - leg_len
    shoulder_y = hip_y - body_h
    head_cy = shoulder_y - r * 0.95
    body_w = (r * 1.35 if spec["shirt_style"] in ("puka", "kaka") else r * 1.15) * spec.get("width", 1.0)
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
        rnd2 = random.Random(5)
        for _ in range(14):
            px, py = rnd2.uniform(cx - body_w * 0.6, cx + body_w * 0.6), rnd2.uniform(q_top + r * 0.05, q_bot - r * 0.05)
            rr = rnd2.uniform(r * 0.08, r * 0.2)
            d.ellipse([px - rr, py - rr * 0.6, px + rr, py + rr * 0.6], fill=_darken(spec["shorts"], rnd2.uniform(0.78, 0.9)))
        _text(d, (cx + body_w * 0.2, q_bot - r * 0.32), "STREET", int(r * 0.15), (70, 70, 70))
        _text(d, (cx - body_w * 0.22, q_bot - r * 0.12), "NINE", int(r * 0.15), (70, 70, 70))
    if spec["shirt_style"] == "eric":
        d.rectangle([cx - body_w * 0.62, q_top + r * 0.1, cx + body_w * 0.62, q_top + r * 0.35], fill=(250, 205, 60))
        for i in range(12):
            d.rectangle([cx - body_w * 0.62 + i * body_w * 1.24 / 12, q_bot - r * 0.12, cx - body_w * 0.62 + (i + 1) * body_w * 1.24 / 12, q_bot], fill=(230, 70, 70) if i % 2 == 0 else (255, 255, 255))
    if spec["shirt_style"] in ("moon", "sam", "muoi"):
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
    if spec["shirt_style"] in ("sam", "eric"):
        # hàng nút
        for i in range(3):
            _ell(d, cx, by0 + r * 0.35 + i * r * 0.22, r * 0.06, r * 0.06, (255, 240, 240), w=2)
    if spec.get("necklace"):
        d.arc([cx - r * 0.24, by0 - r * 0.12, cx + r * 0.24, by0 + r * 0.24], 10, 170, fill=spec["necklace"], width=2 * SS)

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
            elif spec["sleeve"] == "flutter":
                _ell(d, sx + ux * r * 0.1, sh_y + uy * r * 0.1 - r * 0.05, r * 0.4, r * 0.24, spec["shirt"])
            elif spec["sleeve"] == "short":
                _limb(d, (sx, sh_y), (sx + ux * r * 0.3, sh_y + uy * r * 0.3), th * 0.8, spec["shirt"])
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
            elif spec["sleeve"] == "flutter":
                _ell(d, sx + ux * r * 0.1, sh_y + uy * r * 0.1 - r * 0.05, r * 0.4, r * 0.24, spec["shirt"])
                for k in range(5):
                    d.ellipse([sx + ux * r * 0.1 - r * 0.4 + k * r * 0.2 - r * 0.05, sh_y + uy * r * 0.1 + r * 0.12, sx + ux * r * 0.1 - r * 0.4 + k * r * 0.2 + r * 0.05, sh_y + uy * r * 0.1 + r * 0.22], fill=spec["shirt"], outline=OUT, width=2)
            elif spec["sleeve"] == "short":
                _limb(d, (sx, sh_y), (sx + ux * r * 0.3, sh_y + uy * r * 0.3), th * 0.8, spec["shirt"])
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
    elif pose == "lion":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.7, sh_y - r * 0.4), (cx + s * sh_w * 0.45, sh_y - r * 1.3))
    elif pose == "drum":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.85, sh_y + r * 0.55), (cx + s * sh_w * 0.4, sh_y + r * 1.05))
    elif pose == "cry":
        for s in (-1, 1):
            arm(s, (cx + s * sh_w * 0.95, sh_y + r * 0.35), (cx + s * r * 0.4, sh_y - r * 0.75))
    elif pose == "eat":
        arm(-1, (cx - sh_w * 0.72, sh_y + r * 0.7), (cx - sh_w * 0.78, sh_y + r * 1.35))
        arm(1, (cx + sh_w * 0.95, sh_y + r * 0.35), (cx + r * 0.25, sh_y - r * 0.6))

    # ----- đầu
    _ell(d, cx, head_cy, r, r * 0.98, skin)
    # tai
    for s in (-1, 1):
        _ell(d, cx + s * r * 0.98, head_cy + r * 0.12, r * 0.16, r * 0.2, skin)
        if spec.get("earrings"):
            _ell(d, cx + s * r * 0.98, head_cy + r * 0.32, r * 0.06, r * 0.06, spec["earrings"], w=2)
    _face(d, cx, head_cy, r, spec, expr, look)
    _hair_front(d, cx, head_cy, r, spec)

    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img = img.resize((W // SS, H // SS), Image.LANCZOS)
    return img


# ------------------------------------------------------------------ cún Lu
LU_BROWN = (165, 98, 52)
LU_DARK = (120, 68, 35)
LU_MUZZLE = (225, 195, 160)


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
    _ell(d, head_cx, head_cy + r * 0.45, r * 0.55, r * 0.42, LU_MUZZLE)
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
    elif kind == "slipper":
        W, H = int(r * 1.3), int(r * 0.7)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rrect(d, [r * 0.05, r * 0.15, W - r * 0.05, H - r * 0.05], int(r * 0.25), (60, 110, 200), w=3)
        d.arc([r * 0.25, -r * 0.05, W - r * 0.25, r * 0.5], 0, 180, fill=OUT, width=4 * SS)
        d.arc([r * 0.3, 0, W - r * 0.3, r * 0.45], 0, 180, fill=(230, 80, 80), width=2 * SS)
    elif kind == "bowl":
        W, H = int(r * 1.2), int(r * 0.8)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.chord([r * 0.05, r * 0.05, W - r * 0.05, H - r * 0.05], 0, 180, fill=(230, 90, 90), outline=OUT, width=3 * SS)
        _ell(d, W / 2, r * 0.3, W / 2 - r * 0.05, r * 0.2, (255, 250, 235), w=3)
        for k in range(5):
            _ell(d, W * 0.25 + k * W * 0.12, r * 0.28 + (k % 2) * r * 0.06, r * 0.06, r * 0.06, (200, 150, 90), outline=None)
    elif kind == "lion":
        # đầu lân đỏ vàng, miệng há, mắt to, sừng, râu
        W, H = int(r * 2.4), int(r * 2.2)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx, cy = W / 2, H * 0.55
        _ell(d, cx, cy, r * 1.0, r * 0.85, (220, 50, 50), w=4)
        # bờm vàng
        for k in range(14):
            a = math.pi + k * math.pi / 13
            px, py = cx + math.cos(a) * r * 1.0, cy + math.sin(a) * r * 0.85
            _ell(d, px, py, r * 0.2, r * 0.2, (250, 200, 60), w=3)
        # sừng
        _poly(d, [(cx - r * 0.1, cy - r * 0.8), (cx + r * 0.1, cy - r * 0.8), (cx, cy - r * 1.25)], (250, 200, 60), w=3)
        # mắt to
        for sgn in (-1, 1):
            _ell(d, cx + sgn * r * 0.45, cy - r * 0.2, r * 0.3, r * 0.3, (255, 255, 255), w=3)
            _ell(d, cx + sgn * r * 0.45, cy - r * 0.2, r * 0.15, r * 0.15, OUT, outline=None)
            _ell(d, cx + sgn * r * 0.45, cy - r * 0.55, r * 0.22, r * 0.12, (60, 160, 90), w=2)  # lông mày xanh
        # mũi, miệng há
        _ell(d, cx, cy + r * 0.1, r * 0.22, r * 0.16, (250, 200, 60), w=3)
        d.chord([cx - r * 0.6, cy + r * 0.15, cx + r * 0.6, cy + r * 0.95], 0, 180, fill=(120, 30, 40), outline=OUT, width=4 * SS)
        for k in range(5):
            xx = cx - r * 0.5 + k * r * 0.25
            _poly(d, [(xx, cy + r * 0.3), (xx + r * 0.2, cy + r * 0.3), (xx + r * 0.1, cy + r * 0.5)], (255, 255, 255), w=2)
        # râu
        for sgn in (-1, 1):
            d.line([(cx + sgn * r * 0.5, cy + r * 0.5), (cx + sgn * r * 1.15, cy + r * 0.95)], fill=(255, 255, 255), width=3 * SS)
    elif kind == "tail":
        # thân/đuôi lân: tấm vải đỏ vàng lượn sóng
        W, H = int(r * 2.6), int(r * 1.3)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pts = [(r * 0.1, H * 0.2), (W - r * 0.1, H * 0.35), (W - r * 0.3, H * 0.95), (r * 0.3, H * 0.9)]
        _poly(d, pts, (220, 50, 50), w=4)
        for k in range(5):
            x = r * 0.3 + k * (W - r * 0.6) / 5
            d.rectangle([x, H * 0.5, x + (W - r * 0.6) / 10, H * 0.85], fill=(250, 200, 60))
        for k in range(8):
            _ell(d, r * 0.25 + k * (W - r * 0.5) / 7, H * 0.95, r * 0.12, r * 0.12, (250, 200, 60), w=2)
    elif kind == "drum":
        W, H = int(r * 1.6), int(r * 1.5)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rrect(d, [r * 0.1, r * 0.3, W - r * 0.1, H - r * 0.05], int(r * 0.15), (200, 50, 50), w=4)
        _ell(d, W / 2, r * 0.32, W / 2 - r * 0.1, r * 0.22, (240, 220, 180), w=4)
        for k in range(8):
            a = k * math.pi / 4
            _ell(d, W / 2 + math.cos(a) * (W / 2 - r * 0.2), r * 0.32 + math.sin(a) * r * 0.16, r * 0.04, r * 0.04, (250, 200, 60), outline=None)
        d.line([(r * 0.1, H * 0.7), (W - r * 0.1, H * 0.7)], fill=(250, 200, 60), width=3 * SS)
    elif kind == "sticks":
        W, H = int(r * 1.2), int(r * 1.0)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.line([(r * 0.1, H - r * 0.1), (W * 0.45, r * 0.1)], fill=(190, 140, 80), width=5 * SS)
        d.line([(W - r * 0.1, H - r * 0.1), (W * 0.55, r * 0.1)], fill=(190, 140, 80), width=5 * SS)
        _ell(d, W * 0.45, r * 0.12, r * 0.1, r * 0.1, (220, 50, 50), w=2)
        _ell(d, W * 0.55, r * 0.12, r * 0.1, r * 0.1, (220, 50, 50), w=2)
    elif kind == "fan":
        # quạt Ông Địa
        W, H = int(r * 1.3), int(r * 1.3)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.pieslice([r * 0.05, r * 0.05, W - r * 0.05, H + r * 0.8], 200, 340, fill=(250, 220, 120), outline=OUT, width=3 * SS)
        for k in range(6):
            a = math.radians(200 + k * 28)
            d.line([(W / 2, H * 0.9), (W / 2 + math.cos(a) * r * 0.6, H * 0.9 + math.sin(a) * r * 0.6)], fill=(200, 150, 80), width=2 * SS)
        d.rectangle([W / 2 - r * 0.05, H * 0.85, W / 2 + r * 0.05, H - r * 0.02], fill=(120, 70, 40), outline=OUT, width=2)
    elif kind == "mask":
        # mặt nạ Ông Địa cười
        W, H = int(r * 1.4), int(r * 1.5)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _ell(d, W / 2, H * 0.52, r * 0.62, r * 0.68, (250, 215, 170), w=4)
        _ell(d, W / 2, H * 0.2, r * 0.5, r * 0.22, (40, 30, 30), outline=None)
        for sgn in (-1, 1):
            d.arc([W / 2 + sgn * r * 0.28 - r * 0.15, H * 0.4, W / 2 + sgn * r * 0.28 + r * 0.15, H * 0.56], 200, 340, fill=OUT, width=3 * SS)
            _ell(d, W / 2 + sgn * r * 0.38, H * 0.62, r * 0.12, r * 0.12, (250, 160, 160), outline=None)
        d.chord([W / 2 - r * 0.35, H * 0.55, W / 2 + r * 0.35, H * 0.9], 0, 180, fill=(120, 30, 40), outline=OUT, width=3 * SS)
        d.rectangle([W / 2 - r * 0.3, H * 0.6, W / 2 + r * 0.3, H * 0.7], fill=(255, 255, 255))
    elif kind == "lantern":
        # lồng đèn ngôi sao đỏ
        W, H = int(r * 1.3), int(r * 1.9)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx, cy = W / 2, H * 0.6
        d.line([(cx, r * 0.02), (cx, cy - r * 0.55)], fill=(120, 70, 40), width=3 * SS)
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r * 0.6 if k % 2 == 0 else r * 0.26
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        _poly(d, pts, (235, 60, 60), w=3)
        pts2 = [(cx + (x - cx) * 0.45, cy + (y - cy) * 0.45) for x, y in pts]
        d.polygon(pts2, fill=(255, 220, 110))
        d.ellipse([cx - r * 0.1, cy - r * 0.1, cx + r * 0.1, cy + r * 0.1], fill=(255, 250, 200))
    elif kind == "mooncake":
        W, H = int(r * 1.2), int(r * 0.8)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _ell(d, W / 2, H * 0.6, r * 0.52, r * 0.3, (200, 130, 50), w=3)
        _ell(d, W / 2, H * 0.4, r * 0.52, r * 0.3, (225, 160, 70), w=3)
        for k in range(8):
            a = k * math.pi / 4
            _ell(d, W / 2 + math.cos(a) * r * 0.32, H * 0.4 + math.sin(a) * r * 0.18, r * 0.07, r * 0.05, (200, 130, 50), outline=None)
        _ell(d, W / 2, H * 0.4, r * 0.12, r * 0.08, (200, 130, 50), outline=None)
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
    canvas = Image.new("RGB", (1700, 560), (245, 240, 230))
    x = 20
    for n, pose, ex in (("kaka", "crossed", "smirk"), ("puka", "claws", "grin"), ("moon", "stand", "smile"), ("sam", "cheer", "laugh"), ("muoi", "eat", "smile"), ("eric", "claws", "pout")):
        s_ = sprite(n, pose, ex)
        canvas.paste(s_, (x, 540 - s_.height), s_)
        x += s_.width - 70
    l = lu("sit", "smile")
    canvas.paste(l, (x, 540 - l.height), l)
    for i, k in enumerate(("lion", "tail", "drum", "sticks", "fan", "mask", "lantern", "mooncake", "slipper", "bowl")):
        p = prop(k)
        canvas.paste(p, (20 + i * 150, 10), p)
    canvas.save("/tmp/claude-0/-home-user-movies/4eb93384-7854-5b1d-b894-3192c5ee23bc/scratchpad/characters_v3.png")
    print("ok")
