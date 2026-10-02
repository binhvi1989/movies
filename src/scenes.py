# -*- coding: utf-8 -*-
"""Biên đạo từng cảnh cho nhân vật cắt dán từ chân dung (kiểu 2.5D: nhún, nghiêng, nhảy, xoay, bóng đổ).

Mỗi hàm cảnh nhận `s` (từ timeline.json) và trả về dict(actors, camera, sfx, title, night, no_bubble).
K["khoá"] = (bắt_đầu, kết_thúc) của câu thoại so với đầu cảnh. Bong bóng thoại và cử động khi nói tự động.
Toạ độ: khung 1280x720, (x, y) là điểm giữa bàn chân nhân vật.
"""
import math

from anim import Actor, Track

FLOOR = 668
FAR = 585

RED = (255, 90, 80)
YEL = (255, 220, 70)
PINK = (255, 150, 200)
BLUE = (120, 190, 255)
GREEN = (120, 240, 120)
WHITE = (255, 255, 255)

# chiều cao gần đúng (px) ở scale 1, để đặt đạo cụ vào tay / đầu
H_OF = {"moon": 470, "sam": 456, "kaka": 447, "muoi": 423, "puka": 404, "eric": 376, "lu": 291}


def _t(s):
    L = [l["rel"] for l in s["lines"]]
    E = [l["rel"] + l["dur"] for l in s["lines"]]
    K = {l["key"]: (l["rel"], l["rel"] + l["dur"]) for l in s["lines"] if l.get("key")}
    return L, E, s["dur"], K


# ------------------------------------------------------------------ tiện ích
def kid(name, x0, gy=FLOOR, z=10, scale=1.0, **tr):
    """Nhân vật cắt dán; gy = cao độ mặt đất (bóng đổ). Có thể truyền x=[...], y=[...] riêng để di chuyển/nhảy."""
    ground = tr.pop("ground", gy)
    yy = tr.pop("y", gy)
    xx = tr.pop("x", x0)
    return Actor("cut", name, z=z, x=xx, y=yy, scale=scale, ground=ground, **tr)


def pop(text, t0, t1, x, y, size=70, color=YEL, rot=-8, jitter=True):
    a = Actor("text", z=50, text=[(0, ""), (t0, text), (t1, "")], x=x, y=y, size=size, color=color,
              scale=[(t0, 0.2), (t0 + 0.25, 1.15), (t0 + 0.4, 1.0), (t1 - 0.2, 1.0), (t1, 0.3)], rot=rot)
    if jitter:
        a.set("sway", 3.0).set("bobf", 3.0)
    return a


def name_card(name, role, t0, t1, x, y):
    return [
        Actor("text", z=55, text=[(0, ""), (t0, name), (t1, "")], x=x, y=y, size=58, color=YEL,
              scale=[(t0, 0.2), (t0 + 0.3, 1.1), (t0 + 0.45, 1.0)], rot=-4),
        Actor("text", z=55, text=[(0, ""), (t0 + 0.2, role), (t1, "")], x=x, y=y + 58, size=34, color=WHITE,
              scale=[(t0 + 0.2, 0.2), (t0 + 0.5, 1.05), (t0 + 0.65, 1.0)], rot=-4),
    ]


def hearts(t0, t1, x, y, n=3):
    out = []
    for i in range(n):
        tt = t0 + i * 0.5
        out.append(Actor("text", z=52, text=[(0, ""), (tt, "♥"), (t1, "")], x=x + (i - 1) * 60, size=54, color=(255, 90, 120),
                         y=[(tt, y), (t1, y - 120)], alpha=[(tt, 1.0), (t1, 0.0)], scale=[(tt, 0.3), (tt + 0.3, 1.0)]))
    return out


def stars(t0, t1, x, y, n=4):
    out = []
    for i in range(n):
        tt = t0 + i * 0.12
        a = i * 2 * math.pi / n
        out.append(Actor("text", z=52, text=[(0, ""), (tt, "✦"), (t1, "")], size=44, color=YEL,
                         x=[(tt, x), (t1, x + math.cos(a) * 140)], y=[(tt, y), (t1, y + math.sin(a) * 90)],
                         alpha=[(tt, 1.0), (t1, 0.0)], rot=i * 30))
    return out


def notes(t0, t1, x, y, n=6):
    """Nốt nhạc bay lên theo nhịp trống."""
    out = []
    for i in range(n):
        tt = t0 + i * (t1 - t0) / n
        out.append(Actor("text", z=52, text=[(0, ""), (tt, "♪" if i % 2 else "♫"), (tt + 1.2, "")], size=46, color=YEL if i % 2 else PINK,
                         x=[(tt, x + (i % 3 - 1) * 90), (tt + 1.2, x + (i % 3 - 1) * 120)], y=[(tt, y), (tt + 1.2, y - 110)],
                         alpha=[(tt, 1.0), (tt + 1.2, 0.0)], rot=(i % 3 - 1) * 15))
    return out


def _keys(actor, key, default):
    return actor.tracks[key].keys if key in actor.tracks else [(0, default)]


def jump(actor, t0, h=60, n=1, period=0.5):
    y0 = actor.state(t0)["y"]
    ys = _keys(actor, "y", y0)
    sq = _keys(actor, "squash", 1.0)
    for k in range(n):
        a = t0 + k * period
        ys += [(a, y0), (a + period * 0.5, y0 - h), (a + period, y0)]
        sq += [(a, 0.92), (a + period * 0.25, 1.06), (a + period * 0.75, 1.0), (a + period, 0.92), (a + period + 0.1, 1.0)]
    actor.set("y", ys).set("squash", sq)
    return actor


def spin(actor, t0, n=4, step=0.15):
    fs = _keys(actor, "flip", False)
    for k in range(n * 2 + 1):
        fs.append((t0 + k * step, k % 2 == 1))
    actor.set("flip", fs)
    return actor


def shake(actor, t0, t1, amp=12, step=0.12):
    xs = _keys(actor, "x", actor.state(t0)["x"])
    base = actor.state(t0)["x"]
    t, k = t0, 0
    while t < t1:
        xs.append((t, base + (amp if k % 2 == 0 else -amp)))
        t += step
        k += 1
    xs.append((t1, base))
    actor.set("x", xs)
    return actor


def wobble(actor, t0, t1, deg=8, step=0.18):
    """Lắc lư nghiêng người qua lại (nhảy múa)."""
    rs = _keys(actor, "rot", 0)
    t, k = t0, 0
    while t < t1:
        rs.append((t, deg if k % 2 == 0 else -deg))
        t += step
        k += 1
    rs.append((t1, 0))
    actor.set("rot", rs)
    return actor


def walk(actor, t0, t1, x0, x1, flip_auto=True):
    xs = _keys(actor, "x", x0)
    actor.set("x", xs + [(t0, x0), (t1, x1)])
    bs = _keys(actor, "bob", 0)
    actor.set("bob", bs + [(t0, 7), (t1 - 0.01, 7), (t1, 0)])
    actor.set("bobf", 4.0)
    if flip_auto:
        fs = _keys(actor, "flip", False)
        actor.set("flip", fs + [(t0, x1 < x0), (t1, False)])
    return actor


def hand(actor, side=1, lift=0.45):
    """Điểm gần bàn tay (x,y) của nhân vật ở trạng thái đứng: side -1 trái, 1 phải."""
    st = actor.state(0)
    h = H_OF.get(actor.name, 400) * st["scale"]
    return st["x"] + side * h * 0.22, st["y"] - h * lift


def follow(prop, actor, dx, dy):
    """Đạo cụ bám theo chuyển động x/y của nhân vật (lệch dx, dy)."""
    xs = [(t, v + dx) for t, v in _keys(actor, "x", 640)]
    ys = [(t, v + dy) for t, v in _keys(actor, "y", FLOOR)]
    prop.set("x", xs).set("y", ys)
    if "flip" in actor.tracks:
        prop.set("flip", actor.tracks["flip"].keys)
    return prop


# ------------------------------------------------------------------ các cảnh
def sc_intro(s):
    L, E, T, K = _t(s)
    acts = []
    door_y = 445
    t_kids = K["kids"][0] + 0.2
    order = (("kaka", 520), ("puka", 568), ("moon", 616), ("sam", 664), ("muoi", 712), ("eric", 760))
    for i, (n, x) in enumerate(order):
        tt = t_kids + i * 0.18
        a = kid(n, x, door_y, z=10 + i, scale=0.33, visible=[(0, False), (tt, True)],
                y=[(0, door_y + 150), (tt, door_y + 150), (tt + 0.35, door_y)])
        jump(a, K["hello"][0] + i * 0.08, 28, 2, 0.4)
        a.set("bob", [(0, 0), (tt + 0.4, 3)]).set("bobf", 2.5 + i * 0.3)
        acts.append(a)
    lu = kid("lu", -200, door_y + 2, z=20, scale=0.33, x=[(0, -200), (t_kids + 0.9, -200), (t_kids + 2.2, 470), (K["zoom"][0], 470), (K["zoom"][0] + 1.0, 810)],
             bob=6, bobf=5)
    acts.append(lu)
    for i, (w_, x) in enumerate((("quậy!", 300), ("ồn!", 980), ("vui!", 200), ("Trung thu!", 1060))):
        tt = K["kids"][0] + 1.2 + i * 0.35
        acts.append(Actor("text", z=51, text=[(0, ""), (tt, w_), (K["hello"][0], "")], x=x, size=48, color=PINK if i % 2 else YEL,
                          y=[(tt, 520), (K["hello"][0], 380)], alpha=[(tt, 1.0), (K["hello"][0], 0.0)], rot=-10 + i * 7))
    cam = Track([(0, (640, 360, 1.0)), (K["zoom"][0] + 0.3, (640, 360, 1.0)), (T, (640, 330, 1.9))])
    return dict(actors=acts, camera=cam, sfx=[(0.3, "pop"), (t_kids, "pop"), (t_kids + 1.4, "bark"), (K["hello"][0], "sparkle")],
                title=[(0.2, T - 0.3)], no_bubble=True)


def sc_kaka(s):
    L, E, T, K = _t(s)
    acts = []
    kaka = kid("kaka", 640)
    walk(kaka, 0.1, K["intro"][0], -150, 640)
    jump(kaka, K["intro"][1] - 0.6, 40, 1, 0.45)
    acts.append(kaka)
    acts += name_card("KAKA", "anh Hai", K["intro"][0] + 0.3, K["intro"][1] + 1.0, 230, 180)
    # tập múa lân với đầu lân
    t0, t1 = K["dance"][0] + 0.6, K["drop"][0]
    lion = Actor("prop", "lion", z=14, scale=1.6, visible=[(0, False), (t0, True), (K["li"][1] + 0.6, False)])
    xs = [(0, 640)]
    hop = []
    t = t0
    k = 0
    while t < t1:
        hop.append((t, 640 + (-70 if k % 2 == 0 else 70)))
        t += 0.42
        k += 1
    kaka.set("x", kaka.tracks["x"].keys + [(t0, 640)] + hop + [(t1, 900), (t1 + 0.3, 930)])
    for k2 in range(len(hop)):
        jump(kaka, t0 + k2 * 0.42, 45, 1, 0.42)
    wobble(kaka, t0, t1, 7, 0.21)
    follow(lion, kaka, 0, -H_OF["kaka"] * 0.74)
    lion.set("rot", [(t, -v * 0.6) for t, v in kaka.tracks["rot"].keys])
    acts.append(lion)
    acts += notes(t0, t1, 640, 320)
    acts.append(pop("tùng tùng cắc!", t0 + 0.2, t1, 640, 150, 50, YEL, -5))
    # đụng kệ giày
    acts.append(pop("BỊCH!", K["drop"][0] + 0.2, K["drop"][1] + 0.3, 930, 230, 70, RED, -12))
    acts += stars(K["drop"][0] + 0.2, K["drop"][1] + 0.6, 930, 300)
    kaka.set("rot", kaka.tracks["rot"].keys + [(t1 + 0.05, 0), (t1 + 0.3, 18), (K["li"][0], 18), (K["li"][0] + 0.4, 0)])
    kaka.set("emote", [(0, None), (K["drop"][0] + 0.2, "stars"), (K["li"][0] + 0.4, None)])
    shake(kaka, K["drop"][0] + 0.2, K["drop"][0] + 0.9, 8)
    kaka.set("x", kaka.tracks["x"].keys + [(K["li"][0] + 0.4, 930), (K["li"][1], 640)])
    acts.append(pop("hì hì", K["li"][0] + 0.3, K["li"][1] + 0.4, 860, 300, 48, PINK, 8))
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (t0, "liondrum"), (K["drop"][0] + 0.2, "boing"), (K["li"][0] + 0.3, "laugh")], title=None)


def sc_puka(s):
    L, E, T, K = _t(s)
    acts = []
    puka = kid("puka", 640, z=11)
    walk(puka, 0.1, K["intro"][0], 1450, 640)
    jump(puka, K["intro"][0] + 0.4, 55, 2, 0.4)
    acts.append(puka)
    acts += name_card("PUKA", "chị Ba", K["intro"][0] + 0.3, K["intro"][1] + 0.8, 230, 180)
    # Kaka đi ngang, Puka nấp rồi hù
    kaka = kid("kaka", -200, z=10, scale=0.95)
    walk(kaka, L[1], K["boo"][0] - 0.2, -200, 420)
    kaka.set("x", kaka.tracks["x"].keys + [(K["oai"][0], 420), (K["oai"][0] + 0.4, 300)])
    jump(kaka, K["boo"][0] + 0.05, 70, 1, 0.4)
    kaka.set("rot", [(0, 0), (K["boo"][0] + 0.05, 0), (K["boo"][0] + 0.25, -15), (K["oai"][1], -15), (K["oai"][1] + 0.3, 0)])
    kaka.set("emote", [(0, None), (K["boo"][0], "sweat"), (K["hihi"][1], None)])
    acts.append(kaka)
    puka.set("x", puka.tracks["x"].keys + [(L[1], 640), (L[1] + 0.6, 1000), (K["boo"][0] - 0.3, 1000), (K["boo"][0], 560)])
    puka.set("scale", [(0, 1.0), (L[1] + 0.6, 1.0), (L[1] + 0.9, 0.85), (K["boo"][0] - 0.3, 0.85), (K["boo"][0], 1.05)])
    puka.set("y", puka.tracks["y"].keys + [(L[1] + 0.6, FLOOR), (L[1] + 0.9, FAR), (K["boo"][0] - 0.3, FAR), (K["boo"][0], FLOOR)])
    puka.set("ground", [(0, FLOOR), (L[1] + 0.9, FAR), (K["boo"][0], FLOOR)])
    jump(puka, K["boo"][0], 50, 1, 0.35)
    acts.append(pop("HÙ!", K["boo"][0], K["boo"][1] + 0.4, 560, 200, 90, RED, -10))
    acts.append(pop("Oái!", K["oai"][0], K["oai"][1] + 0.2, 300, 250, 60, BLUE, 8))
    jump(puka, K["hihi"][0], 30, 3, 0.3)
    puka.set("emote", [(0, None), (K["hihi"][0], "stars"), (K["hihi"][1] + 0.5, None)])
    acts.append(pop("HI HI!", K["hihi"][0] + 0.2, K["hihi"][1] + 0.5, 800, 250, 60, PINK, 8))
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["boo"][0], "boing"), (K["oai"][0], "swoosh"), (K["hihi"][0], "laugh")], title=None)


def sc_moon(s):
    L, E, T, K = _t(s)
    acts = []
    moon = kid("moon", 640)
    walk(moon, 0.1, K["intro"][0], -150, 640)
    moon.set("rot", [(0, 0), (K["intro"][0] + 2.0, 0), (K["intro"][0] + 2.4, -6), (K["intro"][1], -6), (K["intro"][1] + 0.3, 0)])
    moon.set("emote", [(0, None), (K["intro"][0] + 2.2, "question"), (K["intro"][1] + 0.3, None)])
    acts.append(moon)
    acts += name_card("MOON", "em (lớn tuổi nhất nhà)", K["intro"][0] + 0.3, K["intro"][1] + 0.5, 250, 180)
    hx, hy = hand(moon, 1)
    book = Actor("prop", "book", z=12, x=hx, y=hy + 20, scale=1.3, visible=[(0, False), (L[1], True), (K["lantern"][0], False)],
                 bob=4, bobf=1.5)
    acts.append(book)
    # anh Hai, chị Ba đứng cạnh (so chiều cao)
    kaka = kid("kaka", -200, z=9, scale=0.95)
    walk(kaka, L[1] - 0.3, L[1] + 0.6, -200, 330)
    puka = kid("puka", 1500, z=9, scale=0.95)
    walk(puka, L[1] - 0.3, L[1] + 0.6, 1500, 950)
    jump(puka, L[1] + 1.0, 25, 2, 0.35)
    acts += [kaka, puka]
    # làm lồng đèn: lồng đèn hiện trên tay Moon
    lantern = Actor("prop", "lantern", z=12, x=hx, y=hy + 40, scale=1.5, visible=[(0, False), (K["lantern"][0] + 0.8, True)])
    lantern.set("scale", [(K["lantern"][0] + 0.8, 0.2), (K["lantern"][0] + 1.1, 1.6), (K["lantern"][0] + 1.25, 1.5)])
    acts.append(lantern)
    acts += stars(K["lantern"][0] + 0.8, K["lantern"][1] + 0.6, hx, hy)
    jump(moon, K["lantern"][0] + 0.8, 30, 1, 0.4)
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["intro"][0] + 2.2, "boing"), (K["lantern"][0] + 0.8, "sparkle")], title=None)


def sc_sam(s):
    L, E, T, K = _t(s)
    acts = []
    sam = kid("sam", 640)
    walk(sam, 0.1, K["intro"][0], 1450, 640)
    jump(sam, K["intro"][0] + 0.3, 45, 2, 0.4)
    spin(sam, K["twirl"][0] + 0.3, 5, 0.14)
    wobble(sam, K["twirl"][0], K["twirl"][1], 6, 0.2)
    sam.set("emote", [(0, None), (K["twirl"][0], "stars"), (K["twirl"][1] + 0.5, None), (K["later"][0], "music"), (K["later"][1] + 0.5, None)])
    acts.append(sam)
    acts += name_card("SAM", "chị Tư", K["intro"][0] + 0.3, K["intro"][1] + 0.8, 230, 180)
    acts += stars(K["twirl"][0] + 0.4, K["twirl"][1] + 0.3, 640, 300)
    acts.append(pop("đẹp!", K["twirl"][1] - 0.2, K["twirl"][1] + 0.6, 950, 260, 56, PINK, 8))
    acts.append(pop("Sam ơi, phụ má!", K["call"][0], K["call"][1] + 0.3, 640, 110, 46, RED, -3))
    # lì: xoay người quay lưng, ngắm gương
    sam.set("flip", sam.tracks["flip"].keys + [(K["call"][0] + 0.3, True), (K["later"][1] + 0.5, False)])
    sam.set("rot", sam.tracks["rot"].keys + [(K["later"][0], 0), (K["later"][0] + 0.3, 8), (K["later"][1], 8), (K["later"][1] + 0.3, 0)])
    acts.append(pop("hứ", K["later"][1], K["later"][1] + 0.8, 820, 320, 48, PINK, 10))
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["twirl"][0] + 0.3, "sparkle"), (K["call"][0], "pop"), (K["later"][1], "boing")], title=None)


def sc_muoi(s):
    L, E, T, K = _t(s)
    acts = []
    muoi = kid("muoi", 560, z=11)
    walk(muoi, 0.1, K["intro"][0], -200, 560)
    jump(muoi, K["intro"][0] + 0.5, 35, 2, 0.45)
    acts.append(muoi)
    acts += name_card("MUỘI", "chị Năm", K["intro"][0] + 0.3, K["intro"][1] + 0.8, 230, 180)
    # bánh trung thu trên bàn, Muội lấy ăn
    cake = Actor("prop", "mooncake", z=12, scale=1.6, x=[(0, 1010), (K["cake"][0] + 1.2, 1010), (K["cake"][0] + 1.8, 560)],
                 y=[(0, 548), (K["cake"][0] + 1.2, 548), (K["cake"][0] + 1.8, FLOOR - 165)])
    acts.append(cake)
    muoi.set("x", muoi.tracks["x"].keys + [(K["cake"][0], 560), (K["cake"][0] + 1.0, 880), (K["cake"][0] + 1.8, 640)])
    muoi.set("emote", [(0, None), (K["cake"][0], "hearts"), (K["stop"][0], "sweat"), (K["yum"][0], "hearts"), (T, None)])
    moon = kid("moon", 1500, z=10, scale=0.95)
    walk(moon, K["stop"][0] - 0.6, K["stop"][0], 1500, 1000)
    moon.set("emote", [(0, None), (K["stop"][0], "angry"), (K["stop"][1] + 0.5, None)])
    shake(moon, K["stop"][0], K["stop"][1], 6, 0.1)
    acts.append(moon)
    # cắn bánh: bánh nhỏ dần
    cake.set("scale", [(0, 1.6), (K["yum"][0], 1.6), (K["yum"][0] + 0.4, 1.2), (K["yum"][0] + 0.8, 0.8), (K["yum"][1], 0.4)])
    wobble(muoi, K["yum"][0], K["yum"][1], 5, 0.25)
    acts.append(pop("ngon quá!", K["yum"][0] + 0.3, K["yum"][1] + 0.5, 400, 250, 52, YEL, -8))
    acts += hearts(K["yum"][0], K["yum"][1] + 0.5, 640, 300)
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["cake"][0] + 1.2, "swoosh"), (K["stop"][0], "boing"), (K["yum"][0], "pop")], title=None)


def sc_eric(s):
    L, E, T, K = _t(s)
    acts = []
    eric = kid("eric", 640, z=11)
    walk(eric, 0.1, K["intro"][0], 1450, 640)
    jump(eric, K["intro"][0] + 0.3, 50, 3, 0.35)
    wobble(eric, L[1], L[1] + 1.5, 10, 0.2)
    acts.append(eric)
    acts += name_card("ERIC", "em Út", K["intro"][0] + 0.3, K["intro"][1] + 0.8, 230, 180)
    hx, hy = hand(eric, -1, 0.45)
    hx -= 45
    lantern = Actor("prop", "lantern", z=12, scale=1.1, x=[(0, hx), (K["grab"][0] + 0.6, hx), (K["grab"][0] + 1.0, 330)],
                    y=[(0, hy + 40), (K["grab"][0] + 0.6, hy + 40), (K["grab"][0] + 1.0, FLOOR - 230)], rot=[(0, 0), (K["grab"][0] + 0.6, 0), (K["grab"][0] + 1.0, -20)])
    lantern.set("x", lantern.tracks["x"].keys + [(K["kaka"][1], 330), (K["kaka"][1] + 0.6, hx)])
    lantern.set("y", lantern.tracks["y"].keys + [(K["kaka"][1], FLOOR - 230), (K["kaka"][1] + 0.6, hy + 40)])
    lantern.set("rot", lantern.tracks["rot"].keys + [(K["kaka"][1], -20), (K["kaka"][1] + 0.6, 0)])
    acts.append(lantern)
    muoi = kid("muoi", -200, z=10, scale=0.95)
    walk(muoi, K["grab"][0] - 0.8, K["grab"][0], -200, 380)
    muoi.set("emote", [(0, None), (K["grab"][0], "stars"), (K["grab"][1], None), (K["kaka"][0], "sweat"), (K["ok"][0], None)])
    muoi.set("flip", muoi.tracks["flip"].keys + [(K["kaka"][0] + 0.3, True), (K["kaka"][1] + 0.6, False)])
    acts.append(muoi)
    eric.set("emote", [(0, None), (K["cry"][0], "cry"), (K["ok"][0], None), (K["ok"][0] + 0.2, "stars"), (K["ok"][1] + 0.5, None)])
    shake(eric, K["cry"][0], K["cry"][1], 10, 0.1)
    kaka = kid("kaka", 1500, z=9, scale=0.95)
    walk(kaka, K["kaka"][0] - 0.6, K["kaka"][0], 1500, 950)
    kaka.set("emote", [(0, None), (K["kaka"][0], "angry"), (K["kaka"][1] + 0.3, None)])
    kaka.set("flip", kaka.tracks["flip"].keys + [(K["kaka"][0], True), (K["ok"][0], False)])
    acts.append(kaka)
    jump(eric, K["ok"][0] + 0.2, 40, 2, 0.35)
    acts.append(pop("HI HI!", K["ok"][0] + 0.3, K["ok"][1] + 0.5, 850, 260, 56, PINK, 8))
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["grab"][0] + 0.6, "swoosh"), (K["cry"][0], "cry"), (K["kaka"][0], "boing"), (K["ok"][0], "ding")], title=None)


def sc_lu(s):
    L, E, T, K = _t(s)
    acts = []
    lu = kid("lu", 420, 598, z=10, scale=1.0)
    jump(lu, K["bark"][0], 30, 2, 0.35)
    lu.set("flip", [(0, False)] + [(K["nope"][0] + k * 0.15, k % 2 == 1) for k in range(7)] + [(K["nope"][1] + 0.2, False)])
    acts.append(lu)
    acts += name_card("LU", "cún cưng", K["bark"][0] + 0.3, L[1] + 1.5, 230, 180)
    moon = kid("moon", 1500, z=11, scale=0.95)
    walk(moon, K["food"][0] - 0.8, K["food"][0], 1500, 880)
    hx, hy = hand(moon, -1, 0.42)
    bowl = Actor("prop", "bowl", z=12, scale=1.2, x=[(0, 1500), (K["food"][0] - 0.8, 1500), (K["food"][0], hx + 10), (K["food"][1], hx + 10), (K["food"][1] + 0.4, 640)],
                 y=[(0, hy + 30), (K["food"][1], hy + 30), (K["food"][1] + 0.4, FLOOR + 10)], visible=[(0, False), (K["food"][0] - 0.8, True)])
    acts += [moon, bowl]
    acts.append(pop("hông ăn!", K["nope"][0], K["nope"][1] + 0.4, 420, 280, 50, BLUE, -6))
    moon.set("emote", [(0, None), (K["nope"][0], "sweat"), (K["run"][0], None)])
    # anh chị chạy ngang, Lu nhảy xuống chạy theo
    for i, n in enumerate(("kaka", "puka", "sam", "eric")):
        a = kid(n, -200, z=11, scale=0.9)
        t0 = K["run"][0] + 0.9 + i * 0.3
        walk(a, t0, t0 + 2.2, -200, 1500)
        a.set("x", [(0, -200)] + a.tracks["x"].keys)
        acts.append(a)
    lu.set("x", lu.tracks["x"].keys + [(K["run"][0] + 1.0, 420), (K["run"][0] + 1.3, 520), (K["run"][0] + 2.4, 1500)])
    lu.set("y", lu.tracks["y"].keys + [(K["run"][0] + 1.0, 598), (K["run"][0] + 1.3, FLOOR)])
    lu.set("ground", [(0, 598), (K["run"][0] + 1.3, FLOOR)])
    lu.set("bob", [(0, 0), (K["run"][0] + 1.3, 8)]).set("bobf", 5)
    walk(moon, K["run"][0] + 1.8, K["run"][0] + 2.6, 880, 1500)
    acts.append(pop("GÂU GÂU!", K["run"][1], T, 700, 300, 64, YEL, -8))
    return dict(actors=acts, camera=None, sfx=[(K["bark"][0], "bark"), (K["food"][1] + 0.4, "pop"), (K["run"][0] + 1.0, "bark"), (K["run"][1], "bark")], title=None)


def sc_plan(s):
    L, E, T, K = _t(s)
    acts = []
    # cả nhà đứng thành hàng trong phòng khách
    line = (("kaka", 300, 1.0), ("sam", 470, 0.95), ("puka", 620, 0.95), ("moon", 790, 0.95), ("muoi", 960, 0.95), ("eric", 1120, 0.95))
    who = {}
    for i, (n, x, sc) in enumerate(line):
        a = kid(n, x, z=10 + i, scale=sc)
        walk(a, 0.05 + i * 0.1, K["plan"][0] - 0.2, -200 + i * 40, x)
        who[n] = a
        acts.append(a)
    lu = kid("lu", 1230, z=16, scale=0.9, bob=3, bobf=2)
    acts.append(lu)
    # Kaka cầm đầu lân giơ lên
    lion = Actor("prop", "lion", z=20, scale=1.4, visible=[(0, False), (K["plan"][0] + 0.4, True)], x=300, y=FLOOR - H_OF["kaka"] * 0.6)
    lion.set("scale", [(K["plan"][0] + 0.4, 0.2), (K["plan"][0] + 0.7, 1.55), (K["plan"][0] + 0.85, 1.4)])
    acts.append(lion)
    jump(who["kaka"], K["plan"][0] + 0.4, 40, 1, 0.4)
    jump(who["sam"], K["tail"][0], 35, 2, 0.35)
    jump(who["puka"], K["tail"][0] + 0.15, 35, 2, 0.35)
    tail = Actor("prop", "tail", z=20, scale=1.3, x=545, y=FLOOR - 150, visible=[(0, False), (K["tail"][0] + 0.3, True)])
    acts.append(tail)
    drum = Actor("prop", "drum", z=20, scale=1.3, x=790, y=FLOOR - 120, visible=[(0, False), (K["drum"][0] + 0.3, True)])
    acts.append(drum)
    jump(who["moon"], K["drum"][0] + 0.3, 30, 1, 0.4)
    lantern = Actor("prop", "lantern", z=20, scale=1.3, x=1030, y=FLOOR - 180, visible=[(0, False), (K["drum"][0] + 1.2, True), (K["cakeagain"][0], False)])
    cake = Actor("prop", "mooncake", z=20, scale=1.4, x=1030, y=FLOOR - 200, visible=[(0, False), (K["cakeagain"][0] + 0.3, True)])
    acts += [lantern, cake]
    who["muoi"].set("emote", [(0, None), (K["cakeagain"][0], "hearts"), (K["cakeagain"][1] + 0.5, None)])
    jump(who["muoi"], K["cakeagain"][0], 30, 2, 0.4)
    # Eric làm Ông Địa: mặt nạ + quạt
    mask = Actor("prop", "mask", z=21, scale=1.2, x=1120, y=FLOOR - H_OF["eric"] * 0.95 * 0.6, visible=[(0, False), (K["explain"][0] + 0.5, True)])
    fan = Actor("prop", "fan", z=21, scale=1.3, x=1200, y=FLOOR - 170, visible=[(0, False), (K["explain"][0] + 1.0, True)])
    acts += [mask, fan]
    who["eric"].set("emote", [(0, None), (K["what"][0], "question"), (K["explain"][0], None), (K["yes"][0], "stars"), (K["yes"][1] + 0.5, None)])
    jump(who["eric"], K["yes"][0], 45, 2, 0.35)
    wobble(who["kaka"], K["explain"][0], K["explain"][1], 6, 0.25)
    acts.append(pop("Ông Địa!", K["explain"][0] + 0.3, K["explain"][1] + 0.3, 1120, 180, 54, YEL, 6))
    return dict(actors=acts, camera=None, sfx=[(K["plan"][0] + 0.4, "sparkle"), (K["tail"][0], "boing"), (K["drum"][0] + 0.3, "pop"), (K["cakeagain"][0], "pop"), (K["explain"][0] + 0.5, "sparkle"), (K["yes"][0], "ding")], title=None)


def sc_practice(s):
    L, E, T, K = _t(s)
    acts = []
    kaka = kid("kaka", 520, z=12)
    lion = Actor("prop", "lion", z=14, scale=1.6)
    puka = kid("puka", 700, z=11, scale=0.95)
    sam = kid("sam", 850, z=11, scale=0.95)
    tail = Actor("prop", "tail", z=13, scale=1.5)
    moon = kid("moon", 1120, z=10, scale=0.9)
    drum = Actor("prop", "drum", z=11, scale=1.3, x=1120, y=FLOOR - 110)
    sticks = Actor("prop", "sticks", z=12, scale=1.1, x=1120, y=FLOOR - 230)
    eric = kid("eric", 250, z=11, scale=0.95)
    fan = Actor("prop", "fan", z=12, scale=1.2)
    muoi = kid("muoi", 130, z=10, scale=0.85, bob=2, bobf=1.5)
    cake = Actor("prop", "mooncake", z=11, scale=1.1, x=160, y=FLOOR - 200)
    acts += [kaka, lion, puka, sam, tail, moon, drum, sticks, eric, fan, muoi, cake]
    # Moon đánh trống: dùi nhịp
    st = K["drum"][0]
    ys = []
    t = st
    while t < K["fall"][0]:
        ys += [(t, FLOOR - 230), (t + 0.11, FLOOR - 180), (t + 0.22, FLOOR - 230)]
        t += 0.44
    sticks.set("y", [(0, FLOOR - 230)] + ys)
    moon.set("bob", [(0, 0), (st, 5), (K["fall"][0], 0)]).set("bobf", 2.3)
    acts += notes(st, K["fall"][0], 1120, 330, 10)
    # lân nhảy: Kaka nhảy sang trái, đuôi chạy sang phải
    jt = K["jump"][0]
    for k in range(6):
        jump(kaka, jt + k * 0.45, 55, 1, 0.45)
    kaka.set("x", [(0, 520), (jt, 520), (K["split"][0], 380), (K["slow"][0], 250), (K["fall"][0], 250), (K["fall"][0] + 0.4, 330)])
    wobble(kaka, jt, K["fall"][0], 8, 0.22)
    follow(lion, kaka, 0, -H_OF["kaka"] * 0.74)
    lion.set("rot", [(t, -v * 0.6) for t, v in kaka.tracks["rot"].keys])
    puka.set("x", [(0, 700), (jt, 700), (K["split"][0], 850), (K["slow"][0], 950), (K["fall"][0], 950), (K["fall"][0] + 0.4, 420)])
    sam.set("x", [(0, 850), (jt, 850), (K["split"][0], 1000), (K["slow"][0], 1080), (K["fall"][0], 1080), (K["fall"][0] + 0.4, 520)])
    for a in (puka, sam):
        a.set("bob", [(0, 0), (jt, 7), (K["fall"][0], 0)]).set("bobf", 4)
    tail.set("x", [(0, 775), (jt, 775), (K["split"][0], 925), (K["slow"][0], 1015), (K["fall"][0], 1015), (K["fall"][0] + 0.4, 470)])
    tail.set("y", [(0, FLOOR - 160)]).set("rot", [(0, 0)] + [(jt + k * 0.3, 8 if k % 2 == 0 else -8) for k in range(12)] + [(K["fall"][0], 0)])
    puka.set("emote", [(0, None), (K["slow"][0], "sweat"), (K["fall"][0], None)])
    sam.set("emote", [(0, None), (K["hair"][0], "angry"), (K["fall"][0], None)])
    acts.append(pop("ơ ơ ơ!", K["split"][0] + 0.3, K["split"][1], 640, 220, 54, PINK, -6))
    # Eric Ông Địa phe phẩy quạt chạy vòng
    eric.set("x", [(0, 250), (jt, 250)] + [(jt + 0.6 + k * 0.6, 420 if k % 2 == 0 else 250) for k in range(8)])
    eric.set("flip", [(0, False)] + [(jt + 0.6 + k * 0.6 - 0.3, k % 2 == 1) for k in range(9)])
    eric.set("bob", [(0, 0), (jt, 6), (K["fall"][0], 0)]).set("bobf", 4)
    follow(fan, eric, 70, -170)
    fan.set("rot", [(0, 0)] + [(jt + k * 0.2, 25 if k % 2 == 0 else -25) for k in range(30)])
    # Lu cắn đuôi, cả đám té
    lu = kid("lu", -200, z=15, scale=0.9, bob=8, bobf=5)
    lu.set("x", [(0, -200), (K["fall"][0] - 1.0, -200), (K["fall"][0] + 0.3, 1000)])
    lu.set("rot", [(0, 0), (K["fall"][0] + 0.3, 0), (K["fall"][0] + 0.6, -25), (K["again"][0], -25), (K["again"][0] + 0.4, 0)])
    acts.append(lu)
    tf = K["fall"][0] + 0.5
    for a, rot in ((kaka, -70), (puka, 60), (sam, -55), (eric, 75)):
        a.set("rot", a.tracks["rot"].keys + [(tf, 0), (tf + 0.3, rot), (K["again"][0] + 0.3, rot), (K["again"][0] + 0.8, 0)] if "rot" in a.tracks else [(0, 0), (tf, 0), (tf + 0.3, rot), (K["again"][0] + 0.3, rot), (K["again"][0] + 0.8, 0)])
        a.set("y", a.tracks["y"].keys + [(tf, FLOOR), (tf + 0.3, FLOOR + 40)] if "y" in a.tracks else [(0, FLOOR), (tf, FLOOR), (tf + 0.3, FLOOR + 40)])
    lion.set("y", lion.tracks["y"].keys + [(tf, FLOOR - 250), (tf + 0.4, FLOOR - 60)])
    lion.set("rot", lion.tracks["rot"].keys + [(tf, 0), (tf + 0.4, 120)])
    tail.set("rot", tail.tracks["rot"].keys + [(tf, 0), (tf + 0.4, -40)])
    acts.append(pop("BỊCH!", tf, tf + 1.2, 500, 260, 76, RED, -12))
    acts += stars(tf, tf + 1.0, 500, 330)
    eric.set("emote", [(0, None), (K["cry"][0], "cry"), (K["again"][1] - 0.3, None), (K["again"][1], "stars")])
    moon.set("x", [(0, 1120), (K["again"][0] - 0.3, 1120), (K["again"][0] + 0.4, 450)])
    moon.set("emote", [(0, None), (K["again"][0], "hearts"), (T, None)])
    return dict(actors=acts, camera=None,
                sfx=[(st, "liondrum"), (jt, "boing"), (K["split"][0] + 0.3, "swoosh"), (K["fall"][0] - 0.8, "bark"), (tf, "boing"), (K["cry"][0], "cry"), (K["again"][1], "ding")], title=None)


def sc_fight(s):
    L, E, T, K = _t(s)
    acts = []
    eric = kid("eric", 760, z=11)
    muoi = kid("muoi", -200, z=10)
    walk(muoi, K["start"][0] + 0.3, K["grab"][0], -200, 470)
    hx, hy = hand(eric, -1, 0.5)
    fan = Actor("prop", "fan", z=13, scale=1.4, x=[(0, hx), (K["grab"][0], hx)], y=[(0, hy + 30)], rot=[(0, 0)])
    acts += [eric, muoi, fan]
    eric.set("emote", [(0, None), (K["no"][0], "angry"), (K["cry"][0], "cry"), (K["lu"][0] + 1.0, None), (K["share"][0], "hearts")])
    muoi.set("emote", [(0, None), (K["grab"][0], "hearts"), (K["pull"][0], "angry"), (K["lu"][0] + 1.0, "sweat"), (K["sorry"][0], None)])
    # giằng co cái quạt
    tug = []
    t, k = K["no"][0], 0
    while t < K["lu"][0] + 0.8:
        tug.append((t, (-1) ** k * 25))
        t += 0.26
        k += 1
    muoi.set("x", muoi.tracks["x"].keys + [(t_, 470 + d) for t_, d in tug] + [(K["lu"][0] + 0.9, 470)])
    eric.set("x", [(0, 760)] + [(t_, 760 + d) for t_, d in tug] + [(K["lu"][0] + 0.9, 760)])
    for a in (muoi, eric):
        a.set("rot", [(0, 0)] + [(t_, -d * 0.5) for t_, d in tug] + [(K["lu"][0] + 0.9, 0)])
    fan.set("x", fan.tracks["x"].keys + [(t_, 615 + d) for t_, d in tug] + [(K["lu"][0] + 0.9, 615)])
    fan.set("rot", [(0, 0)] + [(t_, d) for t_, d in tug] + [(K["lu"][0] + 0.9, 0)])
    acts.append(pop("hừm!", K["pull"][0], K["pull"][1], 615, 230, 52, RED, 0))
    # Lu ngoạm quạt chạy
    lu = kid("lu", -300, z=14, scale=0.9, bob=8, bobf=5)
    lu.set("x", [(0, -300), (K["lu"][0] + 0.2, -300), (K["lu"][0] + 0.9, 615), (K["lu"][0] + 1.1, 615), (K["lu"][0] + 1.9, 1600)])
    fan.set("x", fan.tracks["x"].keys + [(K["lu"][0] + 1.1, 615), (K["lu"][0] + 1.9, 1600)])
    fan.set("y", [(0, hy + 30), (K["lu"][0] + 0.9, hy + 30), (K["lu"][0] + 1.1, FLOOR - 120)])
    acts.append(lu)
    acts.append(pop("GÂU!", K["lu"][0] + 0.8, K["lu"][0] + 1.6, 615, 300, 64, YEL, -8))
    acts.append(pop("Ơ!", K["o"][0], K["o"][1] + 0.4, 470, 300, 56, PINK, -6))
    acts.append(pop("Ơ!", K["o"][0] + 0.1, K["o"][1] + 0.4, 760, 300, 56, PINK, 6))
    # rượt quanh ghế: Lu chạy trước gần, quay lại ở xa; cả nhà theo sau
    c0, c1 = K["chase"][0], K["laugh"][0]
    def loop(a, off, sc):
        per = 3.4
        xs, ys, scs, fl, gr = [], [], [], [], []
        t = c0 - off * per
        while t < c1 + 0.3:
            xs += [(t, -250), (t + per * 0.5, 1500), (t + per * 0.5 + 0.01, 1500), (t + per, -250)]
            ys += [(t, FLOOR), (t + per * 0.5, FLOOR), (t + per * 0.5 + 0.01, FAR), (t + per, FAR)]
            scs += [(t, sc), (t + per * 0.5, sc), (t + per * 0.5 + 0.01, sc * 0.7), (t + per, sc * 0.7)]
            fl += [(t, False), (t + per * 0.5, True)]
            t += per
        cut = lambda ks: [(tt, v) for tt, v in ks if tt < c1 - 0.2]  # noqa: E731
        a.set("x", a.tracks["x"].keys + [(c0 - 0.01, -250)] + cut(xs))
        a.set("y", [(0, FLOOR)] + cut(ys)).set("ground", [(0, FLOOR)] + cut(ys))
        a.set("scale", [(0, sc)] + cut(scs)).set("flip", [(0, False)] + cut(fl))
        a.set("bob", [(0, 0), (c0, 8)]).set("bobf", 5)
    lu.set("x", lu.tracks["x"].keys + [(c0 - 0.02, 1600)])
    loop(lu, 0.0, 0.9)
    chasers = {}
    for i, (n, sc) in enumerate((("kaka", 1.0), ("puka", 0.95), ("sam", 0.95), ("moon", 0.95))):
        a = kid(n, -250, z=12 + i, scale=sc)
        a.set("x", [(0, -250)])
        loop(a, 0.14 + i * 0.13, sc)
        chasers[n] = a
        acts.append(a)
    for a in (muoi, eric):
        a.set("x", a.tracks["x"].keys + [(c0 - 0.01, a.state(c0 - 0.02)["x"]), (c0 + 0.5, 1050 if a is muoi else 1180)])
        a.set("scale", [(0, 1.0), (c0, 1.0), (c0 + 0.5, 0.9)])
    # Kaka té
    tf = c1 - 0.3
    kaka = chasers["kaka"]
    kx = kaka.state(tf)["x"]
    kaka.set("x", [(tt, v) for tt, v in kaka.tracks["x"].keys if tt < tf] + [(tf, kx), (tf + 0.3, kx + 60)])
    kaka.set("rot", [(0, 0), (tf, 0), (tf + 0.3, -75), (K["stop"][1], -75), (K["stop"][1] + 0.5, 0)])
    kaka.set("y", [(tt, v) for tt, v in kaka.tracks["y"].keys if tt < tf] + [(tf, FLOOR), (tf + 0.3, FLOOR + 30)])
    kaka.set("ground", [(0, FLOOR)])
    kaka.set("scale", [(tt, v) for tt, v in kaka.tracks["scale"].keys if tt < tf] + [(tf, 1.0)])
    kaka.set("flip", [(tt, v) for tt, v in kaka.tracks["flip"].keys if tt < tf] + [(tf, False)])
    kaka.set("bob", [(0, 0), (c0, 8), (tf, 0)])
    kaka.set("emote", [(0, None), (tf + 0.3, "stars"), (K["stop"][1], None)])
    acts.append(pop("BỊCH!", tf + 0.2, tf + 1.3, min(kx + 60, 1100), 330, 70, RED, -12))
    acts += stars(tf + 0.2, tf + 1.2, min(kx + 60, 1100), 400)
    for n in ("puka", "sam", "moon"):
        a = chasers[n]
        ax = a.state(c1)["x"]
        a.set("x", [(tt, v) for tt, v in a.tracks["x"].keys if tt < c1] + [(c1, ax)])
        a.set("y", [(tt, v) for tt, v in a.tracks["y"].keys if tt < c1] + [(c1, FLOOR)])
        a.set("ground", [(0, FLOOR)])
        a.set("scale", [(tt, v) for tt, v in a.tracks["scale"].keys if tt < c1] + [(c1, 0.95)])
        a.set("flip", [(tt, v) for tt, v in a.tracks["flip"].keys if tt < c1] + [(c1, False)])
        a.set("bob", [(0, 0), (c0, 8), (c1, 0)])
    puka = chasers["puka"]
    puka.set("x", puka.tracks["x"].keys + [(c1 + 0.01, 300)])
    chasers["sam"].set("x", chasers["sam"].tracks["x"].keys + [(c1 + 0.01, 1100)])
    chasers["moon"].set("x", chasers["moon"].tracks["x"].keys + [(c1 + 0.01, 1230)])
    jump(puka, K["laugh"][0], 40, 3, 0.35)
    puka.set("emote", [(0, None), (K["laugh"][0], "stars"), (K["laugh"][1] + 0.4, None)])
    acts.append(pop("HA HA HA!", K["laugh"][0] + 0.2, K["laugh"][1] + 0.3, 300, 280, 56, YEL, -10))
    # Lu dừng, thả quạt trước Eric
    lu.set("x", lu.tracks["x"].keys + [(K["stop"][0], 820)])
    lu.set("y", lu.tracks["y"].keys + [(K["stop"][0], FLOOR)]).set("ground", [(0, FLOOR)])
    lu.set("scale", lu.tracks["scale"].keys + [(K["stop"][0], 0.9)]).set("flip", lu.tracks["flip"].keys + [(K["stop"][0], False)])
    lu.set("bob", [(0, 0), (K["lu"][0] + 0.2, 8), (K["stop"][0], 0)])
    fan.set("x", fan.tracks["x"].keys + [(K["stop"][0], 1600), (K["stop"][0] + 0.01, 820), (K["stop"][0] + 1.0, 1000)])
    fan.set("y", fan.tracks["y"].keys + [(K["stop"][0], FLOOR - 120), (K["stop"][0] + 1.0, FLOOR - 40)])
    fan.set("rot", fan.tracks["rot"].keys + [(K["stop"][0], 0), (K["stop"][0] + 1.0, 30)])
    fan.set("visible", [(0, True), (K["share"][0], False)])
    for a, x in ((eric, 1180), (muoi, 1050)):
        a.set("x", a.tracks["x"].keys + [(K["stop"][0], x), (K["stop"][0] + 0.8, x - 130)])
    muoi.set("rot", muoi.tracks["rot"].keys + [(K["sorry"][0], 0), (K["sorry"][0] + 0.3, 8), (K["sorry"][1], 8), (K["sorry"][1] + 0.3, 0)])
    fan2 = Actor("prop", "fan", z=20, scale=1.4, x=985, y=FLOOR - 190, visible=[(0, False), (K["share"][0], True)], rot=[(K["share"][0], -20), (K["share"][0] + 0.5, 20), (K["share"][1], -20)])
    acts.append(fan2)
    jump(eric, K["share"][0], 35, 2, 0.4)
    acts += hearts(K["share"][0] + 0.3, T, 980, 260)
    return dict(actors=acts, camera=None,
                sfx=[(K["grab"][0], "swoosh"), (K["no"][0], "boing"), (K["cry"][0], "cry"), (K["lu"][0] + 0.2, "swoosh"), (K["lu"][0] + 0.8, "bark"),
                     (c0, "bark"), (tf + 0.2, "boing"), (K["laugh"][0], "laugh"), (K["stop"][0] + 0.5, "pop"), (K["share"][0], "ding")], title=None)


def sc_midautumn(s):
    L, E, T, K = _t(s)
    acts = []
    # đội lân: Kaka đầu lân giữa, Puka + Sam đuôi phía sau bên phải, Moon trống bên trái, Eric Ông Địa, Muội lồng đèn + bánh
    kaka = kid("kaka", 560, z=14)
    lion = Actor("prop", "lion", z=16, scale=1.7)
    puka = kid("puka", 740, z=12, scale=0.92)
    sam = kid("sam", 890, z=12, scale=0.92)
    tail = Actor("prop", "tail", z=13, scale=1.5, x=815, y=FLOOR - 150)
    moon = kid("moon", 180, z=10, scale=0.9)
    drum = Actor("prop", "drum", z=11, scale=1.3, x=180, y=FLOOR - 110)
    sticks = Actor("prop", "sticks", z=12, scale=1.1, x=180, y=FLOOR - 230)
    eric = kid("eric", 340, z=15, scale=0.95)
    mask = Actor("prop", "mask", z=17, scale=1.3)
    fan = Actor("prop", "fan", z=17, scale=1.3)
    muoi = kid("muoi", 1120, z=11, scale=0.9)
    lantern = Actor("prop", "lantern", z=12, scale=1.4, x=1040, y=FLOOR - 200)
    cake = Actor("prop", "mooncake", z=12, scale=1.2, x=1210, y=FLOOR - 190)
    lu = kid("lu", 1000, z=18, scale=0.85)
    acts += [kaka, lion, puka, sam, tail, moon, drum, sticks, eric, mask, fan, muoi, lantern, cake, lu]
    d0, d1 = K["drum"][0], K["cheer"][0]
    # trống
    ys = []
    t = d0
    while t < d1:
        ys += [(t, FLOOR - 230), (t + 0.11, FLOOR - 180), (t + 0.22, FLOOR - 230)]
        t += 0.44
    sticks.set("y", [(0, FLOOR - 230)] + ys)
    moon.set("bob", [(0, 0), (d0, 5), (d1, 0)]).set("bobf", 2.3)
    acts += notes(d0, d1, 180, 330, 14)
    # lân múa: nhảy theo nhịp, lắc đầu, di chuyển qua lại
    l0 = K["lion"][0]
    for k in range(16):
        jump(kaka, l0 + k * 0.45, 60 if k % 4 == 3 else 35, 1, 0.45)
    kaka.set("x", [(0, 560), (l0, 560), (l0 + 2.0, 700), (l0 + 4.0, 480), (l0 + 6.0, 650), (d1, 560)])
    wobble(kaka, l0, d1, 9, 0.225)
    follow(lion, kaka, 0, -H_OF["kaka"] * 0.74)
    lion.set("rot", [(t_, -v * 0.8) for t_, v in kaka.tracks["rot"].keys])
    # đuôi lân vẫy
    for a, base in ((puka, 740), (sam, 890)):
        a.set("x", [(0, base), (l0, base), (l0 + 2.0, base + 140), (l0 + 4.0, base - 80), (l0 + 6.0, base + 90), (d1, base)])
        a.set("bob", [(0, 0), (l0, 8), (d1, 0)]).set("bobf", 2.2)
    tail.set("x", [(0, 815), (l0, 815), (l0 + 2.0, 955), (l0 + 4.0, 735), (l0 + 6.0, 905), (d1, 815)])
    tail.set("rot", [(0, 0)] + [(l0 + k * 0.225, 10 if k % 2 == 0 else -10) for k in range(int((d1 - l0) / 0.225))] + [(d1, 0)])
    tail.set("bob", 6).set("bobf", 2.2)
    # Ông Địa Eric: mặt nạ + quạt, chạy lạch bạch quanh lân
    e0 = K["ongdia"][0]
    eric.set("x", [(0, 340), (e0, 340)] + [(e0 + 0.7 + k * 0.7, 430 if k % 2 == 0 else 300) for k in range(10)])
    eric.set("flip", [(0, False)] + [(e0 + 0.7 + k * 0.7 - 0.35, k % 2 == 1) for k in range(11)])
    eric.set("bob", [(0, 0), (e0, 7), (d1, 0)]).set("bobf", 4)
    follow(mask, eric, 0, -H_OF["eric"] * 0.95 * 0.6)
    follow(fan, eric, 75, -170)
    fan.set("rot", [(0, 0)] + [(e0 + k * 0.2, 25 if k % 2 == 0 else -25) for k in range(int((d1 - e0) / 0.2))])
    eric.set("emote", [(0, None), (K["ongdia"][0], "stars"), (K["ongdia"][1] + 1.0, None)])
    acts.append(pop("Ha ha ha!", K["ongdia"][0] + 0.5, K["ongdia"][1] + 0.5, 340, 170, 54, YEL, -6))
    # Muội múa lồng đèn, thưởng bánh
    muoi.set("bob", [(0, 0), (K["fan"][0], 6), (d1, 0)]).set("bobf", 2.2)
    wobble(muoi, K["fan"][0], K["reward"][0], 6, 0.3)
    lantern.set("rot", [(0, 0)] + [(K["fan"][0] + k * 0.3, 15 if k % 2 == 0 else -15) for k in range(int((d1 - K["fan"][0]) / 0.3))])
    cake.set("x", [(0, 1210), (K["reward"][0] + 1.0, 1210), (K["reward"][0] + 1.6, 640)])
    cake.set("y", [(0, FLOOR - 190), (K["reward"][0] + 1.0, FLOOR - 190), (K["reward"][0] + 1.3, FLOOR - 420), (K["reward"][0] + 1.6, FLOOR - 300)])
    cake.set("visible", [(0, True), (K["reward"][1] + 0.6, False)])
    muoi.set("emote", [(0, None), (K["reward"][0], "hearts"), (K["reward"][1] + 0.5, None)])
    acts.append(pop("ngoạm!", K["reward"][0] + 1.6, K["reward"][1] + 0.6, 640, 230, 50, YEL, -5))
    # Lu chạy vòng
    lu.set("x", [(0, 1000), (K["lu"][0], 1000)] + [(K["lu"][0] + 0.5 + k * 0.7, 1150 if k % 2 == 0 else 960) for k in range(8)])
    lu.set("flip", [(0, False)] + [(K["lu"][0] + 0.5 + k * 0.7 - 0.35, k % 2 == 1) for k in range(9)])
    lu.set("bob", [(0, 0), (K["lu"][0], 8), (d1, 0)]).set("bobf", 5)
    acts.append(pop("GÂU GÂU!", K["lu"][0], K["lu"][1] + 0.5, 1050, 300, 56, YEL, -8))
    # khán giả vỗ tay: chữ hoan hô bay
    for i in range(6):
        tt = K["clap"][0] + 0.4 + i * 0.3
        acts.append(Actor("text", z=52, text=[(0, ""), (tt, "👏" if False else "hoan hô!"), (tt + 1.5, "")], size=40, color=WHITE if i % 2 else YEL,
                          x=[(tt, 120 + i * 210), (tt + 1.5, 120 + i * 210)], y=[(tt, 520), (tt + 1.5, 380)], alpha=[(tt, 1.0), (tt + 1.5, 0.0)], rot=-8 + i * 3))
    for a in (kaka, puka, sam, moon, eric, muoi):
        jump(a, K["cheer"][0] + 0.1, 45, 2, 0.4)
    acts.append(pop("HOAN HÔ!", K["cheer"][0] + 0.2, K["cheer"][1] + 0.8, 640, 150, 84, YEL, -5))
    acts += stars(K["cheer"][0] + 0.2, K["cheer"][1] + 0.8, 640, 250, 8)
    cam = Track([(0, (640, 360, 1.0)), (l0, (640, 360, 1.0)), (l0 + 1.0, (600, 420, 1.25)), (K["ongdia"][0], (600, 420, 1.25)), (K["ongdia"][0] + 0.8, (640, 360, 1.0))])
    return dict(actors=acts, camera=cam,
                sfx=[(d0, "liondrum"), (d0 + 4.5, "liondrum"), (d0 + 9.0, "liondrum"), (d0 + 13.5, "liondrum"), (l0, "boing"), (K["ongdia"][0], "laugh"),
                     (K["reward"][0] + 1.6, "pop"), (K["lu"][0], "bark"), (K["clap"][0] + 0.4, "clap"), (K["cheer"][0], "sparkle")], title=None)


def sc_ending(s):
    L, E, T, K = _t(s)
    acts = []
    order = (("kaka", 230), ("puka", 390), ("moon", 540), ("sam", 690), ("muoi", 850), ("eric", 1010))
    who = {}
    for i, (n, x) in enumerate(order):
        a = kid(n, x, z=10 + i, scale=0.9, bob=2, bobf=1.2 + i * 0.1)
        a.set("rot", [(0, (-1) ** i * 4)])
        jump(a, K["cheer"][0] + i * 0.06, 40, 2, 0.4)
        who[n] = a
        acts.append(a)
    acts.append(kid("lu", 1140, z=16, scale=0.85, bob=3, bobf=2))
    cake = Actor("prop", "mooncake", z=20, scale=1.5, x=[(0, 850), (K["give"][0] + 0.4, 850), (K["give"][0] + 1.0, 1010)], y=FLOOR - 200)
    acts.append(cake)
    who["muoi"].set("emote", [(0, None), (K["give"][0], "hearts"), (K["thanks"][1], None)])
    who["eric"].set("emote", [(0, None), (K["thanks"][0], "stars"), (K["thanks"][1] + 0.5, None), (K["cheer"][0], "hearts")])
    jump(who["eric"], K["thanks"][0], 35, 2, 0.4)
    acts += hearts(K["love"][0] + 0.6, K["love"][1] + 1.5, 640, 330, 4)
    acts.append(Actor("text", z=60, text=[(0, ""), (K["moral"][0] + 1.0, "Anh em như thể tay chân"), (T, "")], x=640, y=110, size=58, color=YEL,
                      scale=[(K["moral"][0] + 1.0, 0.2), (K["moral"][0] + 1.35, 1.1), (K["moral"][0] + 1.5, 1.0)], rot=-3))
    acts += hearts(K["cheer"][0], T, 640, 300, 5)
    cam = Track([(0, (640, 400, 1.0)), (K["moral"][0], (640, 430, 1.2)), (K["cheer"][0], (640, 360, 1.0))])
    return dict(actors=acts, camera=cam, sfx=[(K["give"][0] + 0.4, "pop"), (K["thanks"][0], "ding"), (K["love"][0] + 0.6, "ding"), (K["moral"][0] + 1.0, "sparkle"), (K["cheer"][0], "sparkle"), (K["lu"][0], "bark")],
                title=None, no_bubble=True)


def sc_outro(s):
    L, E, T, K = _t(s)
    acts = []
    door_y = 445
    for i, (n, x) in enumerate((("kaka", 520), ("puka", 568), ("moon", 616), ("sam", 664), ("muoi", 712), ("eric", 760))):
        a = kid(n, x, door_y, z=10 + i, scale=0.33, bob=3, bobf=2.5 + i * 0.2)
        jump(a, K["bye"][0] + i * 0.08, 25, 2, 0.4)
        acts.append(a)
    acts.append(kid("lu", 810, door_y + 2, z=20, scale=0.33, bob=4, bobf=4))
    acts.append(Actor("text", z=60, text=[(0, ""), (K["end"][0] + 0.1, "HẾT"), (T, "")], x=640, y=130, size=96, color=YEL,
                      scale=[(K["end"][0] + 0.1, 0.2), (K["end"][0] + 0.4, 1.15), (K["end"][0] + 0.55, 1.0)], rot=-4))
    acts.append(Actor("text", z=60, text=[(0, ""), (K["bye"][0], "Chúc mấy bé Trung thu vui!"), (T, "")], x=640, y=230, size=46, color=WHITE,
                      scale=[(K["bye"][0], 0.2), (K["bye"][0] + 0.3, 1.0)], rot=0))
    return dict(actors=acts, camera=None, sfx=[(K["end"][0], "ding"), (K["bye"][0], "sparkle")], title=None, no_bubble=True)


BUILDERS = {
    "01_intro": sc_intro, "02_kaka": sc_kaka, "03_puka": sc_puka, "04_moon": sc_moon, "05_sam": sc_sam,
    "06_muoi": sc_muoi, "07_eric": sc_eric, "08_lu": sc_lu, "09_plan": sc_plan, "10_practice": sc_practice,
    "11_fight": sc_fight, "12_midautumn": sc_midautumn, "13_ending": sc_ending, "14_outro": sc_outro,
}


def build(s):
    out = BUILDERS[s["id"]](s)
    out.setdefault("night", False)
    out["actors"].sort(key=lambda a: a.z)
    return out
