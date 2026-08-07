from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User
from schemas.contracts import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = ChatService(db)
    return svc.answer(str(body.workspace_id), str(user.id), body.message)


@router.get("/history")
def chat_history(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = ChatService(db)
    messages = svc.history(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [{"role": m.role.value, "content": m.content} for m in messages],
    }
