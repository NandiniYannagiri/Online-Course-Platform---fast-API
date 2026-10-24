from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Course, User, Lesson, Enrollment, Progress
from dependencies import require_roles
from course_schemas import CourseCreate, CourseResponse
from fastapi import HTTPException
from course_schemas import (
    CourseCreate,
    CourseResponse,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    EnrollmentCreate,
    EnrollmentResponse,
    MyEnrollmentResponse,
    EnrolledStudentResponse,
    ProgressCreate,
    ProgressResponse,
    ProgressSummaryResponse,
    StudentProgressResponse
)

import os
import shutil
from fastapi import UploadFile, File
from fastapi.responses import FileResponse




router = APIRouter(prefix='/courses', tags=["Courses"])
enrollment_router = APIRouter(prefix="/enrollments",tags=["Enrollments"])
progress_router = APIRouter(prefix="/progress",tags=["Progress"])


@router.post("/", response_model=CourseResponse, status_code=201)
def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    new_course = Course(
        instructor_id=current_user.id,
        title=course_data.title,
        description=course_data.description,
        price=course_data.price,
        is_published=False
    )

    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    return new_course


@router.get("/", response_model=list[CourseResponse])
def get_courses(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    courses = (
        db.query(Course)
        .filter(Course.is_published == True)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return courses


@router.patch("/{course_id}/publish", response_model=CourseResponse)
def publish_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    if course.instructor_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="You can publish only your own courses"
        )

    course.is_published = True

    db.commit()
    db.refresh(course)

    return course


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.is_published == True
        )
        .first()
    )

    if course is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Published course not found"
        )

    return course


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    if course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can update only your own courses"
        )

    course.title = course_data.title
    course.description = course_data.description
    course.price = course_data.price

    db.commit()
    db.refresh(course)

    return course



@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    db.delete(course)
    db.commit()

    return {
        "message": "Course deleted successfully"
    }



@router.post(
    "/{course_id}/lessons",
    response_model=LessonResponse,
    status_code=201
)
def create_lesson(
    course_id: int,
    lesson_data: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    if course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can add lessons only to your own courses"
        )

    existing_lesson = db.query(Lesson).filter(
        Lesson.course_id == course_id,
        Lesson.order_number == lesson_data.order_number
    ).first()

    if existing_lesson:
        raise HTTPException(
            status_code=409,
            detail="This lesson order number is already used"
        )

    new_lesson = Lesson(
        course_id=course_id,
        title=lesson_data.title,
        content=lesson_data.content,
        order_number=lesson_data.order_number
    )

    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)

    return new_lesson


@router.get("/{course_id}/lessons", response_model=list[LessonResponse])
def get_course_lessons(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.is_published == True
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Published course not found"
        )

    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course_id)
        .order_by(Lesson.order_number)
        .all()
    )

    return lessons


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )

    course = db.query(Course).filter(
        Course.id == lesson.course_id
    ).first()

    if course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can update lessons only in your own courses"
        )

    existing_lesson = db.query(Lesson).filter(
        Lesson.course_id == lesson.course_id,
        Lesson.order_number == lesson_data.order_number,
        Lesson.id != lesson_id
    ).first()

    if existing_lesson:
        raise HTTPException(
            status_code=409,
            detail="This lesson order number is already used"
        )

    lesson.title = lesson_data.title
    lesson.content = lesson_data.content
    lesson.order_number = lesson_data.order_number

    db.commit()
    db.refresh(lesson)

    return lesson


@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )

    course = db.query(Course).filter(
        Course.id == lesson.course_id
    ).first()

    if course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can delete lessons only from your own courses"
        )

    db.delete(lesson)
    db.commit()

    return {
        "message": "Lesson deleted successfully"
    }


@router.post(
    "/enrollments",
    response_model=EnrollmentResponse,
    status_code=201
)
def enroll_in_course(
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    course = db.query(Course).filter(
        Course.id == enrollment_data.course_id,
        Course.is_published == True
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Published course not found"
        )

    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.course_id == course.id
    ).first()

    if existing_enrollment:
        raise HTTPException(
            status_code=409,
            detail="You are already enrolled in this course"
        )

    new_enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course.id
    )

    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)

    return new_enrollment


@enrollment_router.get("/my", response_model=list[MyEnrollmentResponse])
def get_my_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    enrollments = db.query(Enrollment).filter(
        Enrollment.student_id == current_user.id
    ).all()

    return enrollments


@router.get("/{course_id}/students", response_model=list[EnrolledStudentResponse])
def get_enrolled_students(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.instructor_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found or you do not own this course"
        )

    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.is_active == True
    ).all()

    students = []

    for enrollment in enrollments:
        student = db.query(User).filter(
            User.id == enrollment.student_id
        ).first()

        if student:
            students.append(student)

    return students

@progress_router.post("/", response_model=ProgressResponse, status_code=201)
def mark_lesson_completed(
    data: ProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    enrollment = db.query(Enrollment).filter(
        Enrollment.id == data.enrollment_id,
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Active enrollment not found"
        )

    lesson = db.query(Lesson).filter(
        Lesson.id == data.lesson_id,
        Lesson.course_id == enrollment.course_id
    ).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found in this enrolled course"
        )

    existing_progress = db.query(Progress).filter(
        Progress.enrollment_id == enrollment.id,
        Progress.lesson_id == lesson.id
    ).first()

    if existing_progress:
        return existing_progress

    progress = Progress(
        enrollment_id=enrollment.id,
        lesson_id=lesson.id
    )

    db.add(progress)
    db.commit()
    db.refresh(progress)

    return progress


@enrollment_router.get(
    "/{enrollment_id}/progress",
    response_model=ProgressSummaryResponse
)
def get_enrollment_progress(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    enrollment = db.query(Enrollment).filter(
        Enrollment.id == enrollment_id,
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Active enrollment not found"
        )

    total_lessons = db.query(Lesson).filter(
        Lesson.course_id == enrollment.course_id
    ).count()

    completed_lessons = db.query(Progress).filter(
        Progress.enrollment_id == enrollment.id
    ).count()

    if total_lessons == 0:
        percentage = 0.0
    else:
        percentage = (completed_lessons / total_lessons) * 100

    return {
        "enrollment_id": enrollment.id,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": round(percentage, 2)
    }


@router.get(
    "/{course_id}/students/progress",
    response_model=list[StudentProgressResponse]
)
def get_students_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.instructor_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found or you do not own this course"
        )

    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.is_active == True
    ).all()

    result = []

    total_lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).count()

    for enrollment in enrollments:
        student = db.query(User).filter(
            User.id == enrollment.student_id
        ).first()

        completed_lessons = db.query(Progress).filter(
            Progress.enrollment_id == enrollment.id
        ).count()

        if total_lessons == 0:
            percentage = 0.0
        else:
            percentage = (completed_lessons / total_lessons) * 100

        result.append({
            "student_id": student.id,
            "student_name": student.name,
            "enrollment_id": enrollment.id,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percentage": round(percentage, 2)
        })

    return result


@router.post("/lessons/{lesson_id}/upload")
def upload_lesson_pdf(
    lesson_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["instructor"]))
):
    lesson = db.query(Lesson).join(Course).filter(
        Lesson.id == lesson_id,
        Course.instructor_id == current_user.id
    ).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found or you do not own this course"
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join("uploads", file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    lesson.file_path = file_path
    db.commit()
    db.refresh(lesson)

    return {
        "message": "PDF uploaded successfully",
        "lesson_id": lesson.id,
        "file_path": lesson.file_path
    }


@router.get("/lessons/{lesson_id}/view")
def view_lesson_pdf(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    lesson = db.query(Lesson).join(Course).join(
        Enrollment,
        Enrollment.course_id == Course.id
    ).filter(
        Lesson.id == lesson_id,
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found or you are not enrolled in this course"
        )

    if not lesson.file_path or not os.path.exists(lesson.file_path):
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    return FileResponse(
        path=lesson.file_path,
        media_type="application/pdf",
        content_disposition_type="inline"
    )