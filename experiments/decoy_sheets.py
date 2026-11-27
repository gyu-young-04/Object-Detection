# -*- coding: utf-8 -*-
# 살아남은 미끼 박스 117건을 번호를 붙인 모음 이미지로 만든다(채점용). 카테고리, 점수 높은 순으로 정렬.
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
e1 = json.load(open(os.path.join(ROOT, "outputs", "detections_e1.json"), encoding="utf-8"))
e1b = json.load(open(os.path.join(ROOT, "outputs", "detections_e1b.json"), encoding="utf-8"))
DECOYS = ["cushion", "blanket", "comforter", "pillow", "shelf"]


def boxes(name, k):
    for src in (e1, e1b):
        if k in src[name]["boxes"]:
            return src[name]["boxes"][k]


tiny = {}
for dj in ["detections_labeled.json", "detections_labeled_new20.json", "detections_labeled_set2.json"]:
    for name, r in json.load(open(os.path.join(E, dj), encoding="utf-8")).items():
        if name not in CONTROL:
            tiny[name] = r["detections"]
surv = []
for name, ts in tiny.items():
    dets = [{"category": t["category"], "score": t["score"], "box": t["box"], "photo": name, "core": True} for t in ts]
    for k in DECOYS:
        for b in boxes(name, k):
            dets.append({"category": k, "score": b["score"], "box": b["box"], "photo": name, "core": False})
    surv += [d for d in remove_conflicts(dets, 0.7) if not d["core"]]
surv.sort(key=lambda d: (DECOYS.index(d["category"]), -d["score"]))
for i, d in enumerate(surv, 1):
    d["id"] = i
out = os.path.join(ROOT, "outputs", "decoy_review")
os.makedirs(out, exist_ok=True)
json.dump([{k: d[k] for k in ("id", "photo", "category", "score", "box")} for d in surv], open(os.path.join(out, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 22)
CW, CH, HEAD, COLS, ROWS = 400, 330, 30, 4, 3
per = COLS * ROWS
for s in range(0, len(surv), per):
    chunk = surv[s:s + per]
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
        ImageDraw.Draw(crop).rectangle([(x1 - cx1) * sc, (y1 - cy1) * sc, (x2 - cx1) * sc, (y2 - cy1) * sc], outline=(230, 57, 70), width=3)
        ox, oy = (k % COLS) * CW, (k // COLS) * CH
        sheet.paste(crop, (ox + 4, oy + HEAD + 4))
        dr.rectangle([ox, oy, ox + CW - 1, oy + HEAD - 1], fill=(40, 40, 40))
        dr.text((ox + 6, oy + 2), f"#{d['id']} {d['category']} {d['score']:.2f}", fill="white", font=font)
        dr.rectangle([ox, oy, ox + CW - 1, oy + CH - 1], outline=(180, 180, 180))
    sheet.save(os.path.join(out, f"sheet_{s // per + 1}.jpg"), quality=88)
print(len(surv), "건 ->", (len(surv) + per - 1) // per, "장")
for c in DECOYS:
    print(c, [d["id"] for d in surv if d["category"] == c][0], "~", [d["id"] for d in surv if d["category"] == c][-1])
