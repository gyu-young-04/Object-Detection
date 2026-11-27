# -*- coding: utf-8 -*-
# base 새 박스 71건의 채점(OP=이름이 맞음, A=애매, X=틀림)을 저장하고, tiny와 같은 기준으로 최종 비교한다.
import json
import os
import statistics
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou, remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
L = {}
for ids, v in [
    ((1, 3, 6, 8, 9, 24, 26, 27, 29, 41, 43, 44, 46, 47, 49, 52, 54, 55, 56, 57, 65, 69, 70, 71), "OP"),
    ((2, 5, 10, 11, 12, 13, 14, 17, 20, 21, 22, 23, 38, 40, 42, 51, 53, 58, 61, 67), "A"),
    ((4, 7, 15, 16, 18, 19, 25, 28, 30, 31, 32, 33, 34, 35, 36, 37, 39, 45, 48, 50, 59, 60, 62, 63, 64, 66, 68), "X"),
]:
    for i in ids:
        assert i not in L, i
        L[i] = v
assert sorted(L) == list(range(1, 72)), [i for i in range(1, 72) if i not in L]

items = json.load(open(os.path.join(ROOT, "outputs", "base_review", "index.json"), encoding="utf-8"))
for d in items:
    d["v"] = L[d["id"]]
json.dump({"labeler": "Claude (박스를 잘라 붙인 모음 이미지로 판정, 사용자 검수 전 초안). OP는 이름이 맞음(맞아요+이미 제자리 구분 안 함)",
           "date": "2026-11-23", "source": "Grounding DINO base(해상도 400, 카테고리 6개, 충돌 규칙 후)에서만 나온 새 박스 71건 (tiny 채점 박스와 위치가 안 맞는 것)",
           "boxes": items}, open(os.path.join(E, "precision_labels_base_new71.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("새 박스 71건:", dict(Counter(L.values())))
print("새 박스 카테고리별 (OP/A/X):")
for c in ["clothes", "book", "bag", "bottle", "shoes", "box"]:
    cc = Counter(d["v"] for d in items if d["category"] == c)
    print(f"  {c:8} OP {cc['OP']:2}  A {cc['A']:2}  X {cc['X']:2}")

# ---- tiny 채점 데이터와 base 비교 ----
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
CONTROL = {"web7.webp", "web8.webp"}
base = json.load(open(os.path.join(ROOT, "outputs", "detections_base_400.json"), encoding="utf-8"))
tiny = {}
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        tiny[name] = [{"category": d["category"], "score": d["score"], "box": d["box"], "v": lab[name][str(i)]["v"]} for i, d in enumerate(r["detections"], 1)]

base_boxes = []  # (category, 최종 판정 OP/A/X)
new_by_key = {(d["photo"], tuple(d["box"]), d["category"]): d["v"] for d in items}
for name, r in base.items():
    dets = [{"category": c, "score": b["score"], "box": b["box"]} for c in CATS for b in r["boxes"][c]]
    for b in remove_conflicts(dets, 0.7):
        v = None
        for t in tiny.get(name, []):
            if t["category"] == b["category"] and iou(t["box"], b["box"]) > 0.5:
                v = "OP" if t["v"] in "OP" else t["v"]
                break
        if v is None:
            v = new_by_key[(name, tuple(b["box"]), b["category"])]
        base_boxes.append((b["category"], v, b["score"]))

def line(title, vs):
    c = Counter(vs)
    n = len(vs)
    print(f"{title:34} {n:3}건  맞음(OP) {c['OP']:3}  애매 {c['A']:3}  틀림 {c['X']:3}  엄격 {c['OP'] / n * 100:5.1f}%  관대 {(c['OP'] + c['A']) / n * 100:5.1f}%  틀림비율 {c['X'] / n * 100:4.1f}%")

print("\n===== 최종 비교 (같은 40장, 같은 채점자 기준) =====")
tiny_all = [("OP" if t["v"] in "OP" else t["v"]) for ts in tiny.values() for t in ts]
line("tiny (현재, 점수 0.30 이상)", tiny_all)
tiny37 = [("OP" if t["v"] in "OP" else t["v"]) for ts in tiny.values() for t in ts if t["score"] >= 0.37]
line("tiny + 점수 0.37 이상", tiny37)
line("base (점수 0.30 이상)", [v for _, v, _ in base_boxes])
base37 = [v for _, v, s in base_boxes if s >= 0.37]
line("base + 점수 0.37 이상", base37)

print("\n카테고리별 엄격 정밀도 (맞음/전체): tiny -> base")
for c in CATS:
    tv = [("OP" if t["v"] in "OP" else t["v"]) for ts in tiny.values() for t in ts if t["category"] == c]
    bv = [v for cat, v, _ in base_boxes if cat == c]
    tc, bc = Counter(tv), Counter(bv)
    print(f"  {c:8} tiny {tc['OP']:3}/{len(tv):3} ({tc['OP'] / len(tv) * 100:5.1f}%, 틀림 {tc['X'] / len(tv) * 100:4.1f}%)  ->  base {bc['OP']:3}/{len(bv):3} ({bc['OP'] / len(bv) * 100:5.1f}%, 틀림 {bc['X'] / len(bv) * 100:4.1f}%)")

tp = sum(1 for v in tiny_all if v == "OP")
bp = sum(1 for _, v, _ in base_boxes if v == "OP")
print(f"\n찾아낸 맞는 박스 수: tiny {tp}건, base {bp}건 (base 새 박스 중 맞음 {sum(1 for v in L.values() if v == 'OP')}건 포함)")

print("\n===== 점수 기준을 올릴 때: 맞는 박스 수 대비 정밀도 곡선 =====")
tiny_sv = [(t["score"], "OP" if t["v"] in "OP" else t["v"]) for ts in tiny.values() for t in ts]
base_sv = [(s, v) for _, v, s in base_boxes]
print(f"{'기준':>6} | {'tiny 남는박스':>10} {'맞는박스':>7} {'정밀도':>7} {'틀림':>5} | {'base 남는박스':>10} {'맞는박스':>7} {'정밀도':>7} {'틀림':>5}")
for thr in [0.30, 0.33, 0.35, 0.37, 0.40, 0.42, 0.45, 0.50]:
    row = []
    for sv in (tiny_sv, base_sv):
        k = [v for s, v in sv if s >= thr]
        c = Counter(k)
        row.append((len(k), c["OP"], c["OP"] / len(k) * 100 if k else 0, c["X"]))
    print(f"  {thr:.2f} | {row[0][0]:10} {row[0][1]:7} {row[0][2]:6.1f}% {row[0][3]:5} | {row[1][0]:10} {row[1][1]:7} {row[1][2]:6.1f}% {row[1][3]:5}")
