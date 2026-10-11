def iou(a, b):
    # a, b는 [x1, y1, x2, y2]. 두 박스가 겹치는 정도를 0~1 사이로 돌려준다.
    inter_x1 = max(a[0], b[0])
    inter_y1 = max(a[1], b[1])
    inter_x2 = min(a[2], b[2])
    inter_y2 = min(a[3], b[3])

    inter = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter

    return inter / union if union > 0 else 0.0


def remove_duplicates(detections, iou_threshold=0.5):
    # 점수가 높은 것부터 살펴보면서, 이미 남긴 같은 카테고리 박스와 많이 겹치면 중복으로 보고 버린다.
    kept = []
    for d in sorted(detections, key=lambda d: d["score"], reverse=True):
        duplicate = False
        for k in kept:
            if k["category"] == d["category"] and iou(k["box"], d["box"]) > iou_threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(d)
    return kept
