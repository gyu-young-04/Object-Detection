# -*- coding: utf-8 -*-
# 박스가 몰린 사진(JUWY3uzN_Is, bSoV4nbrkzA)이 통계를 얼마나 끌고 가는지: 있을 때/없을 때, 사진 단위 평균과 비교.
import json
import os
import statistics
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
HEAVY = {"unsplash_JUWY3uzN_Is.jpg", "unsplash_bSoV4nbrkzA.jpg"}
CONTROL = {"web7.webp", "web8.webp"}
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]

rows = []  # (photo, category, verdict) - Claude 채점 306건
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            rows.append((name, d["category"], "OP" if lab[name][str(i)]["v"] in "OP" else lab[name][str(i)]["v"]))

def micro(sub):
    return sum(1 for _, _, v in sub if v == "OP") / len(sub) * 100 if sub else float("nan")

def macro(sub):
    by = defaultdict(list)
    for p, _, v in sub:
        by[p].append(v == "OP")
    return statistics.mean(sum(x) / len(x) for x in by.values()) * 100 if by else float("nan"), len(by)

print("[Claude 채점 306건] 박스 몰린 2장의 영향")
print(f"{'':10} {'전체(박스 평균)':>16} {'2장 제외':>10} {'사진 단위 평균':>16}")
for cat in CATS + ["전체"]:
    sub = [r for r in rows if cat == "전체" or r[1] == cat]
    sub2 = [r for r in sub if r[0] not in HEAVY]
    mac, n = macro(sub)
    print(f"{cat:10} {micro(sub):13.1f}% ({len(sub):3}) {micro(sub2):7.1f}% ({len(sub2):3}) {mac:11.1f}% ({n}장)")
box = [r for r in rows if r[1] == "box"]
print(f"\n상자 {len(box)}건 중 2장 비중: {sum(1 for r in box if r[0] in HEAVY)}건 ({sum(1 for r in box if r[0] in HEAVY) / len(box) * 100:.0f}%)")

fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
print(f"\n[사용자 판정] 지금 {len(fb)}건, {len(set(r['photo'] for r in fb))}장")
cc = Counter(r["category"] for r in fb)
heavy_cc = Counter(r["category"] for r in fb if r["photo"] in HEAVY)
for cat in CATS:
    if cc[cat]:
        print(f"  {cat:8} {cc[cat]:3}건 (그중 몰린 2장에서 {heavy_cc[cat]}건)")
