import argparse
import json
import os
import time

from PIL import Image

from detect import detect, load_model
from merge import remove_duplicates
from visualize import draw_detections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
SKIP = {"sample.jpg"}

# 앞에 있을수록 먼저 탐지한다. 정리 효과가 가장 큰 옷을 맨 앞에 둔다.
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


def detect_progressive(image, categories, processor, model):
    # 카테고리를 순서대로 하나씩 돌리고, 하나가 끝날 때마다 그 결과를 바로 내보낸다(제너레이터).
    # 카테고리를 한 문장에 묶으면 서로 간섭하므로 따로 돌린다.
    for category in categories:
        found = detect(image, [category], processor, model)
        for d in found:
            d["category"] = category
        yield category, remove_duplicates(found)


def detect_each(image, categories, processor, model):
    detections = []
    for _, found in detect_progressive(image, categories, processor, model):
        detections += found
    return detections


def main(categories, size):
    os.makedirs(OUT_DIR, exist_ok=True)
    processor, model = load_model()
    set_size(processor, size)

    all_results = {}
    for path in list_images():
        name = os.path.basename(path)
        image = Image.open(path).convert("RGB")
        print(name)

        start = time.time()
        detections = []
        timeline = []
        first_result = None
        for category, found in detect_progressive(image, categories, processor, model):
            elapsed = time.time() - start
            if found and first_result is None:
                first_result = elapsed
            detections += found
            timeline.append({"category": category, "count": len(found), "seconds": round(elapsed, 1)})
            print(f"  {elapsed:5.1f}초  {category:8} {len(found):2d}건")
        total = time.time() - start

        first_text = f"{first_result:.1f}초" if first_result is not None else "없음"
        print(f"  -> 첫 결과 {first_text} / 전체 {total:.1f}초 / 합계 {len(detections)}건")

        out_name = f"{os.path.splitext(name)[0]}_det{size}.jpg"
        draw_detections(image, detections, categories).save(os.path.join(OUT_DIR, out_name))
        all_results[name] = {
            "first_result_seconds": None if first_result is None else round(first_result, 1),
            "total_seconds": round(total, 1),
            "timeline": timeline,
            "detections": detections,
        }

    with open(os.path.join(OUT_DIR, f"detections_{size}.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    firsts = [r["first_result_seconds"] for r in all_results.values() if r["first_result_seconds"] is not None]
    totals = [r["total_seconds"] for r in all_results.values()]
    print(f"\n[요약] 첫 결과까지 평균 {sum(firsts) / len(firsts):.1f}초, 전체 평균 {sum(totals) / len(totals):.1f}초 ({len(totals)}장)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("categories", nargs="*", default=CORE_CATEGORIES)
    parser.add_argument("--size", type=int, default=400)
    args = parser.parse_args()
    main(args.categories, args.size)
