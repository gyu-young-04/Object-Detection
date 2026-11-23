# [hello_flask.py] Flask(웹 서버)가 무엇인지 눈으로 확인하는 공부용 예제. 프로젝트 본 코드와는 상관없다.
# 실행: python study\hello_flask.py  ->  브라우저에서 http://localhost:5000 열기  (끄기: 터미널에서 Ctrl+C)
# 흐름: 브라우저가 주소를 요청 -> 서버가 아래 함수를 실행 -> 함수가 돌려준 값이 브라우저로 간다(응답)

import time #현재시간 표현하기위함

from flask import Flask, jsonify, request # 각각 무슨역할인가

app = Flask(__name__)  # 서버 본체를 만든다(flask) 
# 이 파이썬의 이름으로하는 서버?

# 브라우저에 보낼 화면(HTML). 글자 구조는 HTML, 버튼 동작은 아래 <script>(JavaScript)가 맡는다
PAGE = """<!doctype html>
<meta charset="utf-8">
<h1>Flask 연습</h1>
<button onclick="getTime()">서버 시간 가져오기 (GET)</button>
<p id="timeOut"></p>
<input id="msg" value="안녕하세요">
<button onclick="sendMsg()">서버로 보내기 (POST)</button>
<p id="echoOut"></p>
<script>
async function getTime() {
  const res = await fetch("/api/time");   // 서버에 GET 요청
  const data = await res.json();          // 응답 JSON을 객체로
  document.getElementById("timeOut").textContent = "서버 시간: " + data.now;
}
async function sendMsg() {
  const res = await fetch("/api/echo", {  // 서버에 POST 요청 (글자를 JSON으로 실어 보냄)
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text: document.getElementById("msg").value}),
  });
  const data = await res.json();
  document.getElementById("echoOut").textContent = `서버가 받은 글자: ${data.you_said} (${data.length}자)`;
}
setInterval(getTime, 1000);   // 1000밀리초 = 1초마다 
</script>
"""


@app.route("/")  # "주소가 / 이면 아래 함수를 실행해라"라는 연결표
def home():
    return PAGE  # 글자(HTML)를 돌려주면 브라우저가 화면으로 그린다


@app.route("/api/time") #이러한 방식으로 정보를 요청할때
def get_time():
    return jsonify({"now": time.strftime("%H:%M:%S")})  # dict를 JSON 글자로 바꿔서 응답



@app.route("/api/echo", methods=["POST"])  # POST: 브라우저가 서버로 데이터를 "보낼" 때
def echo():
    data = request.get_json()  # 브라우저가 보낸 JSON을 dict로 받는다
    return jsonify({"you_said": data["text"], "length": len(data["text"])})


# 터미널에서 이 파일을 직접 실행했을 때만 서버를 켠다
if __name__ == "__main__":
    app.run(port=5000)
