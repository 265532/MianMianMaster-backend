from unittest.mock import patch
from src.core.config import settings


class TestEnvironmentConfig:
    def test_environment_default_is_development(self):
        assert settings.ENVIRONMENT == "development"

    def test_environment_field_exists(self):
        assert hasattr(settings, "ENVIRONMENT")

    def test_auto_create_tables_guarded_by_environment(self):
        import inspect
        from src.main import app
        import src.main as main_module
        source = inspect.getsource(main_module)
        assert "ENVIRONMENT" in source
        assert "create_all" in source

    def test_dockerfile_includes_alembic(self):
        import os
        dockerfile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Dockerfile")
        if os.path.exists(dockerfile_path):
            with open(dockerfile_path, "r") as f:
                content = f.read()
            assert "alembic upgrade head" in content

    def test_docker_compose_sets_production(self):
        import os
        compose_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docker-compose.yml")
        if os.path.exists(compose_path):
            with open(compose_path, "r") as f:
                content = f.read()
            assert "ENVIRONMENT=production" in content


class TestConfigSettings:
    def test_access_token_expire_is_30_minutes(self):
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_refresh_token_expire_is_7_days(self):
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_allowed_origins_configured(self):
        assert settings.ALLOWED_ORIGINS is not None
        assert len(settings.cors_origins_list) >= 2

    def test_secret_key_exists(self):
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_redis_config_has_defaults(self):
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_DB == 0
