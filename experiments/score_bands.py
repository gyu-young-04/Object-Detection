# -*- coding: utf-8 -*-
# 점수 구간별 표: 점수가 높을수록 정말 맞는 박스가 많은가? (Claude 채점 306건 + 사용자 판정 + 0.20 실험 표본)
import json
import math
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
KO = {"clothes": "옷", "book": "책", "bag": "가방", "bottle": "병", "shoes": "신발", "box": "상자"}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0, 0
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


rows = []  # Claude 채점: photo, category, score, verdict(OP/A/X), note
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            l = lab[name][str(i)]
            rows.append({"photo": name, "cat": d["category"], "score": d["score"], "v": "OP" if l["v"] in "OP" else l["v"], "note": l.get("note", "")})
print("Claude 채점", len(rows), "건")

bins = [(0.30, 0.35), (0.35, 0.40), (0.40, 0.50), (0.50, 1.01)]
print("\n[점수 구간별 - Claude 채점, 점수 0.30 이상 전체]")
print(f"{'구간':>10} {'건수':>5} {'맞음':>5} {'애매':>5} {'틀림':>5} {'엄격정밀도':>9} {'95%구간':>10} {'틀림비율':>8}")
for lo, hi in bins:
    sub = [r for r in rows if lo <= r["score"] < hi]
    c = Counter(r["v"] for r in sub)
    a, b = wilson(c["OP"], len(sub))
    print(f"{lo:.2f}-{min(hi, 1):.2f} {len(sub):5} {c['OP']:5} {c['A']:5} {c['X']:5} {c['OP'] / len(sub) * 100:8.1f}% {a * 100:4.0f}~{b * 100:3.0f}% {c['X'] / len(sub) * 100:7.1f}%")

# 0.30 미만은 0.20 실험 표본(사진 단위 표본이 아니라 구간 무작위 표본)
t = json.load(open(os.path.join(E, "precision_labels_t020.json"), encoding="utf-8"))["boxes"]
for band, total in [("0.25-0.30", 131), ("0.20-0.25", 243)]:
    sub = [d for d in t if d["band"] == band]
    c = Counter(d["v"] for d in sub)
    a, b = wilson(c["OP"], len(sub))
    print(f"{band:>10} 표본{len(sub):3}/전체{total:3}  맞음 {c['OP']:3} 애매 {c['A']:3} 틀림 {c['X']:3} -> {c['OP'] / len(sub) * 100:5.1f}% ({a * 100:.0f}~{b * 100:.0f}%) 틀림 {c['X'] / len(sub) * 100:.1f}%")

print("\n[카테고리 x 점수 구간 엄격 정밀도(맞음/건수), 0.30 이상]")
cut = [(0.30, 0.37), (0.37, 0.45), (0.45, 1.01)]
print(f"{'':8}" + "".join(f"{lo:.2f}-{min(hi, 1):.2f}".rjust(14) for lo, hi in cut) + "        전체")
for cat in CATS:
    line = f"{KO[cat]:6}"
    for lo, hi in cut:
        sub = [r for r in rows if r["cat"] == cat and lo <= r["score"] < hi]
        k = sum(1 for r in sub if r["v"] == "OP")
        line += f"{k:4}/{len(sub):3}={k / len(sub) * 100 if sub else float('nan'):5.0f}% "
    sub = [r for r in rows if r["cat"] == cat]
    line += f"  {sum(1 for r in sub if r['v'] == 'OP')}/{len(sub)}"
    print(line)

# 사용자 판정 141건을 점수 구간별로 (box 좌표로 점수를 찾는다)
fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
print("\n[사용자 판정]", len(fb), "건, 점수가 기록된 것:", sum(1 for r in fb if "score" in r))
by = defaultdict(Counter)
for r in fb:
    s = r["score"]
    key = next((f"{lo:.2f}-{min(hi, 1):.2f}" for lo, hi in bins if lo <= s < hi), "0.30미만")
    by[key][r["verdict"]] += 1
for k in sorted(by):
    c = by[k]
    judged = c["O"] + c["P"] + c["X"]
    print(f"  {k}: 맞음(O+P) {c['O'] + c['P']} 틀림 {c['X']} 확인불가 {c['U']} -> 판정된 것 중 맞음 {(c['O'] + c['P']) / judged * 100 if judged else float('nan'):.0f}%")
