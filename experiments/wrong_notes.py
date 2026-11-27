# -*- coding: utf-8 -*-
# 틀림(X)과 애매(A)로 채점한 박스의 메모를 카테고리별로 모아서 본다 (유형 분류의 재료).
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
rows = []
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            l = lab[name][str(i)]
            v = "OP" if l["v"] in "OP" else l["v"]
            if v in ("X", "A"):
                rows.append((d["category"], v, d["score"], l.get("note", "")))
for cat in ["clothes", "book", "bag", "bottle", "shoes", "box"]:
    for v in ("X", "A"):
        sub = [r for r in rows if r[0] == cat and r[1] == v]
        print(f"\n## {cat} {v} ({len(sub)}건)")
        for r in sorted(sub, key=lambda r: -r[2]):
            print(f"  {r[2]:.2f} {r[3]}")
