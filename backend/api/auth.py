from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User
from repositories.base import UserRepository
from schemas.contracts import LoginRequest, RegisterRequest, TokenResponse, UserOut
from services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_by_email(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = repo.create(name=body.name, email=body.email, password_hash=hash_password(body.password))
    token, expires = create_access_token(str(user.id))
    return TokenResponse(
        success=True,
        access_token=token,
        expires_in=expires,
        user=UserOut.from_orm(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token, expires = create_access_token(str(user.id))
    return TokenResponse(
        success=True,
        access_token=token,
        expires_in=expires,
        user=UserOut.from_orm(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
