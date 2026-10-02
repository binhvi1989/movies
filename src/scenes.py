# -*- coding: utf-8 -*-
"""Biên đạo từng cảnh: ai xuất hiện, đi đâu, biểu cảm gì, hiệu ứng gì.

Mỗi hàm cảnh nhận `s` (từ timeline.json) và trả về dict(actors, camera, sfx, title, night).
Mốc thời gian lấy theo khoá của câu thoại: K["ten_khoa"] = (bắt_đầu, kết_thúc) so với đầu cảnh.
Lời thoại và bong bóng thoại / cử động miệng được render tự động theo người nói.
Toạ độ: khung 1280x720, (x, y) là điểm giữa bàn chân nhân vật.
"""
import math

from anim import Actor, Track

FLOOR = 650
FAR = 560
SOFA = 600      # chân khi ngồi trên sofa

RED = (255, 90, 80)
YEL = (255, 220, 70)
PINK = (255, 150, 200)
BLUE = (120, 190, 255)
GREEN = (120, 240, 120)


def _t(s):
    L = [l["rel"] for l in s["lines"]]
    E = [l["rel"] + l["dur"] for l in s["lines"]]
    K = {l["key"]: (l["rel"], l["rel"] + l["dur"]) for l in s["lines"] if l.get("key")}
    return L, E, s["dur"], K


def pop(text, t0, t1, x, y, size=70, color=YEL, rot=-8, jitter=True):
    """Chữ hiệu ứng bật lên (HA HA, GÂU GÂU...)."""
    a = Actor("text", z=50, text=[(0, ""), (t0, text), (t1, "")], x=x, y=y, size=size, color=color,
              scale=[(t0, 0.2), (t0 + 0.25, 1.15), (t0 + 0.4, 1.0), (t1 - 0.2, 1.0), (t1, 0.3)], rot=rot)
    if jitter:
        a.set("sway", 3.0).set("bobf", 3.0)
    return a


def name_card(name, role, t0, t1, x, y):
    return [
        Actor("text", z=55, text=[(0, ""), (t0, name), (t1, "")], x=x, y=y, size=58, color=YEL,
              scale=[(t0, 0.2), (t0 + 0.3, 1.1), (t0 + 0.45, 1.0)], rot=-4),
        Actor("text", z=55, text=[(0, ""), (t0 + 0.2, role), (t1, "")], x=x, y=y + 58, size=34, color=(255, 255, 255),
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


def jump(actor, t0, h=60, n=1, period=0.5, y0=FLOOR):
    """Nhảy n lần từ t0."""
    ys = actor.tracks["y"].keys if "y" in actor.tracks else [(0, y0)]
    for k in range(n):
        a = t0 + k * period
        ys += [(a, y0), (a + period * 0.5, y0 - h), (a + period, y0)]
    actor.set("y", ys)
    return actor


def spin(actor, t0, n=4, step=0.15):
    fs = actor.tracks["flip"].keys if "flip" in actor.tracks else [(0, False)]
    for k in range(n * 2 + 1):
        fs.append((t0 + k * step, k % 2 == 1))
    actor.set("flip", fs)
    return actor


def shake(actor, t0, t1, amp=12, step=0.12):
    xs = actor.tracks["x"].keys if "x" in actor.tracks else []
    base = actor.state(t0)["x"]
    t = t0
    k = 0
    while t < t1:
        xs.append((t, base + (amp if k % 2 == 0 else -amp)))
        t += step
        k += 1
    xs.append((t1, base))
    actor.set("x", xs)
    return actor


# ------------------------------------------------------------------ các cảnh
def sc_intro(s):
    L, E, T, K = _t(s)
    acts = []
    door_y = 440
    t_kids = K["kids"][0] + 0.2
    kids = (("kaka", 560), ("puka", 610), ("moon", 660), ("sam", 710))
    for i, (n, x) in enumerate(kids):
        tt = t_kids + i * 0.22
        a = Actor("kid", n, z=10 + i, x=x, scale=0.34, pose=[(0, "stand"), (tt, "cheer")], expr=[(0, "smile"), (tt, "laugh")],
                  y=[(0, door_y + 160), (tt, door_y + 160), (tt + 0.35, door_y)], bob=[(0, 0), (tt + 0.35, 4)], bobf=2.5 + i * 0.3,
                  visible=[(0, False), (tt, True)])
        jump(a, K["hello"][0], 30, 2, 0.4, door_y)
        acts.append(a)
    lu = Actor("lu", z=20, pose="run", expr="laugh", scale=0.4, y=door_y + 2,
               x=[(0, -200), (t_kids + 0.9, -200), (t_kids + 2.2, 480), (K["zoom"][0], 480), (K["zoom"][0] + 1.0, 760)])
    acts.append(lu)
    # chữ "quậy" bay lên
    for i, (w, x) in enumerate((("quậy!", 300), ("ồn!", 980), ("vui!", 200), ("quậy!", 1080))):
        tt = K["kids"][0] + 1.2 + i * 0.35
        acts.append(Actor("text", z=51, text=[(0, ""), (tt, w), (K["hello"][0], "")], x=x, size=48, color=PINK if i % 2 else YEL,
                          y=[(tt, 520), (K["hello"][0], 380)], alpha=[(tt, 1.0), (K["hello"][0], 0.0)], rot=-10 + i * 7))
    cam = Track([(0, (640, 360, 1.0)), (K["zoom"][0] + 0.3, (640, 360, 1.0)), (T, (640, 330, 1.9))])
    return dict(actors=acts, camera=cam, sfx=[(0.3, "pop"), (t_kids, "pop"), (t_kids + 1.4, "bark"), (K["hello"][0], "sparkle")], title=[(0.2, T - 0.3)],
                no_bubble=True)


def sc_kaka(s):
    L, E, T, K = _t(s)
    acts = []
    kaka = Actor("kid", "kaka", z=10, y=FLOOR)
    kaka.walk(0.1, K["intro"][0], -150, 640)
    kaka.set("pose", [(0, "walk"), (K["intro"][0], "crossed"), (K["juggle"][0], "cheer"), (K["drop"][0] + 0.3, "stand"), (K["li"][0], "crossed"), (K["love"][0], "hug")])
    kaka.set("expr", [(0, "smile"), (K["intro"][0], "smirk"), (K["juggle"][0], "wide"), (K["drop"][0] + 0.3, "o"), (K["li"][0], "grin"), (K["love"][0], "smile")])
    jump(kaka, K["intro"][1] - 0.6, 40, 1, 0.45)
    acts.append(kaka)
    acts += name_card("KAKA", "anh Hai", K["intro"][0] + 0.3, K["intro"][1] + 1.0, 230, 180)
    # tung dép: 3 chiếc dép bay vòng
    jt0, jt1 = K["juggle"][0] + 0.9, K["drop"][0]
    for i in range(3):
        xs, ys, rs = [(0, 640)], [(0, FLOOR - 120)], [(0, 0)]
        t = jt0
        ph = i * 2 * math.pi / 3
        while t < jt1:
            k = (t - jt0) * 2.2 * math.pi + ph
            xs.append((t, 640 + math.cos(k) * 90))
            ys.append((t, FLOOR - 230 + math.sin(k) * 110))
            rs.append((t, (t - jt0) * 400 + i * 120))
            t += 0.08
        # rớt xuống: chiếc giữa rớt trúng đầu
        land_y = FLOOR - 330 if i == 1 else FLOOR + 10
        xs += [(jt1, 640 + (i - 1) * 100), (jt1 + 0.5, 640 + (i - 1) * 110)]
        ys += [(jt1, FLOOR - 320), (jt1 + 0.5, land_y)]
        rs += [(jt1, 0), (jt1 + 0.5, 20 * i)]
        acts.append(Actor("prop", "slipper", z=14, scale=0.9, visible=[(0, False), (jt0, True), (K["li"][1] + 0.5, False)],
                          x=xs, y=ys, rot=rs))
    acts.append(pop("BỊCH!", K["drop"][0] + 0.3, K["drop"][1] + 0.3, 640, 260, 70, RED, -12))
    acts += stars(K["drop"][0] + 0.3, K["drop"][1] + 0.6, 640, 330)
    shake(kaka, K["drop"][0] + 0.3, K["drop"][0] + 1.0, 8)
    # các em tới gần, Kaka ôm
    puka = Actor("kid", "puka", z=12, x=[(0, -200), (K["love"][0], -200), (K["love"][0] + 0.8, 470)], y=FLOOR + 5, scale=0.85,
                 pose=[(0, "walk"), (K["love"][0] + 0.8, "cheer")], expr=[(0, "smile"), (K["love"][0] + 0.8, "laugh")], bob=[(0, 0), (K["love"][0] + 0.8, 5)], bobf=3)
    sam = Actor("kid", "sam", z=12, x=[(0, 1500), (K["love"][0], 1500), (K["love"][0] + 0.8, 810)], y=FLOOR + 5, scale=0.9,
                pose=[(0, "walk"), (K["love"][0] + 0.8, "cheer")], expr=[(0, "smile"), (K["love"][0] + 0.8, "laugh")], bob=[(0, 0), (K["love"][0] + 0.8, 5)], bobf=2.6,
                flip=[(0, True), (K["love"][0] + 0.8, False)])
    acts += [puka, sam]
    acts += hearts(K["love"][0] + 1.0, K["love"][1] + 0.8, 640, 240)
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (jt0, "swoosh"), (K["drop"][0] + 0.3, "boing"), (K["love"][0] + 1.0, "ding")], title=None)


def sc_puka(s):
    L, E, T, K = _t(s)
    acts = []
    puka = Actor("kid", "puka", z=10, y=FLOOR)
    puka.walk(0.1, K["intro"][0], 1450, 640)
    puka.set("pose", [(0, "walk"), (K["intro"][0], "claws"), (K["one"][0], "cheer"), (K["blanket"][0], "stand"), (K["no"][0], "claws")])
    puka.set("expr", [(0, "smile"), (K["intro"][0], "grin"), (K["one"][0], "laugh"), (K["blanket"][0], "pout"), (K["call"][0], "angry"), (K["no"][0], "angry")])
    jump(puka, K["one"][0], 70, 2, 0.4)
    jump(puka, K["no"][0], 35, 3, 0.33)
    puka.set("sway", [(0, 0), (K["intro"][0], 4), (K["blanket"][0], 0)])
    acts.append(puka)
    acts += name_card("PUKA", "chị Ba", K["intro"][0] + 0.3, K["one"][1] + 0.5, 230, 180)
    acts.append(pop("số 1!", K["one"][0], K["one"][1] + 0.5, 900, 280, 64, YEL, 10))
    blanket = Actor("prop", "blanket", z=11, x=640, scale=2.3,
                    y=[(0, FLOOR - 500), (K["blanket"][0] + 0.8, FLOOR - 500), (K["blanket"][0] + 1.4, FLOOR - 60)],
                    visible=[(0, False), (K["blanket"][0] + 0.8, True), (K["no"][1] + 0.3, False)])
    # mền rung theo mỗi lần "hông"
    shake(blanket, K["no"][0], K["no"][1], 10, 0.1)
    acts.append(blanket)
    acts.append(pop("hứ!", K["no"][1] + 0.3, T, 860, 420, 52, PINK, 10))
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["one"][0], "boing"), (K["blanket"][0] + 1.0, "swoosh"), (K["no"][0], "boing")], title=None)


def sc_moon(s):
    L, E, T, K = _t(s)
    acts = []
    moon = Actor("kid", "moon", z=10, y=FLOOR)
    moon.walk(0.1, K["intro"][0], -150, 640)
    moon.set("pose", [(0, "walk"), (K["intro"][0], "hold"), (K["sigh"][0], "stand"), (K["book"][0], "hold"), (K["hug"][0] + 0.6, "hug")])
    moon.set("expr", [(0, "smile"), (K["intro"][0], "smile"), (K["weird"][0] + 0.5, "wide"), (K["call"][0], "flat"), (K["sigh"][0], "sleepy"), (K["book"][0], "smile"), (K["hug"][0] + 0.6, "laugh")])
    book = Actor("prop", "book", z=11, x=[(0, -150), (K["intro"][0], 640)], y=FLOOR - 115, scale=1.1,
                 visible=[(0, False), (K["intro"][0], True), (K["sigh"][0], False), (K["book"][0], True), (K["hug"][0] + 0.6, False)])
    acts += [moon, book]
    acts += name_card("MOON", "em (lớn tuổi nhất nhà)", K["intro"][0] + 0.3, K["weird"][1], 250, 180)
    acts.append(pop("?", K["weird"][0] + 0.6, K["weird"][1], 790, 250, 80, YEL, 10))
    kaka = Actor("kid", "kaka", z=9, scale=0.9, y=FLOOR, x=[(0, -200), (K["call"][0] - 0.6, -200), (K["call"][0], 330)],
                 pose=[(0, "walk"), (K["call"][0], "point"), (K["sigh"][1], "crossed")], expr=[(0, "smile"), (K["call"][0], "grin"), (K["sigh"][1], "smirk")])
    puka = Actor("kid", "puka", z=9, scale=0.8, y=FLOOR, x=[(0, 1500), (K["call"][0] - 0.6, 1500), (K["call"][0], 950)],
                 pose=[(0, "walk"), (K["call"][0], "claws")], expr=[(0, "smile"), (K["call"][0], "grin"), (K["sigh"][0], "laugh")],
                 flip=[(0, True), (K["call"][0], False)])
    jump(kaka, K["call"][0], 30, 1, 0.4)
    jump(puka, K["sigh"][0] + 0.5, 25, 2, 0.35)
    acts += [kaka, puka]
    acts.append(pop("hihi", K["sigh"][0] + 0.5, K["sigh"][1] + 0.3, 1000, 300, 48, PINK, 8))
    sam = Actor("kid", "sam", z=12, scale=0.8, y=FLOOR + 6, x=[(0, 1500), (K["hug"][0] - 0.3, 1500), (K["hug"][0] + 0.6, 780)],
                pose=[(0, "walk"), (K["hug"][0] + 0.6, "hug")], expr=[(0, "laugh")], flip=[(0, True), (K["hug"][0] + 0.6, False)],
                walkspeed=3.2, bob=[(0, 0), (K["hug"][0] + 0.6, 4)])
    puka.set("x", puka.tracks["x"].keys + [(K["hug"][0], 950), (K["hug"][0] + 0.6, 1120)])
    acts.append(sam)
    acts += hearts(K["hug"][0] + 0.8, T, 700, 250)
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["weird"][0] + 0.6, "boing"), (K["hug"][0] + 0.8, "ding")], title=None)


def sc_sam(s):
    L, E, T, K = _t(s)
    acts = []
    sam = Actor("kid", "sam", z=10, y=FLOOR)
    sam.walk(0.1, K["intro"][0], 1450, 640)
    sam.set("pose", [(0, "walk"), (K["intro"][0], "cheer"), (K["twirl"][0], "stand"), (K["face"][0], "claws"), (K["laugh"][0], "cheer")])
    sam.set("expr", [(0, "smile"), (K["intro"][0], "laugh"), (K["twirl"][0], "wink"), (K["face"][0], "wide"), (K["face"][0] + 0.4, "o"),
                     (K["face"][0] + 0.8, "grin"), (K["laugh"][0], "laugh")])
    jump(sam, K["intro"][0] + 0.3, 50, 2, 0.4)
    spin(sam, K["twirl"][0] + 0.3, 5, 0.14)
    sam.set("sway", [(0, 0), (K["face"][0], 8), (K["laugh"][0], 0)])
    sam.set("bob", [(0, 0), (K["face"][0], 10), (K["laugh"][0], 5)]).set("bobf", 3.5)
    acts.append(sam)
    acts += name_card("SAM", "em Út", K["intro"][0] + 0.3, K["intro"][1] + 0.8, 230, 180)
    acts += stars(K["twirl"][0] + 0.4, K["twirl"][1] + 0.3, 640, 300)
    acts += stars(K["twirl"][0] + 1.2, K["twirl"][1] + 0.8, 640, 330)
    acts.append(pop("đẹp!", K["twirl"][1] - 0.2, K["twirl"][1] + 0.6, 950, 260, 56, PINK, 8))
    # cả nhà tới cười
    kaka = Actor("kid", "kaka", z=9, scale=0.85, y=FLOOR, x=[(0, -200), (K["face"][0] - 0.8, -200), (K["face"][0], 230)],
                 pose=[(0, "walk"), (K["face"][0], "stand"), (K["laugh"][0], "cheer")], expr=[(0, "smile"), (K["face"][0], "wide"), (K["laugh"][0], "laugh")],
                 bob=[(0, 0), (K["laugh"][0], 7)], bobf=3)
    moon = Actor("kid", "moon", z=9, scale=0.85, y=FLOOR, x=[(0, 1500), (K["face"][0] - 0.8, 1500), (K["face"][0], 1050)],
                 pose=[(0, "walk"), (K["face"][0], "hold"), (K["laugh"][0], "cheer")], expr=[(0, "smile"), (K["face"][0], "wide"), (K["laugh"][0], "laugh")],
                 flip=[(0, True), (K["face"][0], False)], bob=[(0, 0), (K["laugh"][0], 6)], bobf=3)
    puka = Actor("kid", "puka", z=9, scale=0.8, y=FLOOR, x=[(0, -200), (K["face"][0] - 0.6, -200), (K["face"][0] + 0.2, 420)],
                 pose=[(0, "walk"), (K["face"][0] + 0.2, "claws"), (K["laugh"][0], "sit")], expr=[(0, "smile"), (K["face"][0] + 0.2, "wide"), (K["laugh"][0], "laugh")],
                 rot=[(0, 0), (K["laugh"][0], 0), (K["laugh"][0] + 0.4, -30)])
    acts += [kaka, moon, puka]
    acts.append(pop("Bleee!", K["face"][0] + 0.1, K["face"][1] + 0.4, 640, 250, 64, GREEN, -8))
    acts.append(pop("HA HA HA!", K["laugh"][0], K["laugh"][1] + 0.5, 300, 320, 60, YEL, -10))
    acts.append(pop("HI HI HI!", K["laugh"][0] + 0.3, K["laugh"][1] + 0.5, 1000, 320, 60, PINK, 8))
    return dict(actors=acts, camera=None, sfx=[(K["intro"][0], "pop"), (K["twirl"][0] + 0.3, "sparkle"), (K["face"][0], "boing"), (K["laugh"][0], "laugh")], title=None)


def sc_lu(s):
    L, E, T, K = _t(s)
    acts = []
    lu = Actor("lu", z=10, pose=[(0, "sit"), (K["run"][0] + 1.0, "run")], expr=[(0, "smile"), (K["bark"][0], "laugh"), (K["food"][0], "smile"), (K["run"][0] + 1.0, "laugh")],
               x=[(0, 420), (K["run"][0] + 1.0, 420), (K["run"][0] + 1.8, 1500), (K["run"][0] + 1.81, -300), (K["run"][0] + 2.3, -300), (T, 1500)],
               y=[(0, SOFA), (K["run"][0] + 1.0, SOFA), (K["run"][0] + 1.2, FLOOR)], scale=[(0, 1.0), (K["run"][0] + 1.0, 1.1)])
    jump(lu, K["bark"][0], 30, 2, 0.35, SOFA)
    # lắc đầu
    lu.set("flip", [(0, False)] + [(K["nope"][0] + k * 0.15, k % 2 == 1) for k in range(7)] + [(K["nope"][1] + 0.2, False)])
    acts.append(lu)
    acts += name_card("LU", "cún cưng", K["bark"][0] + 0.3, L[1] + 1.5, 420, 230)
    moon = Actor("kid", "moon", z=11, scale=0.9, y=FLOOR, x=[(0, 1500), (K["food"][0] - 0.8, 1500), (K["food"][0], 880)],
                 pose=[(0, "walk"), (K["food"][0], "hold"), (K["nope"][1], "stand")], expr=[(0, "smile"), (K["nope"][0], "wide"), (K["run"][0], "laugh")],
                 flip=[(0, True), (K["food"][0], False)])
    bowl = Actor("prop", "bowl", z=12, scale=1.0, x=[(0, 1500), (K["food"][0] - 0.8, 1500), (K["food"][0], 880), (K["food"][1], 880), (K["food"][1] + 0.4, 640)],
                 y=[(0, FLOOR - 110), (K["food"][1], FLOOR - 110), (K["food"][1] + 0.4, FLOOR + 10)], visible=[(0, False), (K["food"][0] - 0.8, True)])
    acts += [moon, bowl]
    acts.append(pop("hông ăn!", K["nope"][0], K["nope"][1] + 0.4, 420, 300, 50, BLUE, -6))
    # các anh chị chạy ngang, Lu chạy theo
    for i, (n, sc) in enumerate((("kaka", 0.9), ("puka", 0.8), ("sam", 0.85))):
        t0 = K["run"][0] + 0.9 + i * 0.3
        acts.append(Actor("kid", n, z=11, scale=sc, y=FLOOR + 4, pose="walk", expr="laugh", walkspeed=3.2,
                          x=[(0, -200), (t0, -200), (t0 + 2.2, 1500)]))
    moon.set("x", moon.tracks["x"].keys + [(K["run"][0] + 1.8, 880), (K["run"][0] + 2.6, 1500)])
    moon.set("pose", moon.tracks["pose"].keys + [(K["run"][0] + 1.8, "walk")])
    acts.append(pop("GÂU GÂU!", K["run"][1], T, 700, 300, 64, YEL, -8))
    return dict(actors=acts, camera=None, sfx=[(K["bark"][0], "bark"), (K["food"][1] + 0.4, "pop"), (K["run"][0] + 1.0, "bark"), (K["run"][1], "bark")], title=None)


def sc_morning(s):
    L, E, T, K = _t(s)
    acts = []
    acts.append(pop("Mấy đứa ơi, dậy đi học!", K["call"][0], K["call"][1] + 0.4, 640, 100, 46, RED, -3))
    kaka = Actor("kid", "kaka", z=10, x=300, y=545, scale=0.85, pose="sit", expr=[(0, "sleepy"), (K["kaka"][0], "sleepy"), (K["kaka"][1], "o"), (K["kaka"][1] + 0.8, "sleepy")],
                 sway=[(0, 0), (K["kaka"][1], 3), (K["kaka"][1] + 1.0, 0)], bobf=1.5, rot=[(0, 0), (K["kaka"][1] + 0.5, 0), (K["kaka"][1] + 1.0, 25)])
    zzz = Actor("prop", "zzz", z=11, x=[(0, 380), (T, 420)], y=[(0, 470), (T, 420)], scale=[(0, 0.8), (T, 1.1)],
                visible=[(0, True), (K["kaka"][0], False), (K["kaka"][1] + 0.8, True), (K["moon"][0], False)])
    acts += [kaka, zzz]
    puka = Actor("kid", "puka", z=9, x=560, y=FLOOR + 20, scale=0.75, pose="stand", expr=[(0, "pout"), (K["puka"][0], "angry")])
    blanket = Actor("prop", "blanket", z=12, x=560, y=FLOOR - 20, scale=2.0)
    shake(blanket, K["puka"][0], K["puka"][1], 8, 0.12)
    acts += [puka, blanket]
    sam = Actor("kid", "sam", z=9, y=FLOOR - 30, scale=0.85, pose="stand", expr="wink",
                x=[(0, 1330), (K["sam"][0] - 0.3, 1330), (K["sam"][0], 1225), (K["sam"][1] + 0.1, 1225), (K["sam"][1] + 0.4, 1330)], look=-1.0)
    acts.append(sam)
    moon = Actor("kid", "moon", z=11, x=930, y=FLOOR, scale=0.95, pose=[(0, "hold"), (K["moon"][0], "point")], expr=[(0, "smile"), (K["moon"][0], "grin")],
                 flip=[(0, False), (K["moon"][0], True)])
    jump(moon, K["moon"][0], 40, 1, 0.45)
    bag = Actor("prop", "backpack", z=10, x=1010, y=FLOOR - 150, scale=1.0)
    acts += [moon, bag]
    acts.append(pop("✓", K["moon"][0] + 0.3, K["moon"][1] + 0.6, 1080, 330, 70, GREEN, 0))
    lu = Actor("lu", z=13, pose=[(0, "sit"), (K["lu"][0] - 0.2, "run")], expr=[(0, "smile"), (K["lu"][0] - 0.2, "laugh")], scale=0.9, y=FLOOR + 10,
               x=[(0, 760), (K["lu"][0] - 0.2, 760)] + [(K["lu"][0] + 0.3 + k * 0.7, 1000 if k % 2 == 0 else 450) for k in range(6)],
               flip=[(0, False)] + [(K["lu"][0] + 0.3 + k * 0.7 - 0.35, k % 2 == 1) for k in range(7)])
    acts.append(lu)
    acts.append(pop("GÂU GÂU!", K["lu"][0], K["lu"][1] + 0.8, 700, 260, 60, YEL, -8))
    return dict(actors=acts, camera=None, sfx=[(K["call"][0], "pop"), (K["kaka"][1], "yawn"), (K["kaka"][1] + 1.0, "boing"), (K["lu"][0], "bark"), (K["lu"][0] + 1.0, "bark")], title=None)


def sc_moon_finds(s):
    L, E, T, K = _t(s)
    acts = []
    moon = Actor("kid", "moon", z=12, y=FLOOR, scale=0.95, pose="stand", expr="smile")
    moon.walk(0.05, K["moon1"][0], 930, 720)
    moon.set("flip", [(0, False), (0.05, True), (K["moon1"][0], True), (K["moon3"][0], False)])
    moon.set("pose", moon.tracks["pose"].keys + [(K["moon1"][0], "pull"), (K["moon2"][0], "point"), (K["puka2"][0], "cheer"), (K["moon3"][0] - 0.8, "walk"), (K["moon3"][0], "point"), (K["sam1"][0], "hug")])
    moon.set("x", moon.tracks["x"].keys + [(K["moon3"][0] - 0.8, 720), (K["moon3"][0], 1000)])
    moon.set("expr", [(0, "smile"), (K["moon1"][0], "grin"), (K["moon2"][0], "laugh"), (K["moon3"][0], "smile"), (K["sam1"][0], "laugh")])
    puka = Actor("kid", "puka", z=9, x=500, scale=0.78, pose=[(0, "stand"), (K["puka1"][0], "stand"), (K["puka2"][0], "cheer")],
                 expr=[(0, "pout"), (K["puka1"][0], "wide"), (K["moon2"][0], "laugh")], y=[(0, FLOOR + 20), (K["puka1"][0] - 0.2, FLOOR + 20), (K["puka1"][0], FLOOR)])
    jump(puka, K["puka2"][0], 70, 2, 0.4)
    # Moon kéo mền: mền giật rồi bay đi
    blanket = Actor("prop", "blanket", z=13, scale=2.0, x=[(0, 500), (K["moon1"][0], 500), (K["moon1"][1] - 0.4, 560), (K["moon1"][1], 230)],
                    y=[(0, FLOOR - 20), (K["moon1"][1] - 0.4, FLOOR - 20), (K["moon1"][1] - 0.1, FLOOR - 200), (K["moon1"][1] + 0.3, FLOOR + 40)],
                    rot=[(0, 0), (K["moon1"][1] - 0.4, 0), (K["moon1"][1] + 0.3, 35)])
    shake(blanket, K["moon1"][0], K["moon1"][1] - 0.4, 10, 0.1)
    acts += [moon, puka, blanket]
    acts.append(pop("oái!", K["moon1"][1] - 0.2, K["moon1"][1] + 0.6, 480, 280, 54, PINK, -8))
    # Sam ra khỏi tủ
    sam = Actor("kid", "sam", z=10, y=FLOOR - 30, scale=0.85, pose=[(0, "stand"), (K["sam1"][0], "cheer")], expr=[(0, "wink"), (K["moon3"][0] + 0.5, "wide"), (K["sam1"][0], "laugh")],
                x=[(0, 1330), (K["moon3"][0] + 0.5, 1330), (K["moon3"][0] + 1.0, 1225), (K["sam1"][0], 1225), (K["sam1"][0] + 0.5, 1140)], look=[(0, -1.0), (K["sam1"][0], 0.0)])
    jump(sam, K["sam1"][0] + 0.8, 40, 2, 0.4, FLOOR - 30)
    acts.append(sam)
    acts.append(pop("?", K["moon3"][0] + 1.0, K["moon3"][1], 1200, 250, 70, YEL, 10))
    acts += hearts(K["sam1"][0] + 0.6, T, 1080, 300)
    kaka = Actor("kid", "kaka", z=8, x=300, y=545, scale=0.85, pose="sit", expr=[(0, "sleepy"), (K["moon2"][0], "laugh")])
    acts.append(kaka)
    return dict(actors=acts, camera=None, sfx=[(K["moon1"][0], "pop"), (K["moon1"][1] - 0.3, "swoosh"), (K["puka2"][0], "boing"), (K["sam1"][0] + 0.6, "ding")], title=None)


def sc_kaka_monkey(s):
    L, E, T, K = _t(s)
    acts = []
    kaka = Actor("kid", "kaka", z=12, y=FLOOR, scale=1.0, pose=[(0, "stand"), (K["monkey"][0], "monkey"), (K["e"][0], "point"), (K["go"][0] + 0.8, "walk"), (K["stay"][0], "point")],
                 expr=[(0, "smirk"), (K["monkey"][0], "grin"), (K["monkey"][0] + 0.8, "o"), (K["monkey"][0] + 1.5, "wide"), (K["monkey"][0] + 2.2, "grin"),
                       (K["sam"][0], "wide"), (K["e"][0], "angry"), (K["go"][0], "laugh"), (K["stay"][0], "smile")])
    kaka.walk(0.1, K["monkey"][0], -150, 640)
    hop = [(K["monkey"][0], 640)] + [(K["monkey"][0] + 0.4 + k * 0.4, 560 if k % 2 == 0 else 720) for k in range(10)] + [(K["sam"][0], 640)]
    kaka.set("x", kaka.tracks["x"].keys + hop)
    kaka.set("flip", [(0, False)] + [(K["monkey"][0] + 0.2 + k * 0.4, k % 2 == 1) for k in range(11)] + [(K["sam"][0], False)])
    kaka.set("bob", [(0, 0), (K["monkey"][0], 12), (K["sam"][0], 0)]).set("bobf", 4.5)
    kaka.set("sway", [(0, 0), (K["monkey"][0], 7), (K["sam"][0], 0)])
    acts.append(kaka)
    acts.append(pop("ú ù ú!", K["monkey"][0] + 0.8, L[1] + 1.0, 640, 230, 56, YEL, -8))
    puka = Actor("kid", "puka", z=10, x=300, y=FLOOR, scale=0.85, pose=[(0, "stand"), (K["monkey"][0] + 0.6, "cheer"), (K["sam"][0], "sit")],
                 expr=[(0, "pout"), (K["monkey"][0] + 0.6, "laugh")], bob=[(0, 0), (K["monkey"][0] + 0.6, 7)], bobf=3.5,
                 rot=[(0, 0), (K["sam"][0], 0), (K["sam"][0] + 0.4, -25)])
    sam = Actor("kid", "sam", z=10, x=980, scale=0.85, pose=[(0, "stand"), (K["monkey"][0] + 0.8, "cheer"), (K["sam"][0], "point"), (K["e"][1], "lie")],
                expr=[(0, "sad"), (K["monkey"][0] + 0.8, "laugh"), (K["sam"][0], "grin"), (K["e"][1], "laugh")], bob=[(0, 0), (K["monkey"][0] + 0.8, 7)], bobf=3.2,
                rot=[(0, 0), (K["e"][1], 0), (K["e"][1] + 0.5, 80)], y=[(0, FLOOR), (K["e"][1], FLOOR), (K["e"][1] + 0.5, FLOOR + 60)], flip=[(0, True)])
    moon = Actor("kid", "moon", z=9, x=1180, y=FLOOR - 10, scale=0.8, pose="hold", expr=[(0, "smile"), (K["monkey"][0] + 1.0, "laugh")])
    acts += [puka, sam, moon]
    acts.append(pop("HA HA HA!", K["go"][0], K["go"][0] + 2.5, 300, 330, 60, YEL, -10))
    acts.append(pop("HI HI HI!", K["go"][0] + 0.4, K["go"][0] + 2.5, 1000, 330, 60, PINK, 8))
    # đi học: tất cả bước ra bên phải, đeo cặp
    walk_t = K["go"][0] + 2.6
    for i, (a, sc) in enumerate(((kaka, 1.0), (puka, 0.85), (sam, 0.85), (moon, 0.8))):
        x_now = a.state(walk_t)["x"]
        a.set("x", [(t, v) for t, v in a.tracks["x"].keys if t < walk_t] + [(walk_t, x_now), (walk_t + 0.1 + i * 0.3, x_now), (K["lu"][0], 1700)])
        a.set("pose", [(t, v) for t, v in a.tracks["pose"].keys if t < walk_t] + [(walk_t, "walk")])
        a.set("rot", ([(t, v) for t, v in a.tracks["rot"].keys if t < walk_t] if "rot" in a.tracks else [(0, 0)]) + [(walk_t, 0)])
        a.set("y", [(0, FLOOR)])
        a.set("expr", [(t, v) for t, v in a.tracks["expr"].keys if t < walk_t] + [(walk_t, "smile")])
        a.set("bob", ([(t, v) for t, v in a.tracks["bob"].keys if t < walk_t] if "bob" in a.tracks else [(0, 0)]) + [(walk_t, 0)])
        a.set("flip", ([(t, v) for t, v in a.tracks["flip"].keys if t < walk_t] if "flip" in a.tracks else [(0, False)]) + [(walk_t, False)])
        a.set("walkspeed", 3.0)
        acts.append(Actor("prop", "backpack", z=13, scale=sc, visible=[(0, False), (walk_t, True)],
                          x=[(walk_t, x_now - 20), (walk_t + 0.1 + i * 0.3, x_now - 20), (K["lu"][0], 1680)], y=FLOOR - 140 * sc))
    # Kaka quay lại dặn Lu
    kaka.set("x", kaka.tracks["x"].keys + [(K["stay"][0] - 0.5, 1700), (K["stay"][0], 1050)])
    kaka.set("flip", kaka.tracks["flip"].keys + [(K["stay"][0] - 0.5, True), (K["stay"][0], True)])
    kaka.set("pose", kaka.tracks["pose"].keys + [(K["stay"][0] - 0.5, "walk"), (K["stay"][0], "point")])
    lu = Actor("lu", z=14, pose=[(0, "run"), (K["lu"][0], "sit")], expr=[(0, "laugh"), (K["stay"][0] + 0.5, "smile")], scale=0.9, y=FLOOR + 6,
               x=[(0, -300), (walk_t + 1.0, -300), (K["lu"][0], 640)])
    acts.append(lu)
    acts.append(pop("hức...", K["stay"][1], T, 640, 330, 46, BLUE, -5))
    return dict(actors=acts, camera=None, sfx=[(K["monkey"][0], "boing"), (K["monkey"][0] + 0.8, "boing"), (K["go"][0], "laugh"), (walk_t, "pop"), (K["lu"][0], "bark")], title=None)


def sc_fight(s):
    L, E, T, K = _t(s)
    acts = []
    t_tug0, t_tug1 = K["p1"][0], K["lu"][0] + 0.9
    tug = []
    t = t_tug0
    k = 0
    while t < t_tug1:
        tug.append((t, (-1) ** k * 18))
        t += 0.28
        k += 1
    puka = Actor("kid", "puka", z=10, y=FLOOR, scale=0.95, pose=[(0, "walk"), (K["start"][0] + 0.6, "pull")],
                 expr=[(0, "smile"), (K["start"][0] + 0.6, "angry"), (K["lu"][0] + 1.0, "wide"), (K["o"][0], "o")],
                 x=[(0, -150), (K["start"][0] + 0.6, 500)] + [(t, 500 + d) for t, d in tug] + [(K["lu"][0] + 1.0, 500)],
                 rot=[(0, 0)] + [(t, -d * 0.6) for t, d in tug] + [(K["lu"][0] + 1.0, 0)])
    sam = Actor("kid", "sam", z=10, y=FLOOR, scale=0.9, pose=[(0, "walk"), (K["start"][0] + 0.6, "pull")], flip=[(0, True)],
                expr=[(0, "smile"), (K["start"][0] + 0.6, "angry"), (K["lu"][0] + 1.0, "wide"), (K["o"][0], "o")],
                x=[(0, 1450), (K["start"][0] + 0.6, 780)] + [(t, 780 + d) for t, d in tug] + [(K["lu"][0] + 1.0, 780)],
                rot=[(0, 0)] + [(t, -d * 0.6) for t, d in tug] + [(K["lu"][0] + 1.0, 0)])
    jump(puka, K["p2"][0], 30, 2, 0.3)
    jump(sam, K["s2"][0], 30, 2, 0.3)
    teddy = Actor("prop", "teddy", z=12, scale=1.2, y=FLOOR - 100, x=[(0, 640)] + [(t, 640 + d) for t, d in tug],
                  rot=[(0, 0)] + [(t, d) for t, d in tug], visible=[(0, False), (K["start"][0] + 0.4, True), (K["lu"][0] + 0.9, False)])
    acts += [puka, sam, teddy]
    acts.append(pop("hừm!", K["p2"][0], K["s2"][1], 640, 240, 52, RED, 0))
    lu = Actor("lu", z=14, pose="run", expr=[(0, "smile"), (K["lu"][0] + 0.9, "laugh")], scale=1.0, y=FLOOR + 8,
               x=[(0, -300), (K["lu"][0] + 0.2, -300), (K["lu"][0] + 0.9, 640), (K["lu"][0] + 1.1, 640), (K["lu"][0] + 1.9, 1600)],
               item=[(0, None), (K["lu"][0] + 0.9, "teddy")])
    acts.append(lu)
    acts.append(pop("GÂU!", K["lu"][0] + 0.8, K["lu"][0] + 1.6, 640, 300, 64, YEL, -8))
    acts.append(pop("Ơ!", K["o"][0], K["o"][1] + 0.4, 500, 330, 56, PINK, -6))
    acts.append(pop("Ơ!", K["o"][0] + 0.1, K["o"][1] + 0.4, 800, 330, 56, PINK, 6))
    cam = Track([(0, (640, 360, 1.0)), (K["p1"][0], (640, 360, 1.0)), (K["p1"][0] + 0.4, (640, 380, 1.15)), (K["lu"][0], (640, 380, 1.15)), (K["lu"][0] + 0.4, (640, 360, 1.0))])
    return dict(actors=acts, camera=cam, sfx=[(K["start"][0] + 0.6, "boing"), (K["p1"][0] - 0.3, "pop"), (K["lu"][0] + 0.2, "swoosh"), (K["lu"][0] + 0.8, "bark")], title=None)


def sc_chase(s):
    L, E, T, K = _t(s)
    acts = []
    stop = K["stop"][0] + 0.5
    tf = K["slip"][0]

    def loop_x(t0, period, offset=0.0, until=stop):
        xs, ys, scs, flips = [], [], [], []
        t = t0 - offset * period
        while t < until:
            xs += [(t, -250), (t + period * 0.5, 1500), (t + period * 0.5 + 0.01, 1500), (t + period, -250)]
            ys += [(t, FLOOR), (t + period * 0.5, FLOOR), (t + period * 0.5 + 0.01, FAR), (t + period, FAR)]
            scs += [(t, 1.0), (t + period * 0.5, 1.0), (t + period * 0.5 + 0.01, 0.62), (t + period, 0.62)]
            flips += [(t, False), (t + period * 0.5, True)]
            t += period
        return xs, ys, scs, flips

    period = 3.6
    lx, ly, ls, lf = loop_x(0.0, period)
    cut = lambda keys: [(t, v) for t, v in keys if t < stop - 0.3]  # noqa: E731
    lu = Actor("lu", z=15, pose=[(0, "run"), (stop, "stand")], expr="laugh", item=[(0, "teddy"), (K["stop"][0] + 1.2, None)],
               x=cut(lx) + [(stop, 640)], y=cut(ly) + [(stop, FLOOR)], scale=cut(ls) + [(stop, 1.05)], flip=cut(lf) + [(stop, False)])
    acts.append(lu)
    chasers = (("kaka", 1.0, 0.16, "grin"), ("puka", 0.9, 0.3, "laugh"), ("sam", 0.9, 0.44, "o"), ("moon", 0.95, 0.58, "wide"))
    kids = {}
    for n, sc, off, ex in chasers:
        xs, ys, scs, fl = loop_x(0.0, period, off)
        a = Actor("kid", n, z=14, pose="walk", expr=ex, walkspeed=3.4, x=xs, y=ys, flip=fl, scale=[(t, v * sc) for t, v in scs], bob=0)
        kids[n] = a
        acts.append(a)
    # dừng vòng chạy tại lúc Kaka té
    for n, a in kids.items():
        st = a.state(tf)
        for key in ("x", "y", "scale", "flip"):
            a.set(key, [(t, v) for t, v in a.tracks[key].keys if t < tf] + [(tf, st[key])])
    kaka, moon, sam, puka = kids["kaka"], kids["moon"], kids["sam"], kids["puka"]
    for a, x, y, sc in ((kaka, 300, FLOOR, 1.0), (moon, 1000, FLOOR, 0.95), (sam, 1130, FLOOR, 0.85), (puka, 520, FLOOR, 0.9)):
        a.set("x", a.tracks["x"].keys + [(tf + 0.01, x)])
        a.set("y", a.tracks["y"].keys + [(tf + 0.01, y)])
        a.set("scale", a.tracks["scale"].keys + [(tf + 0.01, sc)])
    kaka.set("pose", [(0, "walk"), (tf, "cheer"), (tf + 0.4, "sit"), (K["ok"][0], "sit")])
    kaka.set("rot", [(0, 0), (tf, 0), (tf + 0.4, -30), (K["ok"][0], -30), (K["ok"][0] + 0.5, 0)])
    kaka.set("expr", [(0, "grin"), (tf, "wide"), (K["puka"][0], "pout"), (K["ok"][0], "smirk"), (K["stop"][0], "laugh")])
    kaka.set("y", kaka.tracks["y"].keys + [(tf + 0.4, FLOOR + 30), (K["ok"][0] + 0.5, FLOOR)])
    kaka.set("x", kaka.tracks["x"].keys + [(tf + 0.01, 300), (tf + 0.4, 380)])
    acts.append(pop("BỊCH!", K["fall"][0], K["fall"][1] + 0.3, 380, 330, 70, RED, -12))
    acts += stars(K["fall"][0], K["fall"][1] + 0.5, 380, 400)
    moon.set("pose", [(0, "walk"), (tf, "hug")]).set("expr", [(0, "wide"), (tf, "wide"), (K["puka"][0], "smile"), (K["stop"][0], "laugh")])
    sam.set("pose", [(0, "walk"), (tf, "stand")]).set("expr", [(0, "o"), (tf, "wide"), (K["puka"][0], "laugh")]).set("rot", [(0, 0), (tf, 15), (tf + 0.6, 0)])
    puka.set("pose", [(0, "walk"), (tf, "stand"), (K["puka"][0], "cheer")]).set("expr", [(0, "laugh"), (tf, "wide"), (K["puka"][0], "laugh")])
    jump(puka, K["puka"][0], 40, 3, 0.35)
    acts.append(pop("HA HA HA!", K["puka"][0] + 0.2, K["puka"][1] + 0.3, 520, 300, 56, YEL, -10))
    teddy = Actor("prop", "teddy", z=12, scale=1.2, x=700, y=[(K["stop"][0] + 1.0, FLOOR - 140), (K["stop"][0] + 1.5, FLOOR)],
                  rot=[(K["stop"][0] + 1.0, 0), (K["stop"][0] + 1.5, 15)], visible=[(0, False), (K["stop"][0] + 1.2, True)])
    acts.append(teddy)
    acts.append(pop("hì hì", K["stop"][1] - 0.5, T, 640, 300, 50, PINK, -5))
    return dict(actors=acts, camera=None, sfx=[(K["kaka"][0], "pop"), (K["chase"][0], "bark"), (tf, "swoosh"), (K["fall"][0], "boing"), (K["puka"][0], "laugh"), (K["stop"][0] + 1.2, "pop")], title=None)


def sc_lesson(s):
    L, E, T, K = _t(s)
    acts = []
    puka = Actor("kid", "puka", z=10, x=[(0, 520), (K["give"][0] + 1.4, 520), (K["give"][0] + 2.0, 580)], y=FLOOR, scale=0.9,
                 pose=[(0, "hold"), (K["give"][0] + 2.0, "point"), (K["hug"][0], "hug"), (K["study"][0], "stand"), (K["now"][0], "cheer"), (K["now"][1], "sit")],
                 expr=[(0, "flat"), (K["give"][0] + 0.8, "smile"), (K["hug"][0], "laugh"), (K["da1"][0], "sleepy"), (K["now"][0], "laugh"), (K["riddle"][0], "smile"), (K["laugh"][0], "laugh")])
    sam = Actor("kid", "sam", z=11, x=[(0, 800), (K["hug"][0], 800), (K["hug"][0] + 0.5, 690)], y=FLOOR, scale=0.85, flip=[(0, True), (K["hug"][0], False)],
                pose=[(0, "stand"), (K["give"][0] + 2.2, "hold"), (K["hug"][0], "hug"), (K["study"][0], "stand"), (K["now"][1], "sit")],
                expr=[(0, "sad"), (K["give"][0] + 2.2, "wide"), (K["hug"][0], "laugh"), (K["da2"][0], "sleepy"), (K["promise"][0], "wide"), (K["now"][0], "laugh"), (K["riddle"][0], "smile"), (K["what"][0], "o"), (K["laugh"][0], "laugh")])
    jump(sam, K["hug"][0], 50, 2, 0.4)
    jump(puka, K["now"][0], 60, 1, 0.45)
    teddy = Actor("prop", "teddy", z=12, scale=1.1, y=FLOOR - 95, x=[(0, 520), (K["give"][0] + 1.4, 520), (K["give"][0] + 2.2, 790)],
                  visible=[(0, True), (K["hug"][0] + 0.3, False)])
    acts += [puka, sam, teddy]
    acts += hearts(K["hug"][0] + 0.3, K["hug"][1] + 1.0, 640, 300)
    moon = Actor("kid", "moon", z=9, x=[(0, 1450), (K["study"][0] - 0.6, 1450), (K["study"][0], 980)], y=FLOOR, scale=0.95,
                 pose=[(0, "walk"), (K["study"][0], "hold"), (K["now"][1], "sit")], expr=[(0, "smile"), (K["study"][0], "laugh"), (K["da1"][0], "flat"), (K["now"][0], "laugh"), (K["riddle"][0], "smile"), (K["laugh"][0], "laugh")],
                 flip=[(0, True), (K["study"][0], False)])
    book = Actor("prop", "book", z=10, x=[(0, 1450), (K["study"][0] - 0.6, 1450), (K["study"][0], 980)], y=FLOOR - 115, scale=1.1,
                 visible=[(0, False), (K["study"][0], True), (K["now"][1], False)])
    acts += [moon, book]
    acts.append(pop("dạ...", K["da1"][0], K["da2"][1] + 0.3, 560, 300, 44, BLUE, -6))
    kaka = Actor("kid", "kaka", z=11, x=[(0, -200), (K["promise"][0] - 0.6, -200), (K["promise"][0], 250)], y=FLOOR, scale=0.95,
                 pose=[(0, "walk"), (K["promise"][0], "point"), (K["now"][1], "sit"), (K["answer"][0], "cheer")],
                 expr=[(0, "smirk"), (K["promise"][0], "grin"), (K["riddle"][0], "smirk"), (K["answer"][0], "laugh")])
    acts.append(kaka)
    acts.append(pop("!!!", K["promise"][1] - 0.3, K["now"][1], 560, 250, 60, YEL, 5))
    # ngồi học chung trên sofa
    sit_t = K["now"][1]
    for a, x in ((kaka, 170), (puka, 330), (sam, 480), (moon, 640)):
        a.set("x", a.tracks["x"].keys + [(sit_t - 0.01, a.state(sit_t - 0.01)["x"]), (sit_t + 0.6, x)])
        a.set("y", [(0, FLOOR), (sit_t - 0.01, FLOOR), (sit_t + 0.6, SOFA)])
    for x in (330, 480, 640):
        acts.append(Actor("prop", "book", z=12, scale=0.9, x=x + 60, y=SOFA - 70, visible=[(0, False), (sit_t + 0.6, True), (K["riddle"][0], False)]))
    acts.append(pop("✓ ngoan!", sit_t + 1.0, K["riddle"][0], 480, 330, 50, GREEN, 0))
    acts.append(pop("?", K["what"][0], K["what"][1] + 0.3, 540, 330, 70, YEL, 10))
    acts.append(pop("bong bóng!", K["answer"][0] + 0.6, K["laugh"][1], 640, 240, 56, BLUE, -6))
    acts.append(pop("HA HA HA!", K["laugh"][0], K["laugh"][1] + 0.5, 300, 320, 58, YEL, -10))
    acts.append(pop("HI HI HI!", K["laugh"][0] + 0.3, K["laugh"][1] + 0.5, 1000, 320, 58, PINK, 8))
    for a in (kaka, puka, sam, moon):
        a.set("bob", [(0, 0), (K["laugh"][0], 6), (K["laugh"][1] + 0.5, 0)]).set("bobf", 3.5)
    lu = Actor("lu", z=12, pose=[(0, "sit"), (K["laugh"][0], "run")], expr="laugh", scale=0.85, y=FLOOR + 10,
               x=[(0, 1100), (K["laugh"][0], 1100), (K["laugh"][1] + 0.5, 300)], flip=[(0, False), (K["laugh"][0], True)])
    acts.append(lu)
    return dict(actors=acts, camera=None, sfx=[(K["give"][0] + 1.4, "pop"), (K["hug"][0], "ding"), (K["study"][0], "pop"), (K["now"][0], "boing"), (K["answer"][0] + 0.6, "boing"), (K["laugh"][0], "laugh")], title=None)


def sc_ending(s):
    L, E, T, K = _t(s)
    acts = []
    placement = (("kaka", 180, "smile"), ("puka", 330, "sleepy"), ("sam", 640, "smile"), ("moon", 810, "smile"))
    for n, x, ex in placement:
        a = Actor("kid", n, z=10, x=x, y=SOFA, scale=0.95, pose=[(0, "sit"), (K["cheer"][0], "cheer")],
                  expr=[(0, ex), (K["love"][0] + 1.0, "laugh"), (K["moral"][0], "smile"), (K["cheer"][0], "laugh")],
                  bob=[(0, 0), (K["love"][0] + 1.0, 3), (K["moral"][0], 0), (K["cheer"][0], 6)], bobf=2.5)
        acts.append(a)
    lu = Actor("lu", z=12, pose=[(0, "lie"), (K["lu"][0], "sit")], expr=[(0, "smile"), (K["lu"][0], "laugh")], x=490, y=SOFA - 5, scale=0.95)
    jump(lu, K["lu"][0], 30, 1, 0.4, SOFA - 5)
    acts.append(lu)
    acts.append(Actor("prop", "teddy", z=11, x=575, y=SOFA, scale=0.9))
    acts += hearts(K["love"][0] + 0.6, K["love"][1] + 1.5, 500, 420, 4)
    acts += hearts(K["cheer"][0], T, 640, 400, 5)
    acts.append(Actor("text", z=60, text=[(0, ""), (K["moral"][0] + 1.0, "Anh em như thể tay chân"), (T, "")], x=640, y=120, size=58, color=YEL,
                      scale=[(K["moral"][0] + 1.0, 0.2), (K["moral"][0] + 1.35, 1.1), (K["moral"][0] + 1.5, 1.0)], rot=-3))
    cam = Track([(0, (640, 400, 1.0)), (K["cheer"][0], (560, 460, 1.3)), (K["cheer"][0] + 0.5, (640, 400, 1.0))])
    return dict(actors=acts, camera=cam, sfx=[(K["love"][0] + 0.6, "ding"), (K["moral"][0] + 1.0, "sparkle"), (K["cheer"][0], "sparkle"), (K["lu"][0], "bark")], title=None, night=True, no_bubble=True)


def sc_outro(s):
    L, E, T, K = _t(s)
    acts = []
    door_y = 440
    for i, (n, x) in enumerate((("kaka", 560), ("puka", 610), ("moon", 660), ("sam", 710))):
        a = Actor("kid", n, z=10 + i, x=x, y=door_y, scale=0.34, pose="cheer", expr="laugh", bob=4, bobf=2.5 + i * 0.2)
        jump(a, K["bye"][0] + i * 0.1, 30, 2, 0.4, door_y)
        acts.append(a)
    acts.append(Actor("lu", z=20, pose="sit", expr="laugh", scale=0.4, x=760, y=door_y + 2))
    acts.append(Actor("text", z=60, text=[(0, ""), (K["end"][0] + 0.1, "HẾT"), (T, "")], x=640, y=130, size=96, color=YEL,
                      scale=[(K["end"][0] + 0.1, 0.2), (K["end"][0] + 0.4, 1.15), (K["end"][0] + 0.55, 1.0)], rot=-4))
    acts.append(Actor("text", z=60, text=[(0, ""), (K["bye"][0], "Hẹn gặp lại!"), (T, "")], x=640, y=230, size=50, color=(255, 255, 255),
                      scale=[(K["bye"][0], 0.2), (K["bye"][0] + 0.3, 1.0)], rot=0))
    return dict(actors=acts, camera=None, sfx=[(K["end"][0], "ding"), (K["bye"][0], "sparkle")], title=None, no_bubble=True)


BUILDERS = {
    "01_intro": sc_intro, "02_kaka": sc_kaka, "03_puka": sc_puka, "04_moon": sc_moon, "05_sam": sc_sam,
    "06_lu": sc_lu, "07_morning": sc_morning, "08_moon_finds": sc_moon_finds, "09_kaka_monkey": sc_kaka_monkey,
    "10_fight": sc_fight, "11_chase": sc_chase, "12_lesson": sc_lesson, "13_ending": sc_ending, "14_outro": sc_outro,
}


def build(s):
    out = BUILDERS[s["id"]](s)
    out.setdefault("night", False)
    out["actors"].sort(key=lambda a: a.z)
    return out
