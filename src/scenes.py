# -*- coding: utf-8 -*-
"""Biên đạo từng cảnh: ai xuất hiện, đi đâu, biểu cảm gì, nói gì, hiệu ứng gì.

Mỗi hàm cảnh nhận `s` (từ timeline.json: lines có `rel` = mốc bắt đầu câu so với đầu cảnh, `dur`)
và trả về dict(actors, camera, sfx, title, night).
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


def _t(s):
    L = [l["rel"] for l in s["lines"]]
    E = [l["rel"] + l["dur"] for l in s["lines"]]
    return L, E, s["dur"]


def pop(text, t0, t1, x, y, size=70, color=YEL, rot=-8, jitter=True):
    """Chữ hiệu ứng bật lên (HA HA, GÂU GÂU...)."""
    a = Actor("text", z=50, text=[(0, ""), (t0, text), (t1, "")], x=x, y=y, size=size, color=color,
              scale=[(t0, 0.2), (t0 + 0.25, 1.15), (t0 + 0.4, 1.0), (t1 - 0.2, 1.0), (t1, 0.3)], rot=rot)
    if jitter:
        a.set("sway", 3.0).set("bobf", 3.0)
    return a


def bubble(text, t0, t1, x, y, tail, size=32):
    return Actor("bubble", z=60, text=[(0, ""), (t0, text), (t1, "")], x=x, y=y, tail=tail, size=size)


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
                         y=[(tt, y), (t1, y - 120)], alpha=[(tt, 1.0), (t1, 0.0)], scale=[(tt, 0.3), (tt + 0.3, 1.0)], ease=True))
    return out


# ------------------------------------------------------------------ các cảnh
def sc_intro(s):
    L, E, T = _t(s)
    acts = []
    # bốn anh em ló ra trước cửa (xa, nhỏ)
    door_y = 440
    kids = (("kaka", 560), ("puka", 610), ("moon", 660), ("sam", 710))
    for i, (n, x) in enumerate(kids):
        tt = L[1] + 0.2 + i * 0.25
        acts.append(Actor("kid", n, z=10 + i, x=x, scale=0.34, pose=[(0, "stand"), (tt, "cheer")], expr=[(0, "smile"), (tt, "laugh")],
                          y=[(0, door_y + 160), (tt, door_y + 160), (tt + 0.4, door_y)], bob=[(0, 0), (tt + 0.4, 4)], bobf=2.5,
                          visible=[(0, False), (tt, True)]))
    lu = Actor("lu", z=20, pose="run", expr="laugh", scale=0.4, y=door_y + 2,
               x=[(0, -200), (L[1] + 1.0, -200), (L[1] + 2.4, 480), (L[2], 480), (L[2] + 1.0, 760)],
               flip=False)
    acts.append(lu)
    cam = Track([(0, (640, 360, 1.0)), (L[2] + 0.3, (640, 360, 1.0)), (T, (640, 330, 1.9))])
    title = [(0.2, T - 0.3)]
    return dict(actors=acts, camera=cam, sfx=[(0.3, "pop"), (L[1] + 0.3, "pop"), (L[1] + 1.6, "bark")], title=title)


def sc_kaka(s):
    L, E, T = _t(s)
    kaka = Actor("kid", "kaka", z=10, y=FLOOR, bob=0, bobf=2.0)
    kaka.walk(0.1, L[0] + 0.2, -150, 640)
    kaka.set("pose", [(0, "walk"), (L[0] + 0.2, "crossed"), (L[1], "cheer"), (L[2], "crossed"), (L[3], "hug")])
    kaka.set("expr", [(0, "smile"), (L[0] + 0.2, "smirk"), (L[1], "laugh"), (L[2], "smirk"), (L[2] + 1.5, "wink"), (L[3], "smile")])
    kaka.set("bob", [(0, 0), (L[1], 6), (L[2], 0)]).set("bobf", 3.0)
    acts = [kaka]
    acts += name_card("KAKA", "anh Hai", L[0] + 0.3, E[0] + 1.0, 640, 150)
    # các em cười lăn
    puka = Actor("kid", "puka", z=12, x=[(0, -200), (L[1], -200), (L[1] + 0.8, 330)], y=FLOOR + 5, scale=0.85,
                 pose=[(0, "walk"), (L[1] + 0.8, "cheer"), (L[3], "stand")], expr=[(0, "smile"), (L[1] + 0.8, "laugh"), (L[3], "smile")],
                 bob=[(0, 0), (L[1] + 0.8, 7), (L[3], 0)], bobf=3.2)
    sam = Actor("kid", "sam", z=12, x=[(0, 1500), (L[1], 1500), (L[1] + 0.8, 950)], y=FLOOR + 5, scale=0.9,
                pose=[(0, "walk"), (L[1] + 0.8, "cheer"), (L[3], "stand")], expr=[(0, "smile"), (L[1] + 0.8, "laugh"), (L[3], "smile")],
                bob=[(0, 0), (L[1] + 0.8, 7), (L[3], 0)], bobf=2.8, flip=[(0, True), (L[1] + 0.8, False)])
    acts += [puka, sam]
    acts.append(pop("HA HA HA!", L[1] + 1.0, E[1] + 0.3, 330, 330, 64, YEL, -10))
    acts.append(pop("HI HI!", L[1] + 1.4, E[1] + 0.3, 960, 330, 64, PINK, 8))
    # bị rầy mà cười tỉnh bơ
    acts.append(pop("Kaka!!!", L[2] + 0.3, L[2] + 1.6, 180, 200, 60, RED, -6))
    acts.append(pop("hì hì", L[2] + 1.6, E[2], 820, 300, 50, (200, 240, 255), 6))
    # thương em: kéo hai em lại gần
    puka.set("x", puka.tracks["x"].keys + [(L[3], 330), (L[3] + 0.8, 470)])
    sam.set("x", sam.tracks["x"].keys + [(L[3], 950), (L[3] + 0.8, 810)])
    acts += hearts(L[3] + 0.8, E[3] + 0.8, 640, 240)
    lu = Actor("lu", z=9, pose="sit", scale=0.8, x=[(0, 1500), (L[3], 1500), (L[3] + 1.0, 1100)], y=FLOOR + 10)
    acts.append(lu)
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.3, "pop"), (L[1] + 1.0, "laugh"), (L[3] + 0.8, "ding")], title=None)


def sc_puka(s):
    L, E, T = _t(s)
    puka = Actor("kid", "puka", z=10, y=FLOOR)
    puka.walk(0.1, L[0] + 0.1, 1450, 640)
    puka.set("pose", [(0, "walk"), (L[0] + 0.1, "claws"), (L[2], "stand"), (L[2] + 1.6, "claws")])
    puka.set("expr", [(0, "smile"), (L[0] + 0.1, "grin"), (L[1], "wink"), (L[1] + 1.0, "grin"), (L[2], "pout"), (L[3], "angry")])
    puka.set("bob", [(0, 0), (L[0] + 0.1, 5)]).set("bobf", 2.2)
    puka.set("sway", [(0, 0), (L[1], 4), (L[2], 0)])
    acts = [puka]
    acts += name_card("PUKA", "chị Ba", L[0] + 0.3, E[1] + 0.5, 640, 150)
    # trùm mền
    blanket = Actor("prop", "blanket", z=11, x=640, scale=2.3,
                    y=[(0, FLOOR - 500), (L[2] + 0.5, FLOOR - 500), (L[2] + 1.2, FLOOR - 60)],
                    visible=[(0, False), (L[2] + 0.5, True), (E[3] + 0.2, False)])
    acts.append(blanket)
    acts.append(pop("Puka ơi, đi học!", L[2], L[2] + 2.2, 250, 230, 46, RED, -6))
    acts.append(bubble("Con hông đi đâu!", L[3] - 0.1, E[3] + 0.6, 900, 300, (720, 430)))
    puka.say(L[3] - 0.1, E[3])
    acts.append(pop("hứ!", E[3] + 0.2, T, 860, 420, 52, PINK, 10))
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.2, "pop"), (L[2] + 1.0, "swoosh"), (L[3], "boing")], title=None)


def sc_moon(s):
    L, E, T = _t(s)
    moon = Actor("kid", "moon", z=10, y=FLOOR)
    moon.walk(0.1, L[0] + 0.1, -150, 640)
    moon.set("pose", [(0, "walk"), (L[0] + 0.1, "hold"), (L[2] + 1.2, "hug")])
    moon.set("expr", [(0, "smile"), (L[0] + 0.1, "smile"), (L[1] + 1.0, "wide"), (L[1] + 2.5, "laugh"), (L[2], "smile")])
    book = Actor("prop", "book", z=11, x=[(0, -150), (L[0] + 0.1, 640)], y=FLOOR - 105, scale=1.1,
                 visible=[(0, False), (L[0] + 0.1, True), (L[2] + 1.2, False)])
    acts = [moon, book]
    acts += name_card("MOON", "em (lớn tuổi nhất nhà)", L[0] + 0.3, E[1] + 0.3, 640, 140)
    # anh Hai chị Ba đứng cạnh để so sánh
    kaka = Actor("kid", "kaka", z=9, scale=0.9, y=FLOOR, x=[(0, -200), (L[1] + 0.3, -200), (L[1] + 1.2, 330)],
                 pose=[(0, "walk"), (L[1] + 1.2, "crossed")], expr=[(0, "smile"), (L[1] + 1.2, "smirk")])
    puka = Actor("kid", "puka", z=9, scale=0.8, y=FLOOR, x=[(0, 1500), (L[1] + 0.3, 1500), (L[1] + 1.2, 950)],
                 pose=[(0, "walk"), (L[1] + 1.2, "claws")], expr=[(0, "smile"), (L[1] + 1.2, "grin")],
                 flip=[(0, True), (L[1] + 1.2, False)])
    acts += [kaka, puka]
    acts.append(pop("?", L[1] + 1.5, L[1] + 3.5, 760, 250, 80, YEL, 10))
    acts.append(pop("!", L[1] + 3.6, E[1] + 0.3, 760, 250, 80, YEL, -10))
    # chăm em: Sam chạy tới ôm
    sam = Actor("kid", "sam", z=12, scale=0.8, y=FLOOR + 6, x=[(0, 1500), (L[2] + 0.5, 1500), (L[2] + 1.3, 780)],
                pose=[(0, "walk"), (L[2] + 1.3, "hug")], expr=[(0, "smile"), (L[2] + 1.3, "laugh")],
                flip=[(0, True), (L[2] + 1.3, False)], bob=[(0, 0), (L[2] + 1.3, 4)])
    puka.set("x", puka.tracks["x"].keys + [(L[2] + 0.5, 950), (L[2] + 1.3, 1120)])
    acts.append(sam)
    acts += hearts(L[2] + 1.5, E[2] + 0.9, 700, 250)
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.2, "pop"), (L[1] + 1.5, "boing"), (L[2] + 1.5, "ding")], title=None)


def sc_sam(s):
    L, E, T = _t(s)
    sam = Actor("kid", "sam", z=10, y=FLOOR)
    sam.walk(0.1, L[0] + 0.1, 1450, 640)
    sam.set("pose", [(0, "walk"), (L[0] + 0.1, "stand"), (L[1], "cheer"), (L[2], "claws"), (L[2] + 1.6, "cheer")])
    sam.set("expr", [(0, "smile"), (L[0] + 0.1, "wink"), (L[1], "laugh"), (L[2], "wide"), (L[2] + 0.8, "o"), (L[2] + 1.6, "grin"), (L[2] + 2.4, "wide"), (E[2], "laugh")])
    # xoay điệu đà
    flips = [(0, True), (L[0] + 0.1, False)]
    for k in range(6):
        flips.append((L[1] + 0.3 + k * 0.3, k % 2 == 1))
    flips.append((L[2], False))
    sam.set("flip", flips)
    sam.set("bob", [(0, 0), (L[1], 6), (L[2], 10)]).set("bobf", 2.6)
    sam.set("sway", [(0, 0), (L[2], 6), (E[2], 0)])
    acts = [sam]
    acts += name_card("SAM", "em Út", L[0] + 0.3, E[0] + 0.8, 640, 150)
    # lấp lánh
    for i in range(5):
        tt = L[1] + 0.2 + i * 0.45
        acts.append(Actor("text", z=51, text=[(0, ""), (tt, "✦"), (tt + 0.9, "")], x=640 + (i - 2) * 110, y=250 + (i % 2) * 70, size=50,
                          color=YEL, scale=[(tt, 0.2), (tt + 0.3, 1.0), (tt + 0.9, 0.2)], rot=15 * i))
    # mặt hề: cả nhà cười
    kaka = Actor("kid", "kaka", z=9, scale=0.85, y=FLOOR, x=[(0, -200), (L[2], -200), (L[2] + 0.8, 260)],
                 pose=[(0, "walk"), (L[2] + 0.8, "cheer")], expr=[(0, "smile"), (L[2] + 0.8, "laugh")], bob=[(0, 0), (L[2] + 0.8, 6)], bobf=3)
    moon = Actor("kid", "moon", z=9, scale=0.85, y=FLOOR, x=[(0, 1500), (L[2], 1500), (L[2] + 0.8, 1020)],
                 pose=[(0, "walk"), (L[2] + 0.8, "hold")], expr=[(0, "smile"), (L[2] + 0.8, "laugh")], flip=[(0, True), (L[2] + 0.8, False)],
                 bob=[(0, 0), (L[2] + 0.8, 5)], bobf=3)
    acts += [kaka, moon]
    acts.append(pop("HA HA HA!", L[2] + 1.0, E[2] + 0.4, 300, 320, 60, YEL, -10))
    acts.append(pop("HI HI HI!", L[2] + 1.3, E[2] + 0.4, 1000, 320, 60, PINK, 8))
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.2, "pop"), (L[1] + 0.3, "sparkle"), (L[2] + 1.0, "laugh")], title=None)


def sc_lu(s):
    L, E, T = _t(s)
    lu = Actor("lu", z=10, pose=[(0, "sit"), (L[1] + 0.6, "run")], expr=[(0, "smile"), (L[0] + 1.0, "laugh")],
               x=[(0, 420), (L[1] + 0.6, 420), (L[1] + 1.4, 1500), (L[1] + 1.41, -300), (L[1] + 3.0, -300), (E[1] + 0.9, 1500)],
               y=[(0, SOFA), (L[1] + 0.6, SOFA), (L[1] + 0.8, FLOOR)], scale=[(0, 1.0), (L[1] + 0.6, 1.1)])
    acts = [lu]
    acts += name_card("LU", "cún cưng", L[0] + 0.3, E[0] + 0.8, 420, 230)
    # chén cơm còn nguyên (biếng ăn)
    acts.append(pop("biếng ăn", L[1] + 0.1, L[1] + 1.4, 900, 300, 44, BLUE, -5))
    # các anh chị chạy ngang
    for i, (n, sc) in enumerate((("kaka", 0.9), ("puka", 0.8), ("moon", 0.95), ("sam", 0.85))):
        t0 = L[1] + 1.4 + i * 0.35
        acts.append(Actor("kid", n, z=11, scale=sc, y=FLOOR + 4, pose="walk", expr="laugh", walkspeed=3.0,
                          x=[(0, -200), (t0, -200), (t0 + 2.4, 1500)], flip=[(0, False)]))
    acts.append(pop("GÂU GÂU!", E[1] + 0.2, T, 700, 300, 64, YEL, -8))
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.3, "pop"), (L[1] + 1.4, "bark"), (E[1] + 0.2, "bark")], title=None)


def sc_morning(s):
    L, E, T = _t(s)
    acts = []
    acts.append(pop("Mấy đứa ơi, dậy đi học!", L[0] + 0.9, E[0] + 0.5, 640, 110, 50, RED, -3))
    # Kaka ngồi trên giường ngáp
    kaka = Actor("kid", "kaka", z=10, x=300, y=545, scale=0.85, pose="sit", expr=[(0, "sleepy"), (L[1], "o"), (L[1] + 1.2, "sleepy")],
                 sway=[(0, 0), (L[1], 3), (L[1] + 1.4, 0)], bobf=1.5)
    zzz = Actor("prop", "zzz", z=11, x=[(0, 380), (T, 420)], y=[(0, 470), (T, 420)], scale=[(0, 0.8), (T, 1.1)],
                visible=[(0, True), (L[1], False), (L[1] + 1.3, True), (L[2], False)])
    acts += [kaka, zzz]
    # Puka trốn gầm giường: lộ cái đầu dưới mép giường
    puka = Actor("kid", "puka", z=9, x=560, y=FLOOR + 20, scale=0.75, pose="stand", expr=[(0, "pout"), (L[1] + 1.2, "angry")],
                 visible=[(0, False), (L[1] + 1.0, True)])
    blanket = Actor("prop", "blanket", z=12, x=560, y=FLOOR - 20, scale=2.0, visible=[(0, False), (L[1] + 1.0, True)])
    acts += [puka, blanket]
    # Sam núp sau tủ
    sam = Actor("kid", "sam", z=9, y=FLOOR - 30, scale=0.85, pose="stand", expr="wink",
                x=[(0, 1330), (L[1] + 2.0, 1330), (L[1] + 2.6, 1225)], look=-1.0)
    acts.append(sam)
    # Moon chỉnh tề
    moon = Actor("kid", "moon", z=11, x=930, y=FLOOR, scale=0.95, pose=[(0, "hold"), (L[2], "cheer")], expr=[(0, "smile"), (L[2], "laugh")],
                 bob=[(0, 0), (L[2], 4)])
    bag = Actor("prop", "backpack", z=10, x=1010, y=FLOOR - 150, scale=1.0, visible=[(0, False), (L[2], True)])
    acts += [moon, bag]
    acts.append(pop("✓", L[2] + 0.5, E[2] + 0.4, 1060, 330, 70, (120, 240, 120), 0))
    # Lu chạy vòng vòng
    lu = Actor("lu", z=13, pose=[(0, "sit"), (L[3], "run")], expr=[(0, "smile"), (L[3], "laugh")], scale=0.9, y=FLOOR + 10,
               x=[(0, 760), (L[3], 760)] + [(L[3] + 0.6 + k * 0.9, 1000 if k % 2 == 0 else 450) for k in range(6)],
               flip=[(0, False)] + [(L[3] + 0.6 + k * 0.9 - 0.45, k % 2 == 1) for k in range(7)])
    acts.append(lu)
    acts.append(pop("GÂU GÂU!", L[3] + 1.2, E[3] + 0.5, 700, 260, 60, YEL, -8))
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.9, "pop"), (L[1], "yawn"), (L[3] + 1.2, "bark"), (L[3] + 2.4, "bark")], title=None)


def sc_moon_finds(s):
    L, E, T = _t(s)
    acts = []
    moon = Actor("kid", "moon", z=12, y=FLOOR, scale=0.95, pose="stand", expr="smile")
    moon.walk(L[0], L[0] + 1.3, 930, 700)
    moon.set("pose", moon.tracks["pose"].keys + [(L[1], "point"), (L[2] + 1.2, "cheer"), (L[3], "walk"), (L[3] + 1.0, "hug")])
    moon.set("flip", [(0, False), (L[0], True), (L[0] + 1.3, True), (L[3], False), (L[3] + 1.0, False)])
    moon.set("x", moon.tracks["x"].keys + [(L[3], 700), (L[3] + 1.0, 1000)])
    moon.say(L[1], E[1]).say(L[2] + 1.0, E[2]).say(L[3] + 1.0, E[3])
    puka = Actor("kid", "puka", z=9, x=500, scale=0.78, pose=[(0, "stand"), (L[2], "stand"), (L[2] + 0.5, "cheer")],
                 expr=[(0, "pout"), (L[1] + 0.8, "wide"), (L[2] + 0.5, "laugh")],
                 y=[(0, FLOOR + 20), (L[2], FLOOR + 20), (L[2] + 0.5, FLOOR)])
    blanket = Actor("prop", "blanket", z=13, x=[(0, 500), (L[2], 500), (L[2] + 0.5, 330)], scale=2.0,
                    y=[(0, FLOOR - 20), (L[2], FLOOR - 20), (L[2] + 0.5, FLOOR + 40)],
                    rot=[(0, 0), (L[2] + 0.5, 20)])
    puka.say(L[2] + 0.4, L[2] + 1.1)
    acts += [moon, puka, blanket]
    acts.append(bubble("Puka ơi, ra đi! Hôm nay cô cho vẽ tranh nè!", L[1], E[1] + 0.3, 760, 250, (690, 400), 30))
    acts.append(bubble("Thiệt hông?", L[2] + 0.3, L[2] + 1.4, 330, 330, (470, 470), 32))
    acts.append(bubble("Thiệt mà!", L[2] + 1.4, E[2] + 0.3, 820, 300, (700, 420), 32))
    # Sam ra khỏi tủ
    sam = Actor("kid", "sam", z=10, y=FLOOR - 30, scale=0.85, pose=[(0, "stand"), (L[3] + 1.2, "hug")], expr=[(0, "wink"), (L[3] + 1.2, "laugh")],
                x=[(0, 1225), (L[3] + 0.6, 1225), (L[3] + 1.2, 1130)], look=[(0, -1.0), (L[3] + 1.2, 0.0)])
    acts.append(sam)
    acts.append(bubble("Út đi học, chiều về chị kể chuyện cho nghe.", L[3] + 0.8, E[3] + 0.5, 800, 230, (980, 400), 30))
    acts += hearts(L[3] + 1.4, E[3] + 0.8, 1080, 300)
    kaka = Actor("kid", "kaka", z=8, x=300, y=545, scale=0.85, pose="sit", expr=[(0, "sleepy"), (L[2] + 0.5, "laugh")])
    acts.append(kaka)
    return dict(actors=acts, camera=None, sfx=[(L[1], "pop"), (L[2] + 0.4, "boing"), (L[3] + 1.2, "ding")], title=None)


def sc_kaka_monkey(s):
    L, E, T = _t(s)
    acts = []
    kaka = Actor("kid", "kaka", z=12, y=FLOOR, scale=1.0, pose=[(0, "stand"), (L[1], "monkey")],
                 expr=[(0, "smirk"), (L[1], "grin"), (L[1] + 0.8, "o"), (L[1] + 1.5, "wide"), (L[1] + 2.2, "grin"), (L[3], "laugh")])
    kaka.walk(0.1, L[0] + 0.3, -150, 640)
    kaka.set("x", kaka.tracks["x"].keys + [(L[1], 640)] + [(L[1] + 0.5 + k * 0.5, 560 if k % 2 == 0 else 720) for k in range(8)] + [(L[3], 640)])
    kaka.set("flip", [(0, False)] + [(L[1] + 0.25 + k * 0.5, k % 2 == 1) for k in range(9)] + [(L[3], False)])
    kaka.set("bob", [(0, 0), (L[1], 10), (L[3], 0)]).set("bobf", 4.0)
    kaka.set("sway", [(0, 0), (L[1], 6), (L[3], 0)])
    acts.append(kaka)
    acts.append(pop("ú ù ú!", L[1] + 0.5, E[1], 640, 230, 56, YEL, -8))
    puka = Actor("kid", "puka", z=10, x=300, y=FLOOR, scale=0.85, pose=[(0, "stand"), (L[1] + 0.6, "cheer"), (L[2], "sit")],
                 expr=[(0, "pout"), (L[1] + 0.6, "laugh")], bob=[(0, 0), (L[1] + 0.6, 7)], bobf=3.5,
                 rot=[(0, 0), (L[2], 0), (L[2] + 0.4, -25)])
    sam = Actor("kid", "sam", z=10, x=980, scale=0.85, pose=[(0, "stand"), (L[1] + 0.8, "cheer"), (L[2] + 0.4, "lie")],
                expr=[(0, "sad"), (L[1] + 0.8, "laugh")], bob=[(0, 0), (L[1] + 0.8, 7)], bobf=3.2,
                rot=[(0, 0), (L[2] + 0.4, 0), (L[2] + 0.9, 80)], y=[(0, FLOOR), (L[2] + 0.4, FLOOR), (L[2] + 0.9, FLOOR + 60)])
    moon = Actor("kid", "moon", z=9, x=1180, y=FLOOR - 10, scale=0.8, pose="hold", expr=[(0, "smile"), (L[1] + 1.0, "laugh")])
    acts += [puka, sam, moon]
    acts.append(pop("HA HA HA!", L[2], E[2] + 0.3, 300, 330, 60, YEL, -10))
    acts.append(pop("HI HI HI!", L[2] + 0.4, E[2] + 0.3, 1000, 330, 60, PINK, 8))
    # đi học: tất cả bước ra bên phải, đeo cặp
    walk_t = L[3] + 0.8
    for i, (a, sc) in enumerate(((kaka, 1.0), (puka, 0.85), (sam, 0.85), (moon, 0.8))):
        xs = a.tracks["x"].keys
        x_now = a.state(walk_t)["x"]
        a.set("x", xs + [(walk_t, x_now), (walk_t + 0.1 + i * 0.3, x_now), (T + 0.5, 1700)])
        a.set("pose", a.tracks["pose"].keys + [(walk_t, "walk")])
        a.set("rot", a.tracks["rot"].keys + [(walk_t, 0)] if "rot" in a.tracks else [(0, 0)])
        a.set("y", [(0, FLOOR)] if a is not sam else [(0, FLOOR), (walk_t, FLOOR)])
        a.set("expr", a.tracks["expr"].keys + [(walk_t, "smile")])
        a.set("bob", a.tracks["bob"].keys + [(walk_t, 0)] if "bob" in a.tracks else [(0, 0)])
        a.set("walkspeed", 2.6)
        bag = Actor("prop", "backpack", z=13, scale=sc, visible=[(0, False), (walk_t, True)],
                    x=[(walk_t, x_now - 20), (walk_t + 0.1 + i * 0.3, x_now - 20), (T + 0.5, 1680)], y=FLOOR - 140 * sc)
        acts.append(bag)
    lu = Actor("lu", z=14, pose="run", expr="laugh", scale=0.9, y=FLOOR + 6, x=[(0, -300), (walk_t + 1.2, -300), (T + 0.5, 1700)])
    acts.append(lu)
    return dict(actors=acts, camera=None, sfx=[(L[1], "boing"), (L[1] + 0.8, "boing"), (L[2], "laugh"), (walk_t, "pop")], title=None)


def sc_fight(s):
    L, E, T = _t(s)
    acts = []
    # Puka bên trái kéo, Sam bên phải kéo (lật) - gấu ở giữa
    tug = [(L[1] + k * 0.3, (-1) ** k * 18) for k in range(12)]
    puka = Actor("kid", "puka", z=10, y=FLOOR, scale=0.95, pose=[(0, "stand"), (L[0] + 0.6, "pull")],
                 expr=[(0, "smile"), (L[0] + 0.6, "angry"), (L[3] + 1.2, "wide")],
                 x=[(0, -150), (L[0] + 0.6, 500)] + [(t, 500 + d) for t, d in tug] + [(L[3] + 1.0, 500)],
                 rot=[(0, 0)] + [(t, -d * 0.6) for t, d in tug] + [(L[3] + 1.0, 0)])
    sam = Actor("kid", "sam", z=10, y=FLOOR, scale=0.9, pose=[(0, "stand"), (L[0] + 0.6, "pull")], flip=[(0, True)],
                expr=[(0, "smile"), (L[0] + 0.6, "angry"), (L[3] + 1.2, "wide")],
                x=[(0, 1450), (L[0] + 0.6, 780)] + [(t, 780 + d) for t, d in tug] + [(L[3] + 1.0, 780)],
                rot=[(0, 0)] + [(t, -d * 0.6) for t, d in tug] + [(L[3] + 1.0, 0)])
    puka.set("pose", puka.tracks["pose"].keys + [(0, "walk")])
    sam.set("pose", sam.tracks["pose"].keys + [(0, "walk")])
    teddy = Actor("prop", "teddy", z=12, scale=1.2, y=FLOOR - 100, x=[(0, 640)] + [(t, 640 + d) for t, d in tug],
                  rot=[(0, 0)] + [(t, d) for t, d in tug], visible=[(0, False), (L[0] + 0.4, True), (L[3] + 1.0, False)])
    acts += [puka, sam, teddy]
    acts.append(bubble("Của em!", L[1] - 0.1, L[1] + 0.9, 980, 300, (830, 430)))
    acts.append(bubble("Của chị!", L[1] + 0.9, E[1] + 0.3, 300, 300, (450, 430)))
    sam.say(L[1] - 0.1, L[1] + 0.9)
    puka.say(L[1] + 0.9, E[1] + 0.2)
    acts.append(pop("hừm!", L[2] + 0.3, E[2], 640, 260, 52, RED, 0))
    # Lu phóng tới ngoạm gấu
    lu = Actor("lu", z=14, pose="run", expr=[(0, "smile"), (L[3] + 1.0, "laugh")], scale=1.0, y=FLOOR + 8,
               x=[(0, -300), (L[3] + 0.2, -300), (L[3] + 1.0, 640), (L[3] + 1.2, 640), (L[3] + 2.0, 1600)],
               item=[(0, None), (L[3] + 1.0, "teddy")])
    acts.append(lu)
    acts.append(pop("GÂU!", L[3] + 0.9, L[3] + 1.8, 640, 300, 64, YEL, -8))
    acts.append(pop("Ơ!", L[3] + 1.4, E[3] + 0.6, 500, 330, 56, PINK, -6))
    acts.append(pop("Ơ!", L[3] + 1.5, E[3] + 0.6, 800, 330, 56, PINK, 6))
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.6, "boing"), (L[1] - 0.4, "pop"), (L[3] + 0.3, "swoosh"), (L[3] + 0.9, "bark")], title=None)


def sc_chase(s):
    L, E, T = _t(s)
    acts = []
    # vòng chạy: trước sofa từ trái sang phải (gần), rồi phía trên từ phải sang trái (xa, nhỏ)
    def loop_x(t0, period, offset=0.0):
        xs, ys, scs, flips = [], [], [], []
        k = 0
        t = t0 - offset * period
        while t < L[2] + 0.5:
            xs += [(t, -250), (t + period * 0.5, 1500), (t + period * 0.5 + 0.01, 1500), (t + period, -250)]
            ys += [(t, FLOOR), (t + period * 0.5, FLOOR), (t + period * 0.5 + 0.01, FAR), (t + period, FAR)]
            scs += [(t, 1.0), (t + period * 0.5, 1.0), (t + period * 0.5 + 0.01, 0.62), (t + period, 0.62)]
            flips += [(t, False), (t + period * 0.5, True)]
            t += period
            k += 1
        return xs, ys, scs, flips
    period = 4.0
    stop = L[2] + 0.5
    lx, ly, ls, lf = loop_x(0.0, period)
    cut = lambda keys: [(t, v) for t, v in keys if t < stop - 0.3]  # noqa: E731  bỏ các khung sau lúc dừng
    lu = Actor("lu", z=15, pose=[(0, "run"), (stop, "stand")], expr="laugh", item=[(0, "teddy"), (L[2] + 1.0, None)],
               x=cut(lx) + [(stop, 640)], y=cut(ly) + [(stop, FLOOR)], scale=cut(ls) + [(stop, 1.05)], flip=cut(lf) + [(stop, False)])
    # Lu chạy đến mốc L[2] thì dừng giữa: nối đường
    acts.append(lu)
    chasers = (("puka", 0.9, 0.16, "laugh"), ("sam", 0.9, 0.3, "o"), ("moon", 0.95, 0.44, "wide"), ("kaka", 1.0, 0.58, "grin"))
    kids = {}
    for n, sc, off, ex in chasers:
        xs, ys, scs, fl = loop_x(0.0, period, off)
        a = Actor("kid", n, z=14, pose="walk", expr=ex, walkspeed=3.2, x=xs, y=ys, flip=fl,
                  scale=[(t, v * sc) for t, v in scs], bob=0)
        kids[n] = a
        acts.append(a)
    acts.append(pop("Lu ơi, đứng lại!", L[0] + 0.5, E[0], 640, 150, 50, RED, -4))
    # Kaka té, Moon đỡ Sam, Puka cười
    tf = L[1] + 0.6
    for n, a in kids.items():
        st = a.state(tf)
        a.set("x", [(0, st["x"])] + [(t, v) for t, v in a.tracks["x"].keys if t < tf] + [(tf, st["x"])])
        a.set("y", [(t, v) for t, v in a.tracks["y"].keys if t < tf] + [(tf, st["y"])])
        a.set("scale", [(t, v) for t, v in a.tracks["scale"].keys if t < tf] + [(tf, st["scale"])])
        a.set("flip", [(t, v) for t, v in a.tracks["flip"].keys if t < tf] + [(tf, False)])
    # đặt lại vị trí cho đoạn sau
    kaka, moon, sam, puka = kids["kaka"], kids["moon"], kids["sam"], kids["puka"]
    for a, x, y, sc in ((kaka, 300, FLOOR, 1.0), (moon, 1000, FLOOR, 0.95), (sam, 1130, FLOOR, 0.85), (puka, 520, FLOOR, 0.9)):
        a.set("x", a.tracks["x"].keys + [(tf + 0.01, x)])
        a.set("y", a.tracks["y"].keys + [(tf + 0.01, y)])
        a.set("scale", a.tracks["scale"].keys + [(tf + 0.01, sc)])
    kaka.set("pose", [(0, "walk"), (tf, "sit")]).set("rot", [(0, 0), (tf, 0), (tf + 0.3, -30)]).set("expr", [(0, "grin"), (tf, "wide"), (L[2], "laugh")])
    kaka.set("y", kaka.tracks["y"].keys + [(tf + 0.3, FLOOR + 30)])
    acts.append(pop("BỊCH!", tf + 0.2, tf + 1.5, 300, 330, 70, RED, -12))
    moon.set("pose", [(0, "walk"), (tf, "hug")]).set("expr", [(0, "wide"), (tf, "smile"), (L[2], "laugh")])
    sam.set("pose", [(0, "walk"), (tf, "stand")]).set("expr", [(0, "o"), (tf, "wide"), (tf + 1.0, "laugh")]).set("rot", [(0, 0), (tf, 15), (tf + 0.6, 0)])
    puka.set("pose", [(0, "walk"), (tf, "cheer")]).set("expr", [(0, "laugh")]).set("bob", [(0, 0), (tf, 8)]).set("bobf", 3.5)
    acts.append(pop("HA HA HA!", tf + 1.2, E[1] + 0.3, 520, 300, 60, YEL, -10))
    # Lu dừng, thả gấu, le lưỡi
    teddy = Actor("prop", "teddy", z=12, scale=1.2, x=700, y=[(L[2] + 0.8, FLOOR - 140), (L[2] + 1.3, FLOOR)],
                  rot=[(L[2] + 0.8, 0), (L[2] + 1.3, 15)], visible=[(0, False), (L[2] + 1.0, True)])
    acts.append(teddy)
    acts.append(bubble("Chơi chung vui hơn mà!", L[2] + 2.4, E[2] + 0.6, 640, 230, (640, 420), 32))
    return dict(actors=acts, camera=None, sfx=[(L[0], "bark"), (tf, "boing"), (tf + 1.2, "laugh"), (L[2] + 1.2, "pop")], title=None)


def sc_lesson(s):
    L, E, T = _t(s)
    acts = []
    puka = Actor("kid", "puka", z=10, x=[(0, 520), (L[0] + 1.6, 520), (L[0] + 2.2, 580)], y=FLOOR, scale=0.9,
                 pose=[(0, "hold"), (L[0] + 2.2, "point"), (L[1], "hug"), (L[3], "sit")],
                 expr=[(0, "flat"), (L[0] + 0.8, "smile"), (L[1], "laugh"), (L[3], "smile")])
    sam = Actor("kid", "sam", z=11, x=[(0, 800), (L[1], 800), (L[1] + 0.6, 690)], y=FLOOR, scale=0.85, flip=[(0, True), (L[1], False)],
                pose=[(0, "stand"), (L[0] + 2.4, "hold"), (L[1], "hug"), (L[3], "sit")],
                expr=[(0, "sad"), (L[0] + 2.4, "wide"), (L[1], "laugh"), (L[3], "smile")])
    teddy = Actor("prop", "teddy", z=12, scale=1.1, y=FLOOR - 95, x=[(0, 520), (L[0] + 1.6, 520), (L[0] + 2.4, 790)],
                  visible=[(0, True), (L[1] + 0.3, False)])
    acts += [puka, sam, teddy]
    puka.say(L[0] + 1.6, E[0])
    acts.append(bubble("Thôi em chơi trước đi, chị chơi sau.", L[0] + 1.5, E[0] + 0.4, 400, 250, (500, 420), 30))
    acts += hearts(L[1] + 0.3, E[1] + 1.0, 640, 300)
    moon = Actor("kid", "moon", z=9, x=[(0, 1450), (L[2] - 0.6, 1450), (L[2] + 0.4, 980)], y=FLOOR, scale=0.95,
                 pose=[(0, "walk"), (L[2] + 0.4, "hold"), (L[3], "sit")], expr=[(0, "smile"), (L[2] + 0.4, "laugh"), (L[3], "smile")],
                 flip=[(0, True), (L[2] + 0.4, False)])
    book = Actor("prop", "book", z=10, x=[(0, 1450), (L[2] - 0.6, 1450), (L[2] + 0.4, 980)], y=FLOOR - 105, scale=1.1,
                 visible=[(0, False), (L[2] + 0.4, True), (L[3], False)])
    moon.say(L[2] + 0.4, E[2])
    acts += [moon, book]
    acts.append(bubble("Giờ học bài chung nha!", L[2] + 0.3, E[2] + 0.3, 900, 230, (980, 400), 32))
    # ngồi học chung trên sofa, Kaka kể chuyện cười
    sit_t = L[3]
    for a, x in ((puka, 330), (sam, 480), (moon, 640)):
        a.set("x", a.tracks["x"].keys + [(sit_t - 0.01, a.state(sit_t - 0.01)["x"]), (sit_t + 0.6, x)])
        a.set("y", [(0, FLOOR), (sit_t - 0.01, FLOOR), (sit_t + 0.6, SOFA)])
    book2 = Actor("prop", "book", z=12, scale=0.9, x=[(sit_t + 0.6, 400)], y=SOFA - 70, visible=[(0, False), (sit_t + 0.6, True)])
    book3 = Actor("prop", "book", z=12, scale=0.9, x=[(sit_t + 0.6, 600)], y=SOFA - 70, visible=[(0, False), (sit_t + 0.6, True)])
    acts += [book2, book3]
    kaka = Actor("kid", "kaka", z=11, x=[(0, -200), (sit_t + 0.8, -200), (sit_t + 1.6, 170)], y=[(0, FLOOR), (sit_t + 1.6, SOFA)], scale=0.95,
                 pose=[(0, "walk"), (sit_t + 1.6, "sit")], expr=[(0, "smirk"), (sit_t + 1.6, "laugh")])
    kaka.say(L[3] + 3.0, E[3] + 0.3)
    acts.append(kaka)
    acts.append(pop("hí hí", L[3] + 3.2, E[3] + 0.6, 180, 380, 48, PINK, -8))
    acts.append(pop("✓ ngoan!", L[3] + 1.2, L[3] + 3.0, 480, 330, 50, (120, 240, 120), 0))
    return dict(actors=acts, camera=None, sfx=[(L[0] + 1.2, "pop"), (E[1] + 0.1, "ding"), (L[2] - 0.2, "pop"), (L[3] + 3.2, "laugh")], title=None)


def sc_ending(s):
    L, E, T = _t(s)
    acts = []
    placement = (("kaka", 180, "sit", "smile"), ("puka", 330, "sit", "sleepy"), ("sam", 640, "sit", "smile"), ("moon", 810, "sit", "smile"))
    for n, x, p, ex in placement:
        acts.append(Actor("kid", n, z=10, x=x, y=SOFA, scale=0.95, pose=p, expr=[(0, ex), (L[1] + 1.0, "laugh"), (L[2], "smile")],
                          bob=[(0, 0), (L[1] + 1.0, 3), (L[2], 0)], bobf=1.5))
    acts.append(Actor("lu", z=12, pose="lie", expr="smile", x=490, y=SOFA - 5, scale=0.95))
    acts.append(Actor("prop", "teddy", z=11, x=575, y=SOFA, scale=0.9))
    acts += hearts(L[1] + 0.6, E[1] + 1.5, 500, 420, 4)
    acts.append(Actor("text", z=60, text=[(0, ""), (L[2] + 1.0, "Anh em như thể tay chân"), (T, "")], x=640, y=120, size=58, color=YEL,
                      scale=[(L[2] + 1.0, 0.2), (L[2] + 1.35, 1.1), (L[2] + 1.5, 1.0)], rot=-3))
    cam = Track([(0, (640, 400, 1.0)), (T, (560, 460, 1.3))])
    return dict(actors=acts, camera=cam, sfx=[(L[1] + 0.6, "ding"), (L[2] + 1.0, "sparkle")], title=None, night=True)


def sc_outro(s):
    L, E, T = _t(s)
    acts = []
    door_y = 440
    for i, (n, x) in enumerate((("kaka", 560), ("puka", 610), ("moon", 660), ("sam", 710))):
        acts.append(Actor("kid", n, z=10 + i, x=x, y=door_y, scale=0.34, pose="cheer", expr="laugh", bob=4, bobf=2.5 + i * 0.2))
    acts.append(Actor("lu", z=20, pose="sit", expr="laugh", scale=0.4, x=760, y=door_y + 2))
    acts.append(Actor("text", z=60, text=[(0, ""), (L[0] + 0.2, "HẾT"), (T, "")], x=640, y=130, size=96, color=YEL,
                      scale=[(L[0] + 0.2, 0.2), (L[0] + 0.5, 1.15), (L[0] + 0.65, 1.0)], rot=-4))
    acts.append(Actor("text", z=60, text=[(0, ""), (E[0] + 0.3, "Hẹn gặp lại!"), (T, "")], x=640, y=230, size=50, color=(255, 255, 255),
                      scale=[(E[0] + 0.3, 0.2), (E[0] + 0.6, 1.0)], rot=0))
    return dict(actors=acts, camera=None, sfx=[(L[0] + 0.2, "ding"), (E[0] + 0.3, "sparkle")], title=None)


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
