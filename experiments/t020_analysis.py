# -*- coding: utf-8 -*-
# 0.20 실험 분석: (1) 0.30 이상 박스가 기존 결과와 같은지 확인, (2) 0.20~0.30 구간의 새 박스 수를 세고, (3) 채점용 모음 이미지를 만든다.
import json
import os
import random
import sys
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou, remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
t020 = json.load(open(os.path.join(ROOT, "outputs", "detections_t020.json"), encoding="utf-8"))
tiny = {}
for dj in ["detections_labeled.json", "detections_labeled_new20.json", "detections_labeled_set2.json"]:
    for name, r in json.load(open(os.path.join(E, dj), encoding="utf-8")).items():
        if name not in CONTROL:
            tiny[name] = r["detections"]

surv = []
for name, r in t020.items():
    dets = [{"category": c, "score": b["score"], "box": b["box"], "photo": name} for c in CATS for b in r["boxes"][c]]
    surv += remove_conflicts(dets, 0.7)
hi = [d for d in surv if d["score"] >= 0.30]
lo = [d for d in surv if d["score"] < 0.30]
old_n = sum(len(v) for v in tiny.values())
matched = sum(1 for d in hi if any(o["category"] == d["category"] and iou(o["box"], d["box"]) > 0.9 for o in tiny[d["photo"]]))
print(f"0.30 이상: 이번 {len(hi)}건 / 기존 {old_n}건, 기존 박스와 같은 것 {matched}건")
b1 = [d for d in lo if d["score"] >= 0.25]
b2 = [d for d in lo if d["score"] < 0.25]
print(f"새 박스: 0.25~0.30 {len(b1)}건, 0.20~0.25 {len(b2)}건 (합계 {len(lo)}건)")
print("  카테고리별 0.25~0.30:", dict(Counter(d["category"] for d in b1)))
print("  카테고리별 0.20~0.25:", dict(Counter(d["category"] for d in b2)))
print(f"사진당 시간 중앙값: {sorted(r['seconds'] for r in t020.values())[len(t020) // 2]:.0f}초")

random.seed(11)
s1 = random.sample(b1, 60) if len(b1) > 60 else b1  # 0.25~0.30 구간에서 60건
s2 = random.sample(b2, 30) if len(b2) > 30 else b2  # 0.20~0.25 구간에서 30건
for d in s1:
    d["band"] = "0.25-0.30"
for d in s2:
    d["band"] = "0.20-0.25"
sample = s1 + s2
sample.sort(key=lambda d: (d["band"] != "0.25-0.30", d["photo"], d["box"][1]))
for i, d in enumerate(sample, 1):
    d["id"] = i
out = os.path.join(ROOT, "outputs", "t020_review")
os.makedirs(out, exist_ok=True)
json.dump([{k: d[k] for k in ("id", "photo", "category", "score", "box", "band")} for d in sample], open(os.path.join(out, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
KO = {"clothes": "옷", "book": "책", "bag": "가방", "bottle": "병", "shoes": "신발", "box": "상자"}
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 22)
CW, CH, HEAD, COLS, ROWS = 400, 330, 30, 4, 3
per = COLS * ROWS
for s in range(0, len(sample), per):
    chunk = sample[s:s + per]
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
        dr.text((ox + 6, oy + 2), f"#{d['id']} {KO[d['category']]} {d['score']:.2f}", fill="white", font=font)
        dr.rectangle([ox, oy, ox + CW - 1, oy + CH - 1], outline=(180, 180, 180))
    sheet.save(os.path.join(out, f"sheet_{s // per + 1}.jpg"), quality=88)
print(f"채점용 박스 {len(sample)}건 (0.25~0.30 무작위 {len(s1)}건 + 0.20~0.25 무작위 {len(s2)}건) -> 모음 이미지 {(len(sample) + per - 1) // per}장")
