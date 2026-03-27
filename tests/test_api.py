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


def test_job_and_assessment():
    # Login
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a Knowledge Graph node (skill)
    skill_resp = client.post("/api/v1/business/knowledge-graph", headers=headers, json={
        "concept_name": "Python",
        "description": "Python Programming",
        "tags": ["backend", "language"]
    })
    assert skill_resp.status_code == 200
    skill_id = skill_resp.json()["data"]["id"]

    
    # 2. Create Job Position
    job_resp = client.post("/api/v1/jobs", headers=headers, json={
        "title": "Backend Developer",
        "level": "junior",
        "industry": "IT",
        "skill_ids": [skill_id]
    })
    assert job_resp.status_code == 200
    job_id = job_resp.json()["data"]["id"]
    
    # 3. Get Job Skill Tree
    tree_resp = client.get(f"/api/v1/jobs/{job_id}/skill-tree", headers=headers)
    assert tree_resp.status_code == 200
    assert tree_resp.json()["data"]["job_title"] == "Backend Developer"
    
    # 4. Create Assessment
    assess_resp = client.post("/api/v1/assessments", headers=headers, json={
        "title": "Python Test",
        "job_position_id": job_id,
        "questions": [
            {
                "knowledge_graph_id": skill_id,
                "question_type": "single_choice",
                "content": "What is Python?",
                "options": [{"id": "A", "text": "Snake"}, {"id": "B", "text": "Language"}],
                "correct_answer": "B",
                "score_weight": 10.0
            }
        ]
    })
    assert assess_resp.status_code == 200
    assessment_data = assess_resp.json()["data"]
    assess_id = assessment_data["id"]
    question_id = assessment_data["questions"][0]["id"]
    
    # 5. Submit Assessment
    submit_resp = client.post("/api/v1/assessments/submit", headers=headers, json={
        "assessment_id": assess_id,
        "answers": [
            {
                "question_id": question_id,
                "answer": "B" # Correct
            }
        ]
    })
    assert submit_resp.status_code == 200
    assert submit_resp.json()["data"]["total_score"] == 10.0
    
    # 6. Check Job Match
    match_resp = client.get(f"/api/v1/jobs/{job_id}/match", headers=headers)
    assert match_resp.status_code == 200
    # 10.0 out of 10.0 for that skill -> 100% mastery -> 100% match
    assert match_resp.json()["data"] == 100.0


