# -*- coding: utf-8 -*-
"""Tách nền chân dung (assets/refs) thành ảnh RGBA cắt dán (assets/cutouts).

Nền chân dung là dải màu hồng kem + sàn gỗ; dùng tô loang (flood fill) từ mép ảnh với ngưỡng màu,
sau đó dọn phần bóng dưới chân và làm mịn viền alpha.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def flood_bg(arr, tol=28, seeds=None):
    """Đánh dấu nền bằng tô loang từ các điểm mép, so màu với điểm lân cận (gradient mượt vẫn loang được)."""
    h, w, _ = arr.shape
    a = arr.astype(np.int16)
    bg = np.zeros((h, w), bool)
    if seeds is None:
        seeds = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1), (0, w // 2), (h - 1, w // 2), (h // 2, 0), (h // 2, w - 1)]
    q = deque()
    for y, x in seeds:
        if not bg[y, x]:
            bg[y, x] = True
            q.append((y, x))
    while q:
        y, x = q.popleft()
        c = a[y, x]
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx]:
                if np.abs(a[ny, nx] - c).max() <= tol:
                    bg[ny, nx] = True
                    q.append((ny, nx))
    return bg


def fit_background(arr, margin=0.04):
    """Ước lượng nền 2D: vùng trên (dải màu toả tròn) khớp mặt bậc hai từ các điểm mép trái/phải/trên;
    vùng sàn (phía dưới, khác màu hẳn) lấy trung vị từng hàng từ hai mép."""
    h, w, _ = arr.shape
    m = max(2, int(w * margin))
    rowbg = np.median(np.concatenate([arr[:, :m, :], arr[:, w - m:, :]], axis=1), axis=1)  # (h,3)
    top = rowbg[: max(1, h // 20)].mean(axis=0)
    floor_rows = np.abs(rowbg - top).max(axis=1) > 40
    # hàng sàn đầu tiên (liên tục từ dưới lên)
    fy = h
    while fy > 0 and floor_rows[fy - 1]:
        fy -= 1
    ys, xs = np.mgrid[0:h, 0:w]
    sel = np.zeros((h, w), bool)
    sel[:fy, :m] = True
    sel[:fy, w - m:] = True
    # dải trên: chỉ lấy điểm giống màu góc (loại tóc/búi tóc chạm mép)
    corner = np.concatenate([arr[:m, :m].reshape(-1, 3), arr[:m, w - m:].reshape(-1, 3)]).mean(axis=0)
    topband = np.zeros((h, w), bool)
    topband[: max(2, int(h * margin)), :] = True
    topband &= np.abs(arr - corner).max(axis=2) < 45
    sel |= topband
    sel &= ys < fy
    X = np.stack([np.ones(sel.sum()), xs[sel], ys[sel], xs[sel] ** 2, ys[sel] ** 2, xs[sel] * ys[sel]], axis=1).astype(np.float64)
    Xall = np.stack([np.ones(h * w), xs.ravel(), ys.ravel(), xs.ravel() ** 2, ys.ravel() ** 2, (xs * ys).ravel()], axis=1).astype(np.float64)
    bg = np.empty_like(arr)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(X, arr[sel, c].astype(np.float64), rcond=None)
        bg[:, :, c] = (Xall @ coef).reshape(h, w)
    # vùng sàn: dùng trung vị hàng
    bg[fy:, :, :] = rowbg[fy:, None, :]
    return bg, fy


def cutout(src, dst, tol=30, scale=0.5, green_bg=False, shape_mask=None, bright_bg=None, shade=True):
    im = Image.open(src).convert("RGB")
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32)
    h, w, _ = arr.shape
    bgest, fy = fit_background(arr)
    dist = np.abs(arr - bgest).max(axis=2)
    bg = dist <= tol
    # bóng dưới chân: ở vùng sàn, điểm tối hơn sàn nhưng cùng sắc độ
    eps = 1e-3
    chroma = arr / (arr.sum(axis=2, keepdims=True) + eps)
    chroma_bg = bgest / (bgest.sum(axis=2, keepdims=True) + eps)
    cdist = np.abs(chroma - chroma_bg).max(axis=2)
    bright = arr.sum(axis=2) / (bgest.sum(axis=2) + eps)
    floor = np.zeros((h, w), bool)
    floor[fy:, :] = True
    if shade:
        bg |= (cdist < 0.04) & (bright > 0.5) & (bright < 0.97) & floor
    if green_bg:
        g = arr[:, :, 1]
        bg |= (g > arr[:, :, 0] + 15) & (g > arr[:, :, 2] + 15)
    if bright_bg is not None:
        bg |= arr.sum(axis=2) > bright_bg
    if shape_mask is not None:
        bg |= ~shape_mask
    fg0 = ~bg
    dil = np.asarray(Image.fromarray((fg0 * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    keep = largest_component(dil)
    fg = fg0 & keep
    holes = ~fg & ~largest_component_touching_border(~fg)
    fg |= holes
    alpha = (fg * 255).astype(np.uint8)
    a_img = Image.fromarray(alpha).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA")
    out.putalpha(a_img)
    bbox = out.getbbox()
    out = out.crop(bbox)
    out.save(dst)
    return out.size


def largest_component_touching_border(mask):
    """Thành phần của mask nối với mép ảnh (nền thật sự)."""
    h, w = mask.shape
    seen = np.zeros_like(mask)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return seen


def largest_component(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask)
    best = None
    best_n = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            if mask[y, x] and not seen[y, x]:
                comp = []
                q = deque([(y, x)])
                seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    comp.append((cy, cx))
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                if len(comp) > best_n:
                    best_n = len(comp)
                    best = comp
    out = np.zeros_like(mask)
    if best:
        ys, xs = zip(*best)
        out[list(ys), list(xs)] = True
    return out


if __name__ == "__main__":
    refs = os.path.join(ROOT, "assets", "refs")
    outd = os.path.join(ROOT, "assets", "cutouts")
    os.makedirs(outd, exist_ok=True)
    names = sys.argv[1:] or ["kaka", "puka", "moon", "sam", "muoi", "eric", "lu"]
    PARAMS = {"kaka": 26, "puka": 26, "moon": 16, "sam": 26, "muoi": 12, "eric": 26, "lu": -1}
    for n in names:
        src = [f for f in os.listdir(refs) if f.startswith(n + ".")][0]
        shape = None
        bright = None
        if n == "lu":
            # mặt nạ hình dáng Lu (toạ độ ảnh 1000x1400 sau khi thu 0.5)
            from PIL import ImageDraw
            m = Image.new("L", (1000, 1400), 0)
            dm = ImageDraw.Draw(m)
            for cx, cy, rx, ry in ((492, 470, 248, 195), (292, 560, 60, 125), (698, 555, 58, 125), (510, 880, 165, 225),
                                   (378, 1140, 110, 160), (632, 1140, 90, 160), (488, 640, 88, 70)):
                dm.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
            shape = np.asarray(m) > 0
            bright = 520  # nền hồng kem sáng hơn lông Lu
        size = cutout(os.path.join(refs, src), os.path.join(outd, n + ".png"), tol=PARAMS[n], green_bg=(n == "lu"), shape_mask=shape, bright_bg=bright, shade=(n != "lu"))
        print(n, size)
