# [rules.py] 탐지된 물건에 "어디로 보낼지"(목적지)를 붙이고, 목적지별로 묶어서 안내문을 만든다.
# 흐름: attach_destination(목적지 붙이기) -> group_by_destination(목적지별로 묶기) -> summarize(안내문 만들기)
# 아래 표의 목적지는 일반적인 기본값이다. (사용자가 고치는 기능은 이후에 만든다)

# 카테고리(모델에 묻는 영어 단어) -> 화면에 보일 한글 이름, 기본 목적지, 이유 문장
CATEGORY_INFO = {
    "clothes": {"ko": "옷", "destination": "옷장", "reason": "옷은 옷장에 보관하는 게 일반적입니다"},
    "book": {"ko": "책", "destination": "책장", "reason": "책은 책장에 꽂아두는 게 일반적입니다"},
    "bag": {"ko": "가방", "destination": "가방 걸이", "reason": "가방은 걸이나 정해진 자리에 둡니다"},
    "bottle": {"ko": "병", "destination": "분리수거", "reason": "빈 병이라면 분리수거로 보냅니다"},
    "shoes": {"ko": "신발", "destination": "신발장", "reason": "신발은 신발장에 보관합니다"},
    "box": {"ko": "상자", "destination": "수납함", "reason": "상자는 수납하거나 정리해 둡니다"},
}
# 표에 없는 카테고리가 나왔을 때 쓰는 목적지
UNKNOWN_DESTINATION = "기타"

# 목적지 목록 (표의 순서대로, 중복 없이). 박스 색을 목적지별로 칠할 때 쓴다.
DESTINATIONS = []
for _info in CATEGORY_INFO.values():
    if _info["destination"] not in DESTINATIONS:
        DESTINATIONS.append(_info["destination"])
DESTINATIONS.append(UNKNOWN_DESTINATION)


def attach_destination(detections):
    # 탐지 결과마다 한글 이름(label_ko), 목적지(destination), 이유(reason)를 덧붙인다
    for d in detections:
        info = CATEGORY_INFO.get(d["category"])
        if info is None:
            d["label_ko"] = d["category"]
            d["destination"] = UNKNOWN_DESTINATION
            d["reason"] = ""
        else:
            d["label_ko"] = info["ko"]
            d["destination"] = info["destination"]
            d["reason"] = info["reason"]


def group_by_destination(detections):
    # {"옷장": [탐지1, 탐지2], "책장": [...]} 형태로 목적지별로 묶는다
    groups = {}
    for d in detections:
        if d["destination"] not in groups:
            groups[d["destination"]] = []
        groups[d["destination"]].append(d)
    return groups


def summarize(groups):
    # 목적지별 안내문을 글줄 목록으로 만든다
    lines = []
    for destination, items in groups.items():
        lines.append(f"[{destination}] {len(items)}건")
        # 이 목적지로 가는 물건을 종류별로 세어서 한 줄씩 적는다
        counts = {}
        for d in items:
            counts[d["category"]] = counts.get(d["category"], 0) + 1
        for category, n in counts.items():
            info = CATEGORY_INFO.get(category)
            if info is None:
                lines.append(f"    {category} x{n}")
            else:
                lines.append(f"    {info['ko']} x{n}  - {info['reason']}")
    return lines
