from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import (
    create_token,
    hash_password,
    require_user,
    role_for_email,
    verify_password,
)
from app.db.session import get_db
from app.models import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserOut

router = APIRouter()


@router.post("/signup", response_model=AuthResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = body.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Некорректный email")
    if len(body.password) < 6:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Пароль минимум 6 символов"
        )
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Этот email уже зарегистрирован")

    user = User(
        email=email,
        password_hash=hash_password(body.password),
        name=body.name,
        role=role_for_email(email),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthResponse(token=create_token(user), user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
    return AuthResponse(token=create_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(
    claims: dict = Depends(require_user), db: Session = Depends(get_db)
) -> UserOut:
    user = db.get(User, int(claims["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Пользователь не найден")
    return UserOut.model_validate(user)
