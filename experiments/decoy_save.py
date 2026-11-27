# -*- coding: utf-8 -*-
# 미끼 박스 117건(충돌 규칙을 거쳐 살아남은 것)의 채점을 저장하고, 미끼를 새 카테고리로 봤을 때의 정밀도를 계산한다.
# 판정 기준: cushion/pillow = 베개·쿠션이 맞음, blanket/comforter = 이불·담요·침구 덮개가 맞음, shelf = 선반·책장·수납장·서랍장·장롱 등 수납 가구가 맞음.
import json
import math
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
OP = {1, 4, 22, 30, 36, 42, 43, 44, 49, 52, 56, 57, 58, 59, 60, 61, 62, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 75, 77, 80, 81, 84, 86, 87, 89, 90, 92, 94, 95, 96, 97, 101, 102, 104, 106, 107, 108, 113, 114, 117}
A = {5, 7, 11, 12, 18, 23, 24, 26, 27, 31, 34, 35, 38, 40, 41, 51, 54, 63, 74, 76, 79, 83, 85, 91, 98, 99, 103, 105, 109, 110, 111, 112, 115, 116}
X = {2, 3, 6, 8, 9, 10, 13, 14, 15, 16, 17, 19, 20, 21, 25, 28, 29, 32, 33, 37, 39, 45, 46, 47, 48, 50, 53, 55, 78, 82, 88, 93, 100}
assert OP | A | X == set(range(1, 118)) and not (OP & A) and not (OP & X) and not (A & X)
items = json.load(open(os.path.join(ROOT, "outputs", "decoy_review", "index.json"), encoding="utf-8"))
for d in items:
    d["v"] = "OP" if d["id"] in OP else ("A" if d["id"] in A else "X")
json.dump({"labeler": "Claude (박스를 잘라 붙인 모음 이미지로 판정, 사용자 검수 전 초안). OP는 이름이 맞음",
           "date": "2026-11-27", "source": "미끼 후보(cushion, blanket, comforter, pillow, shelf)를 기존 채점 박스 306건과 충돌 규칙(겹침 0.7, 점수 높은 쪽)에 함께 넣어 살아남은 미끼 박스 117건. tiny, 해상도 400, 점수 0.30 이상",
           "criteria": {"cushion/pillow": "베개·쿠션이 맞음", "blanket/comforter": "이불·담요·침구 덮개가 맞음(침대 위 덩이 포함)", "shelf": "선반·책장·수납장·서랍장·장롱 등 수납 가구가 맞음(주방 수납장 포함)",
                        "A": "일부만 보이거나 비슷한 다른 물건(소파, 매트리스, 러그, 얇은 조각 등)", "X": "다른 물건(옷, 가방, 책상, 냉장고 등)"},
           "boxes": items}, open(os.path.join(ROOT, "docs", "eval", "precision_labels_decoys.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


print(f"{'미끼':10} {'건수':>4} {'맞음':>4} {'애매':>4} {'틀림':>4} {'엄격 정밀도(95%)':>18} {'맞음+애매':>9}")
groups = [("cushion", ["cushion"]), ("pillow", ["pillow"]), ("blanket", ["blanket"]), ("comforter", ["comforter"]), ("shelf", ["shelf"]),
          ("쿠션류(cushion+pillow)", ["cushion", "pillow"]), ("침구류(blanket+comforter)", ["blanket", "comforter"]), ("전체", ["cushion", "pillow", "blanket", "comforter", "shelf"])]
for title, cats in groups:
    sub = [d for d in items if d["category"] in cats]
    c = Counter(d["v"] for d in sub)
    lo, hi = wilson(c["OP"], len(sub))
    print(f"{title:22} {len(sub):4} {c['OP']:4} {c['A']:4} {c['X']:4} {c['OP'] / len(sub) * 100:6.1f}% ({lo * 100:.0f}~{hi * 100:.0f}%) {(c['OP'] + c['A']) / len(sub) * 100:8.1f}%")

print("\n[점수 구간별 - 전체 미끼]")
for lo_s, hi_s in [(0.30, 0.40), (0.40, 0.50), (0.50, 1.01)]:
    sub = [d for d in items if lo_s <= d["score"] < hi_s]
    c = Counter(d["v"] for d in sub)
    print(f"  {lo_s:.2f}~{min(hi_s, 1):.2f}: {len(sub):3}건 맞음 {c['OP']:2} 애매 {c['A']:2} 틀림 {c['X']:2} -> 맞음 {c['OP'] / len(sub) * 100:.0f}%")
print("\n[점수 구간별 - 카테고리별 (맞음/건수)]")
for cat in ["cushion", "pillow", "blanket", "comforter", "shelf"]:
    line = f"  {cat:10}"
    for lo_s, hi_s in [(0.30, 0.40), (0.40, 0.50), (0.50, 1.01)]:
        sub = [d for d in items if d["category"] == cat and lo_s <= d["score"] < hi_s]
        line += f" {sum(1 for d in sub if d['v'] == 'OP'):2}/{len(sub):2}"
    print(line)
