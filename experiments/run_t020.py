# -*- coding: utf-8 -*-
# 점수 기준 실험: tiny로 채점된 40장을 점수 0.20 이상으로 한 번 돌려 저장한다. (0.20 이상이면 0.25, 0.30 등은 나중에 잘라서 비교할 수 있다)
# 해상도 400, 카테고리 6개를 하나씩, 같은 카테고리의 중복 박스 제거까지는 기존 파이프라인과 같다.
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
from pipeline import CORE_CATEGORIES, set_size

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
photos = []
for dj in ["detections_labeled.json", "detections_labeled_new20.json", "detections_labeled_set2.json"]:
    for name in json.load(open(os.path.join(E, dj), encoding="utf-8")):
        if name not in CONTROL and name not in photos:
            photos.append(name)
print("사진", len(photos), "장, 점수 0.20 이상", flush=True)

processor, model = load_model()
set_size(processor, 400)
out_path = os.path.join(ROOT, "outputs", "detections_t020.json")
results = {}
t_all = time.time()
for n, name in enumerate(photos, 1):
    image = Image.open(os.path.join(ROOT, "data", name)).convert("RGB")
    t0 = time.time()
    per = {}
    for cat in CORE_CATEGORIES:
        found = remove_duplicates(detect(image, [cat], processor, model, box_threshold=0.20, text_threshold=0.20))
        per[cat] = [{"score": d["score"], "box": d["box"]} for d in found]
    results[name] = {"seconds": round(time.time() - t0, 1), "boxes": per}
    print(f"[{n}/{len(photos)}] {name}: {sum(len(v) for v in per.values())}건 {time.time() - t0:.0f}초", flush=True)
    json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
print(f"완료 {time.time() - t_all:.0f}초")
