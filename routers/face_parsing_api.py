import sys
import os
from pathlib import Path
import torch
import numpy as np
from PIL import Image
import io
from fastapi import APIRouter, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from diffusers import StableDiffusionXLInpaintPipeline
# [참고] 마스크를 살짝 좁히는 로직 (PIL 이용 시)
from PIL import ImageFilter

# 1. 경로 설정 (반드시 모든 import 보다 위에 있어야 합니다)
# 이 파일의 위치: project/routers/face_parsing_api.py
# 프로젝트 루트: project/
CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE_PATH.parent.parent
FACE_PARSING_ROOT = PROJECT_ROOT / "models" / "face_parsing"

# 파이썬 경로에 추가 (순서가 중요합니다)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(FACE_PARSING_ROOT) not in sys.path:
    sys.path.insert(0, str(FACE_PARSING_ROOT))

# 2. 이제 실제 모델 로직 임포트
try:
    # face_parsing 폴더 내부의 inference.py에서 직접 가져옵니다.
    from inference import load_model, prepare_image
    print("✅ 모델 임포트 성공!")
except ImportError as e:
    # 위 방법이 실패할 경우 전체 경로로 시도
    try:
        from models.face_parsing.inference import load_model, prepare_image
        print("✅ 모델 임포트 성공 (Full Path)!")
    except ImportError as e:
        print(f"❌ 임포트 최종 실패: {e}")
        raise e # 여기서 멈춰야 아래에서 NameError가 안 납니다.

router = APIRouter(
    prefix="/parsing",  # 이 파일의 모든 API 주소 앞에 붙을 공통 경로
    tags=["Face Parsing"] # Swagger 문서에서 그룹화할 이름
)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
MODEL_NAME = "resnet34"
WEIGHT_PATH = "./weights/resnet34.pt"
NUM_CLASSES = 19 # 모델이 얼굴을 총 19개의 영역(카테고리)으로 구분할 수 있다

# 모델 전역 객체로 생성
parsing_model = load_model(MODEL_NAME, NUM_CLASSES, WEIGHT_PATH, DEVICE)

@router.post("/simulate-nose-surgery")
async def simulate_surgery(file: UploadFile = File(...)):
    # 1. 이미지 읽기
    contents = await file.read()
    original_image = Image.open(io.BytesIO(contents)).convert('RGB')
    original_size = original_image.size # (width, height)

    # 2. Face Parsing 수행 (전처리 -> 추론 -> 결과 해석)
    with torch.no_grad():
        input_tensor = prepare_image(original_image).to(DEVICE)
        output = parsing_model(input_tensor)[0]
        # 결과값에서 가장 확률 높은 클래스 선택
        mask = output.squeeze(0).cpu().numpy().argmax(0)
    # 추론 코드 바로 아래에 추가
    unique_values = np.unique(mask)
    print(f"모델이 찾아낸 부위 번호들: {unique_values}")
    # 3. 코(Nose) 마스크 생성 (라벨 번호 10번이 '코'입니다)
    # 512x512 크기의 결과를 원본 크기로 복구
    mask_pil = Image.fromarray(mask.astype(np.uint8))
    restored_mask = np.array(mask_pil.resize(original_size, resample=Image.NEAREST))
    
    # 코 영역(10)만 흰색(255), 나머지는 검은색(0)인 이진 마스크 생성
    nose_mask_array = (restored_mask == 10).astype(np.uint8) * 255
    nose_mask_image = Image.fromarray(nose_mask_array)

    # --- 이미지 반환 로직 ---
    
    # 1. 메모리에 이미지 파일을 임시로 저장할 버퍼 생성
    img_byte_arr = io.BytesIO()
    
    # 2. 생성한 마스크 이미지를 PNG 형태로 버퍼에 저장
    nose_mask_image.save(img_byte_arr, format='PNG')
    
    # 3. 버퍼의 커서를 맨 앞으로 돌림 (읽기 위해)
    img_byte_arr.seek(0)

    # 4. 스트리밍 방식으로 이미지 반환
    return StreamingResponse(img_byte_arr, media_type="image/png")


# 1. SDXL 모델 로드 (서버 시작 시 한 번만)
# M1 Pro의 메모리를 고려하여 float16 정밀도를 사용합니다.
model_id = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
    model_id, 
    torch_dtype=torch.float16,  # 모델의 연산 정밀도
    variant="fp16", # 허깅페이스 서버에서 float16으로 압축돼있는 파일 버전을 내려받겠다
    use_safetensors=True # safetensors 라는 안전한 포맷 사용 (.bin, .pt 보다 해킹 위험 낮고 모델 읽어오는 속도가 더 빠름)
)
# 맥 GPU(MPS) 가속 설정
pipe.to("mps")


@router.post("/simulate-nose-surgery-diff")
async def simulate_nose_surgery(file: UploadFile = File(...), 
                                prompt: str = Form("A beautiful face with a well-defined nose"),
                                negative_prompt: str = Form("deformed, ugly, bad anatomy, blur, low quality")):
    print(f"Received prompt: {prompt}")
    print(f"Received negative prompt: {negative_prompt}")

    # 1. 이미지 읽기
    contents = await file.read()
    original_image = Image.open(io.BytesIO(contents)).convert('RGB')
    original_size = original_image.size # (width, height)

    # 2. Face Parsing 수행 (전처리 -> 추론 -> 결과 해석)
    with torch.no_grad():
        input_tensor = prepare_image(original_image).to(DEVICE)
        output = parsing_model(input_tensor)[0]
        # 결과값에서 가장 확률 높은 클래스 선택
        mask = output.squeeze(0).cpu().numpy().argmax(0)
    # 추론 코드 바로 아래에 추가
    unique_values = np.unique(mask)
    # 3. 코(Nose) 마스크 생성 (라벨 번호 10번이 '코'입니다)
    # 512x512 크기의 결과를 원본 크기로 복구
    mask_pil = Image.fromarray(mask.astype(np.uint8))
    restored_mask = np.array(mask_pil.resize(original_size, resample=Image.NEAREST))
    
    # 코 영역(10)만 흰색(255), 나머지는 검은색(0)인 이진 마스크 생성
    nose_mask_array = (restored_mask == 10).astype(np.uint8) * 255
    nose_mask_image = Image.fromarray(nose_mask_array)
    nose_mask_image = nose_mask_image.filter(ImageFilter.MinFilter(5))

    # 2. SDXL 인페인팅 실행
    # strength: 원본을 얼마나 유지할지 (0.7~0.8 추천)
    # guidance_scale: 프롬프트를 얼마나 따를지 (7.5~12 추천)
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt, # 이상한 모양이나 흉측한 형태, 화질 저하 방지
        image=original_image,
        mask_image=nose_mask_image,
        num_inference_steps=30, # 생성 단계 수 숫자 높을수록 계산 많이 한거, 더 정교해짐 (근데 시간도 오래걸림)
        strength=0.8, # 기존의 형태를 얼마나 무시하고 새로 그릴 것인가 
        guidance_scale=7.5,
        # num_images_per_prompt=4, # 한 번에 4장 생성 명령
    ).images[0]

    # 3. 결과 반환
    img_byte_arr = io.BytesIO()
    result.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # 4. 스트리밍 방식으로 이미지 반환
    return StreamingResponse(img_byte_arr, media_type="image/png")