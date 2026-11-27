# -*- coding: utf-8 -*-
# 틀림(X)/애매(A) 박스 메모를 유형으로 분류해서 카테고리별로 센다. 규칙은 위에서부터 먼저 맞는 것을 쓴다.
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트 (experiments 폴더의 한 단계 위)
E = os.path.join(ROOT, "docs", "eval")
CONTROL = {"web7.webp", "web8.webp"}
CATS = ["clothes", "book", "bag", "bottle", "shoes", "box"]
KO = {"clothes": "옷", "book": "책", "bag": "가방", "bottle": "병", "shoes": "신발", "box": "상자"}

# (유형 이름, 메모에 들어 있으면 이 유형으로 보는 단어들)
RULES = [
    ("크기·가림: 너무 작거나 일부만 보임", ["너무 작", "작아서", "작은 ", "작음", "겹쳐 있어", "겹치거나", "어둡", "가려짐", "확인 불가", "확인 어려움", "경계 불명", "작으나"]),
    ("덩어리: 여러 물건이 한 박스에 섞임", ["섞인", "섞임", "전체", "섞여", "사진 전체"]),
    ("침구·쿠션·천류를 옷으로 (이불, 담요, 쿠션, 베개, 수건, 천, 소파)", ["이불", "담요", "쿠션", "베개", "수건", "천", "소파", "시트", "비닐", "봉지", "커튼"]),
    ("가방·쇼핑백을 다른 이름으로 (가방, 토트백, 쇼핑백, 파우치)", ["책가방", "토트백", "가방", "쇼핑백", "파우치", "필통"]),
    ("책·종이·서류를 다른 이름으로 (책 더미, 종이, 파일, 노트북)", ["책 더미", "서가", "종이", "파일", "노트북", "수첩", "인쇄물", "골판지 트레이", "상자를 책"]),
    ("가구·수납용품을 상자로 (서랍, 선반, 바구니, 캐비닛, 건조대, 액자)", ["서랍", "선반", "바구니", "캐비닛", "건조대", "액자", "탁자", "수납", "궤짝", "통을", "용기", "정리함", "골판지 판", "스피커"]),
]
rows = []
for dj, lj in [("detections_labeled.json", "precision_labels.json"), ("detections_labeled_new20.json", "precision_labels_new20.json"),
               ("detections_labeled_set2.json", "precision_labels_set2.json")]:
    det = json.load(open(os.path.join(E, dj), encoding="utf-8"))
    lab = json.load(open(os.path.join(E, lj), encoding="utf-8"))["labels"]
    for name, r in det.items():
        if name in CONTROL:
            continue
        for i, d in enumerate(r["detections"], 1):
            l = lab[name][str(i)]
            v = "OP" if l["v"] in "OP" else l["v"]
            rows.append((d["category"], v, d["score"], l.get("note", "")))


def kind(note):
    for title, words in RULES:
        if any(w in note for w in words):
            return title
    return "기타 (다른 물건을 이름만 바꿔 부름)"


bad = [r for r in rows if r[1] in ("X", "A")]
print(f"전체 {len(rows)}건 중 틀림 {sum(1 for r in bad if r[1] == 'X')}건, 애매 {sum(1 for r in bad if r[1] == 'A')}건")
tab = defaultdict(Counter)
for cat, v, s, note in bad:
    tab[kind(note)][(cat, v)] += 1
titles = [t for t, _ in RULES] + ["기타 (다른 물건을 이름만 바꿔 부름)"]
print(f"\n{'유형':<48} {'틀림':>4} {'애매':>4} {'합계':>4}   카테고리별(틀림+애매)")
for t in titles:
    c = tab[t]
    x = sum(n for (cat, v), n in c.items() if v == "X")
    a = sum(n for (cat, v), n in c.items() if v == "A")
    per = ", ".join(f"{KO[cat]} {sum(n for (cc, v), n in c.items() if cc == cat)}" for cat in CATS if any(cc == cat for (cc, v) in c))
    print(f"{t:<48} {x:4} {a:4} {x + a:4}   {per}")
print("\n[기타로 분류된 메모 - 확인용]")
for cat, v, s, note in bad:
    if kind(note).startswith("기타"):
        print(f"  {KO[cat]} {v} {s:.2f} {note}")
print("\n[규칙별 분류 결과 확인용 - 유형별 메모 예시]")
shown = defaultdict(int)
for cat, v, s, note in bad:
    k = kind(note)
    if shown[k] < 6:
        shown[k] += 1
        print(f"  [{k[:10]}] {KO[cat]} {v} {note}")
