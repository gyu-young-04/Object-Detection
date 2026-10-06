import sys
import time

import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

MODEL_ID = "IDEA-Research/grounding-dino-tiny"


def load_model():
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID)
    model.eval()
    return processor, model


def detect(image, categories, processor, model, box_threshold=0.3, text_threshold=0.25):
    # Grounding DINO는 카테고리를 "a. b. c." 처럼 마침표로 구분한 한 문장으로 받는다.
    text = ". ".join(categories) + "."
    inputs = processor(images=image, text=text, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    results = processor.post_process_grounded_object_detection(
        outputs,
        inputs.input_ids,
        threshold=box_threshold,
        text_threshold=text_threshold,
        target_sizes=[image.size[::-1]],  # (height, width)
    )[0]

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


if __name__ == "__main__":
    image_path = sys.argv[1]
    categories = sys.argv[2:] or ["clothes", "trash", "book"]

    image = Image.open(image_path).convert("RGB")

    t0 = time.time()
    processor, model = load_model()
    print(f"모델 로드: {time.time() - t0:.1f}초")

    t0 = time.time()
    detections = detect(image, categories, processor, model)
    print(f"탐지 시간: {time.time() - t0:.1f}초")

    print(f"탐지 {len(detections)}건")
    for d in detections:
        print(d)
