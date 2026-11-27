# -*- coding: utf-8 -*-
# E1d: 가구 미끼를 섞은 묶음(한 문장)이 따로 물을 때와 같은 효과인지 확인한다. tiny, 해상도 400, 40장.
# 같은 사진에서 기준 질의("clothes" 한 번)의 시간도 재서, 묶음 시간을 비율로 비교한다(컴퓨터 상태에 따라 절대 시간이 흔들리므로).
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

BUNDLES = {"furn4": ["cushion", "blanket", "comforter", "shelf"], "furn6": ["cushion", "blanket", "pillow", "comforter", "shelf", "drawer"]}
processor, model = load_model()
set_size(processor, 400)
out_path = os.path.join(ROOT, "outputs", "detections_e1d.json")
results = {}
for n, name in enumerate(photos, 1):
    image = Image.open(os.path.join(ROOT, "data", name)).convert("RGB")
    per, secs = {}, {}
    t0 = time.time()
    detect(image, ["clothes"], processor, model)
    secs["ref_clothes"] = round(time.time() - t0, 2)
    for key, cats in BUNDLES.items():
        t0 = time.time()
        found = remove_duplicates(detect(image, cats, processor, model))
        secs[key] = round(time.time() - t0, 2)
        per[key] = [{"score": d["score"], "box": d["box"], "label": d["category"]} for d in found]
    results[name] = {"seconds": secs, "boxes": per}
    print(f"[{n}/{len(photos)}] {name}: {secs}", flush=True)
    json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
print("완료")
