# -*- coding: utf-8 -*-
# 미끼 박스를 새 카테고리로 평가하기 위해, 기존 채점 박스 306건과 충돌 규칙을 거쳐 살아남은 미끼 박스를 센다.
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import remove_conflicts, remove_duplicates

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
e1 = json.load(open(os.path.join(ROOT, "outputs", "detections_e1.json"), encoding="utf-8"))
e1b = json.load(open(os.path.join(ROOT, "outputs", "detections_e1b.json"), encoding="utf-8"))
DECOYS = ["cushion", "blanket", "comforter", "pillow", "shelf"]


def boxes(name, k):
    for src in (e1, e1b):
        if k in src[name]["boxes"]:
            return src[name]["boxes"][k]


tiny = {}
for dj in ["detections_labeled.json", "detections_labeled_new20.json", "detections_labeled_set2.json"]:
    for name, r in json.load(open(os.path.join(E, dj), encoding="utf-8")).items():
        if name not in CONTROL:
            tiny[name] = r["detections"]

surv = []
for name, ts in tiny.items():
    dets = [{"category": t["category"], "score": t["score"], "box": t["box"], "photo": name, "core": True} for t in ts]
    for k in DECOYS:
        for b in boxes(name, k):
            dets.append({"category": k, "score": b["score"], "box": b["box"], "photo": name, "core": False})
    out = remove_conflicts(dets, 0.7)
    surv += [d for d in out if not d["core"]]
print("살아남은 미끼 박스:", len(surv), dict(Counter(d["category"] for d in surv)))
print("점수 0.50 이상:", sum(1 for d in surv if d["score"] >= 0.5))
print("사진 수:", len(set(d["photo"] for d in surv)))
