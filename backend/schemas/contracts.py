from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class WorkspaceCreate(BaseModel):
    name: str = Field(max_length=120)
    description: Optional[str] = None


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    documents: int = 0


class DocumentOut(BaseModel):
    id: UUID
    name: str
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    workspace_id: UUID
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    conversation_id: Optional[str] = None


class SearchRequest(BaseModel):
    workspace_id: UUID
    query: str


class SearchResult(BaseModel):
    document: str
    page: Optional[int]
    text: str
    score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]


class DashboardSummary(BaseModel):
    documents: int
    conversations: int
    storage_used_mb: int
    workspace_count: int


class ErrorResponse(BaseModel):
    success: bool = False
    error: dict
