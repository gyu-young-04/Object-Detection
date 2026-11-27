# -*- coding: utf-8 -*-
# E1 정리 대상 확장 후보(컵·그릇·유리병) 생존 박스 45건의 채점을 저장하고 정밀도를 계산한다. (OP=이름이 맞음, A=애매, X=틀림)
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
L = {}
for ids, v in [((2, 5, 12, 13, 21, 24, 27), "OP"),
               ((1, 4, 8, 9, 11, 18, 19, 23, 25, 28, 29, 31, 39, 44), "A"),
               ((3, 6, 7, 10, 14, 15, 16, 17, 20, 22, 26, 30, 32, 33, 34, 35, 36, 37, 38, 40, 41, 42, 43, 45), "X")]:
    for i in ids:
        assert i not in L
        L[i] = v
assert sorted(L) == list(range(1, 46))
items = json.load(open(os.path.join(ROOT, "outputs", "e1_review", "index.json"), encoding="utf-8"))
for d in items:
    d["v"] = L[d["id"]]
json.dump({"labeler": "Claude (박스를 잘라 붙인 모음 이미지로 판정, 사용자 검수 전 초안). OP는 이름이 맞음",
           "date": "2026-11-25", "source": "E1 정리 대상 확장 후보 cup/bowl/glass jar 중 기존 6개 카테고리와의 충돌 규칙 후 살아남은 박스 45건 (tiny, 해상도 400, 점수 0.30 이상)",
           "boxes": items}, open(os.path.join(ROOT, "docs", "eval", "precision_labels_e1_targets.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
KO = {"cup": "컵", "bowl": "그릇", "glass jar": "유리병"}
print(f"{'후보':8} {'박스':>4} {'맞음':>4} {'애매':>4} {'틀림':>4} {'엄격':>7} {'관대':>7}")
for cat in ["cup", "bowl", "glass jar", None]:
    sub = [d for d in items if cat is None or d["category"] == cat]
    c = Counter(d["v"] for d in sub)
    n = len(sub)
    print(f"{KO.get(cat, '전체'):8} {n:4} {c['OP']:4} {c['A']:4} {c['X']:4} {c['OP'] / n * 100:6.1f}% {(c['OP'] + c['A']) / n * 100:6.1f}%")
print("\n점수 기준을 올리면 (전체 45건)")
for thr in (0.30, 0.40, 0.45, 0.50):
    sub = [d for d in items if d["score"] >= thr]
    c = Counter(d["v"] for d in sub)
    print(f"  >= {thr:.2f}: {len(sub):2}건, 맞음 {c['OP']}, 애매 {c['A']}, 틀림 {c['X']}" + (f", 엄격 {c['OP'] / len(sub) * 100:.0f}%" if sub else ""))
