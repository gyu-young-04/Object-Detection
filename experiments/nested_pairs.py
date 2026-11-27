# -*- coding: utf-8 -*-
# 같은 카테고리에서 큰 박스가 작은 박스를 포함하는 쌍(80% 이상 포함)이 채점 데이터에 얼마나 있고, 판정이 어떻게 나뉘는지 센다.
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import box_area, inside_ratio

E = os.path.join(ROOT, "docs", "eval")
sets = [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
        ("detections_labeled_set2.json", "precision_labels_set2.json")]
CONTROL = {"web7.webp", "web8.webp"}

boxes = []
for dj, lj in sets:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            boxes.append({"photo": name, "id": i, "cat": d["category"], "score": d["score"], "box": d["box"], "v": lab[name][str(i)]["v"]})

def strict(sub):
    n = len(sub)
    c = Counter(b["v"] for b in sub)
    return f"{n:3}건 O{c['O']:2} P{c['P']:2} A{c['A']:2} X{c['X']:2} 엄격 {(c['O']+c['P'])/n*100:5.1f}%" if n else "0건"

by_photo = {}
for b in boxes:
    by_photo.setdefault(b["photo"], []).append(b)

pairs = []  # (큰 박스, 작은 박스)
for photo, bs in by_photo.items():
    for big in bs:
        for small in bs:
            if big is small or big["cat"] != small["cat"]:
                continue
            if box_area(big["box"]) > box_area(small["box"]) and inside_ratio(small["box"], big["box"]) >= 0.8:
                pairs.append((big, small))

print("전체 박스", len(boxes), "건")
print("포개진 쌍(같은 카테고리, 80% 이상 포함):", len(pairs), "쌍")
smalls = {id(s): s for _, s in pairs}
bigs = {id(b): b for b, _ in pairs}
print("  포개진 작은 박스:", len(smalls), "건 /  그것을 품은 큰 박스:", len(bigs), "건")
print("\n카테고리별 쌍 수:", dict(Counter(b["cat"] for b, _ in pairs)))
print("\n(큰 박스 판정, 작은 박스 판정) 조합:")
for k, v in sorted(Counter((b["v"], s["v"]) for b, s in pairs).items(), key=lambda x: -x[1]):
    print(f"  큰 {k[0]} / 작은 {k[1]} : {v}쌍")

print("\n[전체] 현재(포개짐 제거 없음):", strict(boxes))
keep_big = [b for b in boxes if id(b) not in smalls]
print("[작은 박스 제거 = 덩어리 단위 유지]  :", strict(keep_big))
keep_small = [b for b in boxes if id(b) not in bigs]
print("[큰 박스 제거 = 개별 단위 유지]      :", strict(keep_small))
print("\n제거되는 작은 박스만 따로:", strict(list(smalls.values())))
print("제거되는 큰 박스만 따로  :", strict(list(bigs.values())))
