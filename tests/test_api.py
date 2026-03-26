from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.main import app
from src.db.database import Base, get_db
from src.models.user import User, Role, Permission
import pytest
from unittest.mock import patch

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create test data
    admin_role = Role(name="admin", description="Admin Role")
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)
    
    perm = Permission(name="all", resource="all", action="all")
    db.add(perm)
    db.commit()
    db.refresh(perm)
    
    admin_role.permissions.append(perm)
    
    from src.core import security
    hashed = security.get_password_hash("Admin@123")
    user = User(
        username="admin_test",
        email="admin_test@example.com",
        phone="13800138000",
        hashed_password=hashed,
        is_active=True
    )
    user.roles.append(admin_role)
    db.add(user)
    db.commit()
    
    yield
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_openapi_schema():
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

def test_register_user():
    response = client.post("/api/v1/auth/register", json={
        "username": "new_user",
        "email": "new@example.com",
        "password": "Password@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["username"] == "new_user"

def test_login_user():
    response = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "access_token" in data["data"]

def test_get_me():
    # Login first
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    token = login_resp.json()["data"]["access_token"]
    
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "admin_test"


