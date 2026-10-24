
from fastapi import FastAPI
from auth import router as auth_router
from dependencies import get_current_user
from fastapi import Depends
from models import User
from dependencies import require_roles
from courses import router as courses_router
from courses import enrollment_router
from courses import progress_router
from fastapi import Depends
from admin import router as admin_router

app = FastAPI(title="Online Course Platform API")

app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(enrollment_router)
app.include_router(progress_router)
app.include_router(admin_router)


@app.get("/")
def home():
    return {
        "message": "Online Course Platform API is running"
    }

@app.get("/users/me")
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }

@app.get("/instructor/test")
def instructor_test(
    current_user: User = Depends(require_roles(["instructor"]))
):
    return {
        "message": "Instructor access granted",
        "user": current_user.name
    }



