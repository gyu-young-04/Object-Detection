# 개념 정리 (학습용)

구현하면서 계속 마주치게 될 개념들을 미리 정리해둔 문서. 한 번에 다 이해하려 하지 말고, 실제로 그 개념이 필요한 작업을 할 때 다시 찾아보는 용도로 쓰면 된다.

---

## 1. 객체 탐지(Object Detection) 기초

### 바운딩 박스 (Bounding Box)
사진 속에서 물체가 있는 위치를 사각형 좌표로 표시한 것. 보통 `(x, y, width, height)` 또는 `(x1, y1, x2, y2)`(좌상단, 우하단 좌표) 형태로 표현한다. 우리 프로젝트에서 "탐지됐다"는 건 결국 이 좌표값을 얻는다는 뜻이다.

### confidence score (신뢰도 점수)
모델이 "여기 있는 게 내가 찾는 물건이 맞다"고 확신하는 정도를 0~1 사이 숫자로 나타낸 것. 이 값이 특정 기준(threshold)보다 낮으면 결과에서 제외한다. 이 기준값을 조절하면 정확도와 탐지 개수 사이의 트레이드오프가 생긴다(기준을 낮추면 더 많이 잡히지만 오탐도 늘고, 높이면 확실한 것만 잡히지만 놓치는 것도 늘어남).

### IoU (Intersection over Union)
두 바운딩 박스가 얼마나 겹치는지를 비율로 나타낸 값 (겹치는 면적 / 전체 합친 면적). 0에 가까우면 거의 안 겹침, 1에 가까우면 거의 같은 위치. 같은 사진 안에서 같은 물건에 중복으로 박스가 그려졌을 때, IoU가 높은 것끼리는 하나로 합치는 후처리(NMS, Non-Max Suppression)에 사용한다.

---

## 2. 오픈보캐뷸러리 탐지 (Open-Vocabulary Detection)

### 기존 방식(닫힌 어휘) vs 오픈보캐뷸러리
- 기존 방식: 학습 시점에 정해둔 고정 클래스 목록(예: COCO의 80개 클래스)만 인식. 새 클래스를 추가하려면 데이터를 모아 재학습(파인튜닝) 필요.
- 오픈보캐뷸러리: 텍스트로 "무엇을 찾을지" 그때그때 지정. 재학습 없이 새로운 대상을 찾을 수 있음.

### 어떻게 가능한가
모델이 이미지와 텍스트를 같은 벡터 공간(임베딩 공간)에 매핑하도록 대규모 이미지-텍스트 쌍으로 사전학습되어 있다. 텍스트 쿼리와 이미지 영역의 벡터가 얼마나 가까운지(유사도)를 계산해서, 가까운 영역을 탐지 결과로 반환한다. 즉 "찾기"만 할 뿐 그 과정에서 모델 내부 값이 바뀌지 않는다(=재학습이 아님).

### 우리가 쓰는 모델: Grounding DINO
텍스트 프롬프트(예: `"a shirt. trash. a book."`처럼 마침표로 구분된 여러 쿼리)를 입력하면, 이미지에서 매칭되는 영역을 바운딩 박스 + 카테고리 라벨 + confidence score로 반환한다. Hugging Face `transformers` 라이브러리의 `AutoModelForZeroShotObjectDetection`으로 비교적 간단히 쓸 수 있다(직접 빌드가 필요한 공식 레포보다 설치가 쉬움).

### 한계
텍스트로 일반화해서 설명 가능한 것만 잘 찾는다. 완전히 고유해서 말로 설명이 안 되는 특정 물건(예: "우리 집에만 있는 이 특정 도자기 인형")은 구분하지 못한다.

---

## 3. 웹 클라이언트-서버 구조

### 클라이언트 / 서버
- 클라이언트: 사용자가 직접 보는 쪽 (브라우저)
- 서버: 요청을 받아 처리하고 응답을 돌려주는 쪽 (우리 프로젝트에서는 탐지 모델이 도는 파이썬 백엔드)

### HTTP 요청/응답, API
브라우저가 서버에게 "이 사진 처리해줘"라고 보내는 것이 HTTP 요청(request), 서버가 처리 결과를 돌려주는 것이 응답(response). API(Application Programming Interface)는 서버가 "이런 요청을 이런 형식으로 보내면 이런 응답을 준다"고 정해둔 규칙이다.

### 우리 프로젝트에서의 흐름
```
브라우저(사진 촬영/업로드)
  -> HTTP 요청(사진 데이터)
  -> 로컬 서버(파이썬, 같은 네트워크 안)
  -> 탐지 모델 실행
  -> HTTP 응답(탐지 결과: 카테고리 + 좌표 + 목적지)
  -> 브라우저(결과를 사진 위에 오버레이로 표시)
```
사진이 외부 클라우드로 안 나가는 이유는, 이 서버가 사용자 본인 기기에서 돌기 때문이지 PWA나 웹앱이라는 형태 자체 때문이 아니다.

---

## 4. 백엔드 프레임워크 (Flask / FastAPI)

### 라우트(Route/Endpoint)
"어떤 주소로 요청이 오면 어떤 함수를 실행할지" 정의하는 것. 예를 들어 `/detect`라는 주소로 사진을 보내면 탐지 함수가 실행되도록 정할 수 있다.

### 최소 예시 (Flask)
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/detect", methods=["POST"])
def detect():
    image_file = request.files["image"]
    # 여기서 탐지 모델 호출
    results = [{"category": "clothes", "box": [10, 20, 100, 200], "score": 0.87}]
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
```
이 정도가 백엔드의 최소 골격이다. 여기에 탐지 모델 호출, DB 조회/저장 로직을 점점 추가해나가는 방식으로 확장한다.

---

## 5. 프론트엔드 기초

### 카메라 접근 (getUserMedia)
브라우저에서 카메라 스트림을 가져오는 표준 API. `navigator.mediaDevices.getUserMedia({video: true})`로 카메라 권한을 요청하고 스트림을 받는다.

### Canvas로 오버레이 그리기
사진 위에 색깔 박스를 그리려면 `<canvas>` 태그 위에 사진을 그리고, 그 위에 탐지 결과 좌표대로 사각형(`ctx.strokeRect(x, y, w, h)`)을 겹쳐 그리는 방식을 쓴다. 클릭 이벤트도 이 캔버스 좌표를 기준으로 어떤 박스를 클릭했는지 판단한다.

---

## 6. 데이터베이스 기초 (SQLite)

파일 하나로 동작하는 가벼운 DB라 로컬 서버에 쓰기 적합하다. 유저별 예외 규칙(카테고리 → 목적지)을 저장하는 용도로 쓴다.

```sql
CREATE TABLE rules (
    category TEXT PRIMARY KEY,
    destination TEXT NOT NULL
);

INSERT INTO rules (category, destination) VALUES ('clothes', 'closet');

SELECT destination FROM rules WHERE category = 'clothes';

UPDATE rules SET destination = 'laundry_basket' WHERE category = 'clothes';
```
파이썬에서는 `sqlite3` 모듈이 기본 내장돼 있어 별도 설치 없이 바로 쓸 수 있다.

---

## 7. 모델 경량화 (양자화) — 스트레치 목표 참고용

모델 내부의 정밀한 숫자(가중치)를 더 단순한 숫자로 반올림해서, 모델 크기를 줄이고 계산 속도를 높이는 작업. 사진을 압축하면 용량은 줄고 화질은 살짝 떨어지는 것과 비슷한 원리다. 노트북 수준 모델을 라즈베리파이 같은 작은 보드에 올리기 전에 필요한 준비 단계.

---

## 8. Git/GitHub 워크플로우

### 기본 흐름
```bash
git add -A              # 변경사항 스테이징
git commit -m "..."     # 커밋
git push origin main    # 원격 저장소에 반영
```

### 이 프로젝트의 커밋 메시지 컨벤션
`타입: 한글 설명` 형식을 쓴다.
- `feat:` 새 기능 추가
- `fix:` 버그 수정
- `docs:` 문서 추가/수정
- `refactor:` 기능 변화 없는 코드 구조 개선

예: `feat: 사진 업로드 후 탐지 결과 반환 API 구현`
