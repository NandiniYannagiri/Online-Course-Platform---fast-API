
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from main import app
from database import get_db
from models import User, Course, Lesson, Enrollment, Progress
from test_database import (
    create_test_tables,
    override_get_db,
    TestingSessionLocal,
)
from security import create_access_token
from models import User




# Create tables in the separate SQLite test database
create_test_tables()

# Use SQLite instead of MySQL for API tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    # Clear test data before each test
    db = TestingSessionLocal()
    try:
        db.execute(delete(Progress))
        db.execute(delete(Enrollment))
        db.execute(delete(Lesson))
        db.execute(delete(Course))
        db.execute(delete(User))
        db.commit()
    finally:
        db.close()

    with TestClient(app) as test_client:
        yield test_client


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Online Course Platform API is running"
    }


def test_register_student(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test Student",
            "email": "teststudent@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Student"
    assert response.json()["email"] == "teststudent@example.com"
    assert "hashed_password" not in response.json()


def test_login_student(client):
    # Register a student for this test
    client.post(
        "/auth/register",
        json={
            "name": "Test Student",
            "email": "teststudent@example.com",
            "password": "TestPassword123!"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "teststudent@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "name": "Test Student",
            "email": "teststudent@example.com",
            "password": "TestPassword123!"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "teststudent@example.com",
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknownstudent@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_register_duplicate_email(client):
    registration_data = {
        "name": "Test Student",
        "email": "teststudent@example.com",
        "password": "TestPassword123!"
    }

    first_response = client.post(
        "/auth/register",
        json=registration_data
    )

    second_response = client.post(
        "/auth/register",
        json=registration_data
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email is already registered"




def test_create_course_without_login(client):
    response = client.post(
        "/courses/",
        json={
            "title": "Python Basics",
            "description": "Introduction to Python",
            "price": 499
        }
    )

    assert response.status_code in [401, 403]




def test_student_cannot_create_course(client):
    # Register a student
    client.post(
        "/auth/register",
        json={
            "name": "Test Student",
            "email": "studentcourse@example.com",
            "password": "TestPassword123!"
        }
    )

    # Log in as the student
    login_response = client.post(
        "/auth/login",
        json={
            "email": "studentcourse@example.com",
            "password": "TestPassword123!"
        }
    )

    token = login_response.json()["access_token"]

    # Try to create a course as a student
    response = client.post(
        "/courses/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Python Basics",
            "description": "Introduction to Python",
            "price": 499
        }
    )

    assert response.status_code == 403




def test_instructor_can_create_course(client):
    # Create an instructor in the SQLite test database
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="instructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        instructor_id = instructor.id
    finally:
        db.close()

    # Generate a valid token for the instructor
    token = create_access_token(
        user_id=instructor_id,
        role="instructor"
    )

    # Create a course as the instructor
    response = client.post(
        "/courses/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Python Basics",
            "description": "Introduction to Python",
            "price": 499
        }
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Python Basics"
    assert response.json()["instructor_id"] == instructor_id
    assert response.json()["is_published"] is False




def test_instructor_can_publish_own_course(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Instructor One",
            email="instructor1@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        instructor_id = instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(
        user_id=instructor_id,
        role="instructor"
    )

    response = client.patch(
        f"/courses/{course_id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["is_published"] is True


def test_instructor_cannot_publish_others_course(client):
    db = TestingSessionLocal()
    try:
        instructor_one = User(
            name="Instructor One",
            email="instructor1@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        instructor_two = User(
            name="Instructor Two",
            email="instructor2@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        db.add_all([instructor_one, instructor_two])
        db.commit()
        db.refresh(instructor_one)
        db.refresh(instructor_two)

        course = Course(
            instructor_id=instructor_one.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        other_instructor_id = instructor_two.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(
        user_id=other_instructor_id,
        role="instructor"
    )

    response = client.patch(
        f"/courses/{course_id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can publish only your own courses"
    )




def test_instructor_can_update_own_course(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Instructor One",
            email="instructor1@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        course = Course(
            instructor_id=instructor.id,
            title="Old Title",
            description="Old description",
            price=100,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        instructor_id = instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(instructor_id, "instructor")

    response = client.put(
        f"/courses/{course_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Python Course",
            "description": "Updated description",
            "price": 599
        }
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Python Course"
    assert float(response.json()["price"]) == 599.0


def test_instructor_cannot_update_others_course(client):
    db = TestingSessionLocal()
    try:
        owner = User(
            name="Course Owner",
            email="owner@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        other_instructor = User(
            name="Other Instructor",
            email="other@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        db.add_all([owner, other_instructor])
        db.commit()
        db.refresh(owner)
        db.refresh(other_instructor)

        course = Course(
            instructor_id=owner.id,
            title="Original Course",
            description="Original description",
            price=100,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        other_instructor_id = other_instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(other_instructor_id, "instructor")

    response = client.put(
        f"/courses/{course_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Unauthorized Update",
            "description": "Attempted update",
            "price": 999
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can update only your own courses"
    )




def test_instructor_can_delete_own_course(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Instructor One",
            email="instructor1@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        course = Course(
            instructor_id=instructor.id,
            title="Course to Delete",
            description="Test course",
            price=100,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        instructor_id = instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(instructor_id, "instructor")

    response = client.delete(
        f"/courses/{course_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Course deleted successfully"


def test_instructor_cannot_delete_others_course(client):
    db = TestingSessionLocal()
    try:
        owner = User(
            name="Course Owner",
            email="owner@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        other_instructor = User(
            name="Other Instructor",
            email="other@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        db.add_all([owner, other_instructor])
        db.commit()
        db.refresh(owner)
        db.refresh(other_instructor)

        course = Course(
            instructor_id=owner.id,
            title="Protected Course",
            description="Another instructor owns this",
            price=100,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        other_instructor_id = other_instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(other_instructor_id, "instructor")

    response = client.delete(
        f"/courses/{course_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can delete only your own courses"
    )




def test_instructor_can_create_lesson(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="lessoninstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        instructor_id = instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(instructor_id, "instructor")

    response = client.post(
        f"/courses/{course_id}/lessons",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Introduction to Python",
            "content": "Learn Python fundamentals",
            "order_number": 1
        }
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Introduction to Python"
    assert response.json()["course_id"] == course_id
    assert response.json()["order_number"] == 1




def test_instructor_cannot_create_lesson_in_others_course(client):
    db = TestingSessionLocal()
    try:
        owner = User(
            name="Course Owner",
            email="lessonowner@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        other_instructor = User(
            name="Other Instructor",
            email="lessonother@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        db.add_all([owner, other_instructor])
        db.commit()
        db.refresh(owner)
        db.refresh(other_instructor)

        course = Course(
            instructor_id=owner.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        other_instructor_id = other_instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(other_instructor_id, "instructor")

    response = client.post(
        f"/courses/{course_id}/lessons",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Unauthorized Lesson",
            "content": "This should not be created",
            "order_number": 1
        }
    )

    assert response.status_code == 403




def test_instructor_can_update_own_lesson(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="updateinstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        lesson = Lesson(
            course_id=course.id,
            title="Old Lesson Title",
            content="Old content",
            order_number=1
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        instructor_id = instructor.id
        lesson_id = lesson.id
    finally:
        db.close()

    token = create_access_token(instructor_id, "instructor")

    response = client.put(
        f"/courses/lessons/{lesson_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Lesson Title",
            "content": "Updated lesson content",
            "order_number": 1
        }
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Lesson Title"




def test_instructor_cannot_update_others_lesson(client):
    db = TestingSessionLocal()
    try:
        owner = User(
            name="Course Owner",
            email="lessonupdateowner@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        other_instructor = User(
            name="Other Instructor",
            email="lessonupdateother@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )

        db.add_all([owner, other_instructor])
        db.commit()
        db.refresh(owner)
        db.refresh(other_instructor)

        course = Course(
            instructor_id=owner.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        lesson = Lesson(
            course_id=course.id,
            title="Original Lesson",
            content="Original content",
            order_number=1
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        other_instructor_id = other_instructor.id
        lesson_id = lesson.id
    finally:
        db.close()

    token = create_access_token(other_instructor_id, "instructor")

    response = client.put(
        f"/courses/lessons/{lesson_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Unauthorized Update",
            "content": "Changed content",
            "order_number": 1
        }
    )

    assert response.status_code == 403




def test_instructor_can_delete_own_lesson(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="deletelesson@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        lesson = Lesson(
            course_id=course.id,
            title="Lesson to Delete",
            content="Test content",
            order_number=1
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        instructor_id = instructor.id
        lesson_id = lesson.id
    finally:
        db.close()

    token = create_access_token(instructor_id, "instructor")

    response = client.delete(
        f"/courses/lessons/{lesson_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200



def test_student_can_enroll_in_published_course(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="enrollinstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        student = User(
            name="Test Student",
            email="enrollstudent@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )

        db.add_all([instructor, student])
        db.commit()
        db.refresh(instructor)
        db.refresh(student)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=True
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        student_id = student.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(student_id, "student")

    response = client.post(
        "/courses/enrollments",
        headers={"Authorization": f"Bearer {token}"},
        json={"course_id": course_id}
    )

    assert response.status_code == 201
    assert response.json()["student_id"] == student_id
    assert response.json()["course_id"] == course_id
    assert response.json()["is_active"] is True



def test_student_cannot_enroll_twice(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="duplicateenrollinstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        student = User(
            name="Test Student",
            email="duplicateenrollstudent@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )

        db.add_all([instructor, student])
        db.commit()
        db.refresh(instructor)
        db.refresh(student)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=True
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        student_id = student.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(student_id, "student")
    headers = {"Authorization": f"Bearer {token}"}
    enrollment_data = {"course_id": course_id}

    first_response = client.post(
        "/courses/enrollments",
        headers=headers,
        json=enrollment_data
    )
    second_response = client.post(
        "/courses/enrollments",
        headers=headers,
        json=enrollment_data
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "You are already enrolled in this course"
    )



def test_student_cannot_enroll_in_unpublished_course(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="unpublishedinstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        student = User(
            name="Test Student",
            email="unpublishedstudent@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )

        db.add_all([instructor, student])
        db.commit()
        db.refresh(instructor)
        db.refresh(student)

        course = Course(
            instructor_id=instructor.id,
            title="Unpublished Python Course",
            description="Not yet available",
            price=499,
            is_published=False
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        student_id = student.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(student_id, "student")

    response = client.post(
        "/courses/enrollments",
        headers={"Authorization": f"Bearer {token}"},
        json={"course_id": course_id}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Published course not found"



def test_student_cannot_mark_another_students_lesson_complete(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="progressinstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        student_one = User(
            name="Student One",
            email="progressstudent1@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )
        student_two = User(
            name="Student Two",
            email="progressstudent2@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )

        db.add_all([instructor, student_one, student_two])
        db.commit()
        db.refresh(instructor)
        db.refresh(student_one)
        db.refresh(student_two)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=True
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        enrollment = Enrollment(
            student_id=student_one.id,
            course_id=course.id
        )
        lesson = Lesson(
            course_id=course.id,
            title="Introduction",
            content="Python basics",
            order_number=1
        )

        db.add_all([enrollment, lesson])
        db.commit()
        db.refresh(enrollment)
        db.refresh(lesson)

        student_two_id = student_two.id
        enrollment_id = enrollment.id
        lesson_id = lesson.id
    finally:
        db.close()

    token = create_access_token(student_two_id, "student")

    response = client.post(
        "/progress/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enrollment_id": enrollment_id,
            "lesson_id": lesson_id
        }
    )

    assert response.status_code in [403, 404]




def test_student_can_view_own_progress(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="Test Instructor",
            email="ownprogressinstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        student = User(
            name="Progress Student",
            email="ownprogressstudent@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )

        db.add_all([instructor, student])
        db.commit()
        db.refresh(instructor)
        db.refresh(student)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=True
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        lesson = Lesson(
            course_id=course.id,
            title="Introduction",
            content="Python basics",
            order_number=1
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        progress = Progress(
            enrollment_id=enrollment.id,
            lesson_id=lesson.id
        )
        db.add(progress)
        db.commit()

        student_id = student.id
        enrollment_id = enrollment.id
    finally:
        db.close()

    token = create_access_token(student_id, "student")

    response = client.get(
        f"/enrollments/{enrollment_id}/progress",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["enrollment_id"] == enrollment_id
    assert response.json()["total_lessons"] == 1
    assert response.json()["completed_lessons"] == 1
    assert response.json()["progress_percentage"] == 100.0




def test_instructor_cannot_view_others_students(client):
    db = TestingSessionLocal()
    try:
        owner = User(
            name="Course Owner",
            email="studentsowner@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        other_instructor = User(
            name="Other Instructor",
            email="studentsother@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        student = User(
            name="Enrolled Student",
            email="enrolledstudent@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )

        db.add_all([owner, other_instructor, student])
        db.commit()
        db.refresh(owner)
        db.refresh(other_instructor)
        db.refresh(student)

        course = Course(
            instructor_id=owner.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=True
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id
        )
        db.add(enrollment)
        db.commit()

        other_instructor_id = other_instructor.id
        course_id = course.id
    finally:
        db.close()

    token = create_access_token(other_instructor_id, "instructor")

    response = client.get(
        f"/courses/{course_id}/students",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404




def test_student_cannot_view_lesson_pdf_without_enrollment(client):
    db = TestingSessionLocal()
    try:
        instructor = User(
            name="PDF Instructor",
            email="pdfinstructor@example.com",
            hashed_password="test-hash",
            role="instructor",
            is_active=True
        )
        student = User(
            name="Unenrolled Student",
            email="pdfstudent@example.com",
            hashed_password="test-hash",
            role="student",
            is_active=True
        )

        db.add_all([instructor, student])
        db.commit()
        db.refresh(instructor)
        db.refresh(student)

        course = Course(
            instructor_id=instructor.id,
            title="Python Basics",
            description="Learn Python",
            price=499,
            is_published=True
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        lesson = Lesson(
            course_id=course.id,
            title="Python Notes",
            content="Lesson notes",
            order_number=1,
            file_path="uploads/test_notes.pdf"
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        student_id = student.id
        lesson_id = lesson.id
    finally:
        db.close()

    token = create_access_token(student_id, "student")

    response = client.get(
        f"/courses/lessons/{lesson_id}/view",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code in [403, 404]
