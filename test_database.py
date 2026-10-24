
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_database.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


def create_test_tables():
    Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
