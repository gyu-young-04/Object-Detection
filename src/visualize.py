# [visualize.py] 탐지 결과(박스, 라벨, 점수)를 사진 위에 그려서 눈으로 확인할 수 있게 한다.
# 흐름: 사진 복사 -> 박스마다 (테두리 -> 라벨 배경 -> 라벨 글씨) 그리기 -> 완성된 사진 반환
from PIL import ImageDraw, ImageFont  # 사진 위에 도형과 글씨를 그리는 도구 (Pillow)

# 카테고리별로 돌려 쓸 색 목록. (빨강, 초록, 파랑) 순서의 RGB 값
PALETTE = [
    (230, 57, 70),
    (29, 111, 219),
    (42, 157, 143),
    (244, 162, 97),
    (131, 56, 236),
    (6, 214, 160),
    (255, 190, 11),
    (251, 86, 7),
    (58, 134, 255),
    (141, 153, 174),
]
# 요청하지 않은 이상한 라벨이 나왔을 때 쓰는 회색
UNKNOWN_COLOR = (110, 110, 110)


def color_for(category, categories):
    # 우리가 요청한 카테고리면 순서대로 색을 주고, 모델이 엉뚱한 라벨을 내면 회색으로 표시한다.
    if category in categories:
        return PALETTE[categories.index(category) % len(PALETTE)]
    return UNKNOWN_COLOR


def draw_detections(image, detections, categories):
    # 원본은 건드리지 않도록 복사본 위에 그린다 (draw가 그리는 "펜")
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)

    # 사진 크기에 비례해서 선 굵기와 글자 크기를 정한다 (너무 작아지지 않게 최소값 보장)
    short_side = min(canvas.size)
    line_width = max(2, round(short_side / 200))
    font = ImageFont.load_default(size=max(12, round(short_side / 40)))

    # 탐지된 박스를 하나씩 그린다
    for d in detections:
        # (x1, y1) = 박스 왼쪽 위, (x2, y2) = 오른쪽 아래
        x1, y1, x2, y2 = d["box"]
        color = color_for(d["category"], categories)

        # 1) 박스 테두리
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        # 2) 라벨("카테고리 점수") 글씨가 차지할 영역을 계산해서 색 배경을 깐다
        text = f'{d["category"]} {d["score"]:.2f}'
        left, top, right, bottom = draw.textbbox((x1, y1), text, font=font)
        draw.rectangle([left, top, right, bottom], fill=color)
        # 3) 그 위에 흰 글씨를 쓴다
        draw.text((x1, y1), text, fill="white", font=font)

    # 박스가 그려진 사진을 돌려준다
    return canvas
