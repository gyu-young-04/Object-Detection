# -*- coding: utf-8 -*-
# 카테고리를 묻는 순서를 바꿔도 최종 박스가 같은가? (모델 없이 저장된 결과로 확인. 점수 0.30 이상, 40장)
import itertools
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import remove_conflicts, remove_containers, remove_duplicates

CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
t = json.load(open(os.path.join(ROOT, "outputs", "detections_t020.json"), encoding="utf-8"))


def final(name, order):
    dets = []
    for c in order:
        found = [{"category": c, "score": b["score"], "box": b["box"]} for b in t[name]["boxes"][c] if b["score"] >= 0.30]
        dets += remove_containers(remove_duplicates(found), 0.8)
    out = remove_conflicts(dets, 0.7)
    return sorted((d["category"], d["score"], tuple(d["box"])) for d in out)


random.seed(1)
orders = [CATS, ["book", "shoes", "bag", "bottle", "box", "clothes"], list(reversed(CATS))] + [random.sample(CATS, 6) for _ in range(20)]
same_all = 0
diffs = []
for name in t:
    ref = final(name, orders[0])
    ok = all(final(name, o) == ref for o in orders[1:])
    same_all += ok
    if not ok:
        diffs.append(name)
print(f"사진 {len(t)}장, 순서 {len(orders)}가지: 모든 순서에서 같은 결과인 사진 {same_all}장")
for name in diffs:
    ref = final(name, orders[0])
    for o in orders[1:]:
        r = final(name, o)
        if r != ref:
            print("  다른 사진:", name, "순서", o, "박스 수", len(ref), "->", len(r), "| 차이:", set(ref) ^ set(r))
            break
