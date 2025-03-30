from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from aihub.schemas.chat import ChatRequest, ChatResponse
import json
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # TODO: 실제 AI 모델 연동
    return ChatResponse(
        response=f"선택된 모델({request.model})과 에이전트({', '.join(request.agents)})로 응답합니다.",
        model=request.model,
        agents=request.agents
    )

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        # TODO: 실제 AI 모델 연동
        response_text = f"선택된 모델({request.model})과 에이전트({', '.join(request.agents)})로 응답합니다."
        # 응답을 여러 부분으로 나누어 스트리밍
        words = response_text.split()
        for word in words:
            await asyncio.sleep(0.1)  # 실제 AI 모델 응답 시간 시뮬레이션
            yield f"data: {json.dumps({'content': word + ' '})}\n\n"
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    ) 