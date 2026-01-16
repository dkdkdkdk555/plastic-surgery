import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastapi import FastAPI

app = FastAPI()

model_path = '/Users/ukhyeonpark/workspace/ai-models/face_landmark.task'
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# 구성옵션
options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),  # 모델 경로 설정
    running_mode=VisionRunningMode.IMAGE, # 테스크 실행 모드 {IMAGE, VIDEO, LIVE_STREAM}
    num_faces=1, # 최대 탐지할 얼굴 수, 기본값 1
    min_face_detection_confidence=0.5 # 얼굴 탐지 신뢰도 임계값, 기본값 0.5
)



@app.get("/ss")
async def read_root():
    return {"Hello": "World"}

