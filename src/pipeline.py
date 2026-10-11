import json
import os
import sys
import time
from collections import Counter

from PIL import Image

from detect import detect, load_model
from visualize import draw_detections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
SKIP = {"sample.jpg"}

CATEGORIES = [
    "clothes",
    "book",
    "bag",
    "bottle",
    "shoes",
    "cup",
    "box",
    "plastic bag",
    "towel",
    "cable",
]


def list_images():
    names = sorted(os.listdir(DATA_DIR))
    return [
        os.path.join(DATA_DIR, n)
        for n in names
        if n.lower().endswith(IMAGE_EXTS) and n not in SKIP
    ]


def main(categories):
    os.makedirs(OUT_DIR, exist_ok=True)

    # 모델은 한 번만 불러오고, 모든 사진에 재사용한다.
    processor, model = load_model()

    all_results = {}
    for path in list_images():
        name = os.path.basename(path)
        image = Image.open(path).convert("RGB")

        t0 = time.time()
        detections = detect(image, categories, processor, model)
        elapsed = time.time() - t0

        counts = Counter(d["category"] for d in detections)
        print(f"{name:11} {elapsed:5.1f}초  {len(detections):3d}건  {dict(counts)}")

        out_name = os.path.splitext(name)[0] + "_det.jpg"
        draw_detections(image, detections, categories).save(os.path.join(OUT_DIR, out_name))
        all_results[name] = {"seconds": round(elapsed, 1), "detections": detections}

    with open(os.path.join(OUT_DIR, "detections.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 카테고리를 명령어 뒤에 적으면 그걸 쓰고, 안 적으면 위의 CATEGORIES를 쓴다.
    main(sys.argv[1:] or CATEGORIES)
