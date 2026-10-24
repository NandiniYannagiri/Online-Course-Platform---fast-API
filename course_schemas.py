from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: float = Field(default=0, ge=0)


class CourseResponse(BaseModel):
    id: int
    instructor_id: int
    title: str
    description: str | None
    price: float
    is_published: bool

    model_config = ConfigDict(from_attributes=True)


class LessonCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str | None = Field(default=None, max_length=5000)
    order_number: int = Field(ge=1)


class LessonResponse(BaseModel):
    id: int
    course_id: int
    title: str
    content: str | None
    order_number: int
    file_path: str | None

    model_config = ConfigDict(from_attributes=True)



class LessonUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str | None = Field(default=None, max_length=5000)
    order_number: int = Field(ge=1)


class EnrollmentCreate(BaseModel):
    course_id: int = Field(gt=0)


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MyEnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    is_active: bool
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnrolledStudentResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ProgressCreate(BaseModel):
    enrollment_id: int = Field(gt=0)
    lesson_id: int = Field(gt=0)


class ProgressResponse(BaseModel):
    id: int
    enrollment_id: int
    lesson_id: int
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProgressSummaryResponse(BaseModel):
    enrollment_id: int
    total_lessons: int
    completed_lessons: int
    progress_percentage: float


class StudentProgressResponse(BaseModel):
    student_id: int
    student_name: str
    enrollment_id: int
    total_lessons: int
    completed_lessons: int
    progress_percentage: float