from fastapi import APIRouter
from aihub.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # TODO: 실제 AI 모델 연동
    return ChatResponse(
        response=f"선택된 모델({request.model})과 에이전트({', '.join(request.agents)})로 응답합니다.",
        model=request.model,
        agents=request.agents
    ) 