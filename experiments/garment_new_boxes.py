# -*- coding: utf-8 -*-
# garment로 새로 잡힌 박스(기존 채점 옷 박스와 위치가 안 맞는 것)를 사진 위에 번호로 그려서 채점용 이미지를 만든다.
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou

OUT = os.path.join(ROOT, "outputs", "garment_review")
os.makedirs(OUT, exist_ok=True)
data = json.load(open(os.path.join(ROOT, "outputs", "clothes_prompts.json"), encoding="utf-8"))
gold, runs = data["gold"], data["runs"]["garment"]

new = {}  # photo -> [(번호, score, box)]
n = 0
for photo, boxes in runs.items():
    gs = gold.get(photo, [])
    rows = []
    for b in boxes:
        if b["score"] < 0.30:
            continue
        if any(iou(g["box"], b["box"]) > 0.5 for g in gs):
            continue
        n += 1
        rows.append((n, b["score"], b["box"]))
    if rows:
        new[photo] = rows

font_path = r"C:\Windows\Fonts\malgun.ttf"
index = {}
for photo, rows in new.items():
    img = Image.open(os.path.join(ROOT, "data", photo)).convert("RGB")
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font_path, max(14, round(min(img.size) / 30)))
    w = max(2, round(min(img.size) / 200))
    for num, score, box in rows:
        d.rectangle(box, outline=(230, 57, 70), width=w)
        t = f"#{num} {score:.2f}"
        l, tp, r, bt = d.textbbox((box[0], box[1]), t, font=f)
        d.rectangle([l, tp, r, bt], fill=(230, 57, 70))
        d.text((box[0], box[1]), t, fill="white", font=f)
    name = os.path.splitext(photo)[0] + "_garment_new.jpg"
    img.save(os.path.join(OUT, name))
    index[photo] = [{"id": num, "score": s, "box": b} for num, s, b in rows]
    print(f"{photo}: 새 박스 {len(rows)}건  번호 {rows[0][0]}~{rows[-1][0]}  -> {name}")
json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("합계 새 박스", n, "건 /", len(new), "장")
