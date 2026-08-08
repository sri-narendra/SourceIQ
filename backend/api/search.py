from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User
from repositories.base import WorkspaceRepository
from schemas.contracts import SearchRequest, SearchResponse
from services.search_service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    body: SearchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    ws = WorkspaceRepository(db).get_for_user(str(body.workspace_id), str(user.id))
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    svc = SearchService(db)
    results = svc.semantic_search(str(body.workspace_id), body.query)
    return SearchResponse(results=results)
