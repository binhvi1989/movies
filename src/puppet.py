# -*- coding: utf-8 -*-
"""Rối khớp (puppet rig) dựng từ chân dung cắt dán: đầu, thân, hai tay, hai chân với khớp xoay,
chớp mắt, khẩu hình khi nói, tự động vung tay/chân khi đi.

Toạ độ bộ phận cho từng nhân vật đo trên ảnh assets/cutouts/<tên>.png (tỉ lệ 0..1 theo chiều rộng / cao).
Tay chân được tách bằng mặt nạ màu da trong khung hộp đã đo; chỗ tay che thân (Kaka khoanh tay) được vá lại.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUT_DIR = os.path.join(ROOT, "assets", "cutouts")
WORK_H = 620  # độ phân giải làm việc (px) của rối

# (x, y) tỉ lệ. arms: hộp (x0,y0,x1,y1); rest: hướng tay gốc trong ảnh (0 = buông xuống, 180 = giơ lên)
RIGS = {
    "kaka": dict(neck=0.42, shoulders=((0.16, 0.49), (0.85, 0.49)), arms=((0.12, 0.43, 0.5, 0.69), (0.5, 0.43, 0.88, 0.69)), rest=(0, 0),
                 hips=((0.38, 0.86), (0.62, 0.86)), legs_y=0.845, eyes=((0.37, 0.265), (0.61, 0.265)), eye_w=0.075, mouth=(0.5, 0.345, 0.11), inpaint=True,
                 synth_arms=dict(hands=((0.3, 0.55, 0.5, 0.67), (0.5, 0.55, 0.7, 0.67)), length=0.27, thick=0.095)),
    "puka": dict(neck=0.41, shoulders=((0.3, 0.47), (0.7, 0.47)), arms=((0.0, 0.3, 0.3, 0.58), (0.7, 0.3, 1.0, 0.58)), rest=(150, 150),
                 hips=((0.42, 0.82), (0.58, 0.82)), legs_y=0.81, eyes=((0.4, 0.28), (0.61, 0.28)), eye_w=0.085, mouth=(0.5, 0.35, 0.2)),
    "moon": dict(neck=0.33, shoulders=((0.17, 0.38), (0.83, 0.38)), arms=((0.0, 0.39, 0.21, 0.72), (0.79, 0.39, 1.0, 0.72)), rest=(0, 0),
                 hips=((0.42, 0.77), (0.58, 0.77)), legs_y=0.765, eyes=((0.38, 0.19), (0.62, 0.19)), eye_w=0.07, mouth=(0.5, 0.265, 0.12)),
    "sam": dict(neck=0.30, shoulders=((0.18, 0.35), (0.82, 0.35)), arms=((0.0, 0.37, 0.23, 0.68), (0.77, 0.37, 1.0, 0.68)), rest=(0, 0),
                 hips=((0.42, 0.79), (0.58, 0.79)), legs_y=0.785, eyes=((0.42, 0.17), (0.6, 0.17)), eye_w=0.065, mouth=(0.5, 0.235, 0.1)),
    "muoi": dict(neck=0.33, shoulders=((0.12, 0.39), (0.88, 0.39)), arms=((0.0, 0.37, 0.18, 0.72), (0.82, 0.37, 1.0, 0.72)), rest=(0, 0),
                 hips=((0.4, 0.78), (0.6, 0.78)), legs_y=0.775, eyes=((0.38, 0.2), (0.62, 0.2)), eye_w=0.07, mouth=(0.5, 0.285, 0.1)),
    "eric": dict(neck=0.35, shoulders=((0.3, 0.41), (0.7, 0.41)), arms=((0.0, 0.2, 0.34, 0.52), (0.66, 0.2, 1.0, 0.52)), rest=(145, 145),
                 hips=((0.42, 0.83), (0.58, 0.83)), legs_y=0.82, eyes=((0.4, 0.2), (0.6, 0.2)), eye_w=0.06, mouth=(0.5, 0.28, 0.08)),
    "lu": dict(neck=0.44, shoulders=None, arms=None, rest=(0, 0), hips=None, legs_y=None,
               eyes=((0.37, 0.19), (0.63, 0.19)), eye_w=0.05, mouth=(0.5, 0.325, 0.08), dog=True),
}

# tư thế: góc đích của tay trái/phải (None = giữ nguyên ảnh gốc). Góc: 0 buông xuống, 90 ngang, 180 giơ thẳng lên; âm = hướng vào trong.
POSES = {
    "stand": (None, None), "walk": (None, None), "rest": (None, None),
    "wave": (None, 160), "cheer": (165, 165), "lion": (172, 172), "drum": (55, 55), "fan": (None, 125),
    "hold": (-30, -30), "hug": (40, 40), "cry": (-150, -150), "point": (None, 95), "eat": (None, -145),
    "shrug": (25, 25), "pull": (None, 60), "boo": (150, 150), "claws": (140, 140), "sit": (None, None),
}


# ------------------------------------------------------------------ tách bộ phận
_RIG_CACHE = {}


def _skin_mask(arr):
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    return (r > 140) & (r - b > 35) & (g > b + 8) & (b > 85) & (r >= g)


def _soft_alpha(mask, blur=0.8):
    a = Image.fromarray((mask * 255).astype(np.uint8))
    return a.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(blur))


def _inpaint_down(rgb, alpha_shirt, hole):
    """Lấp lỗ (chỗ tay che thân) bằng trung bình màu áo ở hàng gần nhất phía trên và phía dưới, từng cột."""
    h, w, _ = rgb.shape
    out = rgb.copy().astype(np.float32)
    for x in range(w):
        col = hole[:, x]
        if not col.any():
            continue
        ys_ = np.where(col)[0]
        y0, y1 = ys_.min(), ys_.max()
        up = next((rgb[y, x].astype(np.float32) for y in range(y0 - 1, -1, -1) if alpha_shirt[y, x] and not col[y]), None)
        dn = next((rgb[y, x].astype(np.float32) for y in range(y1 + 1, h) if alpha_shirt[y, x] and not col[y]), None)
        if up is None and dn is None:
            continue
        if up is None:
            up = dn
        if dn is None:
            dn = up
        for y in ys_:
            f = (y - y0 + 1) / (y1 - y0 + 2)
            out[y, x] = up * (1 - f) + dn * f
    return out.astype(np.uint8)


def load_rig(name):
    """Tách ảnh cắt dán thành các bộ phận (ở độ phân giải WORK_H). Trả về dict các lớp RGBA + thông số."""
    if name in _RIG_CACHE:
        return _RIG_CACHE[name]
    rig = RIGS[name]
    src = Image.open(os.path.join(CUT_DIR, f"{name}.png")).convert("RGBA")
    sc = WORK_H / src.height
    W, H = int(src.width * sc), WORK_H
    src = src.resize((W, H), Image.LANCZOS)
    arr = np.asarray(src)
    alpha = arr[:, :, 3] > 40
    ys, xs = np.mgrid[0:H, 0:W]
    fx, fy = xs / W, ys / H
    parts = {}
    if rig.get("dog"):
        head = alpha & (fy < rig["neck"] + 0.03)
        body = alpha & (fy >= rig["neck"] - 0.02)
        for key, m in (("head", head), ("torso", body)):
            im = Image.fromarray(arr.copy())
            im.putalpha(Image.fromarray((m * arr[:, :, 3]).astype(np.uint8)))
            parts[key] = im
        info = dict(W=W, H=H, parts=parts, neck=(W * 0.5, H * rig["neck"]), shoulders=None, hips=None, rig=rig)
        _RIG_CACHE[name] = info
        return info
    skin = _skin_mask(arr[:, :, :3]) & alpha
    arm_masks = []
    for (x0, y0, x1, y1) in rig["arms"]:
        box = (fx >= x0) & (fx <= x1) & (fy >= y0) & (fy <= y1)
        m = box & skin
        # giãn nhẹ để lấy viền tay
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        m &= box & alpha
        arm_masks.append(m)
    legs_y = rig["legs_y"]
    leg_l = alpha & (fy >= legs_y) & (fx < 0.5)
    leg_r = alpha & (fy >= legs_y) & (fx >= 0.5)
    head = alpha & (fy < rig["neck"])
    torso = alpha & (fy >= rig["neck"]) & (fy < legs_y) & ~arm_masks[0] & ~arm_masks[1]
    rgb = arr[:, :, :3].copy()
    if rig.get("inpaint"):
        # lỗ = vùng tay nằm bên trong thân (có pixel áo hai bên theo hàng)
        inside = np.zeros_like(alpha)
        for y in range(H):
            row = torso[y]
            if row.any():
                xsr = np.where(row)[0]
                inside[y, xsr.min():xsr.max() + 1] = True
        hole = (arm_masks[0] | arm_masks[1]) & inside & (fy >= rig["neck"]) & (fy < legs_y)
        rgb = _inpaint_down(rgb, torso, hole)
        torso = torso | hole
    base = np.dstack([rgb, arr[:, :, 3]])
    synth = rig.get("synth_arms")
    if synth:
        # tay khoanh -> dựng tay buông thẳng từ vai, ghép bàn tay thật ở cổ tay
        skin_rgb0 = tuple(int(v) for v in arr[:, :, :3][skin & (fy > 0.5) & (fy < 0.7)].reshape(-1, 3).mean(axis=0))
        for i, (hx0, hy0, hx1, hy1) in enumerate(synth["hands"]):
            sx, sy = W * rig["shoulders"][i][0], H * rig["shoulders"][i][1]
            L, th = H * synth["length"], W * synth["thick"]
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            ex, ey = sx + (-1 if i == 0 else 1) * W * 0.01, sy + L
            d.line([(sx, sy), (ex, ey)], fill=skin_rgb0 + (255,), width=int(th))
            d.ellipse([sx - th / 2, sy - th / 2, sx + th / 2, sy + th / 2], fill=skin_rgb0 + (255,))
            # bóng nhẹ một bên cánh tay
            dark = tuple(max(0, c - 28) for c in skin_rgb0) + (255,)
            d.line([(sx + (th * 0.3 if i == 0 else -th * 0.3), sy), (ex + (th * 0.3 if i == 0 else -th * 0.3), ey)], fill=dark, width=max(2, int(th * 0.22)))
            # bàn tay thật
            hm = (fx >= hx0) & (fx <= hx1) & (fy >= hy0) & (fy <= hy1) & skin
            ys_, xs_ = np.where(hm)
            if len(xs_):
                crop = Image.fromarray(base).crop((xs_.min(), ys_.min(), xs_.max() + 1, ys_.max() + 1))
                cm = Image.fromarray((hm[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
                crop.putalpha(cm)
                crop = crop.rotate(-90 if i == 0 else 90, expand=True, resample=Image.BICUBIC)
                hw = int(th * 1.25)
                crop = crop.resize((hw, int(crop.height * hw / crop.width)), Image.LANCZOS)
                layer.alpha_composite(crop, (int(ex - hw / 2), int(ey - th * 0.3)))
            else:
                d.ellipse([ex - th * 0.7, ey - th * 0.3, ex + th * 0.7, ey + th * 1.1], fill=skin_rgb0 + (255,))
            parts["arm_l" if i == 0 else "arm_r"] = layer
    for key, m in (("head", head), ("torso", torso), ("arm_l", arm_masks[0]), ("arm_r", arm_masks[1]), ("leg_l", leg_l), ("leg_r", leg_r)):
        if synth and key in ("arm_l", "arm_r"):
            continue
        im = Image.fromarray(base.copy())
        a = _soft_alpha(m)
        a = Image.fromarray((np.asarray(a).astype(np.float32) * (arr[:, :, 3] / 255.0)).astype(np.uint8))
        im.putalpha(a)
        parts[key] = im
    # màu da gần mắt (để vẽ mí mắt khi chớp)
    ex, ey = rig["eyes"][0]
    sx, sy = int(ex * W), int((ey + 0.06) * H)
    skin_rgb = tuple(int(v) for v in arr[max(0, sy - 2):sy + 3, max(0, sx - 2):sx + 3, :3].reshape(-1, 3).mean(axis=0))
    info = dict(W=W, H=H, parts=parts, neck=(W * 0.5, H * rig["neck"]),
                shoulders=[(W * sx_, H * sy_) for sx_, sy_ in rig["shoulders"]], hips=[(W * hx, H * hy) for hx, hy in rig["hips"]],
                rig=rig, skin=skin_rgb)
    _RIG_CACHE[name] = info
    return info


# ------------------------------------------------------------------ vẽ
def _rot_about(img, pivot, deg):
    """Xoay ảnh quanh điểm pivot (toạ độ ảnh), trả về ảnh và toạ độ góc trên-trái mới sao cho pivot giữ nguyên."""
    if abs(deg) < 0.3:
        return img, (0, 0)
    px, py = pivot
    out = img.rotate(deg, resample=Image.BICUBIC, expand=True, center=(px, py))
    # với expand=True, PIL dịch ảnh: pivot mới = pivot cũ + (out.size - img.size)/2
    dx = (out.width - img.width) / 2
    dy = (out.height - img.height) / 2
    return out, (-dx, -dy)


def _draw_face(head, info, t, talk, mouth, blink):
    """Vẽ mí mắt (chớp) và khẩu hình lên bản sao của lớp đầu."""
    rig = info["rig"]
    W, H = info["W"], info["H"]
    head = head.copy()
    d = ImageDraw.Draw(head)
    if blink:
        ew = rig["eye_w"] * W
        for ex, ey in rig["eyes"]:
            cx, cy = ex * W, ey * H
            d.ellipse([cx - ew * 0.65, cy - ew * 0.5, cx + ew * 0.65, cy + ew * 0.45], fill=info.get("skin", (235, 190, 160)) + (255,))
            d.line([(cx - ew * 0.55, cy + ew * 0.1), (cx + ew * 0.55, cy + ew * 0.1)], fill=(60, 40, 40, 255), width=max(2, int(ew * 0.12)))
    mx, my, mw = rig["mouth"]
    cx, cy, w = mx * W, my * H, mw * W
    if mouth == "talk":
        ph = (t * 7.5) % 1.0
        k = 0.35 + 0.65 * abs(math.sin(ph * math.pi))
        rw, rh = w * 0.55, w * 0.42 * k
        d.ellipse([cx - rw, cy - rh * 0.6, cx + rw, cy + rh], fill=(110, 35, 45, 255), outline=(70, 30, 35, 255), width=2)
        if rh > w * 0.15:
            d.rectangle([cx - rw * 0.7, cy - rh * 0.5, cx + rw * 0.7, cy - rh * 0.5 + max(2, rh * 0.25)], fill=(250, 250, 250, 255))
            d.ellipse([cx - rw * 0.5, cy + rh * 0.2, cx + rw * 0.5, cy + rh * 1.05], fill=(230, 110, 130, 255))
    elif mouth == "cry":
        k = 0.8 + 0.2 * math.sin(t * 9)
        rw, rh = w * 0.6, w * 0.6 * k
        d.ellipse([cx - rw, cy - rh * 0.4, cx + rw, cy + rh], fill=(110, 35, 45, 255), outline=(70, 30, 35, 255), width=2)
        d.ellipse([cx - rw * 0.5, cy + rh * 0.3, cx + rw * 0.5, cy + rh * 1.0], fill=(230, 110, 130, 255))
    elif mouth == "o":
        rw = w * 0.3
        d.ellipse([cx - rw, cy - rw * 1.1, cx + rw, cy + rw * 1.1], fill=(110, 35, 45, 255), outline=(70, 30, 35, 255), width=2)
    elif mouth == "grin":
        rw, rh = w * 0.6, w * 0.3
        d.chord([cx - rw, cy - rh, cx + rw, cy + rh], 0, 180, fill=(250, 250, 250, 255), outline=(70, 30, 35, 255), width=2)
    return head


def _arm_angle(target, rest, side):
    """Góc xoay (độ, theo PIL: dương = ngược chiều kim đồng hồ) để tay đạt góc đích. side -1 trái, 1 phải."""
    if target is None:
        return 0.0
    delta = target - rest
    # PIL xoay ngược chiều kim đồng hồ trên màn hình: tay trái (nhìn từ người xem) cần góc âm để vung ra ngoài
    return -delta if side < 0 else delta


def render(name, st, t):
    """Vẽ rối ở trạng thái st (dict trạng thái actor) tại thời điểm t. Trả về ảnh RGBA và (anchor_x, anchor_y) = giữa bàn chân."""
    info = load_rig(name)
    rig = info["rig"]
    W, H = info["W"], info["H"]
    parts = info["parts"]
    pose = st.get("pose", "stand") or "stand"
    walking = st.get("_walking", 0.0)
    ph = t * 3.6
    swing = math.sin(ph * 2 * math.pi)
    # --- canvas rộng hơn để chứa tay giơ / chân vung
    CW, CH = int(W * 2.4), int(H * 1.25)
    ox, oy = (CW - W) // 2, CH - H - int(H * 0.02)
    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))

    def paste(img, pos):
        canvas.alpha_composite(img, (int(ox + pos[0]), int(oy + pos[1])))

    tilt = st.get("headtilt", 0.0) or 0.0
    talk = bool(st.get("talk"))
    mouth = st.get("mouth") or ("talk" if talk else None)
    seed = sum(ord(c) for c in name)
    blink_period = 3.2 + (seed % 5) * 0.35
    blink = ((t + seed * 0.37) % blink_period) < 0.13
    if st.get("mouth") == "cry":
        blink = True  # nhắm mắt khi khóc

    if rig.get("dog"):
        body = parts["torso"]
        paste(body, (0, 0))
        head = _draw_face(parts["head"], info, t, talk, "talk" if talk else None, blink)
        ang = tilt + (6 * swing if walking else 0) + (4 * math.sin(t * 5) if talk else 0)
        img, off = _rot_about(head, info["neck"], ang)
        paste(img, off)
    else:
        aL, aR = POSES.get(pose, (None, None))
        if st.get("arm_l") is not None:
            aL = st["arm_l"]
        if st.get("arm_r") is not None:
            aR = st["arm_r"]
        restL, restR = rig["rest"]
        if walking:
            aL = (restL if aL is None else aL) + 28 * swing * walking
            aR = (restR if aR is None else aR) - 28 * swing * walking
        # dao động nhỏ theo tư thế cho tự nhiên
        wob = st.get("armwob", 0.0) or 0.0
        if pose in ("wave", "cheer", "lion", "fan", "drum", "boo", "claws") and wob == 0:
            wob = {"wave": 22, "cheer": 10, "lion": 8, "fan": 25, "drum": 30, "boo": 10, "claws": 12}[pose]
        if wob:
            f = {"drum": 4.5, "fan": 3.0}.get(pose, 2.6)
            w1 = wob * math.sin(2 * math.pi * f * t)
            if aL is not None and pose != "wave":
                aL = aL + w1
            if aR is not None:
                aR = aR - w1 if pose in ("drum",) else aR + w1
        legs = [parts["leg_l"], parts["leg_r"]]
        leg_ang = [0.0, 0.0]
        if walking:
            leg_ang = [18 * swing * walking, -18 * swing * walking]
        if pose == "sit":
            leg_ang = [55, -55]
        for i, (leg, hip) in enumerate(zip(legs, info["hips"])):
            img, off = _rot_about(leg, hip, leg_ang[i])
            paste(img, off)

        def draw_head():
            head = _draw_face(parts["head"], info, t, talk, mouth, blink)
            ang = tilt + (3 * swing if walking else 0) + (3.5 * math.sin(t * 6.3) if talk else 0)
            turn = st.get("turn", 0.0) or 0.0
            if abs(turn) > 0.01:
                nw = max(2, int(head.width * (1 - 0.18 * abs(turn))))
                head = head.resize((nw, head.height), Image.LANCZOS)
                dx = (W - nw) / 2 + turn * W * 0.06
                img, off = _rot_about(head, (info["neck"][0] - dx, info["neck"][1]), ang)
                paste(img, (off[0] + dx, off[1]))
            else:
                img, off = _rot_about(head, info["neck"], ang)
                paste(img, off)

        def draw_arms():
            for i, (arm, sh, side, a) in enumerate(((parts["arm_l"], info["shoulders"][0], -1, aL), (parts["arm_r"], info["shoulders"][1], 1, aR))):
                rest = rig["rest"][i]
                ang = _arm_angle(a, rest, side)
                img, off = _rot_about(arm, sh, ang)
                paste(img, off)

        if rig.get("synth_arms"):
            # tay dựng lại nằm dưới tay áo: đầu -> tay -> thân (thân che phần tay dưới tay áo)
            draw_head()
            draw_arms()
            paste(parts["torso"], (0, 0))
        else:
            paste(parts["torso"], (0, 0))
            draw_arms()
            draw_head()
    return canvas, (ox + W / 2, oy + H)


if __name__ == "__main__":
    S = "/tmp/claude-0/-home-user-movies/4eb93384-7854-5b1d-b894-3192c5ee23bc/scratchpad"
    names = ["kaka", "moon", "eric", "muoi"]
    poses = ["walk", "cheer", "cry", "hold", "wave"]
    sheet = Image.new("RGB", (len(poses) * 300, len(names) * 460), (60, 160, 90))
    for j, n in enumerate(names):
        for i, pz in enumerate(poses):
            st = dict(pose=pz, talk=(pz == "wave"), mouth="cry" if pz == "cry" else None, _walking=1.0 if pz == "walk" else 0.0)
            img, (ax, ay) = render(n, st, 0.3 + i * 0.17)
            sc = 440 / img.height
            img = img.resize((int(img.width * sc), 440), Image.LANCZOS)
            sheet.paste(img, (i * 300 + 150 - img.width // 2, j * 460 + 10), img)
    sheet.save(f"{S}/puppet_test.png")
    print("ok")
