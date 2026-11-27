# -*- coding: utf-8 -*-
# 사용자 판정(data/feedback.json)을 같은 박스의 Claude 채점과 비교한다.
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou

fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
E = os.path.join(ROOT, "docs", "eval")
sets = [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
        ("detections_labeled_set2.json", "precision_labels_set2.json")]
ai = {}  # photo -> [(box, category, score, verdict, note)]
for dj, lj in sets:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        for i, d in enumerate(r["detections"], 1):
            x = lab[name][str(i)]
            ai.setdefault(name, []).append((d["box"], d["category"], d["score"], x["v"], x.get("note", ""), i))

print(f"사용자 판정 {len(fb)}건, 사진 {len(set(r['photo'] for r in fb))}장")
print("판정 분포:", dict(Counter(r["verdict"] for r in fb)))
print("카테고리별:")
for cat in ["clothes", "book", "bag", "bottle", "shoes", "box"]:
    sub = [r for r in fb if r["category"] == cat]
    if sub:
        c = Counter(r["verdict"] for r in sub)
        print(f"  {cat:8} {len(sub):3}건  맞아요 {c['O']:2}  이미제자리 {c['P']:2}  틀려요 {c['X']:2}")

pairs = []
unmatched = 0
for r in fb:
    m = None
    for box, cat, score, v, note, i in ai.get(r["photo"], []):
        if iou(box, r["box"]) > 0.9 and cat == r["category"]:
            m = (v, note, i)
            break
    if m is None:
        unmatched += 1
    else:
        pairs.append((r, m))
print(f"\nClaude 채점과 짝이 맞은 박스 {len(pairs)}건 (짝 없음 {unmatched}건)")

tbl = Counter((r["verdict"], m[0]) for r, m in pairs)
print("\n(사용자 판정 → Claude 채점) 건수")
for u in "OPX":
    row = {a: tbl[(u, a)] for a in "OPAX"}
    print(f"  사용자 {u}: Claude O {row['O']:2}  P {row['P']:2}  A {row['A']:2}  X {row['X']:2}")

# 같은 뜻으로 보는 기준: Claude의 O/P = 사용자 O/P 계열, X = X, A는 비교 제외
agree = sum(1 for r, m in pairs if m[0] != "A" and ((r["verdict"] in "OP") == (m[0] in "OP")))
comp = sum(1 for r, m in pairs if m[0] != "A")
print(f"\n애매(A) 제외 비교: {comp}건 중 '맞음 계열 vs 틀림' 일치 {agree}건 ({agree / comp * 100 if comp else 0:.0f}%)")
exact = sum(1 for r, m in pairs if r["verdict"] == m[0])
print(f"O/P/X까지 완전 일치: {exact}건 / {len(pairs)}건")
print("\n판정이 갈린 박스 (애매 제외):")
for r, m in pairs:
    if m[0] != "A" and ((r["verdict"] in "OP") != (m[0] in "OP")):
        print(f"  {r['photo']} #{m[2]} {r['category']} 점수 {r['score']:.2f} | 사용자 {r['verdict']} / Claude {m[0]} ({m[1]})")
print("\nP/O 구분이 갈린 박스:")
for r, m in pairs:
    if m[0] in "OP" and r["verdict"] in "OP" and r["verdict"] != m[0]:
        print(f"  {r['photo']} #{m[2]} {r['category']} | 사용자 {r['verdict']} / Claude {m[0]} ({m[1]})")
