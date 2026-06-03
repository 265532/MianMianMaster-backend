from tests.conftest import fake_redis
from src.core import security
from src.core.config import settings
from jose import jwt


class TestPasswordResetToken:
    def _clear_reset_keys(self):
        for key in fake_redis.scan_iter("pwd_reset:*"):
            fake_redis.delete(key)

    def test_reset_token_contains_jti(self):
        self._clear_reset_keys()
        token = security.create_password_reset_token("test@example.com")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "jti" in payload
        assert payload["type"] == "reset"
        assert payload["sub"] == "test@example.com"

    def test_mark_reset_token_used(self):
        self._clear_reset_keys()
        jti = "test-jti-reset-1"
        assert security.is_reset_token_used(jti) is False
        security.mark_reset_token_used(jti)
        assert security.is_reset_token_used(jti) is True

    def test_reset_token_single_use_via_api(self, client, db_session):
        self._clear_reset_keys()
        from src.models.user import User as UserModel
        original_hash = db_session.query(UserModel).filter(
            UserModel.email == "admin_test@example.com"
        ).first().hashed_password

        try:
            token_resp = client.post("/api/v1/auth/password/reset-token", json={
                "email": "admin_test@example.com"
            })
            assert token_resp.json()["code"] == 200
            reset_token = token_resp.json()["data"]

            first_reset = client.post("/api/v1/auth/password/reset", json={
                "token": reset_token,
                "new_password": "NewPassword@123"
            })
            assert first_reset.json()["code"] == 200

            second_reset = client.post("/api/v1/auth/password/reset", json={
                "token": reset_token,
                "new_password": "AnotherPass@456"
            })
            assert second_reset.json()["code"] == 400
            assert "already been used" in second_reset.json()["message"]
        finally:
            user = db_session.query(UserModel).filter(
                UserModel.email == "admin_test@example.com"
            ).first()
            user.hashed_password = original_hash
            db_session.commit()

    def test_reset_cooldown(self, client):
        self._clear_reset_keys()
        first_req = client.post("/api/v1/auth/password/reset-token", json={
            "email": "admin_test@example.com"
        })
        assert first_req.json()["code"] == 200

        second_req = client.post("/api/v1/auth/password/reset-token", json={
            "email": "admin_test@example.com"
        })
        assert second_req.json()["code"] == 429

    def test_expired_reset_token_rejected(self, client):
        self._clear_reset_keys()
        response = client.post("/api/v1/auth/password/reset", json={
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVzZXQiLCJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxMDAwMDAwMDAwfQ.invalid",
            "new_password": "NewPassword@123"
        })
        assert response.json()["code"] == 400

    def test_reset_token_type_check(self):
        self._clear_reset_keys()
        token = security.create_password_reset_token("test@example.com")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["type"] == "reset"

        access_token = security.create_access_token("testuser")
        at_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
        assert at_payload["type"] == "access"

        result = security.verify_password_reset_token(access_token)
        assert result is None

    def test_weak_password_rejected_in_reset(self, client):
        self._clear_reset_keys()
        token_resp = client.post("/api/v1/auth/password/reset-token", json={
            "email": "admin_test@example.com"
        })
        reset_token = token_resp.json()["data"]
        response = client.post("/api/v1/auth/password/reset", json={
            "token": reset_token,
            "new_password": "weak"
        })
        assert response.json()["code"] == 400
