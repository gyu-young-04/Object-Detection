# [merge.py] 겹치는 중복 박스를 정리한다. 외부 도구 없이 순수 계산만 한다.
# 흐름: iou()로 두 박스의 겹침 정도를 계산 -> remove_duplicates()가 그 값으로 중복을 걸러낸다


def iou(a, b):
    # a, b는 [x1, y1, x2, y2]. 두 박스가 겹치는 정도를 0~1 사이로 돌려준다.

    # 겹치는 영역의 왼쪽 위(x1, y1)와 오른쪽 아래(x2, y2) 모서리
    inter_x1 = max(a[0], b[0])
    inter_y1 = max(a[1], b[1])
    inter_x2 = min(a[2], b[2])
    inter_y2 = min(a[3], b[3])

    # 겹친 넓이(안 겹치면 0), 각 박스의 넓이, 합친 넓이(겹친 부분은 한 번만 센다)
    inter = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter

    # 겹침 비율 = 겹친 넓이 / 합친 넓이 (0이면 안 겹침, 1이면 완전히 같은 박스)
    return inter / union if union > 0 else 0.0


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
