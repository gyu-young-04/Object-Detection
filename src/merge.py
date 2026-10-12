# [merge.py] 겹치는 박스를 정리한다. 외부 도구 없이 순수 계산만 한다.
# 흐름: 겹침 계산(iou, inside_ratio) -> remove_duplicates(같은 물건의 중복 제거)
#                                  -> remove_nested(큰 덩어리 안에 포개진 작은 박스 제거)


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
