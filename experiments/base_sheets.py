# -*- coding: utf-8 -*-
# base에서만 나온 새 박스 71건을 잘라서 모음 이미지(12칸씩)로 만든다. 박스 주변을 조금 넓게 잘라 맥락이 보이게 한다.
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
OUT = os.path.join(ROOT, "outputs", "base_review")
os.makedirs(OUT, exist_ok=True)
KO = {"clothes": "옷", "book": "책", "bag": "가방", "bottle": "병", "shoes": "신발", "box": "상자"}
items = json.load(open(os.path.join(ROOT, "outputs", "base_new_boxes.json"), encoding="utf-8"))
items.sort(key=lambda d: (d["photo"], d["box"][1], d["box"][0]))
for i, d in enumerate(items, 1):
    d["id"] = i
json.dump(items, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 22)
CW, CH, HEAD = 400, 330, 30  # 칸 크기와 머리글 높이
COLS, ROWS = 4, 3
per_sheet = COLS * ROWS
for s in range(0, len(items), per_sheet):
    chunk = items[s:s + per_sheet]
    sheet = Image.new("RGB", (COLS * CW, ROWS * CH), (245, 245, 245))
    dr = ImageDraw.Draw(sheet)
    for k, d in enumerate(chunk):
        img = Image.open(os.path.join(ROOT, "data", d["photo"])).convert("RGB")
        x1, y1, x2, y2 = d["box"]
        pw, ph = (x2 - x1) * 0.15 + 12, (y2 - y1) * 0.15 + 12
        cx1, cy1, cx2, cy2 = max(0, x1 - pw), max(0, y1 - ph), min(img.width, x2 + pw), min(img.height, y2 + ph)
        crop = img.crop((int(cx1), int(cy1), int(cx2), int(cy2)))
        sc = min((CW - 8) / crop.width, (CH - HEAD - 8) / crop.height)
        crop = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))))
        cd = ImageDraw.Draw(crop)
        cd.rectangle([(x1 - cx1) * sc, (y1 - cy1) * sc, (x2 - cx1) * sc, (y2 - cy1) * sc], outline=(230, 57, 70), width=3)
        ox, oy = (k % COLS) * CW, (k // COLS) * CH
        sheet.paste(crop, (ox + 4, oy + HEAD + 4))
        dr.rectangle([ox, oy, ox + CW - 1, oy + HEAD - 1], fill=(40, 40, 40))
        dr.text((ox + 6, oy + 2), f"#{d['id']} {KO[d['category']]} {d['score']:.2f}", fill="white", font=font)
        dr.rectangle([ox, oy, ox + CW - 1, oy + CH - 1], outline=(180, 180, 180))
    name = f"sheet_{s // per_sheet + 1}.jpg"
    sheet.save(os.path.join(OUT, name), quality=88)
    print(name, f"#{chunk[0]['id']}~#{chunk[-1]['id']}")
print("합계", len(items), "건")
