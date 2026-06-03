from unittest.mock import patch
from tests.conftest import fake_redis, override_get_redis
from src.services.auth_service import AuthService, LOGIN_MAX_ATTEMPTS, LOGIN_LOCKOUT_SECONDS
from src.core.exceptions import BusinessException


class TestLoginLockout:
    def _clear_lockout_keys(self):
        for key in fake_redis.scan_iter("login:failed:*"):
            fake_redis.delete(key)
        for key in fake_redis.scan_iter("login:locked:*"):
            fake_redis.delete(key)

    def test_login_success_returns_tokens(self, client):
        self._clear_lockout_keys()
        resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        data = resp.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]

    def test_login_failure_returns_remaining_attempts(self, client):
        self._clear_lockout_keys()
        resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "WrongPass@123"
        })
        data = resp.json()
        assert data["code"] == 401
        assert "attempts remaining" in data["message"]

    def test_five_failures_trigger_lockout(self, client):
        self._clear_lockout_keys()
        for i in range(5):
            client.post("/api/v1/auth/login", json={
                "username": "admin_test",
                "password": f"Wrong{i}@12345"
            })

        response = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        assert response.json()["code"] == 423

    def test_lockout_returns_remaining_time(self, client):
        self._clear_lockout_keys()
        for i in range(5):
            client.post("/api/v1/auth/login", json={
                "username": "admin_test",
                "password": f"Wrong{i}@12345"
            })

        response = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        data = response.json()
        assert data["code"] == 423
        assert "minutes" in data["message"].lower()

    def test_login_success_clears_failure_count_via_api(self, client):
        self._clear_lockout_keys()
        fail_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "WrongPass@123"
        })
        assert fail_resp.json()["code"] == 401

        success_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        assert success_resp.json()["code"] == 200

        for i in range(4):
            resp = client.post("/api/v1/auth/login", json={
                "username": "admin_test",
                "password": f"WrongAgain{i}@12345"
            })
            assert resp.json()["code"] == 401

        final_resp = client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Admin@123"
        })
        assert final_resp.json()["code"] == 200

    def test_login_max_attempts_constant(self):
        assert LOGIN_MAX_ATTEMPTS == 5

    def test_login_lockout_seconds_constant(self):
        assert LOGIN_LOCKOUT_SECONDS == 900

    @patch("src.services.auth_service.get_redis", override_get_redis)
    def test_check_login_lockout_raises_for_locked_unit(self):
        self._clear_lockout_keys()
        fake_redis.setex("login:locked:user:locked_user", 900, "1")
        try:
            AuthService._check_login_lockout("locked_user", "user")
            assert False, "Should have raised"
        except BusinessException as e:
            assert e.code == 423
        finally:
            fake_redis.delete("login:locked:user:locked_user")

    @patch("src.services.auth_service.get_redis", override_get_redis)
    def test_check_login_lockout_passes_for_unlocked(self):
        self._clear_lockout_keys()
        AuthService._check_login_lockout("unlocked_user", "user")

    @patch("src.services.auth_service.get_redis", override_get_redis)
    def test_record_login_failure_increments(self):
        self._clear_lockout_keys()
        remaining = AuthService._record_login_failure("testuser", "user")
        assert remaining == 4
        remaining = AuthService._record_login_failure("testuser", "user")
        assert remaining == 3

    @patch("src.services.auth_service.get_redis", override_get_redis)
    def test_record_login_failure_triggers_lockout_at_max(self):
        self._clear_lockout_keys()
        for i in range(4):
            AuthService._record_login_failure("maxuser", "user")
        try:
            AuthService._record_login_failure("maxuser", "user")
            assert False, "Should have raised"
        except BusinessException as e:
            assert e.code == 423

    @patch("src.services.auth_service.get_redis", override_get_redis)
    def test_clear_login_failures(self):
        self._clear_lockout_keys()
        AuthService._record_login_failure("clearuser", "user")
        assert fake_redis.exists("login:failed:user:clearuser")
        AuthService._clear_login_failures("clearuser", "user")
        assert not fake_redis.exists("login:failed:user:clearuser")
