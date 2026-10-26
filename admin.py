
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
# from security import get_current_user
from dependencies import get_current_user

from pwdlib import PasswordHash
from schemas import UserRegister, UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])
password_hash = PasswordHash.recommended()

def get_admin_user(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }
        for user in users
    ]



@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id == admin.id and not is_active:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot deactivate their own account"
        )

    user.is_active = is_active
    db.commit()
    db.refresh(user)

    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "is_active": user.is_active
    }


@router.post("/instructors", response_model=UserResponse, status_code=201)
def create_instructor(
    instructor_data: UserRegister,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    existing_user = (
        db.query(User)
        .filter(User.email == instructor_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    new_instructor = User(
        name=instructor_data.name,
        email=instructor_data.email,
        hashed_password=password_hash.hash(instructor_data.password),
        role="instructor"
    )

    db.add(new_instructor)
    db.commit()
    db.refresh(new_instructor)

    return new_instructor