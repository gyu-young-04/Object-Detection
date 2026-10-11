import argparse
import json
import os
import time
from collections import Counter

from PIL import Image

from detect import detect, load_model
from merge import remove_duplicates
from visualize import draw_detections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
SKIP = {"sample.jpg"}

CORE_CATEGORIES = ["clothes", "book", "bag", "bottle", "shoes", "box"]


def list_images():
    names = sorted(os.listdir(DATA_DIR))
    return [
        os.path.join(DATA_DIR, n)
        for n in names
        if n.lower().endswith(IMAGE_EXTS) and n not in SKIP
    ]


def set_size(processor, shortest_edge):
    # 입력 사진의 짧은 변을 이 크기로 맞춘다. 작을수록 빠르고, 작은 물건은 놓치기 쉽다.
    processor.image_processor.size = {
        "shortest_edge": shortest_edge,
        "longest_edge": round(shortest_edge * 1333 / 800),
    }


def detect_each(image, categories, processor, model):
    # 카테고리를 한 문장에 묶으면 서로 간섭하므로, 하나씩 따로 돌려서 합친다.
    detections = []
    for category in categories:
        found = detect(image, [category], processor, model)
        for d in found:
            d["category"] = category
        detections += found
    return remove_duplicates(detections)


def main(categories, size):
    os.makedirs(OUT_DIR, exist_ok=True)
    processor, model = load_model()
    set_size(processor, size)

    all_results = {}
    for path in list_images():
        name = os.path.basename(path)
        image = Image.open(path).convert("RGB")

        t0 = time.time()
        detections = detect_each(image, categories, processor, model)
        elapsed = time.time() - t0

        counts = Counter(d["category"] for d in detections)
        print(f"{name:11} {elapsed:5.1f}초  {len(detections):3d}건  {dict(counts)}")

        out_name = f"{os.path.splitext(name)[0]}_det{size}.jpg"
        draw_detections(image, detections, categories).save(os.path.join(OUT_DIR, out_name))
        all_results[name] = {"seconds": round(elapsed, 1), "detections": detections}

    with open(os.path.join(OUT_DIR, f"detections_{size}.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("categories", nargs="*", default=CORE_CATEGORIES)
    parser.add_argument("--size", type=int, default=800)
    args = parser.parse_args()
    main(args.categories, args.size)
