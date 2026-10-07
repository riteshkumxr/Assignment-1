import os
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment settings before importing app modules
test_db_file = Path("test_bulk_certs.db")
test_storage_dir = Path("storage/test_certificates")

os.environ["DATABASE_URL"] = f"sqlite:///{test_db_file.absolute()}"
os.environ["STORAGE_DIR"] = str(test_storage_dir)

from app.config import settings
settings.DATABASE_URL = f"sqlite:///{test_db_file.absolute()}"
settings.STORAGE_DIR = str(test_storage_dir)

import app.database as app_db
from app.database import Base, get_db
from app.main import app

# Create test engine and sessionmaker
test_engine = create_engine(
    f"sqlite:///{test_db_file.absolute()}",
    connect_args={"check_same_thread": False},
    future=True,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch app.database.SessionLocal and engine so background workers use test DB
app_db.engine = test_engine
app_db.SessionLocal = TestSessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test database and storage directory."""
    if test_db_file.exists():
        test_db_file.unlink()
    if test_storage_dir.exists():
        shutil.rmtree(test_storage_dir)

    test_storage_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=test_engine)

    yield

    # Teardown
    test_engine.dispose()
    if test_db_file.exists():
        try:
            test_db_file.unlink()
        except Exception:
            pass
    if test_storage_dir.exists():
        shutil.rmtree(test_storage_dir, ignore_errors=True)


@pytest.fixture
def db_session():
    """Provide a clean transactional session for test inspection."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
