# -*- coding: utf-8 -*-
# garment 새 박스 24건의 채점을 저장하고, 충돌 규칙(다른 카테고리와 같은 자리면 점수 높은 쪽만 남김)을 거친 뒤의 결과를 clothes와 비교한다.
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
sys.path.insert(0, os.path.join(ROOT, "src"))
from merge import iou, remove_conflicts

E = os.path.join(ROOT, "docs", "eval")
L = {
    1: ("X", "깔개가 걸린 어두운 궤짝 부분(옷 아님)"), 2: ("X", "바닥의 백팩을 옷으로"), 3: ("X", "바구니 속 신발을 옷으로"),
    4: ("X", "바구니 속 신발을 옷으로"), 5: ("X", "신발이 든 바구니 전체를 옷으로"), 6: ("X", "바구니 속 신발을 옷으로"),
    7: ("X", "의자와 비닐봉지 부분(옷 아님)"), 8: ("X", "꽃무늬 백팩을 옷으로"), 9: ("X", "의자 위 가방들이 든 큰 박스"),
    10: ("X", "의자 위 천 가방을 옷으로"), 11: ("O", "침대 위 회색 맨투맨"), 12: ("O", "침대 위 흰 양말"),
    13: ("X", "검은 백팩을 옷으로(점수 0.87)"), 14: ("X", "사무용 의자를 옷으로"), 15: ("A", "어두운 가방인지 옷 보관 파우치인지 불확실"),
    16: ("A", "어둡고 일부만 보여 확인 어려움"), 17: ("A", "작고 어두워 확인 어려움"), 18: ("X", "흐린 검은 책자를 옷으로"),
    19: ("X", "칠한 가면을 옷으로"), 20: ("A", "작고 회색 천인지 가방인지 구별 어려움"), 21: ("A", "체크 가방 위에 흰 천이 얹혀 혼재"),
    22: ("O", "바닥의 검은 옷 더미"), 23: ("A", "검은 비닐봉지인지 검은 옷인지 불확실"), 24: ("O", "붉은 옷"),
}
index = json.load(open(os.path.join(ROOT, "outputs", "garment_review", "index.json"), encoding="utf-8"))
new_labels = {}  # (photo, id) -> verdict
out_labels = {}
for photo, rows in index.items():
    out_labels[photo] = {}
    for r in rows:
        v, note = L[r["id"]]
        new_labels[(photo, r["id"])] = v
        out_labels[photo][str(r["id"])] = {"v": v, "note": note, "box": r["box"], "score": r["score"]}
json.dump({"labeler": "Claude (이미지 육안 판정, 사용자 검수 전 초안)", "date": "2026-11-23",
           "source": "outputs/clothes_prompts.json 의 garment 박스 중 기존 채점 옷 박스와 위치가 안 맞는 24건 (15장)",
           "labels": out_labels}, open(os.path.join(E, "precision_labels_garment_new24.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("새 박스 24건:", dict(Counter(v for v, _ in L.values())))

# 기존 채점 데이터 (옷 / 옷 아닌 박스)
sets = [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
        ("detections_labeled_set2.json", "precision_labels_set2.json")]
CONTROL = {"web7.webp", "web8.webp"}
gold, others = {}, {}
for dj, lj in sets:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            if d["category"] == "clothes":
                gold.setdefault(name, []).append({"box": d["box"], "v": lab[name][str(i)]["v"], "score": d["score"]})
            else:
                others.setdefault(name, []).append({"category": d["category"], "score": d["score"], "box": d["box"]})
runs = json.load(open(os.path.join(ROOT, "outputs", "clothes_prompts.json"), encoding="utf-8"))["runs"]["garment"]

def verdict_of(photo, box):
    for g in gold.get(photo, []):
        if iou(g["box"], box) > 0.5:
            return g["v"]
    for r in index.get(photo, []):
        if iou(r["box"], box) > 0.99:
            return new_labels[(photo, r["id"])]
    return None

def summary(title, vs):
    c = Counter(vs)
    n = len(vs)
    print(f"{title:44} {n:3}건  O{c['O']:2} P{c['P']:2} A{c['A']:2} X{c['X']:2}  엄격 {(c['O']+c['P'])/n*100:5.1f}%  관대 {(c['O']+c['P']+c['A'])/n*100:5.1f}%  X비율 {c['X']/n*100:4.1f}%")

# 1) garment 박스 전체(충돌 규칙 전)
all_g = [verdict_of(p, b["box"]) for p, bs in runs.items() for b in bs]
print("채점 안 된 garment 박스:", sum(1 for v in all_g if v is None), "건 (기존 옷 박스와 위치가 안 맞고 새 24건에도 없는 것)")
summary("garment 전체 (충돌 규칙 전)", [v for v in all_g if v])

# 2) 충돌 규칙 적용 후
surv = []
for p, bs in runs.items():
    dets = [{"category": "garment", "score": b["score"], "box": b["box"]} for b in bs] + [dict(o) for o in others.get(p, [])]
    for d in remove_conflicts(dets, 0.7):
        if d["category"] == "garment":
            surv.append(verdict_of(p, d["box"]))
summary("garment 충돌 규칙 후", [v for v in surv if v])
print("   (충돌 규칙으로 지워진 garment 박스:", len(all_g) - len(surv), "건)")

# 3) 기준: 현재 clothes (기존 채점 79건, 이미 충돌 규칙을 거친 상태)
summary("clothes 현재 (기준)", [g["v"] for gs in gold.values() for g in gs])
