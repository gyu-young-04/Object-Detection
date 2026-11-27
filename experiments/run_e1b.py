# -*- coding: utf-8 -*-
# E1b: 미끼 후보 확장 9개를 하나씩 + E1c: 미끼를 한 문장에 묶어 묻기(2개 묶음, 4개 묶음)를 채점된 40장에 돌려 저장한다.
# tiny, 해상도 400, 점수 0.30 (기존과 같은 설정). 질의마다 걸린 시간도 기록한다.
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

SINGLES = ["drawer", "cabinet", "shelf", "drying rack", "paper", "laptop", "pillow", "comforter", "towel"]
BUNDLES = {"bundle2": ["cushion", "blanket"], "bundle4": ["cushion", "blanket", "pillow", "comforter"]}
print("사진", len(photos), "장, 단일 후보", len(SINGLES), "개, 묶음", list(BUNDLES), flush=True)

processor, model = load_model()
set_size(processor, 400)
out_path = os.path.join(ROOT, "outputs", "detections_e1b.json")
results = {}
t_all = time.time()
for n, name in enumerate(photos, 1):
    image = Image.open(os.path.join(ROOT, "data", name)).convert("RGB")
    per, secs = {}, {}
    for key, cats in [(c, [c]) for c in SINGLES] + list(BUNDLES.items()):
        t0 = time.time()
        found = remove_duplicates(detect(image, cats, processor, model))
        secs[key] = round(time.time() - t0, 2)
        per[key] = [{"score": d["score"], "box": d["box"], "label": d["category"]} for d in found]
    results[name] = {"seconds": secs, "boxes": per}
    print(f"[{n}/{len(photos)}] {name}: {sum(len(v) for v in per.values())}건 {sum(secs.values()):.0f}초", flush=True)
    json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
print(f"완료 {time.time() - t_all:.0f}초")
