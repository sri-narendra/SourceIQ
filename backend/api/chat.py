from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import Conversation, Message, User
from repositories.base import ConversationRepository, WorkspaceRepository
from schemas.contracts import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _require_workspace(db: Session, workspace_id: str, user: User):
    ws = WorkspaceRepository(db).get_for_user(workspace_id, str(user.id))
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


def _require_conversation(db: Session, conversation_id: str, user: User) -> Conversation:
    convo = ConversationRepository(db).get(conversation_id)
    if not convo or convo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return convo


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_workspace(db, str(body.workspace_id), user)
    if body.conversation_id:
        _require_conversation(db, str(body.conversation_id), user)
    svc = ChatService(db)
    return svc.answer(
        str(body.workspace_id),
        str(user.id),
        body.message,
        conversation_id=str(body.conversation_id) if body.conversation_id else None,
    )


@router.get("/history")
def chat_history(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_conversation(db, conversation_id, user)
    svc = ChatService(db)
    messages = svc.history(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [{"role": m.role.value, "content": m.content} for m in messages],
    }


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = _require_conversation(db, conversation_id, user)
    for m in db.query(Message).filter(Message.conversation_id == convo.id):
        db.delete(m)
    db.delete(convo)
    db.commit()
    return {"success": True, "message": "Conversation deleted"}
