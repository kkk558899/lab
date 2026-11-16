import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_optional_user
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from app.services import agent_service

router = APIRouter(prefix="/ai", tags=["AI相关的API"])

def _sse_line(payload: dict) -> str:
    """拼一条 SSE 帧：必须以 data: 开头，且以空行（\n\n）结束"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

@router.post("/chat")
def chat(
    data: ChatRequest,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """AI 对话（整包返回）"""
    if not current_user:
        current_user = db.query(User).filter(User.username == "student").first() or db.query(User).first()
    content = agent_service.run_agent(db, current_user, data)
    return Response.success(data=ChatMessage(role="assistant", content=content))

@router.post("/chat/stream")
def chat_stream(
    data: ChatRequest,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """AI 对话（SSE 流式输出与过程可见）"""
    if not current_user:
        current_user = db.query(User).filter(User.username == "student").first() or db.query(User).first()

    def event_gen():
        for event in agent_service.stream_agent(db, current_user, data):
            yield _sse_line(event)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
