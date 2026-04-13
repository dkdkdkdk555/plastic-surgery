# Plastic Surgery Simulation API

AI 기반 성형 시뮬레이션 REST API 서버입니다. BiSeNet 얼굴 파싱, MediaPipe 랜드마크 추출, Stable Diffusion XL 인페인팅을 결합하여 코 성형 시뮬레이션 결과를 생성합니다.

## 주요 기능

| 기능 | 설명 | 모델 |
|------|------|------|
| 얼굴 랜드마크 추출 | 478개의 얼굴 랜드마크 좌표 반환 | MediaPipe FaceLandmarker |
| 얼굴 파싱 | 얼굴을 19개 영역으로 세그멘테이션 | BiSeNet (ResNet34) |
| 코 성형 마스크 생성 | 코 영역만 추출한 이진 마스크 반환 | BiSeNet + Face Parsing |
| 코 성형 시뮬레이션 | AI로 코 성형 후 이미지를 생성 | BiSeNet + SDXL Inpainting |

## 기술 스택

- **Framework**: FastAPI
- **Face Parsing**: BiSeNet (ResNet18 / ResNet34 backbone)
- **Landmark Detection**: MediaPipe FaceLandmarker
- **Image Generation**: Stable Diffusion XL Inpainting (`diffusers/stable-diffusion-xl-1.0-inpainting-0.1`)
- **Device**: CUDA / MPS (Apple Silicon) / CPU 자동 선택

## 프로젝트 구조

```
plastic-surgery/
├── main.py                          # FastAPI 앱 진입점
├── routers/
│   ├── face_parsing_api.py          # 얼굴 파싱 & 성형 시뮬레이션 API
│   └── mediapipe_landmark_api.py    # 얼굴 랜드마크 API
├── models/
│   └── face_parsing/
│       ├── models/
│       │   ├── bisenet.py           # BiSeNet 모델 정의
│       │   └── resnet.py            # ResNet backbone
│       ├── utils/
│       │   ├── common.py            # 시각화 유틸리티
│       │   ├── dataset.py
│       │   ├── loss.py
│       │   └── transform.py
│       ├── inference.py             # 추론 로직
│       ├── onnx_export.py           # ONNX 변환
│       ├── onnx_inference.py        # ONNX 추론
│       └── train.py                 # 모델 학습
└── weights/
    ├── resnet18.pt                  # BiSeNet ResNet18 가중치
    └── resnet34.pt                  # BiSeNet ResNet34 가중치
```

## 설치 및 실행

### 요구 사항

- Python 3.9+
- PyTorch (MPS 또는 CUDA 지원 권장)

### 의존성 설치

```bash
pip install fastapi uvicorn torch torchvision pillow mediapipe opencv-python diffusers transformers accelerate
```

### MediaPipe 모델 다운로드

MediaPipe FaceLandmarker 모델 파일(`face_landmarker.task`)을 다운로드 후 경로를 `routers/mediapipe_landmark_api.py`의 `model_path` 변수에 설정합니다.

```python
# routers/mediapipe_landmark_api.py
model_path = '/your/path/to/face_landmarker.task'
```

### 서버 실행

```bash
uvicorn main:app --reload
```

서버 실행 후 `http://localhost:8000/docs`에서 Swagger UI를 통해 API를 테스트할 수 있습니다.

## API 엔드포인트

### 얼굴 랜드마크

#### `POST /landmark/analyze-face`

얼굴 이미지를 받아 478개 랜드마크의 (x, y, z) 좌표를 JSON으로 반환합니다.

**Request**: `multipart/form-data` — `file` (이미지 파일)

**Response**:
```json
{
  "success": true,
  "landmark_count": 478,
  "landmarks": [
    { "x": 0.512, "y": 0.342, "z": -0.021 },
    ...
  ]
}
```

---

#### `POST /landmark/analyze-face-randmark`

랜드마크가 시각화된 이미지를 반환합니다.

**Request**: `multipart/form-data` — `file` (이미지 파일)

**Response**: `image/jpeg`

---

### 성형 시뮬레이션

#### `POST /parsing/simulate-nose-surgery`

BiSeNet으로 코 영역을 추출한 이진 마스크 이미지를 반환합니다.

**Request**: `multipart/form-data` — `file` (이미지 파일)

**Response**: `image/png` (코 영역이 흰색인 마스크)

---

#### `POST /parsing/simulate-nose-surgery-diff`

BiSeNet으로 코 마스크를 생성하고, SDXL 인페인팅으로 성형 후 이미지를 생성합니다.

**Request**: `multipart/form-data`

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `file` | File | 필수 | 원본 얼굴 이미지 |
| `prompt` | string | `"A beautiful face with a well-defined nose"` | 생성 프롬프트 |
| `negative_prompt` | string | `"deformed, ugly, bad anatomy, blur, low quality"` | 네거티브 프롬프트 |

**Response**: `image/png` (성형 시뮬레이션 결과 이미지)

---

## 얼굴 파싱 레이블

BiSeNet은 얼굴을 19개 클래스로 분류합니다.

| 번호 | 부위 | 번호 | 부위 |
|------|------|------|------|
| 0 | 배경 | 10 | 코 |
| 1 | 피부 | 11 | 입술 (위) |
| 2 | 좌측 눈썹 | 12 | 입술 (아래) |
| 3 | 우측 눈썹 | 13 | 목 |
| 4 | 좌측 눈 | 14 | 목 피부 |
| 5 | 우측 눈 | 15 | 왼쪽 귀 |
| 6 | 안경 | 16 | 오른쪽 귀 |
| 7 | 왼쪽 귀걸이 | 17 | 머리카락 |
| 8 | 오른쪽 귀걸이 | 18 | 모자 |
| 9 | 입 | | |

## BiSeNet 독립 추론 (CLI)

API 서버 없이 이미지 파싱 결과를 저장할 때 사용합니다.

```bash
cd models/face_parsing

python inference.py \
  --model resnet34 \
  --weight ../../weights/resnet34.pt \
  --input ./assets/images/ \
  --output ./assets/results
```

## 참고

- BiSeNet 구현: [Yakhyokhuja Valikhujaev](https://github.com/yakhyo)
- [MediaPipe FaceLandmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker)
- [Stable Diffusion XL Inpainting](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1)
