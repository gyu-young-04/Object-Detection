# -*- coding: utf-8 -*-
# 카테고리별 점수 기준 선정 규칙 적용 (규칙은 내 방 사진을 돌리기 전에 정해 기록한다).
#   규칙: 점수 t 이상인 박스의 엄격 정밀도(맞음/건수)가 60% 이상이면서 건수가 5건 이상인 가장 낮은 t (후보 0.30~0.70, 0.05 간격)
#        그런 t가 없으면 그 카테고리는 "정식/보조 없음(확인 필요만)"
import json
import math
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
KO = {"clothes": "옷", "book": "책", "bag": "가방", "bottle": "병", "shoes": "신발", "box": "상자"}
GRID = [round(0.30 + 0.05 * i, 2) for i in range(9)]
TARGET, MIN_N = 0.60, 5


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


rows = []
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            rows.append((name, d["category"], d["score"], lab[name][str(i)]["v"] in "OP"))

print(f"규칙: 점수 t 이상 박스의 엄격 정밀도 >= {TARGET:.0%}, 건수 >= {MIN_N}인 가장 낮은 t (후보 {GRID[0]}~{GRID[-1]})\n")
chosen = {}
for cat in CATS:
    print(f"[{KO[cat]}]  t:  건수 맞음 정밀도 (95% 구간)")
    pick = None
    for t in GRID:
        sub = [r for r in rows if r[1] == cat and r[2] >= t]
        if not sub:
            continue
        k = sum(1 for r in sub if r[3])
        lo, hi = wilson(k, len(sub))
        ok = len(sub) >= MIN_N and k / len(sub) >= TARGET
        if ok and pick is None:
            pick = t
        print(f"   {t:.2f}: {len(sub):3} {k:3} {k / len(sub) * 100:5.1f}% ({lo * 100:.0f}~{hi * 100:.0f}%) {'<- 선택' if pick == t and ok and all(not (len([r for r in rows if r[1] == cat and r[2] >= tt]) >= MIN_N and sum(1 for r in rows if r[1] == cat and r[2] >= tt and r[3]) / max(1, len([r for r in rows if r[1] == cat and r[2] >= tt])) >= TARGET) for tt in GRID if tt < t) else ''}")
    chosen[cat] = pick
    print(f"   => {KO[cat]}: {'기준 ' + format(pick, '.2f') if pick else '해당 없음(확인 필요만)'}\n")


def summarize(title, rule):
    sel = [r for r in rows if rule(r)]
    k = sum(1 for r in sel if r[3])
    lo, hi = wilson(k, len(sel)) if sel else (0, 0)
    print(f"{title:34} 박스 {len(sel):3} 맞음 {k:3} 정밀도 {k / len(sel) * 100 if sel else 0:5.1f}% ({lo * 100:.0f}~{hi * 100:.0f}%) 전체 맞음 중 {k / sum(1 for r in rows if r[3]) * 100:.0f}% 확보")


print("[40장 위에서 비교 - 설계용이라 낙관적]")
summarize("전체 0.30 (현재)", lambda r: r[2] >= 0.30)
summarize("전체 0.40", lambda r: r[2] >= 0.40)
summarize("전체 0.50", lambda r: r[2] >= 0.50)
summarize("카테고리별 기준(위 규칙)", lambda r: chosen[r[1]] is not None and r[2] >= chosen[r[1]])
print("\n선택된 기준:", {KO[c]: chosen[c] for c in CATS})
