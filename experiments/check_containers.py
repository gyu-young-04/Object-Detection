# -*- coding: utf-8 -*-
# app.py의 /api/results가 큰 박스를 걷어냈는지 확인한다. (서버 없이 test_client, 판정 파일은 건드리지 않는다)
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
import app as appmod
from merge import box_area, inside_ratio

raw = {}
for _p in appmod.RESULTS_PATHS:
    raw.update(__import__("json").load(open(_p, encoding="utf-8")))
new = appmod.app.test_client().get("/api/results").get_json()

def nested_pairs(dets):
    n = 0
    for big in dets:
        for small in dets:
            if big is not small and big["category"] == small["category"] and box_area(big["box"]) > box_area(small["box"]) \
                    and inside_ratio(small["box"], big["box"]) >= 0.8:
                n += 1
    return n

tb = ta = pb = pa = 0
for name in raw:
    b, a = raw[name]["detections"], new[name]["detections"]
    tb += len(b); ta += len(a); pb += nested_pairs(b); pa += nested_pairs(a)
print(f"사진 {len(raw)}장  박스 {tb} -> {ta}건 ({tb - ta}건 제거)")
print(f"포개진 쌍 {pb} -> {pa}쌍")
changed = [(n, len(raw[n]['detections']), len(new[n]['detections'])) for n in raw if len(raw[n]['detections']) != len(new[n]['detections'])]
print("박스 수가 바뀐 사진:", len(changed), "장")
for n, b, a in changed[:6]:
    print(f"  {n}: {b} -> {a}")
# 남은 박스는 원래 박스 그대로인지 (좌표가 안 바뀌었는지)
ok = all(any(x["box"] == y["box"] and x["category"] == y["category"] for y in raw[n]["detections"]) for n in new for x in new[n]["detections"])
print("남은 박스가 모두 원래 박스와 같음:", ok)
