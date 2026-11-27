# -*- coding: utf-8 -*-
# 사용자 판정 53건을 base가 카테고리별로 어떻게 다시 찾는지 센다 (맞는 건 남기고 틀린 건 덜 잡는지).
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou, remove_conflicts

CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
base = json.load(open(os.path.join(ROOT, "outputs", "detections_base_400.json"), encoding="utf-8"))
fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
bd = {}
for name, r in base.items():
    dets = [{"category": c, "score": b["score"], "box": b["box"]} for c in CATS for b in r["boxes"][c]]
    bd[name] = remove_conflicts(dets, 0.7)

print("사용자 판정 → base가 같은 박스를 다시 찾았나 (같은 카테고리, 위치 겹침)")
print(f"{'카테고리':8} {'맞아요(O)':>10} {'이미제자리(P)':>13} {'틀려요(X)':>10}")
for cat in CATS + ["전체"]:
    sub = [r for r in fb if cat == "전체" or r["category"] == cat]
    if not sub:
        continue
    out = []
    for v in "OPX":
        vs = [r for r in sub if r["verdict"] == v]
        f = sum(1 for r in vs if any(b["category"] == r["category"] and iou(b["box"], r["box"]) > 0.5 for b in bd.get(r["photo"], [])))
        out.append(f"{f:2}/{len(vs):2}")
    print(f"{cat:8} {out[0]:>10} {out[1]:>13} {out[2]:>10}")
