# -*- coding: utf-8 -*-
# 화면 순서(이름순)의 26번·30번 사진이 무엇이고, 박스 수와 통계에 얼마나 영향을 주는지 본다.
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
import app as appmod

res = appmod.app.test_client().get("/api/results").get_json()
names = sorted(res)  # 화면은 이름순으로 보여준다
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
judged = Counter(r["photo"] for r in fb)

print(f"{'번호':>3} {'사진':28} {'박스':>4} " + " ".join(f"{c[:5]:>5}" for c in CATS) + "  판정함")
for i, n in enumerate(names, 1):
    c = Counter(d["category"] for d in res[n]["detections"])
    mark = "  <-- " if len(res[n]["detections"]) >= 15 else ""
    print(f"{i:3} {n:28} {len(res[n]['detections']):4} " + " ".join(f"{c[k]:5}" for k in CATS) + f"  {judged[n]:3}{mark}")

tot = sum(len(res[n]["detections"]) for n in names)
big = sorted(names, key=lambda n: -len(res[n]["detections"]))[:3]
print(f"\n전체 박스 {tot}건 중 상위 3장: " + ", ".join(f"{n}({len(res[n]['detections'])}건)" for n in big)
      + f" = {sum(len(res[n]['detections']) for n in big) / tot * 100:.0f}%")
box_tot = sum(1 for n in names for d in res[n]["detections"] if d["category"] == "box")
print("상자 박스", box_tot, "건 중 상위 사진 비중:")
for n in sorted(names, key=lambda n: -sum(1 for d in res[n]["detections"] if d["category"] == "box"))[:4]:
    k = sum(1 for d in res[n]["detections"] if d["category"] == "box")
    print(f"  {n}: {k}건 ({k / box_tot * 100:.0f}%)")
