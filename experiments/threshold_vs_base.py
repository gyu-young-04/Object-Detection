# -*- coding: utf-8 -*-
# base가 "맞는 박스 64% 유지, 틀린 박스 71% 제거"라면, tiny의 점수 기준만 올려도 비슷한지 확인한다.
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
rows = []  # (score, verdict)
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            rows.append((d["score"], lab[name][str(i)]["v"]))
op = [s for s, v in rows if v in "OP"]
xs = [s for s, v in rows if v == "X"]
print(f"tiny 채점 박스 {len(rows)}건 (맞는 O+P {len(op)}, 틀림 X {len(xs)})")
print(f"{'점수 기준':8} {'남는 박스':>8} {'O+P 유지':>10} {'X 제거':>8}")
for thr in [0.30, 0.33, 0.35, 0.37, 0.40, 0.42, 0.45, 0.50]:
    keep = sum(1 for s in op if s >= thr)
    xk = sum(1 for s in xs if s >= thr)
    n = sum(1 for s, _ in rows if s >= thr)
    print(f"  >= {thr:.2f}  {n:8}   {keep / len(op) * 100:8.1f}%  {(1 - xk / len(xs)) * 100:6.1f}%")
print("\n비교: base 는 O+P 64.1% 유지, X 71.4% 제거")
