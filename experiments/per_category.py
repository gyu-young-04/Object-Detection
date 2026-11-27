# -*- coding: utf-8 -*-
# 세 묶음(대조군 제외)의 채점 결과를 카테고리별로 센다.
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
sets = [("detections_labeled.json", "precision_labels.json"),
        ("detections_labeled_new20.json", "precision_labels_new20.json"),
        ("detections_labeled_set2.json", "precision_labels_set2.json")]
CONTROL = {"web7.webp", "web8.webp"}

rows = []  # (cat, verdict, score)
for dj, lj in sets:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            rows.append((d["category"], lab[name][str(i)]["v"], d["score"]))

print(f"전체 {len(rows)}건")
print(f"{'카테고리':8} {'건수':>4}  O  P  A  X   엄격(O+P)  관대(O+P+A)  X비율")
for cat in ["clothes", "book", "bag", "bottle", "shoes", "box"]:
    sub = [r for r in rows if r[0] == cat]
    if not sub:
        continue
    c = Counter(v for _, v, _ in sub)
    n = len(sub)
    print(f"{cat:8} {n:4}  {c['O']:2} {c['P']:2} {c['A']:2} {c['X']:2}   {(c['O']+c['P'])/n*100:5.1f}%    {(c['O']+c['P']+c['A'])/n*100:5.1f}%     {c['X']/n*100:4.1f}%")
