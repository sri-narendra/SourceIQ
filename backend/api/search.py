from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User
from schemas.contracts import SearchRequest, SearchResponse
from services.search_service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    body: SearchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    svc = SearchService(db)
    results = svc.semantic_search(str(body.workspace_id), body.query)
    return SearchResponse(results=results)
