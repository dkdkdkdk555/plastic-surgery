import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import numpy as np
import cv2
import io

app = FastAPI()

model_path = '/Users/ukhyeonpark/workspace/ai-models/face_landmarker.task'
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

# 얼굴 랜드마크 시각화 함수
def visualize(image, detection_result) -> np.ndarray:
    annotated_image = image.copy()
    height, width, _ = image.shape

    if not detection_result.face_landmarks:
        return annotated_image

    for face_landmarks in detection_result.face_landmarks:
        # 각 랜드마크 순회 (NormalizedLandmark 객체)
        for landmark in face_landmarks:
            # 정규화된 좌표(0~1)를 픽셀 좌표로 변환
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            
            # 얼굴에 점 그리기
            cv2.circle(annotated_image, (x, y), 10, (0, 255, 0), -1)
            
    return annotated_image

@app.post("/analyze-face-randmark")
async def analyze_face(file: UploadFile = File(...)):
    # 1. 업로드된 이미지 읽기
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    # OpenCV는 BGR로 읽으므로 RGB로 변환
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    
    # 2. MediaPipe 이미지 객체 생성 및 탐지
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
    detector = FaceLandmarker.create_from_options(options)
    result = detector.detect(mp_image)
    
    if not result.face_landmarks:
        return {"success": False, "message": "얼굴을 찾을 수 없습니다."}

    # 3. 이미지 위에 랜드마크 그리기
    annotated_img_rgb = visualize(rgb_img, result)
    
    # 4. 결과를 다시 BGR로 바꿔서 인코딩 (브라우저 출력용)
    annotated_img_bgr = cv2.cvtColor(annotated_img_rgb, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', annotated_img_bgr)
    
    # 5. 이미지 스트림 반환 (Postman에서 'Body' 탭의 'Preview'로 확인 가능)
    return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type="image/jpeg")


@app.post("/analyze-face")
async def analyze_face(file: UploadFile = File(...)):
    # 1. 업로드된 이미지 읽기
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    # OpenCV는 BGR로 읽으므로 RGB로 변환
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    
    # 2. MediaPipe 이미지 객체 생성 및 탐지
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
    detector = FaceLandmarker.create_from_options(options)
    result = detector.detect(mp_image)
    
    if not result.face_landmarks:
        return {"success": False, "message": "얼굴을 찾을 수 없습니다."}

    # 3. FaceLandmarkerResult를 JSON으로 변환
    # 결과가 리스트 형태이므로 첫 번째 얼굴([0])의 데이터만 추출합니다.
    all_landmarks = []
    for lm in result.face_landmarks[0]:
        all_landmarks.append({
            "x": float(lm.x),
            "y": float(lm.y),
            "z": float(lm.z)
        })

    # 4. JSON 응답
    return {
        "success": True,
        "landmark_count": len(all_landmarks),
        "landmarks": all_landmarks,
    }