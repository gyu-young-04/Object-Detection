# -*- coding: utf-8 -*-
# 사용자가 판정한 사진에서, 화면에 보인 박스 중 판정하지 않고 건너뛴 박스가 몇 건인지 센다.
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou, remove_containers

fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
res = json.load(open(os.path.join(ROOT, "outputs", "detections_new20_400_nocontain.json"), encoding="utf-8"))
photos = sorted(set(r["photo"] for r in fb))
print("판정한 사진", len(photos), "장")
tot_shown = tot_judged = 0
rows = []
for p in photos:
    shown = remove_containers(res[p]["detections"])
    judged = [d for d in shown if any(iou(d["box"], r["box"]) > 0.99 and d["category"] == r["category"] for r in fb if r["photo"] == p)]
    # 큰 박스를 걷어내기 전에 판정한 기록이 있을 수 있어서, 화면 기준 외 판정도 따로 센다
    extra = sum(1 for r in fb if r["photo"] == p) - len(judged)
    rows.append((p, len(shown), len(judged), extra))
    tot_shown += len(shown)
    tot_judged += len(judged)
for p, s, j, e in rows:
    print(f"  {p}: 화면 박스 {s}건, 판정 {j}건, 건너뜀 {s - j}건" + (f" (큰 박스 제거 전에 판정한 기록 {e}건 별도)" if e else ""))
print(f"합계: 화면 박스 {tot_shown}건 중 판정 {tot_judged}건, 건너뜀 {tot_shown - tot_judged}건")
sk = Counter()
for p in photos:
    for d in remove_containers(res[p]["detections"]):
        if not any(iou(d["box"], r["box"]) > 0.99 and d["category"] == r["category"] for r in fb if r["photo"] == p):
            sk[d["category"]] += 1
print("건너뛴 박스의 카테고리:", dict(sk))
