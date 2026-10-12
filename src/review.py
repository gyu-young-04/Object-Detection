# [review.py] 정밀도를 사람이 확인할 수 있도록, 탐지 박스에 번호를 붙인 검수용 이미지를 만든다.
# 흐름: 탐지 결과 JSON 읽기 -> 사진 확대 -> 박스마다 "#번호 한글이름" 그리기 -> outputs/review_*.jpg 저장
# 실행 예: python src\review.py detections_400_nocontain.json
import json
import os
import sys

from PIL import Image, ImageDraw

from rules import CATEGORY_INFO
from visualize import PALETTE, load_font

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")


def main(json_name):
    with open(os.path.join(OUT_DIR, json_name), encoding="utf-8") as f:
        data = json.load(f)

    categories = list(CATEGORY_INFO)
    for name, result in data.items():
        image = Image.open(os.path.join(DATA_DIR, name)).convert("RGB")

        # 작은 사진은 짧은 변이 900px이 되도록 확대해서 박스가 잘 보이게 한다
        scale = max(1.0, 900 / min(image.size))
        image = image.resize((round(image.width * scale), round(image.height * scale)))
        draw = ImageDraw.Draw(image)
        font = load_font(max(16, round(min(image.size) / 28)))

        print(f"\n{name}")
        for number, d in enumerate(result["detections"], 1):
            x1, y1, x2, y2 = [v * scale for v in d["box"]]
            color = PALETTE[categories.index(d["category"]) % len(PALETTE)]
            draw.rectangle([x1, y1, x2, y2], outline=color, width=4)

            text = f"#{number} {d['label_ko']}"
            left, top, right, bottom = draw.textbbox((x1, y1), text, font=font)
            draw.rectangle([left, top, right, bottom], fill=color)
            draw.text((x1, y1), text, fill="white", font=font)
            print(f"  #{number:<2} {d['category']:8} {d['score']:.2f}  {[round(v) for v in d['box']]}")

        out_name = f"review_{os.path.splitext(name)[0]}.jpg"
        image.save(os.path.join(OUT_DIR, out_name))


if __name__ == "__main__":
    main(sys.argv[1])
