from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from database import get_db
from models import User
from schemas import UserRegister, UserResponse
from schemas import UserRegister, UserResponse, UserLogin, TokenResponse
from security import create_access_token


router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    # Public registration is restricted to student accounts.
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=password_hash.hash(user_data.password),
        role="student"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not password_hash.verify(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive"
        )

    access_token = create_access_token(
    user_id=user.id,
    role=user.role
    )

    return {
    "access_token": access_token,
    "token_type": "bearer"
}