# -*- coding: utf-8 -*-
"""Tính mốc thời gian tuyệt đối cho từng cảnh / từng câu thuyết minh từ lines.json."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from story import SCENES  # noqa: E402

GAP = 0.4       # khoảng nghỉ giữa hai câu
TAIL = 1.0      # nghỉ cuối cảnh
LEAD = {"01_intro": 3.2, "14_outro": 0.8}  # thời gian trước câu đầu tiên của cảnh
LEAD_DEFAULT = 0.7
EXTRA = {"13_ending": 1.5, "14_outro": 2.5, "09_kaka_monkey": 1.2, "11_chase": 0.6, "02_kaka": 0.5, "06_lu": 1.2}  # kéo dài cuối cảnh


def build(voice_dir):
    meta = json.load(open(os.path.join(voice_dir, "lines.json")))
    by_scene = {}
    for m in meta:
        by_scene.setdefault(m["scene"], []).append(m)
    t = 0.0
    scenes = []
    for s in SCENES:
        lines = by_scene[s["id"]]
        start = t
        lt = start + LEAD.get(s["id"], LEAD_DEFAULT)
        items = []
        for m in lines:
            items.append(dict(text=m["text"], who=m.get("who", "nar"), key=m.get("key"), file=m["file"], start=lt, dur=m["dur"], rel=lt - start))
            lt += m["dur"] + GAP
        end = lt - GAP + TAIL + EXTRA.get(s["id"], 0.0)
        scenes.append(dict(id=s["id"], bg=s["bg"], start=start, end=end, dur=end - start, lines=items))
        t = end
    return dict(total=t, scenes=scenes)


if __name__ == "__main__":
    tl = build(sys.argv[1])
    json.dump(tl, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    for s in tl["scenes"]:
        print(f"{s['id']:16s} {s['start']:6.1f} -> {s['end']:6.1f}  ({s['dur']:5.1f}s)")
    print(f"Tổng: {tl['total']:.1f}s")
