# [app.py] 웹 서버. 브라우저의 요청을 받아서 store.py 등의 함수를 부르고 결과를 돌려준다.
# 지금(2단계)은 모델을 돌리지 않고, 이미 저장된 탐지 결과(outputs/*.json)를 화면에 보여주고 사용자의 판정을 저장한다.
# 실행: python src\app.py  ->  브라우저에서 http://localhost:5000  (끄기: 터미널에서 Ctrl+C)
# 주소 연결표:
#   /               GET   화면 (web/index.html)
#   /api/results    GET   저장된 탐지 결과
#   /photos/<이름>   GET   data/ 폴더의 사진 파일
#   /api/feedback   GET   저장된 판정 전부 / POST 판정 하나 저장
#   /api/stats      GET   카테고리별 통계와 안내 순서

# api 라는 형식으로 각종 접근 요청들에 어떤 함수와 작동을 실행할지 정의해둔곳 + 서버실행

import json #json 파일을 읽을때 (json을 서버가 이해할 dict으로?)
import os   #폴더 ,파일경로 다룰때 사용함

from flask import Flask, jsonify, request, send_from_directory

# flask - 서버 본체를 만드는 도구
# jsonify - dict 를 json으로 바꿔주는
# request - 브라우저가 보낸 요청이 담긴 상자
# send_from_directory - 이 폴더 안의 이 파일을 브라우저에 그대로 보내라
# (대략 이 폴더에 존재하는 특정파일을 간단히 브라우저한테 보내는 도구)

#app.py와 같은 경로이기에 이름으로만으로도 불러올수있음
from merge import remove_containers
from store import add_feedback, category_stats, load_feedback, rank_categories

#이전에 만들어둔 파이썬을 import로 함수 받아오기

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# dirname - 이전경로 찾는? 그런느낌
# os.path.abspath(__file__) - 이 파일의 전체경로


DATA_DIR = os.path.join(ROOT, "data")  # 사진 폴더
WEB_DIR = os.path.join(ROOT, "web")  # 화면 파일 폴더 (html 저장된곳)
# 화면에 보여줄 탐지 결과 파일들 (사진 이름이 겹치지 않아 그대로 합친다)
RESULTS_PATHS = [
    os.path.join(ROOT, "outputs", "detections_new20_400_nocontain.json"),  # 인터넷 사진 20장
    os.path.join(ROOT, "outputs", "detections_set2_400_nocontain.json"),  # 신발·책·가방 보강 사진 12장
]
#지금은 인터넷 사진 32장에 대한 결과가 보임

app = Flask(__name__)  # 서버 본체

# 서버 정의


@app.route("/")
def home():
    # 화면 파일(HTML)을 그대로 보낸다. 요청마다 파일을 읽어서, HTML만 고칠 때는 서버를 다시 켜지 않아도 된다
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/api/results")  #화면을 열면 index.html이 실행되는데 그 과정에서 요청된 api
def results():
    # 저장된 탐지 결과(JSON 파일들)를 읽어 하나로 합치고, 작은 박스를 품은 큰 박스를 걷어낸 뒤(개별 단위) 돌려준다
    data = {}
    for path in RESULTS_PATHS:
        with open(path, encoding="utf-8") as f:
            data.update(json.load(f))
    for r in data.values():
        r["detections"] = remove_containers(r["detections"])
    return jsonify(data)


#사진이름으로 해당 사진을 브라우저에게 보내는 api
@app.route("/photos/<name>")
def photo(name):
    # data/ 폴더의 사진 파일을 보낸다 (브라우저의 <img src="/photos/이름">이 이 주소를 부른다)
    return send_from_directory(DATA_DIR, name)

# 판정들 전부 불러오는 API?
@app.route("/api/feedback")
def feedback_list():
    # 지금까지 저장된 판정 전부 (화면을 새로 열었을 때 이미 판정한 박스를 표시하려고 쓴다)
    return jsonify(load_feedback())


@app.route("/api/feedback", methods=["POST"])  # 같은 주소라도 POST(보내기)이면 이 함수가 실행된다
def feedback_add():
    # 브라우저가 보낸 판정 하나를 store.py의 함수로 저장한다
    data = request.get_json()
    try:
        add_feedback(data["photo"], data["category"], data["score"], data["box"], data["verdict"])
    except (KeyError, ValueError) as e:
        # 보낸 값이 빠졌거나(KeyError) 판정 값이 이상하면(ValueError) 400(잘못된 요청)으로 알려준다
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True})


@app.route("/api/stats")
def stats():
    # 판정을 카테고리별로 세고, 정밀도가 높은 순서(안내 순서)와 함께 돌려준다
    s = category_stats(load_feedback())
    return jsonify({"stats": s, "order": rank_categories(s)})


# 터미널에서 이 파일을 직접 실행했을 때만 서버를 켠다

#위에서 정의한 서버를 5000번 포트에서 돌아가게 만들기
if __name__ == "__main__":
    app.run(port=5000)
