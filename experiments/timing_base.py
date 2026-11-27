# -*- coding: utf-8 -*-
# 사진 1장에서 Grounding DINO tiny와 base의 속도와 박스 수를 비교한다 (해상도 400, 카테고리 6개를 하나씩).
import os
import sys
import time
import warnings

from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from detect import detect
from merge import remove_duplicates
from pipeline import CORE_CATEGORIES, set_size

photo = sys.argv[1] if len(sys.argv) > 1 else "pexels_10557077.jpeg"
image = Image.open(os.path.join(ROOT, "data", photo)).convert("RGB")
print("사진:", photo, image.size)

for tag, mid in [("tiny", "IDEA-Research/grounding-dino-tiny"), ("base", "IDEA-Research/grounding-dino-base")]:
    t0 = time.time()
    processor = AutoProcessor.from_pretrained(mid)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(mid)
    model.eval()
    load = time.time() - t0
    set_size(processor, 400)
    total = 0
    counts = {}
    t1 = time.time()
    for cat in CORE_CATEGORIES:
        found = remove_duplicates(detect(image, [cat], processor, model))
        counts[cat] = len(found)
        total += len(found)
    run = time.time() - t1
    print(f"[{tag}] 불러오기 {load:.0f}초, 탐지 {run:.1f}초 (카테고리 6개), 박스 {total}건 {counts}", flush=True)
