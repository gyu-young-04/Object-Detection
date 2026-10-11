from PIL import ImageDraw, ImageFont

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
UNKNOWN_COLOR = (110, 110, 110)


def color_for(category, categories):
    # 우리가 요청한 카테고리면 순서대로 색을 주고, 모델이 엉뚱한 라벨을 내면 회색으로 표시한다.
    if category in categories:
        return PALETTE[categories.index(category) % len(PALETTE)]
    return UNKNOWN_COLOR


def draw_detections(image, detections, categories):
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    short_side = min(canvas.size)
    line_width = max(2, round(short_side / 200))
    font = ImageFont.load_default(size=max(12, round(short_side / 40)))

    for d in detections:
        x1, y1, x2, y2 = d["box"]
        color = color_for(d["category"], categories)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        text = f'{d["category"]} {d["score"]:.2f}'
        left, top, right, bottom = draw.textbbox((x1, y1), text, font=font)
        draw.rectangle([left, top, right, bottom], fill=color)
        draw.text((x1, y1), text, fill="white", font=font)

    return canvas
