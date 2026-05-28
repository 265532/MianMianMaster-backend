from unittest.mock import patch
from src.db.redis_client import get_redis
from src.core import security
from src.core.config import settings
from jose import jwt, JWTError


class TestJWTDualToken:
    def test_login_returns_both_tokens(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        data = resp.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_access_token_works_for_api(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        access_token = login_resp.json()["data"]["access_token"]
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert response.json()["code"] == 200

    def test_refresh_token_cannot_access_api(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        refresh_token = login_resp.json()["data"]["refresh_token"]
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        assert response.json()["code"] == 401

    def test_refresh_token_generates_new_pair(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        refresh_token = login_resp.json()["data"]["refresh_token"]
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.json()["code"] == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data

    def test_logout_invalidates_access_token(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        tokens = login_resp.json()["data"]
        access_token = tokens["access_token"]

        logout_resp = client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert logout_resp.json()["code"] == 200

        me_resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert me_resp.json()["code"] == 401

    def test_logout_invalidates_refresh_token(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        tokens = login_resp.json()["data"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {access_token}"
        })

        refresh_resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_resp.json()["code"] == 401

    def test_invalid_refresh_token_rejected(self, client):
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })
        assert response.json()["code"] == 401

    def test_access_token_has_correct_type(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        access_token = login_resp.json()["data"]["access_token"]
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload.get("type") == "access"

    def test_refresh_token_has_correct_type(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        refresh_token = login_resp.json()["data"]["refresh_token"]
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload.get("type") == "refresh"

    def test_tokens_have_jti(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        tokens = login_resp.json()["data"]
        at_payload = jwt.decode(tokens["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
        rt_payload = jwt.decode(tokens["refresh_token"], settings.SECRET_KEY, algorithms=["HS256"])
        assert "jti" in at_payload
        assert "jti" in rt_payload
        assert at_payload["jti"] != rt_payload["jti"]


class TestTokenSecurity:
    def test_access_token_expires_in_30_minutes(self):
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_refresh_token_expires_in_7_days(self):
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_create_access_token_contains_required_fields(self):
        token = security.create_access_token("testuser")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload

    def test_create_refresh_token_contains_required_fields(self):
        from tests.conftest import fake_redis
        fake_redis.flushdb()
        token = security.create_refresh_token(1)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload

    def test_token_blacklist(self):
        from tests.conftest import fake_redis
        fake_redis.flushdb()
        jti = "test-jti-123"
        assert security.is_token_blacklisted(jti) is False
        security.add_token_to_blacklist(jti, 3600)
        assert security.is_token_blacklisted(jti) is True

    def test_refresh_token_validity(self):
        from tests.conftest import fake_redis
        fake_redis.flushdb()
        token = security.create_refresh_token(99)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        jti = payload["jti"]
        assert security.is_refresh_token_valid(99, jti) is True

    def test_revoked_refresh_token_invalid(self):
        from tests.conftest import fake_redis
        fake_redis.flushdb()
        token = security.create_refresh_token(100)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        jti = payload["jti"]
        security.revoke_refresh_token(100)
        assert security.is_refresh_token_valid(100, jti) is False
