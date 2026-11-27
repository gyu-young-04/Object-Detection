# -*- coding: utf-8 -*-
# 0.20 실험의 새 박스 90건 채점을 저장하고, 점수 기준 0.30 / 0.25 / 0.20의 박스 수와 정밀도를 추정한다.
import json
import math
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
L = {}
for ids, v in [((3, 6, 7, 25, 32, 33, 34, 39, 40, 42, 46, 47, 48, 49, 58, 59, 71, 72, 74, 75, 83), "OP"),
               ((1, 5, 8, 13, 15, 21, 24, 27, 30, 31, 38, 41, 43, 44, 45, 50, 51, 52, 55, 56, 57, 60, 62, 66, 67, 69, 77, 78, 79, 81, 85, 87, 90), "A"),
               ((2, 4, 9, 10, 11, 12, 14, 16, 17, 18, 19, 20, 22, 23, 26, 28, 29, 35, 36, 37, 53, 54, 61, 63, 64, 65, 68, 70, 73, 76, 80, 82, 84, 86, 88, 89), "X")]:
    for i in ids:
        assert i not in L, i
        L[i] = v
assert sorted(L) == list(range(1, 91)), [i for i in range(1, 91) if i not in L]
items = json.load(open(os.path.join(ROOT, "outputs", "t020_review", "index.json"), encoding="utf-8"))
for d in items:
    d["v"] = L[d["id"]]
json.dump({"labeler": "Claude (박스를 잘라 붙인 모음 이미지로 판정, 사용자 검수 전 초안). OP는 이름이 맞음",
           "date": "2026-11-25", "source": "tiny, 해상도 400, 점수 0.20 이상 실행에서 0.30 미만 박스 중 무작위 표본: 0.25~0.30 구간 60건(전체 131건), 0.20~0.25 구간 30건(전체 243건)",
           "boxes": items}, open(os.path.join(ROOT, "docs", "eval", "precision_labels_t020.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


bands = {"0.25-0.30": 131, "0.20-0.25": 243}  # 구간 전체 박스 수
print("[구간별 표본 채점]")
est = {}
for band, total in bands.items():
    sub = [d for d in items if d["band"] == band]
    c = Counter(d["v"] for d in sub)
    n = len(sub)
    lo, hi = wilson(c["OP"], n)
    est[band] = {"n": total, "OP": total * c["OP"] / n, "A": total * c["A"] / n, "X": total * c["X"] / n}
    print(f"  {band} (전체 {total}건 중 표본 {n}건): 맞음 {c['OP']} 애매 {c['A']} 틀림 {c['X']} -> 맞음 {c['OP'] / n * 100:.1f}% (95% 구간 {lo * 100:.0f}~{hi * 100:.0f}%), 틀림 {c['X'] / n * 100:.1f}%")

base = {"n": 306, "OP": 131, "A": 133, "X": 42}  # 점수 0.30 이상 (Claude 채점 306건)
print("\n[점수 기준별 추정] (0.30 미만 구간은 표본에서 추정)")
print(f"{'기준':>6} {'박스':>5} {'맞는 박스':>8} {'엄격 정밀도':>10} {'틀림 비율':>8} {'0.30보다 늘어난 맞는 박스':>20}")
cum = dict(base)
rows = [("0.30", dict(base))]
for band in ["0.25-0.30", "0.20-0.25"]:
    cum = {k: cum[k] + est[band][k] for k in cum}
    rows.append(("0.25" if band == "0.25-0.30" else "0.20", dict(cum)))
for title, r in rows:
    print(f"  {title:>5} {r['n']:5.0f} {r['OP']:8.0f} {r['OP'] / r['n'] * 100:9.1f}% {r['X'] / r['n'] * 100:7.1f}% {r['OP'] - base['OP']:15.0f}건 (+{(r['OP'] - base['OP']) / base['OP'] * 100:.0f}%)")
