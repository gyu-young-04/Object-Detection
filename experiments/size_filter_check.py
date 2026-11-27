# -*- coding: utf-8 -*-
# "작은 박스를 크기 기준으로 버리면?"을 두 가지 채점으로 확인한다: (1) Claude 채점 306건 (2) 사용자 판정 141건.
import json
import os
from collections import Counter

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
_sizes = {}


def frac(photo, box):
    if photo not in _sizes:
        _sizes[photo] = Image.open(os.path.join(ROOT, "data", photo)).size
    w, h = _sizes[photo]
    return (box[2] - box[0]) * (box[3] - box[1]) / (w * h) * 100


ai = []  # (넓이 %, 판정)
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            v = lab[name][str(i)]["v"]
            ai.append((frac(name, d["box"]), "OP" if v in "OP" else v))

print("[Claude 채점 306건] 작은 박스를 크기 기준으로 버렸을 때")
c0 = Counter(v for _, v in ai)
print(f"{'기준(사진 대비)':14} {'남는 박스':>8} {'맞음':>5} {'애매':>5} {'틀림':>5} {'엄격':>7} {'틀림 비율':>8} | {'버려진 틀림':>10} {'버려진 맞음':>10}")
for t in (0, 0.25, 0.5, 1, 2, 3):
    keep = [v for f, v in ai if f >= t]
    c = Counter(keep)
    print(f"  {t:4.2f}% 이상   {len(keep):8} {c['OP']:5} {c['A']:5} {c['X']:5} {c['OP'] / len(keep) * 100:6.1f}% {c['X'] / len(keep) * 100:7.1f}% | "
          f"{c0['X'] - c['X']:6}/{c0['X']:2}   {c0['OP'] - c['OP']:7}/{c0['OP']:3}")

fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
print(f"\n[사용자 판정 {len(fb)}건] 크기별 맞아요 비율")
bins = [(0, 0.5), (0.5, 1), (1, 3), (3, 100)]
print(f"{'크기 구간':12} {'판정':>5} {'맞음(O+P)':>9} {'틀려요':>6} {'정밀도':>7}")
for lo, hi in bins:
    sub = [r for r in fb if lo <= frac(r["photo"], r["box"]) < hi]
    ok = sum(1 for r in sub if r["verdict"] in ("O", "P"))
    print(f"  {lo:g}~{hi:g}%{'':3} {len(sub):5} {ok:9} {len(sub) - ok:6} {ok / len(sub) * 100 if sub else 0:6.1f}%")
