import sys  # 터미널 명령어 뒤에 붙인값들을 읽을때 사용하는 도구
import time # 시간 재는 도구 (모델 로드랑 탐지시간 측정하기위해서)

import torch    # 딥러닝 계산 엔진
from PIL import Image   #사진 파일을 열고 다루는 도구(Pillow)
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
# transformers 는 모델 불러오기 도구 ,  (모델 본체)             (전후처리담당)

MODEL_ID = "IDEA-Research/grounding-dino-tiny"

#전후처리담당은 무엇인가 processor는 무엇인가 모델말고 추가적으로 뭘 받은건지 , 

def load_model():
    processor = AutoProcessor.from_pretrained(MODEL_ID) #사진을 모델에 맞게 숫자로 바꾸고 글자를 숫자토큰으로 바꾸고 모델출력을 박스 좌표로 되돌리는 통역사 (4차원좌표?)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID) #학습된 가중치들이 들어있음
    model.eval()    #학습을 하는게 아니기에 추론모드로 바꾸는 (매번 같은 결과가 나오게)
    return processor, model


def detect(image, categories, processor, model, box_threshold=0.3, text_threshold=0.25):
    # Grounding DINO는 카테고리를 "a. b. c." 처럼 마침표로 구분한 한 문장으로 받는다.

    # 뒤에 있는 임계값 2개는 무엇이고 왜 기본값이 0.3 , 0.25인가
    text = ". ".join(categories) + "."
    inputs = processor(images=image, text=text, return_tensors="pt")
    # 사진과 카테고리를 받아와서 숫자배열 형식으로 변환 (processor가)

    with torch.no_grad():   #학습용 기록을 안남기는
        outputs = model(**inputs)   #모델실행 - 결과는 아직 숫자임

    #숫자 날것의 출력을 박스로 바꾸는 작업
    results = processor.post_process_grounded_object_detection( 
        # 위 실행을 하면 키 이름이 scores, boxes, text_labels, labels 로 담아서 돌려주도록 미리 만들어져있음
        outputs,
        inputs.input_ids,
        threshold=box_threshold,    #이 점수 미만의 박스는 버린다
        text_threshold=text_threshold,  #박스가 어떤 단어와 맞는지의 신뢰기준
        target_sizes=[image.size[::-1]],  # (height, width)
    )[0]    #사진 한장


    detections = []
    labels = results.get("text_labels", results["labels"])
    for box, score, label in zip(results["boxes"], results["scores"], labels):
        detections.append(
            {
                "category": label,
                "score": round(float(score), 3),
                "box": [round(float(v), 1) for v in box.tolist()],  # x1, y1, x2, y2
            }
        )
    return detections


if __name__ == "__main__": #이 파일을 직접 실행했을때만 아래가 돌아감
    image_path = sys.argv[1]
    categories = sys.argv[2:] or ["clothes", "trash", "book"]

    image = Image.open(image_path).convert("RGB")

    t0 = time.time() #시작시간
    processor, model = load_model()
    print(f"모델 로드: {time.time() - t0:.1f}초")   #걸린시작 출력

    t0 = time.time()
    detections = detect(image, categories, processor, model)
    print(f"탐지 시간: {time.time() - t0:.1f}초")

    print(f"탐지 {len(detections)}건")
    for d in detections:
        print(d)
