# -*- coding: utf-8 -*-
# 카테고리마다 박스가 사진에서 차지하는 크기와, 작은 박스(사진의 1% 미만)의 판정 분포를 본다.
import json
import os
import statistics
from collections import Counter

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
rows = []  # (category, 사진 대비 넓이 %, 판정)
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        w, h = Image.open(os.path.join(ROOT, "data", name)).size
        for i, d in enumerate(r["detections"], 1):
            b = d["box"]
            v = lab[name][str(i)]["v"]
            rows.append((d["category"], (b[2] - b[0]) * (b[3] - b[1]) / (w * h) * 100, "OP" if v in "OP" else v))

print(f"{'카테고리':8} {'박스':>4} {'넓이 중앙값':>10} {'1% 미만 비율':>11} | 1% 미만 박스의 판정 (맞음/애매/틀림)  | 1% 이상 박스의 판정")
for c in CATS:
    sub = [r for r in rows if r[0] == c]
    small = [r for r in sub if r[1] < 1]
    big = [r for r in sub if r[1] >= 1]
    cs, cb = Counter(r[2] for r in small), Counter(r[2] for r in big)
    print(f"{c:8} {len(sub):4} {statistics.median(r[1] for r in sub):9.1f}% {len(small) / len(sub) * 100:9.0f}%   | "
          f"{len(small):3}건: {cs['OP']:2}/{cs['A']:2}/{cs['X']:2}                   | {len(big):3}건: {cb['OP']:2}/{cb['A']:2}/{cb['X']:2}")
small = [r for r in rows if r[1] < 1]
big = [r for r in rows if r[1] >= 1]
cs, cb = Counter(r[2] for r in small), Counter(r[2] for r in big)
print(f"{'전체':8} {len(rows):4} {statistics.median(r[1] for r in rows):9.1f}% {len(small) / len(rows) * 100:9.0f}%   | "
      f"{len(small):3}건: {cs['OP']:2}/{cs['A']:2}/{cs['X']:2}                   | {len(big):3}건: {cb['OP']:2}/{cb['A']:2}/{cb['X']:2}")
