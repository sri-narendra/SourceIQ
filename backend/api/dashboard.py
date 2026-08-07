from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User
from schemas.contracts import DashboardSummary
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = DashboardService(db)
    return svc.summary(str(user.id))
