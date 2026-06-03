import hashlib
from tests.conftest import fake_redis
from src.services.auth_service import AuthService, SMS_DAILY_LIMIT, SMS_IP_DAILY_LIMIT, SMS_VERIFY_MAX_ATTEMPTS
from src.core.config import settings


class TestSMSSecurity:
    def _clear_sms_keys(self):
        for key in fake_redis.scan_iter("sms:*"):
            fake_redis.delete(key)

    def test_sms_code_hashed_in_database(self, client, db_session):
        self._clear_sms_keys()
        from src.models.user import SmsVerification
        resp = client.post("/api/v1/auth/sms/send", json={
            "phone": "13800138001"
        })
        assert resp.json()["code"] == 200

        record = db_session.query(SmsVerification).filter(
            SmsVerification.phone == "13800138001"
        ).order_by(SmsVerification.id.desc()).first()

        assert record is not None
        assert len(record.code) == 64
        assert not record.code.isdigit()

    def test_sms_daily_limit_constant(self):
        assert SMS_DAILY_LIMIT == 10

    def test_sms_ip_daily_limit_constant(self):
        assert SMS_IP_DAILY_LIMIT == 20

    def test_sms_verify_max_attempts_constant(self):
        assert SMS_VERIFY_MAX_ATTEMPTS == 5

    def test_hash_sms_code_is_deterministic(self):
        code = "123456"
        phone = "13800138000"
        hash1 = AuthService._hash_sms_code(code, phone)
        hash2 = AuthService._hash_sms_code(code, phone)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_hash_sms_code_different_for_different_codes(self):
        phone = "13800138000"
        hash1 = AuthService._hash_sms_code("123456", phone)
        hash2 = AuthService._hash_sms_code("654321", phone)
        assert hash1 != hash2

    def test_hash_sms_code_different_for_different_phones(self):
        code = "123456"
        hash1 = AuthService._hash_sms_code(code, "13800138000")
        hash2 = AuthService._hash_sms_code(code, "13900139000")
        assert hash1 != hash2

    def test_sms_uses_secrets_not_random(self):
        import inspect
        source = inspect.getsource(AuthService.send_sms_code)
        assert "secrets.randbelow" in source
        assert "random.randint" not in source

    def test_sms_cooldown_enforced(self, client):
        self._clear_sms_keys()
        first = client.post("/api/v1/auth/sms/send", json={
            "phone": "13800138002"
        })
        assert first.json()["code"] == 200

        second = client.post("/api/v1/auth/sms/send", json={
            "phone": "13800138002"
        })
        assert second.json()["code"] == 400
        assert "60 seconds" in second.json()["message"]

    def test_sms_verify_error_increments(self, client, db_session):
        self._clear_sms_keys()
        from src.models.user import SmsVerification
        from datetime import datetime, timedelta, timezone

        hashed = AuthService._hash_sms_code("123456", "13800138003")
        sms_record = SmsVerification(
            phone="13800138003",
            code=hashed,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        db_session.add(sms_record)
        db_session.commit()

        for i in range(SMS_VERIFY_MAX_ATTEMPTS):
            client.post("/api/v1/auth/sms/login", json={
                "phone": "13800138003",
                "code": "000000"
            })

        response = client.post("/api/v1/auth/sms/login", json={
            "phone": "13800138003",
            "code": "000000"
        })
        assert response.json()["code"] == 400
        assert "Too many" in response.json()["message"] or "attempts" in response.json()["message"].lower()

    def test_sms_login_with_correct_code(self, client, db_session):
        self._clear_sms_keys()
        from src.models.user import SmsVerification, User as UserModel
        from datetime import datetime, timedelta, timezone

        real_code = "654321"
        hashed = AuthService._hash_sms_code(real_code, "13800138000")
        sms_record = SmsVerification(
            phone="13800138000",
            code=hashed,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        db_session.add(sms_record)
        db_session.commit()

        response = client.post("/api/v1/auth/sms/login", json={
            "phone": "13800138000",
            "code": real_code
        })
        assert response.json()["code"] == 200
        assert "access_token" in response.json()["data"]
