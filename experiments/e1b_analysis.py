# -*- coding: utf-8 -*-
# E1b/E1c 분석: 미끼 후보마다 "지운 틀림 - 잃은 맞음"과 추가 시간 대비 효율, 묶어 묻기의 효과와 시간.
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

tiny = {}
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL or name not in e1b:
            continue
        tiny[name] = [{"category": d["category"], "score": d["score"], "box": d["box"], "v": "OP" if lab[name][str(i)]["v"] in "OP" else lab[name][str(i)]["v"]}
                      for i, d in enumerate(r["detections"], 1)]
print("사진", len(tiny), "장 (E1b가 끝난 만큼)")

base = Counter(t["v"] for ts in tiny.values() for t in ts)
print(f"기준: 맞음 {base['OP']} 애매 {base['A']} 틀림 {base['X']} (정밀도 {base['OP'] / sum(base.values()) * 100:.1f}%)")


def source(key):
    """key가 E1(쿠션 등)에 있으면 E1에서, 아니면 E1b에서 박스를 가져온다."""
    return e1 if key in e1[next(iter(e1))]["boxes"] else e1b


def run(keys, thr=0.7):
    kept, lost = Counter(), Counter()
    for name, ts in tiny.items():
        dets = [dict(t, kind="old") for t in ts]
        for k in keys:
            for b in source(k)[name]["boxes"][k]:
                dets.append({"category": "decoy_" + k, "score": b["score"], "box": b["box"], "kind": "new"})
        out = remove_conflicts(dets, thr)
        ids = {id(d) for d in out}
        for d in dets:
            if d["kind"] == "old":
                (kept if id(d) in ids else lost)[d["v"]] += 1
    return kept, lost


def avg_secs(key):
    src = source(key)
    if src is e1:  # E1은 후보 9개 합계 시간만 기록돼 있어 후보당 평균으로 환산
        return statistics.median(r["seconds"] for r in src.values()) / len(next(iter(src.values()))["boxes"])
    # 컴퓨터가 잠자기에 들어가면 시간이 수백 초로 튀므로 평균이 아니라 중앙값을 쓴다
    return statistics.median(r["seconds"][key] for r in src.values() if key in r["seconds"])


print("\n[미끼 후보 하나씩] (충돌 겹침 0.7)")
print(f"{'후보':12} {'지운 틀림':>8} {'지운 애매':>8} {'잃은 맞음':>8} {'순이득':>6} {'1질의 시간':>8}")
cands = ["cushion", "blanket", "basket", "chair", "picture frame", "phone", "drawer", "cabinet", "shelf", "drying rack", "paper", "laptop", "pillow", "comforter", "towel"]
rows = []
for k in cands:
    kept, lost = run([k])
    gain = lost["X"] - lost["OP"]
    rows.append((k, lost["X"], lost["A"], lost["OP"], gain, avg_secs(k)))
    print(f"{k:12} {lost['X']:6}/{base['X']:2} {lost['A']:6}/{base['A']:3} {lost['OP']:6}/{base['OP']:3} {gain:6} {avg_secs(k):7.1f}초")

print("\n[묶음]  (cushion+blanket 따로 vs 한 문장)")
for title, keys, bundle in [("따로 2번 (cushion, blanket)", ["cushion", "blanket"], None), ("한 문장 (bundle2)", ["bundle2"], "bundle2"),
                            ("따로 4번 (+pillow, comforter)", ["cushion", "blanket", "pillow", "comforter"], None), ("한 문장 (bundle4)", ["bundle4"], "bundle4")]:
    kept, lost = run(keys)
    t = sum(avg_secs(k) for k in keys) if bundle is None else avg_secs(bundle)
    print(f"  {title:28} 지운 틀림 {lost['X']:2}/{base['X']}, 애매 {lost['A']:2}, 잃은 맞음 {lost['OP']}/{base['OP']}, 시간 {t:.1f}초")

print("\n[조합: 순이득이 큰 순서로 하나씩 더할 때]")
chosen = []
rem = [r[0] for r in sorted(rows, key=lambda r: (-r[4], r[5]))]
cur_gain = 0
for k in rem:
    kept, lost = run(chosen + [k])
    g = lost["X"] - lost["OP"]
    if g > cur_gain:
        chosen.append(k)
        cur_gain = g
        print(f"  + {k:12} -> 지운 틀림 {lost['X']}, 잃은 맞음 {lost['OP']}, 순이득 {g}, 추가 시간 합계 {sum(avg_secs(c) for c in chosen):.1f}초")
