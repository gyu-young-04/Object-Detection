# [pipeline.py] 전체를 조립해서 실행하는 총괄 파일. 이 파일을 직접 실행한다.
#   detect.py    : 모델 불러오기, 사진에서 물건 찾기
#   merge.py     : 겹치는 중복 박스 제거
#   visualize.py : 사진 위에 박스 그리기
# 흐름: data/의 사진 -> 카테고리를 하나씩 탐지 -> 중복 제거 -> 박스 그린 사진 + JSON 저장
# 실행 예: python src\pipeline.py --size 400
import argparse  # 터미널 옵션(--size 등)을 읽는 도구
import json  # 결과를 JSON 파일로 저장하는 도구
import os  # 폴더/파일 경로를 다루는 도구
import time  # 시간을 재는 도구

from PIL import Image  # 사진 파일을 여는 도구 (Pillow)

# 아래 세 줄은 우리가 만든 파일에서 함수를 가져온다
from detect import detect, load_model
from merge import remove_duplicates
from visualize import draw_detections

# 이 파일(src) 한 단계 위 = 프로젝트 루트 폴더
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")  # 입력 사진 폴더
OUT_DIR = os.path.join(ROOT, "outputs")  # 결과 저장 폴더
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")  # 처리할 사진 확장자
SKIP = {"sample.jpg"}  # 처리에서 제외할 파일

# 앞에 있을수록 먼저 탐지한다. 정리 효과가 가장 큰 옷을 맨 앞에 둔다.
CORE_CATEGORIES = ["clothes", "book", "bag", "bottle", "shoes", "box"]


def list_images():
    # data/ 폴더에서 사진 파일만 골라(확장자 확인, 제외 파일 빼고) 경로 목록을 만든다
    names = sorted(os.listdir(DATA_DIR))
    return [
        os.path.join(DATA_DIR, n)
        for n in names
        if n.lower().endswith(IMAGE_EXTS) and n not in SKIP
    ]


def set_size(processor, shortest_edge):
    # 입력 사진의 짧은 변을 이 크기로 맞춘다. 작을수록 빠르고, 작은 물건은 놓치기 쉽다.
    # (사진 파일을 바꾸는 게 아니라 processor의 리사이즈 설정을 바꾸는 것)
    processor.image_processor.size = {
        "shortest_edge": shortest_edge,
        "longest_edge": round(shortest_edge * 1333 / 800),
    }


def detect_progressive(image, categories, processor, model):
    # 카테고리를 순서대로 하나씩 돌리고, 하나가 끝날 때마다 그 결과를 바로 내보낸다(제너레이터).
    # 카테고리를 한 문장에 묶으면 서로 간섭하므로 따로 돌린다.
    for category in categories:
        # 이 카테고리 하나만 탐지
        found = detect(image, [category], processor, model)
        # 모델이 이상한 라벨을 내도 우리가 요청한 카테고리 이름으로 통일
        for d in found:
            d["category"] = category
        # 같은 카테고리 안의 중복 박스를 지우고, 이 카테고리의 결과를 바로 내보낸다
        yield category, remove_duplicates(found)


def detect_each(image, categories, processor, model):
    # 위 함수의 결과를 하나의 리스트로 모아서 한꺼번에 돌려준다 (지금은 실험용으로만 쓴다)
    detections = []
    for _, found in detect_progressive(image, categories, processor, model):
        detections += found
    return detections


def main(categories, size):
    # 결과를 저장할 폴더를 만들고, 모델은 한 번만 불러와서 모든 사진에 재사용한다
    os.makedirs(OUT_DIR, exist_ok=True)
    processor, model = load_model()
    set_size(processor, size)

    # 사진별 결과를 모아두는 딕셔너리 (나중에 JSON으로 저장)
    all_results = {}
    # data/의 사진을 하나씩 처리
    for path in list_images():
        name = os.path.basename(path)
        # 사진을 열고, 투명 채널이 있는 형식도 일반 색상(RGB)으로 통일
        image = Image.open(path).convert("RGB")
        print(name)

        start = time.time()
        detections = []
        timeline = []
        first_result = None
        # 카테고리가 하나 끝날 때마다 한 바퀴씩 돈다
        for category, found in detect_progressive(image, categories, processor, model):
            elapsed = time.time() - start
            # 처음으로 결과가 나온 순간만 시간을 기록 ("첫 결과까지 걸린 시간")
            if found and first_result is None:
                first_result = elapsed
            detections += found
            timeline.append({"category": category, "count": len(found), "seconds": round(elapsed, 1)})
            print(f"  {elapsed:5.1f}초  {category:8} {len(found):2d}건")
        total = time.time() - start

        first_text = f"{first_result:.1f}초" if first_result is not None else "없음"
        print(f"  -> 첫 결과 {first_text} / 전체 {total:.1f}초 / 합계 {len(detections)}건")

        # 박스를 그린 사진을 outputs/에 저장 (원본은 그대로)
        out_name = f"{os.path.splitext(name)[0]}_det{size}.jpg"
        draw_detections(image, detections, categories).save(os.path.join(OUT_DIR, out_name))
        # 이 사진의 결과(시간, 카테고리별 타임라인, 탐지 목록)를 모아둔다
        all_results[name] = {
            "first_result_seconds": None if first_result is None else round(first_result, 1),
            "total_seconds": round(total, 1),
            "timeline": timeline,
            "detections": detections,
        }

    # 모든 사진의 결과를 JSON 파일 하나로 저장 (한글이 깨지지 않게 ensure_ascii=False)
    with open(os.path.join(OUT_DIR, f"detections_{size}.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # 전체 사진의 평균 시간을 요약해서 출력
    firsts = [r["first_result_seconds"] for r in all_results.values() if r["first_result_seconds"] is not None]
    totals = [r["total_seconds"] for r in all_results.values()]
    print(f"\n[요약] 첫 결과까지 평균 {sum(firsts) / len(firsts):.1f}초, 전체 평균 {sum(totals) / len(totals):.1f}초 ({len(totals)}장)")


# 터미널에서 이 파일을 직접 실행했을 때만 아래가 돈다
if __name__ == "__main__":
    # 터미널 옵션을 읽는다: 카테고리 목록(안 적으면 기본값), --size(해상도, 기본 400)
    parser = argparse.ArgumentParser()
    parser.add_argument("categories", nargs="*", default=CORE_CATEGORIES)
    parser.add_argument("--size", type=int, default=400)
    args = parser.parse_args()
    main(args.categories, args.size)
