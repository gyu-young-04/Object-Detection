import sys
import time

import torch
from PIL import Image

from detect import detect, load_model

image = Image.open(sys.argv[1]).convert("RGB")
categories = ["cat", "remote control", "couch"]

print(f"CPU 스레드 수: {torch.get_num_threads()}")
processor, model = load_model()

print("\n[원본 해상도로 3회 반복]")
for i in range(3):
    t0 = time.time()
    result = detect(image, categories, processor, model)
    print(f"  {i + 1}회차: {time.time() - t0:.1f}초, 탐지 {len(result)}건")

print("\n[입력 해상도를 줄여서 3회 반복 (짧은 변 400px)]")
processor.image_processor.size = {"shortest_edge": 400, "longest_edge": 667}
for i in range(3):
    t0 = time.time()
    result = detect(image, categories, processor, model)
    print(f"  {i + 1}회차: {time.time() - t0:.1f}초, 탐지 {len(result)}건")
