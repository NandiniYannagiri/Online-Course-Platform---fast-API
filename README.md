# Online Course Platform API

A backend application built using **Python, FastAPI, MySQL, and SQLAlchemy** to manage online courses, lessons, student enrollments, and learning progress.

## Overview

The Online Course Platform provides APIs for students, instructors, and administrators to manage the online learning process.

- **Students:** Register, log in, browse published courses, enroll in courses, and track lesson completion.
- **Instructors:** Create and manage courses, add lessons, upload lesson files, and view enrolled students.
- **Administrators:** Delete courses when required.

## Tech Stack

- **Language:** Python
- **Backend Framework:** FastAPI
- **Database:** MySQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT (JSON Web Tokens)
- **Password Security:** Password hashing
- **Database Migrations:** Alembic
- **API Documentation:** Swagger UI

## Features

### Authentication
- Student registration
- Login with email and password
- JWT-based authentication
- Role-based access control

### Course Management
- Create and update courses
- Publish courses
- List published courses with pagination
- Retrieve course details and lessons
- Delete courses with administrator permissions

### Lesson Management
- Add, update, and delete lessons
- Upload lesson files
- Restrict lesson-file access to enrolled students

### Enrollment Management
- Enroll in published courses
- Prevent duplicate enrollments
- View enrolled courses
- Allow instructors to view enrolled students

### Learning Progress
- Mark lessons as completed
- Track student progress
- Calculate course completion percentage
- Allow instructors to view student progress

## Project Structure

```text
OnlineCoursePlatform/
├── main.py
├── auth.py
├── courses.py
├── models.py
├── database.py
├── security.py
├── dependencies.py
├── course_schemas.py
├── .env
├── .gitignore
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── uploads/
└── venv/
```

*Note: This is the expected structure based on the project files discussed. Adjust it if your actual folders differ.*

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd OnlineCoursePlatform
```

Replace `YOUR_REPOSITORY_URL` with your GitHub repository URL.

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy "pymysql" python-dotenv pyjwt "pwdlib[argon2]" alembic python-multipart
```

Ensure the installed database driver matches the one used in your `DATABASE_URL`.

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=your_mysql_connection_string
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Replace the example values with your own configuration. Never commit `.env` or expose database credentials and secret keys publicly.

### 5. Apply database migrations

```bash
python -m alembic upgrade head
```

Make sure MySQL is running and the configured database exists before applying migrations.

### 6. Start the application

```bash
python -m uvicorn main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

## API Documentation

FastAPI provides interactive API documentation through Swagger UI.

Open:

`http://127.0.0.1:8000/docs`

Use Swagger UI to explore endpoints, provide request data, authenticate, and test API operations.

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register a student |
| POST | `/auth/login` | Log in and receive a JWT |
| GET | `/courses` | List published courses |
| GET | `/courses/{id}` | Retrieve course details |
| POST | `/courses` | Create a course |
| PUT | `/courses/{id}` | Update a course |
| PATCH | `/courses/{id}/publish` | Publish a course |
| DELETE | `/courses/{id}` | Delete a course (admin) |
| POST | `/courses/{id}/lessons` | Add a lesson |
| PUT | `/lessons/{id}` | Update a lesson |
| POST | `/lessons/{id}/upload` | Upload a lesson file |
| DELETE | `/lessons/{id}` | Delete a lesson |
| POST | `/enrollments` | Enroll in a course |
| GET | `/enrollments/my` | View enrolled courses |
| GET | `/courses/{id}/students` | View enrolled students |
| POST | `/progress` | Mark a lesson complete |
| GET | `/enrollments/{id}/progress` | View enrollment progress |

## Security

- Passwords are stored using password hashing.
- JWTs are used for authenticated API access.
- Role-based permissions restrict protected operations.
- Environment variables store sensitive configuration.
- Lesson files are protected by enrollment and authorization checks.

## Future Improvements

- Deploy the backend to a cloud hosting platform.
- Configure managed MySQL hosting.
- Add persistent file storage for lesson uploads.
- Add automated testing and continuous integration.
- Develop a frontend for students and instructors.

## Author

Developed as a practical backend project to demonstrate REST API development, database integration, authentication, authorization, and course management using Python and FastAPI.
