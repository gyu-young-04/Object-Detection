# -*- coding: utf-8 -*-
# E1 분석: (1) 오탐 흡수용 후보가 기존 채점 박스를 얼마나 지우는지(틀린 박스 vs 맞는 박스), (2) 정리 대상 확장 후보가 얼마나 찾는지.
import json
import os
import statistics
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
e1 = json.load(open(os.path.join(ROOT, "outputs", "detections_e1.json"), encoding="utf-8"))
DECOYS = ["cushion", "blanket", "basket", "chair", "picture frame", "phone"]
TARGETS = ["cup", "bowl", "glass jar"]

tiny = {}
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        tiny[name] = [{"category": d["category"], "score": d["score"], "box": d["box"], "v": "OP" if lab[name][str(i)]["v"] in "OP" else lab[name][str(i)]["v"]}
                      for i, d in enumerate(r["detections"], 1)]

secs = [r["seconds"] for r in e1.values()]
print(f"사진 {len(e1)}장, 후보 {len(DECOYS) + len(TARGETS)}개, 사진당 시간 중앙값 {statistics.median(secs):.0f}초 (후보 9개 합계)")

print("\n[후보별 탐지 수 (점수 0.30 이상, 중복 제거 후)]")
print(f"{'후보':14} {'박스':>5} {'사진 수':>7} {'점수 평균':>9}")
for c in TARGETS + DECOYS:
    bs = [b for r in e1.values() for b in r["boxes"][c]]
    ph = sum(1 for r in e1.values() if r["boxes"][c])
    print(f"{c:14} {len(bs):5} {ph:7} {statistics.mean(b['score'] for b in bs) if bs else 0:9.2f}")

def run(cands, thr):
    """기존 채점 박스 + 후보 박스를 같은 사진에서 충돌 규칙에 넣고, 살아남은 기존 박스와 후보 박스를 돌려준다."""
    kept_old = Counter()
    lost_old = Counter()
    kept_new = Counter()
    for name, ts in tiny.items():
        dets = [dict(t, kind="old") for t in ts]
        for c in cands:
            for b in e1[name]["boxes"][c]:
                dets.append({"category": c, "score": b["score"], "box": b["box"], "kind": "new"})
        out = remove_conflicts(dets, thr)
        ids = {id(d) for d in out}
        for d in dets:
            if d["kind"] == "old":
                (kept_old if id(d) in ids else lost_old)[d["v"]] += 1
            elif id(d) in ids:
                kept_new[d["category"]] += 1
    return kept_old, lost_old, kept_new

base = Counter(t["v"] for ts in tiny.values() for t in ts)
print(f"\n[기준] 기존 306건: 맞음 {base['OP']}, 애매 {base['A']}, 틀림 {base['X']}  (엄격 정밀도 {base['OP'] / 306 * 100:.1f}%)")

for thr in (0.7, 0.5):
    print(f"\n===== 오탐 흡수용 6개를 함께 물었을 때 (충돌 기준 겹침 {thr}) =====")
    print(f"{'후보':14} {'지워진 틀림':>10} {'지워진 애매':>10} {'지워진 맞음':>10} | {'남은 박스':>8} {'엄격 정밀도':>10}")
    rows = [(c, [c]) for c in DECOYS] + [("6개 모두", DECOYS)]
    for title, cands in rows:
        ko, lo, kn = run(cands, thr)
        n = sum(ko.values())
        print(f"{title:14} {lo['X']:7}/{base['X']:2} {lo['A']:8}/{base['A']:3} {lo['OP']:8}/{base['OP']:3} | {n:8} {ko['OP'] / n * 100:9.1f}%")

print("\n===== 정리 대상 확장 3개 (기존 6개와 충돌 규칙을 거친 뒤 살아남은 박스) =====")
ko, lo, kn = run(TARGETS, 0.7)
for c in TARGETS:
    raw = sum(len(r["boxes"][c]) for r in e1.values())
    print(f"  {c:10} 탐지 {raw:3}건 -> 충돌 규칙 후 {kn[c]:3}건")
print(f"  (이때 기존 박스 중 지워진 것: 틀림 {lo['X']}, 애매 {lo['A']}, 맞음 {lo['OP']})")
