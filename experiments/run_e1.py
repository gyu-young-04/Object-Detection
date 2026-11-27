# -*- coding: utf-8 -*-
# E1: 카테고리 확장 후보 9개를 채점된 40장에 하나씩 물어 저장한다 (tiny, 해상도 400, 중복 박스 제거까지).
#   정리 대상 확장: cup, bowl, glass jar / 오탐 흡수용: cushion, blanket, basket, chair, picture frame, phone
import json
import os
import sys
import time
import warnings

from PIL import Image

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from detect import detect, load_model
from merge import remove_duplicates
from pipeline import set_size

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
photos = []
for dj in ["detections_labeled.json", "detections_labeled_new20.json", "detections_labeled_set2.json"]:
    for name in json.load(open(os.path.join(E, dj), encoding="utf-8")):
        if name not in CONTROL and name not in photos:
            photos.append(name)
CANDIDATES = ["cup", "bowl", "glass jar", "cushion", "blanket", "basket", "chair", "picture frame", "phone"]
print("사진", len(photos), "장, 후보", len(CANDIDATES), "개", flush=True)

processor, model = load_model()
set_size(processor, 400)
out_path = os.path.join(ROOT, "outputs", "detections_e1.json")
results = {}
t_all = time.time()
for n, name in enumerate(photos, 1):
    image = Image.open(os.path.join(ROOT, "data", name)).convert("RGB")
    t0 = time.time()
    per = {}
    for cand in CANDIDATES:
        found = remove_duplicates(detect(image, [cand], processor, model))
        per[cand] = [{"score": d["score"], "box": d["box"]} for d in found]
    results[name] = {"seconds": round(time.time() - t0, 1), "boxes": per}
    print(f"[{n}/{len(photos)}] {name}: {sum(len(v) for v in per.values())}건 {time.time() - t0:.0f}초", flush=True)
    json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
print(f"완료 {time.time() - t_all:.0f}초")
