# -*- coding: utf-8 -*-
# 박스가 많은 사진에서 판정한 박스와 안 한 박스의 점수·크기를 비교한다. (높은 점수만 골랐다면 정밀도가 부풀 수 있음)
import json
import os
import statistics
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
import app as appmod
import store

res = appmod.app.test_client().get("/api/results").get_json()
fb = store.load_feedback()
judged = {(r["photo"], tuple(r["box"]), r["category"]): r["verdict"] for r in fb}

print("그룹: (사진, 카테고리)에서 박스가 6건 이상이고 일부만 판정한 경우")
for n, v in res.items():
    by_cat = defaultdict(list)
    for d in v["detections"]:
        by_cat[d["category"]].append(d)
    for c, ds in by_cat.items():
        if len(ds) < 6:
            continue
        j = [d for d in ds if (n, tuple(d["box"]), c) in judged]
        u = [d for d in ds if (n, tuple(d["box"]), c) not in judged]
        if not j or not u:
            continue
        area = lambda d: (d["box"][2] - d["box"][0]) * (d["box"][3] - d["box"][1])
        vc = [judged[(n, tuple(d["box"]), c)] for d in j]
        print(f"  {n} / {c}: 전체 {len(ds)}건, 판정 {len(j)}건 (맞음 {sum(x in 'OP' for x in vc)}, 틀림 {sum(x == 'X' for x in vc)})")
        print(f"      점수 평균  판정한 것 {statistics.mean(d['score'] for d in j):.2f} / 안 한 것 {statistics.mean(d['score'] for d in u):.2f}")
        print(f"      박스 크기(넓이 중앙값) 판정한 것 {statistics.median(area(d) for d in j):,.0f} / 안 한 것 {statistics.median(area(d) for d in u):,.0f}")
