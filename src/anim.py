# -*- coding: utf-8 -*-
"""Bộ máy hoạt hình tối giản: keyframe -> trạng thái theo thời gian, và vẽ một khung hình."""
import math

from PIL import Image, ImageDraw, ImageFont

import characters as ch

W, H = 1280, 720
KID_SCALE = 1.45   # phóng to nhân vật so với sprite gốc
PROP_SCALE = 1.3
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT_PATH, size)
    return _fonts[size]


def smooth(f):
    return f * f * (3 - 2 * f)


class Track:
    def __init__(self, keys, discrete=False, ease=True):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.discrete = discrete
        self.ease = ease

    def at(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        for i in range(1, len(ks)):
            if t < ks[i][0]:
                t0, v0 = ks[i - 1]
                t1, v1 = ks[i]
                if self.discrete or isinstance(v0, (str, bool)) or v0 is None or v1 is None:
                    return v0
                f = (t - t0) / (t1 - t0) if t1 > t0 else 1
                if self.ease:
                    f = smooth(f)
                if isinstance(v0, tuple):
                    return tuple(a + (b - a) * f for a, b in zip(v0, v1))
                return v0 + (v1 - v0) * f
        return ks[-1][1]


DEFAULTS = dict(x=640, y=690, scale=1.0, pose="stand", expr="smile", flip=False, look=0.0, alpha=1.0,
                rot=0.0, bob=0.0, bobf=2.0, talk=False, item=None, walkspeed=2.2, visible=True,
                text="", size=48, color=(255, 255, 255), tail=None, sway=0.0)


class Actor:
    """kind: kid | lu | prop | text | bubble ; name: tên nhân vật / loại đạo cụ."""

    def __init__(self, kind, name="", z=0, **tracks):
        self.kind, self.name, self.z = kind, name, z
        self.tracks = {}
        for k, v in tracks.items():
            self.set(k, v)

    def set(self, key, val):
        if isinstance(val, list):
            self.tracks[key] = Track(val, discrete=key in ("pose", "expr", "flip", "talk", "item", "visible", "text", "color", "tail"))
        else:
            self.tracks[key] = Track([(0, val)])
        return self

    def state(self, t):
        st = dict(DEFAULTS)
        for k, tr in self.tracks.items():
            st[k] = tr.at(t)
        return st

    # tiện ích biên đạo
    def walk(self, t0, t1, x0, x1, y0=None, y1=None, end_pose="stand"):
        xs = self.tracks.get("x").keys if "x" in self.tracks else []
        self.set("x", xs + [(t0, x0), (t1, x1)])
        if y0 is not None:
            ys = self.tracks.get("y").keys if "y" in self.tracks else []
            self.set("y", ys + [(t0, y0), (t1, y1 if y1 is not None else y0)])
        ps = self.tracks.get("pose").keys if "pose" in self.tracks else []
        self.set("pose", ps + [(t0, "walk"), (t1, end_pose)])
        fs = self.tracks.get("flip").keys if "flip" in self.tracks else []
        self.set("flip", fs + [(t0, x1 < x0), (t1, False)])
        return self

    def say(self, t0, t1):
        ks = self.tracks.get("talk").keys if "talk" in self.tracks else [(0, False)]
        self.set("talk", ks + [(t0, True), (t1, False)])
        return self


def _rotate(img, deg):
    if abs(deg) < 0.5:
        return img
    return img.rotate(deg, resample=Image.BICUBIC, expand=True)


def _scaled(img, s):
    if abs(s - 1.0) < 1e-3:
        return img
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


def wrap_text(text, f, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_bubble(frame, text, x, y, tail=None, size=34, maxw=420):
    """Bong bóng thoại, (x,y) là tâm bong bóng; tail = điểm mỏ nhọn."""
    f = font(size)
    lines = wrap_text(text, f, maxw)
    lw = max(f.getlength(l) for l in lines)
    lh = size * 1.25
    bw, bh = lw + 44, lh * len(lines) + 30
    x0, y0 = x - bw / 2, y - bh / 2
    d = ImageDraw.Draw(frame)
    if tail:
        tx, ty = tail
        # mỏ bong bóng
        bx = min(max(tx, x0 + 40), x0 + bw - 40)
        base_y = y0 + bh if ty > y else y0
        d.polygon([(bx - 18, base_y), (bx + 18, base_y), (tx, ty)], fill=(255, 255, 255), outline=(40, 30, 30))
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=22, fill=(255, 255, 255), outline=(40, 30, 30), width=4)
    if tail:
        bx = min(max(tail[0], x0 + 40), x0 + bw - 40)
        base_y = y0 + bh if tail[1] > y else y0
        d.polygon([(bx - 15, base_y), (bx + 15, base_y), (tail[0], tail[1])], fill=(255, 255, 255))
        d.line([(bx - 15, base_y), tail, (bx + 15, base_y)], fill=(40, 30, 30), width=4)
    for i, l in enumerate(lines):
        d.text((x, y0 + 15 + lh * i + lh / 2), l, font=f, fill=(40, 30, 30), anchor="mm")


def draw_pop_text(frame, text, x, y, size, color, rot=0.0, alpha=1.0, scale=1.0):
    f = font(int(size * scale))
    pad = int(size * scale * 0.6)
    tw = int(f.getlength(text)) + pad * 2
    th = int(size * scale * 1.4) + pad
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((tw / 2, th / 2), text, font=f, fill=color, anchor="mm", stroke_width=max(2, int(size * scale * 0.12)), stroke_fill=(40, 30, 30))
    layer = _rotate(layer, rot)
    if alpha < 1:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    frame.alpha_composite(layer, (int(x - layer.width / 2), int(y - layer.height / 2)))


def draw_actor(frame, actor, st, t):
    if not st["visible"] or st["alpha"] <= 0:
        return
    kind = actor.kind
    if kind == "bubble":
        if st["text"]:
            draw_bubble(frame, st["text"], st["x"], st["y"], st["tail"], size=int(st["size"]))
        return
    if kind == "text":
        if st["text"]:
            draw_pop_text(frame, st["text"], st["x"], st["y"], st["size"], st["color"], st["rot"], st["alpha"], st["scale"])
        return
    bob = st["bob"] * math.sin(2 * math.pi * st["bobf"] * t) if st["bob"] else 0.0
    sway = st["sway"] * math.sin(2 * math.pi * st["bobf"] * t) if st["sway"] else 0.0
    if kind == "kid":
        expr = st["expr"]
        if st["talk"] and int(t * 8) % 2 == 0:
            expr = "talk"
        phase = (t * st["walkspeed"]) % 1.0 if st["pose"] in ("walk",) else 0.0
        img = ch.sprite(actor.name, st["pose"], expr, round(phase * 8) / 8, bool(st["flip"]), round(st["look"], 1))
    elif kind == "lu":
        phase = (t * 4.0) % 1.0 if st["pose"] == "run" else 0.0
        img = ch.lu(st["pose"], st["expr"], round(phase * 6) / 6, bool(st["flip"]), st["item"])
    elif kind == "prop":
        img = ch.prop(actor.name)
    else:
        raise ValueError(kind)
    img = _scaled(img, st["scale"] * (PROP_SCALE if kind == "prop" else KID_SCALE))
    img = _rotate(img, st["rot"] + sway)
    if st["alpha"] < 1:
        a = img.getchannel("A").point(lambda v: int(v * st["alpha"]))
        img = img.copy()
        img.putalpha(a)
    x = int(st["x"] - img.width / 2)
    y = int(st["y"] + bob - img.height)
    frame.alpha_composite(img, (x, y))


def draw_caption(frame, text, alpha=1.0):
    f = font(36)
    lines = wrap_text(text, f, 1140)
    lh = 46
    bh = lh * len(lines) + 26
    y0 = H - 28 - bh
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw = max(f.getlength(l) for l in lines) + 56
    d.rounded_rectangle([W / 2 - bw / 2, y0, W / 2 + bw / 2, y0 + bh], radius=20, fill=(20, 15, 25, int(150 * alpha)))
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + 13 + lh * i + lh / 2), l, font=f, fill=(255, 250, 230, int(255 * alpha)), anchor="mm",
               stroke_width=3, stroke_fill=(30, 20, 30, int(255 * alpha)))
    frame.alpha_composite(layer)


def apply_camera(frame, cam):
    """cam = (cx, cy, zoom)."""
    cx, cy, z = cam
    if z <= 1.001:
        return frame
    cw, chh = W / z, H / z
    x0 = min(max(cx - cw / 2, 0), W - cw)
    y0 = min(max(cy - chh / 2, 0), H - chh)
    return frame.crop((int(x0), int(y0), int(x0 + cw), int(y0 + chh))).resize((W, H), Image.BILINEAR)
