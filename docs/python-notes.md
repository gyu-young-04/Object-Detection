# 파이썬 문법 노트 (우리 코드로 복습)

`src/detect.py`에 실제로 쓰인 문법만 골라 정리한다. 이 프로젝트 코드는 여기 나오는 문법이 계속 반복되므로, 이것만 읽을 수 있으면 대부분의 코드가 읽힌다.

## 1. import — 남이 만든 도구 가져오기

```python
import sys
import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
```

- `import torch` : torch 라이브러리 전체를 가져온다. 쓸 때는 `torch.no_grad()`처럼 앞에 `torch.`을 붙인다.
- `from PIL import Image` : PIL 라이브러리에서 `Image`만 꺼내온다. 쓸 때 `Image.open(...)`처럼 바로 쓴다.
- `,`로 여러 개를 한 번에 가져올 수 있다.

## 2. 변수와 상수

```python
MODEL_ID = "IDEA-Research/grounding-dino-tiny"
```

`이름 = 값`. 파이썬 관례로 **바뀌지 않는 값은 대문자**로 쓴다(강제는 아니고 약속).

## 3. 함수 — def / return

```python
def load_model():
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID)
    model.eval()
    return processor, model
```

- `def 이름(입력들):` 로 함수를 만들고, **들여쓰기(4칸)가 함수의 범위**다. 들여쓰기가 틀리면 오류가 난다.
- `return`으로 결과를 돌려준다. `return a, b`처럼 쉼표로 여러 개를 돌려주면 받을 때 `processor, model = load_model()`로 한 번에 받는다.

## 4. 함수 인자의 기본값

```python
def detect(image, categories, processor, model, box_threshold=0.3, text_threshold=0.25):
```

`box_threshold=0.3`처럼 `=`이 붙은 인자는 **안 넣으면 그 기본값을 쓴다**. 필요할 때만 `detect(..., box_threshold=0.5)`로 바꿔 부른다.

## 5. 문자열 다루기

```python
text = ". ".join(categories) + "."
```

- `"구분자".join(리스트)` : 리스트의 글자들을 구분자로 이어붙인다. `["cat", "couch"]` → `"cat. couch"`
- `+` : 문자열끼리 이어붙인다. 최종 결과는 `"cat. couch."`

```python
print(f"모델 로드: {time.time() - t0:.1f}초")
```

- **f-string**: 문자열 앞에 `f`를 붙이면 `{}` 안에 변수나 계산식을 바로 넣을 수 있다.
- `:.1f` 는 "소수점 첫째 자리까지"라는 뜻.

## 6. 딕셔너리 — `{키: 값}`

```python
{
    "category": label,
    "score": round(float(score), 3),
    "box": [...],
}
```

- 이름표(키)로 값을 꺼내는 자료형. `d["score"]`처럼 쓴다.
- `results.get("text_labels", results["labels"])` : `"text_labels"`가 있으면 그 값을, **없으면 두 번째 값(기본값)** 을 쓴다. `d["키"]`는 키가 없으면 오류, `.get()`은 안전하다.

## 7. 리스트와 반복문

```python
detections = []                      # 빈 리스트
for box, score, label in zip(results["boxes"], results["scores"], labels):
    detections.append({...})         # 리스트 끝에 추가
```

- `[]` 는 리스트, `.append(x)` 는 끝에 추가.
- `for 변수 in 반복할것:` : 하나씩 꺼내서 아래 들여쓴 코드를 반복한다.
- `zip(a, b, c)` : 세 리스트를 **같은 순서끼리 묶어서** 한 번에 꺼내준다. 박스·점수·라벨이 같은 번호끼리 짝이므로 쓴다.

## 8. 리스트 컴프리헨션 (한 줄 반복)

```python
[round(float(v), 1) for v in box.tolist()]
```

`[결과식 for 변수 in 목록]` : 목록의 각 원소에 결과식을 적용해서 **새 리스트를 만든다**. 일반 반복문으로 풀면 이렇다.

```python
new = []
for v in box.tolist():
    new.append(round(float(v), 1))
```

## 9. 인덱싱과 슬라이싱

```python
results = processor.post_process_...(...)[0]     # 결과 리스트의 첫 번째 원소
target_sizes=[image.size[::-1]]                  # (가로, 세로) → (세로, 가로)
```

- `[0]` : 첫 번째 원소 (번호는 0부터 시작)
- `[::-1]` : 순서를 **뒤집는다**. `image.size`는 (가로, 세로)인데 모델은 (세로, 가로)를 원해서 뒤집었다.

## 10. `**` 로 딕셔너리 풀어서 넘기기

```python
outputs = model(**inputs)
```

`inputs`가 `{"pixel_values": ..., "input_ids": ...}` 같은 딕셔너리일 때, `**inputs`는 이걸 `model(pixel_values=..., input_ids=...)`처럼 **이름 붙은 인자들로 풀어서** 넘긴다는 뜻이다.

## 11. with 문

```python
with torch.no_grad():
    outputs = model(**inputs)
```

`with ...:` 블록 안에서만 어떤 설정을 켜고, 블록이 끝나면 자동으로 끈다. 여기서는 "학습용 계산 기록을 남기지 않는다"는 설정으로, 탐지만 할 때 메모리와 시간을 아낀다.

## 12. 직접 실행할 때만 도는 부분

```python
if __name__ == "__main__":
    image_path = sys.argv[1]
    categories = sys.argv[2:] or ["clothes", "trash", "book"]
```

- `if __name__ == "__main__":` : 이 파일을 **직접 실행했을 때만** 아래가 돈다. 다른 파일이 `from detect import detect`로 가져다 쓸 때는 돌지 않는다.
- `sys.argv` : 명령어 뒤에 붙인 값들의 리스트. `python detect.py a.jpg cat couch` 이면 `["detect.py", "a.jpg", "cat", "couch"]`.
- `sys.argv[2:]` : 2번부터 끝까지(`cat`, `couch`).
- `A or B` : A가 비어 있으면 B를 쓴다. 카테고리를 안 적었을 때 기본 목록을 쓰는 용도.

---

## 직접 해보기 (손으로 쳐보는 연습)

`src/detect.py`를 복사해서 `src/practice.py`로 만든 뒤, 아래를 **직접 타이핑해서** 추가해본다. 막히면 물어보면 된다.

1. 탐지 결과 중 **score가 0.6 이상인 것만** 출력하기 (for + if)
2. 카테고리별로 **몇 개 잡혔는지** 세어서 `{"cat": 2, "couch": 1}` 형태의 딕셔너리로 만들기
3. 박스의 **가로×세로 넓이**를 계산해서 결과 딕셔너리에 `"area"` 키로 추가하기 (박스는 `x1, y1, x2, y2`)
