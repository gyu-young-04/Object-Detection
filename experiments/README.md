# experiments — 실험 스크립트

설계프로젝트2에서 "학습 없이 설정만으로 탐지 정밀도를 얼마나 올릴 수 있나"를 확인하려고 돌린 스크립트 모음이다. 결과와 해석은 `docs/devlog.md`와 `docs/plan.md` 12절에 있고, 이 폴더는 그 숫자를 **다시 만들 수 있게** 남겨 둔 것이다. 앱 코드(`src/`)와 달리 일회성 분석용이라 정리 수준이 낮다.

## 실행 방법

저장소 루트에서 가상환경 파이썬으로 실행한다. 스크립트는 자기 위치를 기준으로 저장소 루트를 찾으므로 어디서 실행해도 된다.

```powershell
.\venv\Scripts\python.exe experiments\score_bands.py
```

한글이 깨지면 먼저 `$env:PYTHONIOENCODING='utf-8'`을 설정한다.

## 준비물과 주의

- `data/`(사진)와 `outputs/`(모델 결과 JSON, 검수 이미지)는 개인 사진과 큰 파일이라 **저장소에 없다(gitignore)**. 모델을 돌리는 스크립트(`run_*`, `time_methods`, `timing_base`)를 먼저 실행해야 `outputs/`가 생기고, 분석 스크립트는 그 결과를 읽는다.
- 채점 결과는 저장소의 `docs/eval/*.json`에 있다. `*_save.py` 안의 번호 목록(OP/A/X)은 채점 당시 모음 이미지의 번호와 짝이 맞는 것이라, 이미지를 다시 만들면 번호가 같아야 한다(`index.json` 순서 고정).
- 모델 실행은 CPU에서 사진당 17~28초이고 컴퓨터 상태에 따라 흔들린다. 시간 측정은 컴퓨터를 다른 일에 쓰지 않을 때 돌린다.
- 이 폴더로 옮긴 뒤 **모두 다시 실행해 보지는 않았다.** 전체 문법 검사와 `score_bands`, `cat_thresholds`, `order_check`, `e1d_analysis`, `e1d_time`, `wrong_types` 실행만 확인했다. 오래된 스크립트는 그 사이 바뀐 코드와 안 맞을 수 있다.
- 채점자는 Claude(사용자 검수 전)이며, 사용자 판정은 `data/feedback.json`(gitignore)에 있다.

## 스크립트 지도

### 모델을 돌려 `outputs/`를 만드는 것 (GPU 없이 느림)

| 스크립트 | 하는 일 |
|---|---|
| `run_t020.py` | 점수 0.20 이상으로 40장을 한 번 돌려 저장(0.25, 0.30은 나중에 잘라 비교) |
| `run_e1.py` | 카테고리 후보 9개(cup, bowl, glass jar, cushion, blanket, basket, chair, picture frame, phone)를 하나씩 질의 |
| `run_e1b.py` | 미끼 후보 9개(drawer, cabinet, shelf 등)와 묶음 질의(`cushion. blanket.` 등) |
| `run_e1d.py` | 가구 미끼를 섞은 묶음 질의와 시간 측정 |
| `run_base_all.py`, `timing_base.py` | tiny와 base 모델 비교(결과, 속도) |
| `time_methods.py` | 해상도(`t1`)와 배치 처리(`t2`)의 시간·정확도 검증 |

### 분석 (저장된 결과와 채점으로 계산, 모델 필요 없음)

| 주제 | 스크립트 |
|---|---|
| 점수 기준 | `t020_analysis.py`(채점용 이미지), `t020_save.py`(채점 저장·추정), `score_bands.py`(구간별 정밀도), `cat_thresholds.py`(카테고리별 기준 규칙), `threshold_vs_base.py` |
| 미끼(경쟁 이름) | `e1_analysis.py`, `e1_followup.py`, `e1_save.py`, `e1b_analysis.py`, `e1d_analysis.py`, `e1d_time.py`, `combo_test.py` |
| 미끼 박스 자체 평가 | `decoy_survivors.py`(개수), `decoy_sheets.py`(채점용 이미지), `decoy_save.py`(채점 저장·정밀도) |
| 틀린 박스 유형 | `wrong_notes.py`(메모 모음), `wrong_types.py`(유형 분류) |
| 모델 크기 | `compare_base.py`, `base_sheets.py`, `base_final.py`, `user_vs_base.py` |
| 옷 표현 | `garment_new_boxes.py`, `garment_compare.py` |
| 순서 | `order_check.py`(카테고리 순서를 바꿔도 최종 박스가 같은가) |
| 크기·편향 | `size_filter_check.py`, `size_by_category.py`, `photo_bias.py`, `bias_sensitivity.py`, `selection_bias.py`, `skipped.py`, `per_category.py` |
| 사용자 vs AI 채점 | `compare_user_ai.py` |
| 포개진 박스 | `nested_pairs.py`, `check_containers.py` |

## 결과 한 줄 요약 (2026-11-27 기준, 같은 40장)

- 점수 구간: 0.30~0.40은 정밀도가 안 오르고 0.50 이상에서 75.9%
- 미끼: cushion + shelf + comforter + blanket은 틀린 박스 40% 제거, 맞는 박스 3.8% 손실. 한 문장 묶음은 질의 1번 시간
- 미끼 박스 자체 정밀도: pillow 91%, shelf 58%, cushion 10%
- 시간: 해상도를 낮추면 맞는 박스를 잃고, 배치 처리는 약 -22%, 카테고리 순서는 총 시간과 결과를 바꾸지 않음
- 카테고리별 점수 기준은 가설 단계이고 내 방 사진 검증용에서 한 번만 확인한다.
