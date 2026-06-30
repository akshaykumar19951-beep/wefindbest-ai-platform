import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_wefindbest.db"
os.environ["SECRET_KEY"] = "test-secret"

from app.db.database import Base
from app.db.session import engine
from app.main import app
from app.db.session import SessionLocal
from app.services.billing_service import seed_default_plans


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_default_plans(db)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    Path("test_wefindbest.db").unlink(missing_ok=True)


@pytest.fixture
def client():
    return TestClient(app)
