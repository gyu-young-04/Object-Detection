# -*- coding: utf-8 -*-
# 시간 줄이기 방법 검증 (tiny, CPU). 컴퓨터를 다른 일에 쓰지 않을 때 돌려야 시간이 정확하다.
#   T1 해상도: 400 / 320 / 256 에서 시간과 기존 채점 박스 유지(맞음 유지, 틀림 제거)
#   T2 배치: 카테고리 6개를 한 번의 모델 실행(사진 6장 복사 묶음)으로 처리했을 때 시간과 결과 동일성
# 사용: python time_methods.py t1 | t2
import json
import os
import statistics
import sys
import time
import warnings
from collections import Counter

import torch
from PIL import Image

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from detect import detect, load_model
from merge import iou, remove_conflicts, remove_duplicates
from pipeline import CORE_CATEGORIES, set_size

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
labeled = {}
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        labeled[name] = [{"category": d["category"], "box": d["box"], "v": "OP" if lab[name][str(i)]["v"] in "OP" else lab[name][str(i)]["v"]}
                         for i, d in enumerate(r["detections"], 1)]
photos = list(labeled)
mode = sys.argv[1]
processor, model = load_model()
print("사진", len(photos), "장, 모드", mode, flush=True)

if mode == "t1":
    sizes = [int(s) for s in sys.argv[2:]] or [400, 320, 256]
    for size in sizes:
        set_size(processor, size)
        secs, kept, lost, new = [], Counter(), Counter(), 0
        for n, name in enumerate(photos, 1):
            image = Image.open(os.path.join(ROOT, "data", name)).convert("RGB")
            t0 = time.time()
            dets = []
            for c in CORE_CATEGORIES:
                dets += remove_duplicates(detect(image, [c], processor, model))
            for d in dets:
                pass
            dets = remove_conflicts(dets, 0.7)
            secs.append(time.time() - t0)
            for l in labeled[name]:
                hit = any(d["category"] == l["category"] and iou(d["box"], l["box"]) > 0.5 for d in dets)
                (kept if hit else lost)[l["v"]] += 1
            new += sum(1 for d in dets if not any(d["category"] == l["category"] and iou(d["box"], l["box"]) > 0.5 for l in labeled[name]))
        print(f"해상도 {size}: 사진당 평균 {statistics.mean(secs):.1f}초 (중앙값 {statistics.median(secs):.1f}) | 기존 채점 박스 유지: 맞음 {kept['OP']}, 애매 {kept['A']}, 틀림 {kept['X']} / 잃음: 맞음 {lost['OP']}, 애매 {lost['A']}, 틀림 {lost['X']} | 새 박스 {new}건", flush=True)

if mode == "t2":
    set_size(processor, 400)
    sample = photos[::4][:10]
    s_seq, s_bat, same, diff = [], [], 0, 0
    for name in sample:
        image = Image.open(os.path.join(ROOT, "data", name)).convert("RGB")
        t0 = time.time()
        seq = {c: detect(image, [c], processor, model) for c in CORE_CATEGORIES}
        s_seq.append(time.time() - t0)
        t0 = time.time()
        inputs = processor(images=[image] * len(CORE_CATEGORIES), text=[c + "." for c in CORE_CATEGORIES], return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        res = processor.post_process_grounded_object_detection(outputs, inputs.input_ids, threshold=0.3, text_threshold=0.25, target_sizes=[image.size[::-1]] * len(CORE_CATEGORIES))
        s_bat.append(time.time() - t0)
        for c, r in zip(CORE_CATEGORIES, res):
            a = sorted(round(float(s), 3) for s in r["scores"])
            b = sorted(d["score"] for d in seq[c])
            if len(a) == len(b) and all(abs(x - y) < 0.01 for x, y in zip(a, b)):
                same += 1
            else:
                diff += 1
        print(f"  {name}: 순차 {s_seq[-1]:.1f}초, 배치 {s_bat[-1]:.1f}초", flush=True)
    print(f"배치 처리: 순차 평균 {statistics.mean(s_seq):.1f}초 vs 배치 평균 {statistics.mean(s_bat):.1f}초 | 결과 같음 {same}/{same + diff} (카테고리 단위)")
