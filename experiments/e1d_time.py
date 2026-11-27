# -*- coding: utf-8 -*-
# E1d 시간: 기준 질의 1번(clothes)과 미끼 묶음(furn4, furn6) 질의의 시간(중앙값, 최소, 최대).
import json
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
d = json.load(open(os.path.join(ROOT, "outputs", "detections_e1d.json"), encoding="utf-8"))
for k in ["ref_clothes", "furn4", "furn6"]:
    v = [r["seconds"][k] for r in d.values()]
    print(k, "중앙값", round(statistics.median(v), 2), "최소", min(v), "최대", max(v))
