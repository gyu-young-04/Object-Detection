# -*- coding: utf-8 -*-
# 조합 시험: 쿠션·이불 흡수 + 옷만 base 모델을 합쳤을 때의 효과를 저장된 결과로 계산한다. (모델은 다시 돌리지 않는다)
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou, remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
DECOYS = ["cushion", "blanket"]

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
base = json.load(open(os.path.join(ROOT, "outputs", "detections_base_400.json"), encoding="utf-8"))
e1 = json.load(open(os.path.join(ROOT, "outputs", "detections_e1.json"), encoding="utf-8"))
new71 = json.load(open(os.path.join(E, "precision_labels_base_new71.json"), encoding="utf-8"))["boxes"]
fb = json.load(open(os.path.join(ROOT, "data", "feedback.json"), encoding="utf-8"))


def label_of(photo, cat, box):
    for t in tiny[photo]:
        if t["category"] == cat and iou(t["box"], box) > 0.5:
            return t["v"]
    for d in new71:
        if d["photo"] == photo and d["category"] == cat and iou(d["box"], box) > 0.5:
            return d["v"]
    return "U"  # 채점되지 않은 박스


def build(photo, variant):
    dets = []
    if variant in ("V0", "V1"):  # tiny 기본(+흡수)
        dets += [dict(t) for t in tiny[photo]]
    if variant in ("V2", "V3"):  # 옷만 base, 나머지는 tiny
        dets += [dict(t) for t in tiny[photo] if t["category"] != "clothes"]
        for b in base[photo]["boxes"]["clothes"]:
            dets.append({"category": "clothes", "score": b["score"], "box": b["box"], "v": label_of(photo, "clothes", b["box"])})
    if variant == "V4":  # base 전부
        for c in CATS:
            for b in base[photo]["boxes"][c]:
                dets.append({"category": c, "score": b["score"], "box": b["box"], "v": label_of(photo, c, b["box"])})
    if variant in ("V1", "V3"):
        for c in DECOYS:
            for b in e1[photo]["boxes"][c]:
                dets.append({"category": c, "score": b["score"], "box": b["box"], "v": "decoy"})
    return dets


def run(variant):
    out = []
    for photo in tiny:
        out += [dict(d, photo=photo) for d in remove_conflicts(build(photo, variant), 0.7) if d["category"] in CATS]
    return out


TITLES = {"V0": "tiny 기본 (현재)", "V1": "tiny + 쿠션·이불 흡수", "V2": "옷만 base (나머지 tiny)", "V3": "옷만 base + 쿠션·이불 흡수", "V4": "base 전부"}
TIME = {"V0": 18, "V1": 26, "V2": 21, "V3": 29, "V4": 37}
print(f"{'조합':26} {'박스':>4} {'맞음':>4} {'애매':>4} {'틀림':>4} {'미채점':>5} {'엄격 정밀도':>10} {'틀림 비율':>8} {'사진당 시간':>10}")
res = {}
for v in ["V0", "V1", "V2", "V3", "V4"]:
    s = run(v)
    res[v] = s
    c = Counter(d["v"] for d in s)
    n = len(s)
    print(f"{TITLES[v]:26} {n:4} {c['OP']:4} {c['A']:4} {c['X']:4} {c['U']:5} {c['OP'] / n * 100:9.1f}% {c['X'] / n * 100:7.1f}% {TIME[v]:8}초")

print("\n[옷 카테고리만]")
for v in ["V0", "V1", "V2", "V3", "V4"]:
    s = [d for d in res[v] if d["category"] == "clothes"]
    c = Counter(d["v"] for d in s)
    n = len(s)
    print(f"  {TITLES[v]:26} {n:3}건  맞음 {c['OP']:3} 애매 {c['A']:3} 틀림 {c['X']:3} 미채점 {c['U']:2}  엄격 {c['OP'] / n * 100:5.1f}%")

print("\n[사용자 판정 141건 기준] 맞는 박스를 얼마나 남기고, 틀려요를 얼마나 거르나")
op = [r for r in fb if r["verdict"] in ("O", "P")]
xs = [r for r in fb if r["verdict"] == "X"]
for v in ["V0", "V1", "V2", "V3", "V4"]:
    def kept(r):
        return any(d["photo"] == r["photo"] and d["category"] == r["category"] and iou(d["box"], r["box"]) > 0.5 for d in res[v])
    ko = sum(1 for r in op if kept(r))
    kx = sum(1 for r in xs if kept(r))
    print(f"  {TITLES[v]:26} 맞는 박스 유지 {ko:3}/{len(op)} ({ko / len(op) * 100:5.1f}%)  틀려요 제거 {len(xs) - kx:2}/{len(xs)} ({(len(xs) - kx) / len(xs) * 100:5.1f}%)")
