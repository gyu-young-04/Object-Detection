# [evaluate.py] 사람이 붙인 판정(O/P/X/A)으로 정밀도를 계산한다.
# 흐름: 탐지 결과 JSON + 판정 JSON 읽기 -> (포개짐 제거 끈 설정 / 켠 설정) 각각 집계 -> 표로 출력
# 실행 예: python src\evaluate.py
import json
import os
import random

from merge import iou, remove_nested

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DETECTIONS = os.path.join(ROOT, "outputs", "detections_400_nocontain.json")
LABELS = os.path.join(ROOT, "docs", "eval", "precision_labels.json")
CONTROL_PHOTOS = {"web7.webp", "web8.webp"}  # 어지럽지 않은 작업실 (대조군)


def load():
    # 탐지 결과에 판정(verdict)과 번호(id)를 붙여서 {사진: [탐지...]} 로 돌려준다
    with open(DETECTIONS, encoding="utf-8") as f:
        detections = json.load(f)
    with open(LABELS, encoding="utf-8") as f:
        labels = json.load(f)["labels"]

    data = {}
    for name, result in detections.items():
        items = []
        for number, d in enumerate(result["detections"], 1):
            d["id"] = number
            d["photo"] = name
            d["verdict"] = labels[name][str(number)]["v"]
            items.append(d)
        data[name] = items
    return data


def apply_contain(data):
    # 파이프라인과 같은 방식(카테고리별로 remove_nested)으로 포개진 박스를 지운 결과를 만든다
    result = {}
    for name, items in data.items():
        kept = []
        for category in sorted({d["category"] for d in items}):
            group = [d for d in items if d["category"] == category]
            kept += remove_nested(group, 0.8)
        result[name] = kept
    return result


def flatten(data, exclude=()):
    return [d for name, items in data.items() if name not in exclude for d in items]


def rate(count, total):
    return f"{count}/{total} = {count / total * 100:4.1f}%" if total else "-"


def report(title, items):
    n = len(items)
    count = {v: sum(1 for d in items if d["verdict"] == v) for v in "OPXA"}
    print(f"\n=== {title} (박스 {n}건) ===")
    print(f"판정: O {count['O']}  P(제자리) {count['P']}  A(애매) {count['A']}  X(틀림) {count['X']}")
    print(f"탐지 정밀도 (카테고리가 맞음)  엄격 (O+P)    : {rate(count['O'] + count['P'], n)}")
    print(f"                               관대 (O+P+A)  : {rate(count['O'] + count['P'] + count['A'], n)}")
    print(f"유효 안내율 (맞고 정리가 필요)  엄격 (O)      : {rate(count['O'], n)}")
    print(f"                               관대 (O+A)    : {rate(count['O'] + count['A'], n)}")
    print(f"불필요 안내 비율 (이미 제자리)  P             : {rate(count['P'], n)}")

    print("카테고리별  (건수 / O P A X / 엄격 정밀도 / 관대 정밀도)")
    for category in ["clothes", "book", "bag", "bottle", "shoes", "box"]:
        sub = [d for d in items if d["category"] == category]
        if not sub:
            continue
        c = {v: sum(1 for d in sub if d["verdict"] == v) for v in "OPXA"}
        m = len(sub)
        print(f"  {category:8} {m:3}건   O{c['O']:2} P{c['P']:2} A{c['A']:2} X{c['X']:2}   "
              f"{(c['O'] + c['P']) / m * 100:5.1f}%   {(c['O'] + c['P'] + c['A']) / m * 100:5.1f}%")


def conflicts(data):
    # 서로 다른 카테고리인데 거의 같은 위치(IoU 0.7 초과)에 있는 박스 쌍
    pairs = []
    for name, items in data.items():
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a["category"] != b["category"] and iou(a["box"], b["box"]) > 0.7:
                    pairs.append((name, a, b))
    return pairs


def main():
    data = load()
    contained = apply_contain(data)

    report("포개짐 제거 끔: 어지러운 방 8곳", flatten(data, CONTROL_PHOTOS))
    report("포개짐 제거 켬: 어지러운 방 8곳", flatten(contained, CONTROL_PHOTOS))

    control = flatten(data, exclude=[n for n in data if n not in CONTROL_PHOTOS])
    print(f"\n=== 대조군(정리된 작업실 2장) ===\n탐지 {len(control)}건 -> 판정 {[d['verdict'] for d in control]}")

    pairs = conflicts(data)
    print(f"\n=== 카테고리가 다른데 같은 위치에 겹친 박스 쌍: {len(pairs)}쌍 ===")
    for name, a, b in pairs:
        print(f"  {name:10} #{a['id']} {a['category']}({a['verdict']}) vs #{b['id']} {b['category']}({b['verdict']})")

    # 사용자가 직접 확인할 표본: 판정이 O 또는 X인 박스 중 무작위 12건 (매번 같은 결과가 나오도록 seed 고정)
    random.seed(1)
    pool = [d for d in flatten(data) if d["verdict"] in ("O", "X", "P")]
    print("\n=== 사용자 검수용 표본 12건 (outputs/review_사진이름.jpg 의 #번호를 보고 판정이 맞는지 확인) ===")
    for d in sorted(random.sample(pool, 12), key=lambda d: (d["photo"], d["id"])):
        print(f"  {d['photo']:10} #{d['id']:<2} {d['category']:8} 내 판정: {d['verdict']}")


if __name__ == "__main__":
    main()
