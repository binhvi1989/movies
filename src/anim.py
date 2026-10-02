# -*- coding: utf-8 -*-
"""Bộ máy hoạt hình tối giản: keyframe -> trạng thái theo thời gian, và vẽ một khung hình."""
import math

from PIL import Image, ImageDraw, ImageFont

import characters as ch
import puppet

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
                text="", size=48, color=(255, 255, 255), tail=None, sway=0.0,
                squash=1.0, ground=None, emote=None, shadow=True,
                mouth=None, headtilt=0.0, turn=0.0, arm_l=None, arm_r=None, armwob=0.0, _walking=0.0)

# ---- nhân vật cắt dán từ chân dung (assets/cutouts/<name>.png), neo giữa bàn chân
import os
CUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cutouts")
CUT_BASE_H = 470  # chiều cao (px) khi scale = 1 của nhân vật cao nhất
CUT_REL_H = {"moon": 1.0, "sam": 0.97, "kaka": 0.95, "muoi": 0.9, "puka": 0.86, "eric": 0.8, "lu": 0.62}
_cut_src = {}
_cut_cache = {}


def cut_image(name, h_px, flip=False, squash=1.0):
    key = (name, int(h_px), flip, round(squash, 2))
    if key in _cut_cache:
        return _cut_cache[key]
    if name not in _cut_src:
        _cut_src[name] = Image.open(os.path.join(CUT_DIR, f"{name}.png")).convert("RGBA")
    src = _cut_src[name]
    h = max(2, int(h_px * squash))
    w = max(2, int(src.width * h_px / src.height / math.sqrt(squash)))
    img = src.resize((w, h), Image.LANCZOS)
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if len(_cut_cache) > 600:
        _cut_cache.clear()
    _cut_cache[key] = img
    return img


class Actor:
    """kind: kid | lu | prop | text | bubble ; name: tên nhân vật / loại đạo cụ."""

    def __init__(self, kind, name="", z=0, **tracks):
        self.kind, self.name, self.z = kind, name, z
        self.tracks = {}
        for k, v in tracks.items():
            self.set(k, v)

    def set(self, key, val):
        if isinstance(val, list):
            self.tracks[key] = Track(val, discrete=key in ("pose", "expr", "flip", "talk", "item", "visible", "text", "color", "tail", "emote", "shadow", "mouth"))
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


def actor_image(actor, st, t):
    """Ảnh RGBA của nhân vật/đạo cụ ở trạng thái st và toạ độ góc trên-trái để dán."""
    kind = actor.kind
    bob = st["bob"] * math.sin(2 * math.pi * st["bobf"] * t) if st["bob"] else 0.0
    sway = st["sway"] * math.sin(2 * math.pi * st["bobf"] * t) if st["sway"] else 0.0
    if kind == "kid":
        expr = st["expr"]
        if st["talk"] and int(t * 8) % 2 == 0:
            expr = "talk"
        phase = (t * st["walkspeed"]) % 1.0 if st["pose"] in ("walk",) else 0.0
        img = ch.sprite(actor.name, st["pose"], expr, round(phase * 8) / 8, bool(st["flip"]), round(st["look"], 1))
    elif kind == "lu":
        expr = st["expr"]
        if st["talk"] and int(t * 8) % 2 == 0:
            expr = "laugh"
        phase = (t * 4.0) % 1.0 if st["pose"] == "run" else 0.0
        img = ch.lu(st["pose"], expr, round(phase * 6) / 6, bool(st["flip"]), st["item"])
    elif kind == "prop":
        img = ch.prop(actor.name)
    elif kind == "puppet":
        sq = st["squash"]
        img, (ax, ay) = puppet.render(actor.name, st, t)
        target_h = CUT_BASE_H * CUT_REL_H.get(actor.name, 0.9) * st["scale"]
        k = target_h / puppet.WORK_H
        nw, nh = max(2, int(img.width * k / math.sqrt(sq))), max(2, int(img.height * k * sq))
        img = img.resize((nw, nh), Image.LANCZOS)
        ax, ay = ax * k / math.sqrt(sq), ay * k * sq
        if st["flip"]:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
            ax = img.width - ax
        if abs(st["rot"] + sway) > 0.3:
            img2 = img.rotate(st["rot"] + sway, resample=Image.BICUBIC, expand=True, center=(ax, ay))
            ax += (img2.width - img.width) / 2
            ay += (img2.height - img.height) / 2
            img = img2
        x = int(st["x"] - ax)
        y = int(st["y"] + bob - ay)
        return img, x, y
    elif kind == "cut":
        sq = st["squash"]
        if st["talk"]:
            sq *= 1.0 + 0.025 * math.sin(2 * math.pi * 7 * t)
        img = cut_image(actor.name, CUT_BASE_H * CUT_REL_H.get(actor.name, 0.9) * st["scale"], bool(st["flip"]), sq)
        img = _rotate(img, st["rot"] + sway)
        x = int(st["x"] - img.width / 2)
        y = int(st["y"] + bob - img.height)
        return img, x, y
    else:
        raise ValueError(kind)
    img = _scaled(img, st["scale"] * (PROP_SCALE if kind == "prop" else KID_SCALE))
    img = _rotate(img, st["rot"] + sway)
    x = int(st["x"] - img.width / 2)
    y = int(st["y"] + bob - img.height)
    return img, x, y


def draw_actor(frame, actor, st, t):
    if not st["visible"] or st["alpha"] <= 0:
        return
    if actor.kind == "bubble":
        if st["text"]:
            draw_bubble(frame, st["text"], st["x"], st["y"], st["tail"], size=int(st["size"]))
        return
    if actor.kind == "text":
        if st["text"]:
            draw_pop_text(frame, st["text"], st["x"], st["y"], st["size"], st["color"], st["rot"], st["alpha"], st["scale"])
        return
    if actor.kind == "puppet":
        st = dict(st)
        x0, x1 = actor.state(max(0, t - 0.06))["x"], actor.state(t + 0.06)["x"]
        speed = abs(x1 - x0) / 0.12
        st["_walking"] = min(1.0, speed / 160.0) if speed > 30 else 0.0
        if st["emote"] == "cry" and not st["mouth"]:
            st["mouth"] = "cry"
    img, x, y = actor_image(actor, st, t)
    if actor.kind in ("cut", "lu", "puppet") and st["shadow"]:
        draw_shadow(frame, st["x"], st["ground"] if st["ground"] is not None else st["y"], img.width * 0.55,
                    lift=max(0.0, (st["ground"] if st["ground"] is not None else st["y"]) - (st["y"] + (st["bob"] * math.sin(2 * math.pi * st["bobf"] * t) if st["bob"] else 0))))
    if st["alpha"] < 1:
        a = img.getchannel("A").point(lambda v: int(v * st["alpha"]))
        img = img.copy()
        img.putalpha(a)
    frame.alpha_composite(img, (x, y))
    if actor.kind in ("cut", "puppet") and st["emote"]:
        draw_emote(frame, st["emote"], x + img.width / 2, y, img.width, img.height, t)


def draw_shadow(frame, x, ground, w, lift=0.0):
    """Bóng đổ mềm dưới chân, nhỏ và nhạt dần khi nhân vật nhảy lên."""
    k = max(0.35, 1.0 - lift / 250.0)
    w = w * k
    h = w * 0.22
    layer = Image.new("RGBA", (int(w) + 8, int(h) + 8), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([2, 2, w + 4, h + 4], fill=(20, 10, 10, int(80 * k)))
    from PIL import ImageFilter
    layer = layer.filter(ImageFilter.GaussianBlur(3))
    frame.alpha_composite(layer, (int(x - w / 2 - 4), int(ground - h / 2 - 4)))


def draw_emote(frame, kind, cx, top, w, h, t):
    """Biểu cảm vẽ thêm quanh đầu nhân vật cắt dán: cry | angry | sweat | hearts | music | zzz | stars | question."""
    d = ImageDraw.Draw(frame)
    head_y = top + h * 0.22
    if kind == "cry":
        for sgn in (-1, 1):
            for k in range(2):
                ph = ((t * 2.2 + k * 0.5 + (0.25 if sgn > 0 else 0)) % 1.0)
                ty = head_y + ph * h * 0.25
                tx = cx + sgn * w * 0.16 + sgn * ph * 8
                r = 7 + 4 * (1 - ph)
                d.ellipse([tx - r, ty - r * 1.4, tx + r, ty + r], fill=(120, 190, 255, 230), outline=(40, 60, 120), width=2)
        draw_pop_text(frame, "oa oa", cx + w * 0.55, top + h * 0.05, 34, (120, 190, 255), rot=8, scale=1 + 0.1 * math.sin(t * 9))
    elif kind == "angry":
        px, py = cx + w * 0.38, top - 6
        for a in (0, 90):
            dx, dy = (14, 0) if a == 0 else (0, 14)
            d.line([(px - dx, py - dy), (px + dx, py + dy)], fill=(230, 50, 50), width=6)
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(255, 220, 220))
    elif kind == "sweat":
        px, py = cx + w * 0.42, head_y - 10 + 6 * math.sin(t * 6)
        d.polygon([(px, py - 16), (px - 9, py + 4), (px + 9, py + 4)], fill=(130, 200, 255))
        d.ellipse([px - 9, py - 4, px + 9, py + 12], fill=(130, 200, 255), outline=(40, 60, 120), width=2)
    elif kind == "hearts":
        for k in range(3):
            ph = (t * 0.8 + k / 3) % 1.0
            draw_pop_text(frame, "♥", cx + (k - 1) * w * 0.35, top - 10 - ph * 70, 40, (255, 90, 120), rot=(k - 1) * 15, alpha=1 - ph)
    elif kind == "music":
        for k in range(2):
            ph = (t * 1.0 + k / 2) % 1.0
            draw_pop_text(frame, "♪" if k else "♫", cx + (k * 2 - 1) * w * 0.4, top - 5 - ph * 60, 42, (255, 230, 90), rot=(k * 2 - 1) * 12, alpha=1 - ph)
    elif kind == "zzz":
        for k in range(3):
            ph = (t * 0.6 + k / 3) % 1.0
            draw_pop_text(frame, "Z", cx + w * 0.3 + ph * 40, top - ph * 80, 28 + k * 8, (120, 140, 230), rot=-10, alpha=1 - ph)
    elif kind == "stars":
        for k in range(4):
            a = t * 3 + k * math.pi / 2
            draw_pop_text(frame, "✦", cx + math.cos(a) * w * 0.45, top + 10 + math.sin(a) * 18, 34, (255, 220, 70), rot=k * 20)
    elif kind == "question":
        draw_pop_text(frame, "?", cx + w * 0.45, top - 10 + 5 * math.sin(t * 5), 60, (255, 220, 70), rot=10)


CAPTION_COLORS = {
    "nar": (255, 250, 230), "ma": (255, 220, 160), "kaka": (150, 210, 255), "puka": (255, 170, 200),
    "moon": (190, 240, 170), "sam": (255, 150, 230), "lu": (255, 200, 120), "all": (255, 230, 90),
    "muoi": (255, 205, 150), "eric": (160, 235, 235),
}


def draw_caption(frame, text, who="nar", alpha=1.0):
    from story import NAMES
    if who != "nar":
        text = f"{NAMES.get(who, who)}: {text}"
    color = CAPTION_COLORS.get(who, (255, 250, 230))
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
        d.text((W / 2, y0 + 13 + lh * i + lh / 2), l, font=f, fill=color + (int(255 * alpha),), anchor="mm",
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
