# -*- coding: utf-8 -*-
# E4: base 결과를 tiny의 채점된 박스(306건)와 위치로 맞춰 비교한다.
import json
import os
import statistics
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou, remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
CONTROL = {"web7.webp", "web8.webp"}

base = json.load(open(os.path.join(ROOT, "outputs", "detections_base_400.json"), encoding="utf-8"))
tiny = {}  # photo -> [{category, score, box, v}]
tiny_secs = []
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        tiny[name] = [{"category": d["category"], "score": d["score"], "box": d["box"], "v": lab[name][str(i)]["v"]}
                      for i, d in enumerate(r["detections"], 1)]
        if "total_seconds" in r and r["total_seconds"] < 60:
            tiny_secs.append(r["total_seconds"])

# base 박스에 파이프라인과 같은 충돌 규칙(카테고리가 다른데 같은 자리면 점수 높은 쪽만)을 적용
base_dets = {}
for name, r in base.items():
    dets = [{"category": c, "score": b["score"], "box": b["box"]} for c in CATS for b in r["boxes"][c]]
    base_dets[name] = remove_conflicts(dets, 0.7)

n_tiny = sum(len(v) for v in tiny.values())
n_base = sum(len(v) for v in base_dets.values())
print(f"사진 {len(base)}장 | tiny 박스 {n_tiny}건 | base 박스(충돌 규칙 후) {n_base}건")
secs = [r["seconds"] for r in base.values()]
print(f"base 사진당 시간: 중앙값 {statistics.median(secs):.0f}초, 평균 {statistics.mean(secs):.0f}초 (최대 {max(secs):.0f}초) / tiny 기록(60초 미만) 중앙값 {statistics.median(tiny_secs):.0f}초")

print("\n[카테고리별 박스 수] tiny -> base")
for c in CATS:
    t = sum(1 for v in tiny.values() for d in v if d["category"] == c)
    b = sum(1 for v in base_dets.values() for d in v if d["category"] == c)
    print(f"  {c:8} {t:3} -> {b:3}")

# tiny의 채점 박스를 base가 다시 찾는지 (같은 카테고리, 위치 IoU > 0.5)
found = Counter()
tot = Counter()
matched_base = {name: set() for name in base_dets}
for name, ts in tiny.items():
    for t in ts:
        tot[t["v"]] += 1
        for j, b in enumerate(base_dets.get(name, [])):
            if b["category"] == t["category"] and iou(b["box"], t["box"]) > 0.5:
                found[t["v"]] += 1
                matched_base[name].add(j)
                break
print("\n[tiny가 판정받은 박스를 base가 다시 찾은 비율]")
for v, lab in [("O", "맞아요류 O"), ("P", "이미 제자리 P"), ("A", "애매 A"), ("X", "틀림 X")]:
    print(f"  {lab:12} {found[v]:3}/{tot[v]:3} ({found[v] / tot[v] * 100:5.1f}%)")
op = found["O"] + found["P"]
optot = tot["O"] + tot["P"]
print(f"  맞는 박스(O+P) 유지 {op}/{optot} ({op / optot * 100:.1f}%), 틀린 박스(X) 제거율 {(tot['X'] - found['X']) / tot['X'] * 100:.1f}%")

# base에서만 나온 박스 (tiny 채점 박스와 안 맞는 것) = 아직 채점 안 된 새 박스
new = [(name, j, b) for name, bs in base_dets.items() for j, b in enumerate(bs) if j not in matched_base[name]]
print(f"\nbase에서만 나온 새 박스(미채점): {len(new)}건 / base 전체 {n_base}건")
print("  카테고리별:", dict(Counter(b['category'] for _, _, b in new)))
print("  점수 평균: 새 박스", round(statistics.mean(b['score'] for _, _, b in new), 2), "/ 맞춘 base 박스", round(statistics.mean(b['score'] for name, bs in base_dets.items() for j, b in enumerate(bs) if j in matched_base[name]), 2))

# 사용자 판정(53건)에 대해 base가 어떻게 되는지
fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))
uf = Counter()
ut = Counter()
for r in fb:
    ut[r["verdict"]] += 1
    for b in base_dets.get(r["photo"], []):
        if b["category"] == r["category"] and iou(b["box"], r["box"]) > 0.5:
            uf[r["verdict"]] += 1
            break
print("\n[사용자 판정 53건을 base가 다시 찾은 비율]")
for v, lab in [("O", "맞아요"), ("P", "이미 제자리"), ("X", "틀려요")]:
    print(f"  {lab:8} {uf[v]:2}/{ut[v]:2} ({uf[v] / ut[v] * 100:5.1f}%)")

json.dump([{"photo": n, "category": b["category"], "score": b["score"], "box": b["box"]} for n, _, b in new],
          open(os.path.join(ROOT, "outputs", "base_new_boxes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
