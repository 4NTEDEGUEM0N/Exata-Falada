import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import app
from app.core import Base, get_db, get_password_hash
from app.models.user_model import UserModel
from sqlalchemy.pool import StaticPool
from app.api.deps import get_storage_provider
from app.integrations.storage.local_storage import LocalStorageProvider


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    admin_user = UserModel(
        username="admin_test",
        password=get_password_hash("testpass"),
        admin=True
    )
    db.add(admin_user)
    
    normal_user = UserModel(
        username="normal_test",
        password=get_password_hash("testpass"),
        admin=False
    )
    db.add(normal_user)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_storage_provider():
    return LocalStorageProvider()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_storage_provider] = override_get_storage_provider

@pytest.fixture(scope="module")
def client(setup_db):
    with TestClient(app) as c:
        yield c
