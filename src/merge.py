# [merge.py] 겹치는 박스를 정리하고, 여러 사진의 결과를 합친다. 외부 도구 없이 순수 계산만 한다.
# 흐름: 겹침 계산(iou, inside_ratio) -> remove_duplicates(같은 물건의 중복 제거)
#                                  -> remove_nested(큰 덩어리 안에 포개진 작은 박스 제거)
#                                  -> remove_conflicts(카테고리가 다른데 같은 위치인 박스 정리)
#       merge_photos: 같은 방을 여러 각도로 찍은 사진들의 결과를 하나로 합친다(합집합)


def box_area(box):
    # box는 [x1, y1, x2, y2]. 박스의 넓이
    return (box[2] - box[0]) * (box[3] - box[1])


def intersection_area(a, b):
    # 두 박스가 겹치는 영역의 넓이 (안 겹치면 0)
    inter_x1 = max(a[0], b[0])
    inter_y1 = max(a[1], b[1])
    inter_x2 = min(a[2], b[2])
    inter_y2 = min(a[3], b[3])
    return max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)


def iou(a, b):
    # 두 박스가 겹치는 정도를 0~1 사이로 돌려준다.
    # 겹침 비율 = 겹친 넓이 / 합친 넓이 (0이면 안 겹침, 1이면 완전히 같은 박스)
    inter = intersection_area(a, b)
    union = box_area(a) + box_area(b) - inter
    return inter / union if union > 0 else 0.0


def inside_ratio(inner, outer):
    # inner 박스가 outer 박스 안에 얼마나 들어 있는지 0~1 (1이면 완전히 안에 있음)
    return intersection_area(inner, outer) / box_area(inner)


def remove_duplicates(detections, iou_threshold=0.5):
    # 점수가 높은 것부터 살펴보면서, 이미 남긴 같은 카테고리 박스와 많이 겹치면 중복으로 보고 버린다.

    # 남기기로 한 박스들을 담는 목록
    kept = []
    # 점수 높은 순으로 하나씩 확인
    for d in sorted(detections, key=lambda d: d["score"], reverse=True):
        duplicate = False
        # 이미 남긴 박스 중에 같은 카테고리이면서 많이 겹치는 게 있으면 중복 표시 후 확인 중단
        for k in kept:
            if k["category"] == d["category"] and iou(k["box"], d["box"]) > iou_threshold:
                duplicate = True
                break
        # 중복이 아닐 때만 남긴다
        if not duplicate:
            kept.append(d)
    return kept


def remove_nested(detections, contain_ratio=0.8):
    # 같은 카테고리에서, 어떤 박스의 contain_ratio 이상이 더 큰 박스 안에 들어 있으면 그 작은 박스를 버린다.
    # 옷더미처럼 큰 덩어리 안의 개별 박스를 없애고 "덩어리 단위"로 안내하기 위한 규칙이다.
    kept = []
    for d in detections:
        nested = False
        for other in detections:
            if other is d or other["category"] != d["category"]:
                continue
            # 더 큰 박스이고, d가 그 안에 충분히 들어 있으면 d는 포개진 박스
            if box_area(other["box"]) > box_area(d["box"]) and inside_ratio(d["box"], other["box"]) >= contain_ratio:
                nested = True
                break
        if not nested:
            kept.append(d)
    return kept


def remove_conflicts(detections, iou_threshold=0.7):
    # 카테고리가 다른데 거의 같은 위치에 겹친 박스는, 같은 물건을 서로 다른 이름으로 부른 것으로 보고
    # 점수가 높은 쪽만 남긴다. (카테고리 우선순위로 정하는 것보다 점수로 정하는 쪽이 나았다: docs/devlog.md)
    kept = []
    for d in sorted(detections, key=lambda d: d["score"], reverse=True):
        conflict = False
        for k in kept:
            if k["category"] != d["category"] and iou(k["box"], d["box"]) > iou_threshold:
                conflict = True
                break
        if not conflict:
            kept.append(d)
    # 원래 순서(카테고리 우선순위 순)를 유지해서 돌려준다. id()는 "같은 객체인지" 구분하는 번호
    kept_ids = {id(d) for d in kept}
    return [d for d in detections if id(d) in kept_ids]


def merge_photos(results_by_photo, photo_names):
    # 같은 방을 여러 각도로 찍은 사진들의 탐지 결과를 하나의 목록으로 합친다(합집합).
    # 사진마다 좌표계가 달라서 박스끼리 비교하지 않고 그대로 이어붙인다.
    # 그래서 같은 물건이 두 사진에 함께 찍혔다면 두 번 집계될 수 있다. (잘못 합치는 것보다 안전한 쪽을 택한 것)
    merged = []
    for name in photo_names:
        merged += results_by_photo[name]
    return merged
