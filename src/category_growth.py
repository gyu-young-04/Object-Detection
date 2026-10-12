# [category_growth.py] 카테고리를 늘릴수록 박스가 얼마나 겹치는지(충돌) 측정한다.
# 흐름: 15개 카테고리로 돌린 결과(JSON)를 읽기 -> 앞에서부터 6, 9, 12, 15개만 골라 충돌 쌍 세기
#       -> "같은 목적지끼리의 충돌(해롭지 않음)"과 "다른 목적지끼리의 충돌(안내가 달라짐)"을 나눠서 세기
# 준비: python src\pipeline.py clothes book bag bottle shoes box towel blanket "plastic bag" cup paper toy cable "remote control" pillow --no-conflict
# 실행: python src\category_growth.py
import json
import os
from collections import Counter

from merge import iou
from rules import CATEGORY_INFO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT = os.path.join(ROOT, "outputs", "detections_400_noconflict.json")
CONTROL = {"web7.webp", "web8.webp"}  # 어지럽지 않은 작업실은 제외

# 앞에 있을수록 먼저 추가한 카테고리 (앞의 6개는 기존 핵심 카테고리)
ORDER = ["clothes", "book", "bag", "bottle", "shoes", "box",
         "towel", "blanket", "plastic bag", "cup", "paper", "toy", "cable", "remote control", "pillow"]

# 새 카테고리에 임시로 붙인 목적지 (실제 규칙표에는 아직 없는 가정)
EXTRA_DESTINATION = {
    "towel": "옷장", "blanket": "옷장", "pillow": "옷장",
    "plastic bag": "분리수거", "cup": "주방", "paper": "책장",
    "toy": "수납함", "cable": "수납함", "remote control": "제자리 보관",
}


def destination_of(category):
    if category in CATEGORY_INFO:
        return CATEGORY_INFO[category]["destination"]
    return EXTRA_DESTINATION[category]


def conflict_pairs(detections, threshold=0.7):
    # 카테고리가 다른데 거의 같은 위치(IoU가 threshold 초과)인 박스 쌍
    pairs = []
    for i, a in enumerate(detections):
        for b in detections[i + 1:]:
            if a["category"] != b["category"] and iou(a["box"], b["box"]) > threshold:
                pairs.append((a, b))
    return pairs


def main():
    with open(RESULT, encoding="utf-8") as f:
        data = json.load(f)
    rooms = {name: r["detections"] for name, r in data.items() if name not in CONTROL}

    print("=== 카테고리 수별 충돌 (어지러운 방 8곳) ===")
    print(f"{'카테고리 수':8} {'박스':5} {'충돌 쌍':7} {'같은 목적지(해롭지 않음)':22} {'다른 목적지(안내가 달라짐)':24}")
    for k in (6, 9, 12, 15):
        allowed = set(ORDER[:k])
        total = same = diff = 0
        for detections in rooms.values():
            kept = [d for d in detections if d["category"] in allowed]
            total += len(kept)
            for a, b in conflict_pairs(kept):
                if destination_of(a["category"]) == destination_of(b["category"]):
                    same += 1
                else:
                    diff += 1
        print(f"{k:<10} {total:<5} {same + diff:<7} {same:<22} {diff:<24}")

    print("\n=== 15개 기준, 다른 목적지끼리 충돌하는 카테고리 쌍 ===")
    counter = Counter()
    for detections in rooms.values():
        for a, b in conflict_pairs(detections):
            if destination_of(a["category"]) != destination_of(b["category"]):
                counter[tuple(sorted((a["category"], b["category"])))] += 1
    for pair, n in counter.most_common():
        print(f"  {pair[0]:14} x {pair[1]:14} {n}쌍  ({destination_of(pair[0])} / {destination_of(pair[1])})")


if __name__ == "__main__":
    main()
