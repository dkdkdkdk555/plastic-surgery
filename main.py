from pathlib import Path
from fastapi import FastAPI
from routers import mediapipe_landmark_api
from routers import face_parsing_api

app = FastAPI()

# 각 지점의 라우터를 본사에 등록(Include)
app.include_router(mediapipe_landmark_api.router)
app.include_router(face_parsing_api.router)

@app.get("/")
def read_root():
    return {"Hello": "Main Server"}