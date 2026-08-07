from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])


class ProfileUpdate(BaseModel):
    name: str | None = None


@router.put("/profile")
def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name:
        user.name = body.name
    db.commit()
    return {"success": True}
