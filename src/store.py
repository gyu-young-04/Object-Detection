# [store.py] 사용자의 판정(맞아요 / 이미 제자리 / 틀려요)을 파일에 저장하고, 카테고리별로 집계한다.
# 외부 도구 없이 파일 읽기·쓰기와 순수 계산만 한다. (모델도 웹도 필요 없다)
# 흐름: add_feedback(판정 하나 저장) -> load_feedback(저장된 판정 전부 읽기) -> category_stats(카테고리별로 세기)
#       -> rank_categories(정밀도 높은 카테고리부터 순서 정하기)
# 확인: 터미널에서 python src\store.py 를 실행하면 가짜 판정으로 동작을 보여주고, 맨 아래 "기대 결과"와 비교할 수 있다.

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDBACK_PATH = os.path.join(ROOT, "data", "feedback.json")  # data/는 git에 올라가지 않는다
VERDICTS = ("O", "P", "X")  # O: 맞아요(정리 필요), P: 이미 제자리, X: 틀려요
MIN_SAMPLES = 5  # 한 카테고리의 판정이 이 개수보다 적으면 "표본 부족"으로 본다
MIN_PHOTOS = 3  # 판정이 이 장수보다 적은 사진에서만 나왔어도 "표본 부족" (한 장의 사진이 카테고리 전체를 대표하는 것을 막는다)



# data/feedback.json 이라는 글자를 불러와서 list로 바꿔주는 함수 (기존에 존재하던 판정결과 불러오기)

# 

def load_feedback(path=FEEDBACK_PATH):
    # 저장된 판정 목록(리스트)을 읽어서 돌려준다. 파일이 아직 없으면 빈 리스트 []를 돌려준다.
    # 힌트: os.path.exists(path), with open(path, encoding="utf-8") as f, json.load(f)
    if not os.path.exists(path):         # 파일이 아직 없으면
        return []                      # ← 빈 리스트를 돌려준다 (아무 판정도 없다는 뜻)
    with open(path, encoding="utf-8") as f:
        return json.load(f)              # ← 파일 내용을 읽어서 Python 목록으로 바꿔 돌려준다


def add_feedback(photo, category, score, box, verdict, path=FEEDBACK_PATH):
    # 판정 하나를 기존 목록 뒤에 추가해서 파일에 저장한다.
    # 한 건의 모양: {"photo": "a.jpg", "category": "shoes", "score": 0.52, "box": [x1, y1, x2, y2], "verdict": "O"}
    #   box는 탐지 결과의 "box"와 같은 [왼쪽 위 x, 왼쪽 위 y, 오른쪽 아래 x, 오른쪽 아래 y]. 나중에 같은 박스를 위치로 다시 찾는 데 쓴다.
    # verdict가 VERDICTS에 없는 값이면 ValueError를 낸다.
    if verdict not in VERDICTS:
        raise ValueError(f"verdict는 {VERDICTS} 중 하나여야 합니다: {verdict}")
    # data/ 폴더가 아직 없을 수도 있으니 만들어 둔다 (이미 있으면 그대로 둠)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 지금까지의 목록을 읽고, 새 판정을 뒤에 붙인 뒤, 전체를 다시 파일에 쓴다
    records = load_feedback(path)
    records.append({"photo": photo, "category": category, "score": score, "box": box, "verdict": verdict})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

#판정결과를 바탕으로 카테고리별 상황 파악

def category_stats(records):    #판정결과를 매개로 전달
    # 판정 목록을 카테고리별로 세어서 dict로 돌려준다.
    # 결과 모양: {"shoes": {"total": 5, "O": 4, "P": 0, "X": 1, "precision": 0.8, "enough": True}, ...}
    #   precision = (O + P) / total   (지금까지 써 온 "엄격 정밀도"와 같은 기준)
    #   enough    = total >= MIN_SAMPLES   (표본이 충분한지)
    
    stats = {}  #빈 딕셔너리
    per_photo = {}  # (카테고리, 사진 이름) -> [맞는 판정 수, 전체 판정 수]. 한 사진에 박스가 몰려도 사진 하나는 한 표만 갖게 하려고 센다
    # 판정을 하나씩 보면서 카테고리별 칸(total, O, P, X)에 센다
    for r in records: #판정에서 하나씩 꺼낸다
        if r["category"] not in stats: #이 카테고리를 처음 봤는가
            stats[r["category"]] = {"total": 0, "O": 0, "P": 0, "X": 0}
        s = stats[r["category"]] #현재의 판정(r)의 상태를 s에 저장
        s["total"] += 1
        s[r["verdict"]] += 1
        #실제 상태를 꺼냈으니 1 증가시켜줌
        tally = per_photo.setdefault((r["category"], r["photo"]), [0, 0])
        tally[0] += 1 if r["verdict"] in ("O", "P") else 0
        tally[1] += 1
    

    # 다 센 뒤에 카테고리마다 정밀도와 표본 충분 여부를 계산해서 덧붙인다
    # stats에는 카테고리별로 판정결과가 저장된 상황
    # stats.values()의 경우는 카테고리의 집계표들
    for cat, s in stats.items():
        s["precision"] = round((s["O"] + s["P"]) / s["total"], 3)
        # 사진마다 정밀도를 먼저 구하고 평균을 낸다 (박스가 많은 사진이 통계를 끌고 가지 않게)
        by_photo = [good / n for (c, _), (good, n) in per_photo.items() if c == cat]
        s["photos"] = len(by_photo)
        s["precision_by_photo"] = round(sum(by_photo) / len(by_photo), 3)
        s["enough"] = s["total"] >= MIN_SAMPLES and s["photos"] >= MIN_PHOTOS
    return stats


# 판정결과로부터 어떤 카테고리가 순위가 높은지 정렬되서 정리


def rank_categories(stats):
    # 정밀도가 높은 카테고리부터 이름 목록으로 돌려준다. 표본 부족(enough가 False)인 카테고리는 맨 뒤로 보낸다.
    # 정렬 기준을 (enough, precision) 두 값의 묶음으로 하면, enough가 True인 것이 먼저 오고 그 안에서 정밀도가 높은 순이 된다
    return sorted(stats, key=lambda c: (stats[c]["enough"], stats[c]["precision"]), reverse=True)


if __name__ == "__main__":
    # 직접 실행하면 가짜 판정 몇 건을 outputs/feedback_demo.json에 저장해서 함수가 맞게 동작하는지 확인한다
    demo = os.path.join(ROOT, "outputs", "feedback_demo.json")
    if os.path.exists(demo):
        os.remove(demo)
    for i, verdict in enumerate(["O", "O", "O", "O", "X"]):
        add_feedback(f"a{i % 3}.jpg", "shoes", 0.5, [10, 20, 110, 220], verdict, demo)  # 사진 3장에 나눠 담는다
    for verdict in ["O", "X"]:
        add_feedback("a0.jpg", "clothes", 0.4, [200, 30, 400, 300], verdict, demo)  # 사진 1장뿐
    stats = category_stats(load_feedback(demo))
    print(stats)
    print(rank_categories(stats))
    # 기대 결과
    #   shoes   : total 5, O 4, P 0, X 1, precision 0.8, enough True
    #   clothes : total 2, O 1, P 0, X 1, precision 0.5, enough False (표본 부족)
    #   순서    : ['shoes', 'clothes']
