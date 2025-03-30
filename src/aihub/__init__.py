from fastapi import FastAPI
from aihub.api.v1 import users, chat
from aihub.core.database import engine
from aihub.models.user import UserModel


# 데이터베이스 테이블 생성
UserModel.metadata.create_all(bind=engine)

app = FastAPI(
    title="AIHub API",
    description="AI 서비스를 위한 API",
    version="0.1.0"
)

# API 라우터 등록 (prefix 제거)
app.include_router(users.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message": "AIHub API에 오신 것을 환영합니다!"}
