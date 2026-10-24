
from sqlalchemy import Column, Integer, String, Boolean
from database import Base
from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    is_active = Column(Boolean, default=True, nullable=False)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    is_published = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    title = Column(String(200), nullable=False)
    content = Column(String(5000), nullable=True)
    order_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "order_number",
            name="uq_lesson_course_order"
        ),
    )



class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    enrolled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_student_course_enrollment"
        ),
    )



class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)

    enrollment_id = Column(
        Integer,
        ForeignKey("enrollments.id"),
        nullable=False
    )

    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id"),
        nullable=False
    )

    completed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "enrollment_id",
            "lesson_id",
            name="uq_enrollment_lesson_progress"
        ),
    )
