# -*- coding: utf-8 -*-
"""Dựng khung hình cho từng cảnh và mã hoá bằng ffmpeg.

    python3 src/render.py --timeline build/timeline.json --out build/segs            # dựng toàn bộ
    python3 src/render.py --timeline build/timeline.json --preview build/preview     # xuất vài ảnh PNG mỗi cảnh
"""
import argparse
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import anim  # noqa: E402
import scenes  # noqa: E402
from backgrounds import background  # noqa: E402
from story import TITLE  # noqa: E402

W, H = anim.W, anim.H
FPS = 24


_NIGHT = None


def night_overlay():
    """Lớp phủ tối xanh ban đêm với vệt đèn ấm mờ dần ở giữa."""
    global _NIGHT
    if _NIGHT is None:
        from PIL import ImageFilter
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse([W * 0.2, -250, W * 0.8, 480], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(90))
        alpha = mask.point(lambda v: int(110 - 85 * v / 255))
        ov = Image.new("RGBA", (W, H), (15, 15, 70, 0))
        ov.putalpha(alpha)
        _NIGHT = ov
    return _NIGHT


def draw_title(frame, t, t0, t1):
    if t < t0 or t > t1:
        return
    a = min(1.0, (t - t0) / 0.5, (t1 - t) / 0.5)
    sc = 0.6 + 0.4 * min(1.0, (t - t0) / 0.4)
    anim.draw_pop_text(frame, TITLE, W / 2, 120, 84, (255, 225, 80), rot=-3, alpha=a, scale=sc)
    anim.draw_pop_text(frame, "Phim hoạt hình cho bé", W / 2, 205, 36, (255, 255, 255), rot=0, alpha=a)


def render_frame(sc, bg, built, t):
    frame = bg.copy()
    if built.get("night"):
        frame.alpha_composite(night_overlay())
    # câu đang nói
    cur = None
    for ln in sc["lines"]:
        if ln["rel"] - 0.05 <= t <= ln["rel"] + ln["dur"] + 0.45:
            cur = ln
            break
    speaking = cur["who"] if cur and ln["rel"] <= t <= ln["rel"] + ln["dur"] else None
    # vẽ theo lớp z, cùng lớp thì ai đứng thấp hơn (gần máy quay) vẽ sau
    states = [(a, a.state(t)) for a in built["actors"]]
    states.sort(key=lambda p: (p[0].z, p[1]["y"]))
    speaker = None
    for a, st in states:
        if speaking and a.kind in ("kid", "lu") and (a.name == speaking or (a.kind == "lu" and speaking == "lu")) and st["visible"]:
            st = dict(st, talk=True)
            speaker = (a, st)
        if speaking == "all" and a.kind in ("kid", "lu") and st["visible"]:
            st = dict(st, talk=True)
        anim.draw_actor(frame, a, st, t)
    # bong bóng thoại tự động phía trên đầu người nói
    if speaker and cur["who"] != "all" and not built.get("no_bubble"):
        a, st = speaker
        img, x, y = anim.actor_image(a, st, t)
        hx, hy = x + img.width / 2, y + 10
        bx = min(max(hx, 230), W - 230)
        by = max(70, hy - 95)
        anim.draw_bubble(frame, cur["text"], bx, by, (hx, hy), size=30, maxw=440)
    if built.get("camera") is not None:
        frame = anim.apply_camera(frame, built["camera"].at(t))
    if built.get("title"):
        for (t0, t1) in built["title"]:
            draw_title(frame, t, t0, t1)
    # phụ đề
    if cur:
        anim.draw_caption(frame, cur["text"], cur["who"])
    # mờ dần đầu / cuối cảnh
    fade = 0.35
    f = 1.0
    if t < fade:
        f = t / fade
    elif t > sc["dur"] - fade:
        f = max(0.0, (sc["dur"] - t) / fade)
    if f < 1.0:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, f)
    return frame


def render_scene(args):
    sc, out_dir, preview = args
    bg = background(sc["bg"]).convert("RGBA")
    built = scenes.build(sc)
    n = int(round(sc["dur"] * FPS))
    if preview:
        os.makedirs(preview, exist_ok=True)
        ts = sorted({min(n - 1, int(k * n / 6)) for k in range(6)} | {min(n - 1, int(l["rel"] * FPS) + 12) for l in sc["lines"]})
        for i in ts:
            fr = render_frame(sc, bg, built, i / FPS).convert("RGB")
            fr.save(os.path.join(preview, f"{sc['id']}_{i:04d}.png"))
        return sc["id"], n
    out = os.path.join(out_dir, f"{sc['id']}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        fr = render_frame(sc, bg, built, i / FPS).convert("RGB")
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg lỗi ở cảnh {sc['id']}")
    return sc["id"], n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--only", default=None, help="chỉ dựng các cảnh có id chứa chuỗi này")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    tl = json.load(open(args.timeline))
    scs = [s for s in tl["scenes"] if not args.only or args.only in s["id"]]
    if args.out:
        os.makedirs(args.out, exist_ok=True)
    jobs = [(s, args.out, args.preview) for s in scs]
    with Pool(args.jobs) as pool:
        for sid, n in pool.imap_unordered(render_scene, jobs):
            print(f"  xong {sid}: {n} khung hình", flush=True)
    if args.out:
        with open(os.path.join(args.out, "list.txt"), "w") as f:
            for s in tl["scenes"]:
                f.write(f"file '{s['id']}.mp4'\n")


if __name__ == "__main__":
    main()
