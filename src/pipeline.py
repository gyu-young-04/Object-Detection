# [pipeline.py] 전체를 조립해서 실행하는 총괄 파일. 이 파일을 직접 실행한다.
#   detect.py    : 모델 불러오기, 사진에서 물건 찾기
#   merge.py     : 박스 정리 (중복, 포개짐, 카테고리 충돌 제거) + 여러 사진 합집합
#   rules.py     : 카테고리에 목적지 붙이기, 목적지별로 묶어 안내문 만들기
#   visualize.py : 사진 위에 박스 그리기
# 흐름: data/의 사진 -> 카테고리를 하나씩 탐지 -> 박스 정리 -> 목적지 붙이기 -> 사진별 안내문 + 박스 그린 사진
#       -> (같은 방 사진을 묶으면) 방 단위로 합집합한 안내문 -> JSON 저장
# 실행 예: python src\pipeline.py --size 400
#          python src\pipeline.py --room 방A=no1.jpg,web5.webp   (두 사진을 같은 방으로 묶어 합집합)
#          python src\pipeline.py --no-contain --no-conflict   (박스 정리를 끄고 비교할 때)


import argparse  # 터미널 옵션(--size 등)을 읽는 도구
import json  # 결과를 JSON 파일로 저장하는 도구
import os  # 폴더/파일 경로를 다루는 도구
import time  # 시간을 재는 도구

from PIL import Image  # 사진 파일을 여는 도구 (Pillow)

# 아래 줄들은 우리가 만든 파일에서 함수를 가져온다
from detect import detect, load_model
from merge import merge_photos, remove_conflicts, remove_duplicates, remove_nested
from rules import DESTINATIONS, attach_destination, group_by_destination, summarize
from visualize import draw_detections

# 이 파일(src) 한 단계 위 = 프로젝트 루트 폴더
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")  # 입력 사진 폴더
OUT_DIR = os.path.join(ROOT, "outputs")  # 결과 저장 폴더
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")  # 처리할 사진 확장자
SKIP = {"sample.jpg"}  # 처리에서 제외할 파일

# 앞에 있을수록 먼저 탐지한다. 정리 효과가 가장 큰 옷을 맨 앞에 둔다.
# (이 순서는 "보여주는 순서"일 뿐이고, 카테고리가 충돌할 때의 승패에는 쓰지 않는다)
CORE_CATEGORIES = ["clothes", "book", "bag", "bottle", "shoes", "box"]
# 작은 박스가 같은 카테고리의 큰 박스 안에 이 비율 이상 들어 있으면 포개진 박스로 보고 버린다
CONTAIN_RATIO = 0.8
# 카테고리가 다른 박스가 이 정도(IoU) 이상 겹치면 같은 물건으로 보고 점수가 높은 쪽만 남긴다
CONFLICT_IOU = 0.7


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


def detect_progressive(image, categories, processor, model, contain_ratio=CONTAIN_RATIO):
    # 카테고리를 순서대로 하나씩 돌리고, 하나가 끝날 때마다 그 결과를 바로 내보낸다(제너레이터).
    # 카테고리를 한 문장에 묶으면 서로 간섭하므로 따로 돌린다.
    for category in categories:
        # 이 카테고리 하나만 탐지
        found = detect(image, [category], processor, model)
        # 모델이 이상한 라벨을 내도 우리가 요청한 카테고리 이름으로 통일
        for d in found:
            d["category"] = category
        # 같은 물건의 중복 박스를 지운다
        found = remove_duplicates(found)
        # 큰 덩어리 안에 포개진 박스를 지운다 (contain_ratio가 None이면 이 단계를 건너뜀)
        nested_dropped = 0
        if contain_ratio is not None:
            before = len(found)
            found = remove_nested(found, contain_ratio)
            nested_dropped = before - len(found)
        # 이 카테고리의 결과와 "포개져서 버린 개수"를 바로 내보낸다
        yield category, found, nested_dropped


def detect_each(image, categories, processor, model):
    # 위 함수의 결과를 하나의 리스트로 모아서 한꺼번에 돌려준다 (지금은 실험용으로만 쓴다)
    detections = []
    for _, found, _ in detect_progressive(image, categories, processor, model):
        detections += found
    return detections


def build_rooms(room_args, photo_names):
    # "방A=no1.jpg,web5.webp" 형태의 옵션을 {"방A": ["no1.jpg", "web5.webp"]} 로 바꾼다.
    # 어느 방에도 묶지 않은 사진은 그 사진 하나가 한 방이다.
    rooms = {}
    assigned = set()
    for arg in room_args:
        room_name, photos = arg.split("=")
        members = []
        for photo in photos.split(","):
            if photo in photo_names:
                members.append(photo)
            else:
                print(f"[경고] --room {room_name}: '{photo}' 사진을 찾을 수 없어 제외합니다")
        rooms[room_name] = members
        assigned.update(members)
    for name in photo_names:
        if name not in assigned:
            rooms[name] = [name]
    return rooms


def main(categories, size, contain_ratio, conflict_iou, room_args):
    # 결과를 저장할 폴더를 만들고, 모델은 한 번만 불러와서 모든 사진에 재사용한다
    os.makedirs(OUT_DIR, exist_ok=True)
    processor, model = load_model()
    set_size(processor, size)

    # 결과 파일 이름에 붙일 꼬리표 (박스 정리를 껐을 때는 파일이 안 덮어써지게 구분)
    tag = f"{size}"
    if contain_ratio is None:
        tag += "_nocontain"
    if conflict_iou is None:
        tag += "_noconflict"

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
        nested_total = 0
        # 카테고리가 하나 끝날 때마다 한 바퀴씩 돈다
        for category, found, nested_dropped in detect_progressive(image, categories, processor, model, contain_ratio):
            elapsed = time.time() - start
            # 처음으로 결과가 나온 순간만 시간을 기록 ("첫 결과까지 걸린 시간")
            if found and first_result is None:
                first_result = elapsed
            # 이 카테고리의 물건에 목적지를 붙이고 모아둔다
            attach_destination(found)
            detections += found
            nested_total += nested_dropped
            timeline.append({"category": category, "count": len(found), "seconds": round(elapsed, 1)})
            print(f"  {elapsed:5.1f}초  {category:8} {len(found):2d}건  (포개져서 제거 {nested_dropped})")
        total = time.time() - start

        # 모든 카테고리가 끝난 뒤, 카테고리가 달라도 같은 위치인 박스는 점수 높은 쪽만 남긴다
        conflict_total = 0
        if conflict_iou is not None:
            before = len(detections)
            detections = remove_conflicts(detections, conflict_iou)
            conflict_total = before - len(detections)
        # 나중에 어느 사진에서 나온 결과인지 알 수 있게 사진 이름을 붙여둔다
        for d in detections:
            d["photo"] = name

        first_text = f"{first_result:.1f}초" if first_result is not None else "없음"
        print(f"  -> 첫 결과 {first_text} / 전체 {total:.1f}초 / 합계 {len(detections)}건 "
              f"/ 포개져서 제거 {nested_total}건 / 카테고리 충돌로 제거 {conflict_total}건")

        # 목적지별로 묶어서 안내문을 출력
        groups = group_by_destination(detections)
        for line in summarize(groups):
            print("  " + line)

        # 박스를 그린 사진을 outputs/에 저장 (원본은 그대로)
        out_name = f"{os.path.splitext(name)[0]}_det{tag}.jpg"
        draw_detections(image, detections, DESTINATIONS).save(os.path.join(OUT_DIR, out_name))
        # 이 사진의 결과(시간, 카테고리별 타임라인, 탐지 목록)를 모아둔다
        all_results[name] = {
            "first_result_seconds": None if first_result is None else round(first_result, 1),
            "total_seconds": round(total, 1),
            "nested_removed": nested_total,
            "conflict_removed": conflict_total,
            "timeline": timeline,
            "detections": detections,
        }

    # 모든 사진의 결과를 JSON 파일 하나로 저장 (한글이 깨지지 않게 ensure_ascii=False)
    with open(os.path.join(OUT_DIR, f"detections_{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # 방 단위 합집합: 같은 방으로 묶은 사진들의 결과를 합쳐서 방 전체 안내문을 만든다
    rooms = build_rooms(room_args, list(all_results))
    results_by_photo = {n: r["detections"] for n, r in all_results.items()}
    room_summaries = {}
    has_multi_photo_room = False
    for room_name, photo_names in rooms.items():
        merged = merge_photos(results_by_photo, photo_names)
        groups = group_by_destination(merged)
        room_summaries[room_name] = {
            "photos": photo_names,
            "count": len(merged),
            "groups": {destination: len(items) for destination, items in groups.items()},
        }
        # 사진이 한 장뿐인 방은 위의 사진별 안내문과 똑같으므로 출력하지 않는다
        if len(photo_names) >= 2:
            has_multi_photo_room = True
            print(f"\n[방: {room_name}] 사진 {len(photo_names)}장 ({', '.join(photo_names)}) 합집합 {len(merged)}건")
            for line in summarize(groups):
                print("  " + line)
    if has_multi_photo_room:
        print("  (참고: 같은 물건이 여러 사진에 찍혔다면 중복으로 집계될 수 있습니다)")
    with open(os.path.join(OUT_DIR, f"rooms_{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(room_summaries, f, ensure_ascii=False, indent=2)

    # 전체 사진의 평균 시간과 제거된 박스 개수를 요약해서 출력
    firsts = [r["first_result_seconds"] for r in all_results.values() if r["first_result_seconds"] is not None]
    totals = [r["total_seconds"] for r in all_results.values()]
    nested_all = sum(r["nested_removed"] for r in all_results.values())
    conflict_all = sum(r["conflict_removed"] for r in all_results.values())
    print(f"\n[요약] 첫 결과까지 평균 {sum(firsts) / len(firsts):.1f}초, 전체 평균 {sum(totals) / len(totals):.1f}초 "
          f"({len(totals)}장), 포개져서 제거 {nested_all}건, 카테고리 충돌로 제거 {conflict_all}건")


# 터미널에서 이 파일을 직접 실행했을 때만 아래가 돈다
if __name__ == "__main__":
    # 터미널 옵션을 읽는다: 카테고리 목록(안 적으면 기본값), --size(해상도, 기본 400),
    # --no-contain / --no-conflict(박스 정리 끄기), --room(같은 방 사진 묶기, 여러 번 쓸 수 있음)
    parser = argparse.ArgumentParser()
    parser.add_argument("categories", nargs="*", default=CORE_CATEGORIES)
    parser.add_argument("--size", type=int, default=400)
    parser.add_argument("--no-contain", action="store_true")
    parser.add_argument("--no-conflict", action="store_true")
    parser.add_argument("--room", action="append", default=[])
    args = parser.parse_args()
    main(
        args.categories,
        args.size,
        None if args.no_contain else CONTAIN_RATIO,
        None if args.no_conflict else CONFLICT_IOU,
        args.room,
    )
