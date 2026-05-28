import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.db.database import Base, get_db
from src.models.user import User, Role, Permission
from src.models.learning import Course, CourseMaterial, UserLearningProgress, UserQuestionCollection, UserWrongQuestion, Badge, UserBadge
from src.models.assessment import Assessment, Question, UserAssessmentRecord, UserSkillMastery
from src.models.community import Post, Comment, PostLike, UserFollow
from src.models.notification import Notification
from src.models.business import KnowledgeGraph, JobPosition, InterviewConfig, InterviewSession, AIStrategy, AgentState
from src.models.system import SystemConfig, AuditLog
from src.models.gamification import UserDailyTask
from src.core import security


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class FakeRedis:
    def __init__(self):
        self._store = {}
        self._ttls = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, **kwargs):
        self._store[key] = value
        return True

    def setex(self, key, time, value):
        self._store[key] = value
        self._ttls[key] = time
        return True

    def delete(self, *keys):
        for key in keys:
            self._store.pop(key, None)
            self._ttls.pop(key, None)
        return len(keys)

    def exists(self, key):
        return 1 if key in self._store else 0

    def incr(self, key):
        if key not in self._store:
            self._store[key] = 0
        self._store[key] = int(self._store[key]) + 1
        return self._store[key]

    def expire(self, key, time):
        if key in self._store:
            self._ttls[key] = time
            return True
        return False

    def ttl(self, key):
        return self._ttls.get(key, -2)

    def pipeline(self):
        return FakeRedisPipeline(self)

    def scan_iter(self, match=None):
        if match:
            import fnmatch
            return [k for k in self._store.keys() if fnmatch.fnmatch(k, match)]
        return list(self._store.keys())

    def keys(self, pattern="*"):
        if pattern == "*":
            return list(self._store.keys())
        import fnmatch
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]

    def flushdb(self):
        self._store.clear()
        self._ttls.clear()


class FakeRedisPipeline:
    def __init__(self, redis_instance):
        self._redis = redis_instance
        self._commands = []

    def incr(self, key):
        self._commands.append(('incr', key))
        return self

    def expire(self, key, time):
        self._commands.append(('expire', key, time))
        return self

    def execute(self):
        results = []
        for cmd in self._commands:
            if cmd[0] == 'incr':
                key = cmd[1]
                results.append(self._redis.incr(key))
            elif cmd[0] == 'expire':
                key, time = cmd[1], cmd[2]
                results.append(self._redis.expire(key, time))
        self._commands.clear()
        return results


fake_redis = FakeRedis()


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_redis():
    return fake_redis


def _noop_decorator(*args, **kwargs):
    def decorator(func):
        return func
    return decorator


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    admin_role = Role(name="admin", description="Admin Role")
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

    perm = Permission(name="all", resource="all", action="all")
    db.add(perm)
    db.commit()
    db.refresh(perm)
    admin_role.permissions.append(perm)

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

    student_role = Role(name="student", description="Student Role")
    db.add(student_role)
    db.commit()
    db.refresh(student_role)

    student_perm = Permission(name="view_assessment", resource="assessment", action="view")
    db.add(student_perm)
    db.commit()
    db.refresh(student_perm)
    student_role.permissions.append(student_perm)

    student_hashed = security.get_password_hash("Student@123")
    student_user = User(
        username="student_test",
        email="student_test@example.com",
        phone="13900139000",
        hashed_password=student_hashed,
        is_active=True
    )
    student_user.roles.append(student_role)
    db.add(student_user)
    db.commit()
    db.close()

    import src.db.redis_client as redis_mod
    redis_mod.redis_client = fake_redis
    redis_mod.get_redis = override_get_redis

    import src.core.security as security_mod
    security_mod.get_redis = override_get_redis

    import src.services.auth_service as auth_mod
    auth_mod.get_redis = override_get_redis

    import src.services.role_service as role_mod
    role_mod.get_redis = override_get_redis

    import src.api.deps as deps_mod
    deps_mod.get_redis = override_get_redis

    limiter_mock = MagicMock()
    limiter_mock.limit = _noop_decorator
    import src.core.limiter as limiter_mod
    limiter_mod.limiter = limiter_mock

    from src.main import app
    app.dependency_overrides[get_db] = override_get_db
    app.state.limiter = limiter_mock

    yield app

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_redis():
    fake_redis.flushdb()
    yield
    fake_redis.flushdb()


@pytest.fixture(scope="session")
def app():
    from src.main import app
    return app


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session")
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def admin_token(client):
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    return resp.json()["data"]["access_token"]


@pytest.fixture
def admin_tokens(client):
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    return resp.json()["data"]


@pytest.fixture
def student_token(client):
    resp = client.post("/api/v1/auth/login", json={
        "username": "student_test",
        "password": "Student@123"
    })
    return resp.json()["data"]["access_token"]
