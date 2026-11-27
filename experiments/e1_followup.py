# -*- coding: utf-8 -*-
# E1 후속: (1) 흡수용 후보 조합별 효과와 시간 비용, (2) 지워진 맞는 박스가 무엇인지, (3) 정리 대상 확장 후보의 생존 박스를 잘라 모음 이미지로 만든다.
import json
import os
import statistics
import sys
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
e1 = json.load(open(os.path.join(ROOT, "outputs", "detections_e1.json"), encoding="utf-8"))
tiny = {}
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        tiny[name] = [{"category": d["category"], "score": d["score"], "box": d["box"], "v": "OP" if lab[name][str(i)]["v"] in "OP" else lab[name][str(i)]["v"],
                       "note": lab[name][str(i)].get("note", ""), "photo": name} for i, d in enumerate(r["detections"], 1)]

def run(cands, thr=0.7):
    kept_old, lost_old, survivors = Counter(), Counter(), []
    lost_ok = []
    for name, ts in tiny.items():
        dets = [dict(t, kind="old") for t in ts]
        for c in cands:
            for b in e1[name]["boxes"][c]:
                dets.append({"category": c, "score": b["score"], "box": b["box"], "kind": "new", "photo": name})
        out = remove_conflicts(dets, thr)
        ids = {id(d) for d in out}
        for d in dets:
            if d["kind"] == "old":
                if id(d) in ids:
                    kept_old[d["v"]] += 1
                else:
                    lost_old[d["v"]] += 1
                    if d["v"] == "OP":
                        lost_ok.append(d)
            elif id(d) in ids:
                survivors.append(d)
    return kept_old, lost_old, survivors, lost_ok

base_op, base_x = 131, 42
print("[흡수용 조합별 효과] 후보 수 -> 추가 시간(후보 하나당 약 4초 가정, 사진당)")
print(f"{'조합':40} {'지워진 틀림':>9} {'지워진 맞음':>10} {'엄격 정밀도':>10} {'추가 시간':>8}")
combos = [["cushion"], ["cushion", "blanket"], ["cushion", "blanket", "basket"], ["cushion", "blanket", "basket", "chair"],
          ["cushion", "blanket", "basket", "chair", "picture frame", "phone"]]
for cm in combos:
    ko, lo, _, _ = run(cm)
    n = sum(ko.values())
    print(f"{' + '.join(cm):40} {lo['X']:5}/{base_x} {lo['OP']:7}/{base_op} {ko['OP'] / n * 100:9.1f}% {len(cm) * 4:6}초")

ko, lo, surv, lost_ok = run(["cushion", "blanket", "basket", "chair", "picture frame", "phone"])
print("\n[6개 모두 썼을 때 지워진 '맞는 박스' 6건]")
for d in lost_ok:
    print(f"  {d['photo']} {d['category']} 점수 {d['score']:.2f}: {d['note']}")

# 정리 대상 확장 후보의 생존 박스를 모음 이미지로
_, _, surv, _ = run(["cup", "bowl", "glass jar"])
surv = [d for d in surv]
surv.sort(key=lambda d: (d["category"], d["photo"], d["box"][1]))
for i, d in enumerate(surv, 1):
    d["id"] = i
os.makedirs(os.path.join(ROOT, "outputs", "e1_review"), exist_ok=True)
json.dump([{k: d[k] for k in ("id", "photo", "category", "score", "box")} for d in surv],
          open(os.path.join(ROOT, "outputs", "e1_review", "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
KO = {"cup": "컵", "bowl": "그릇", "glass jar": "유리병"}
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
        dr.text((ox + 6, oy + 2), f"#{d['id']} {KO[d['category']]} {d['score']:.2f}", fill="white", font=font)
        dr.rectangle([ox, oy, ox + CW - 1, oy + CH - 1], outline=(180, 180, 180))
    sheet.save(os.path.join(ROOT, "outputs", "e1_review", f"sheet_{s // per + 1}.jpg"), quality=88)
print("\n정리 대상 확장 후보 생존 박스", len(surv), "건 -> 모음 이미지", (len(surv) + per - 1) // per, "장 (outputs/e1_review)")
print("카테고리별:", dict(Counter(KO[d['category']] for d in surv)))
