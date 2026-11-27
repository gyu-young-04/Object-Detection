# -*- coding: utf-8 -*-
# E1d 분석: 가구 미끼 묶음(한 문장) vs 같은 단어를 따로 물을 때 vs 기존 조합.
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
e1b = json.load(open(os.path.join(ROOT, "outputs", "detections_e1b.json"), encoding="utf-8"))
e1d = json.load(open(os.path.join(ROOT, "outputs", "detections_e1d.json"), encoding="utf-8"))

tiny = {}
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL or name not in e1d:
            continue
        tiny[name] = [{"category": d["category"], "score": d["score"], "box": d["box"], "v": "OP" if lab[name][str(i)]["v"] in "OP" else lab[name][str(i)]["v"]}
                      for i, d in enumerate(r["detections"], 1)]
base = Counter(t["v"] for ts in tiny.values() for t in ts)
print(f"사진 {len(tiny)}장, 기준: 맞음 {base['OP']} 애매 {base['A']} 틀림 {base['X']} (정밀도 {base['OP'] / sum(base.values()) * 100:.1f}%)")


def boxes(name, key):
    for src in (e1d, e1b, e1):
        if key in src[name]["boxes"]:
            return src[name]["boxes"][key]
    raise KeyError(key)


def run(keys, thr=0.7):
    lost = Counter()
    n_after = 0
    for name, ts in tiny.items():
        dets = [dict(t, kind="old") for t in ts]
        for k in keys:
            for b in boxes(name, k):
                dets.append({"category": "decoy_" + k, "score": b["score"], "box": b["box"], "kind": "new"})
        ids = {id(d) for d in remove_conflicts(dets, thr)}
        for d in dets:
            if d["kind"] == "old":
                if id(d) not in ids:
                    lost[d["v"]] += 1
                else:
                    n_after += 1
    return lost, n_after


ref = statistics.median(r["seconds"]["ref_clothes"] for r in e1d.values())
print(f"기준 질의 1번(clothes) 중앙값 {ref:.1f}초")
rows = [
    ("따로 4번: cushion, blanket, comforter, shelf", ["cushion", "blanket", "comforter", "shelf"], None),
    ("한 문장 furn4 (같은 4단어)", ["furn4"], "furn4"),
    ("따로 6번: +pillow, drawer", ["cushion", "blanket", "pillow", "comforter", "shelf", "drawer"], None),
    ("한 문장 furn6 (같은 6단어)", ["furn6"], "furn6"),
    ("(참고) 기존 한 문장 bundle4: cushion, blanket, pillow, comforter", ["bundle4"], None),
]
print(f"\n{'구성':52} {'지운 틀림':>9} {'지운 애매':>9} {'잃은 맞음':>9} {'순이득':>6} {'정밀도':>7} {'질의 수':>6} {'시간(기준의 몇 배)':>14}")
for title, keys, bundle in rows:
    lost, n_after = run(keys)
    prec = (base["OP"] - lost["OP"]) / n_after * 100
    queries = len(keys) if not (len(keys) == 1 and keys[0].startswith(("furn", "bundle"))) else 1
    if bundle:
        t = statistics.median(r["seconds"][bundle] for r in e1d.values()) / ref
    else:
        t = float(queries)
    print(f"{title:52} {lost['X']:6}/{base['X']:2} {lost['A']:6}/{base['A']:3} {lost['OP']:6}/{base['OP']:3} {lost['X'] - lost['OP']:6} {prec:6.1f}% {queries:6} {t:14.1f}")
