from unittest.mock import patch
from src.db.redis_client import get_redis


class TestCORSSecurity:
    def test_cors_allows_allowed_origin(self, client):
        with patch.object(get_redis, '__call__', return_value=None):
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_allows_second_allowed_origin(self, client):
        with patch.object(get_redis, '__call__', return_value=None):
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:8080",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:8080"

    def test_cors_blocks_disallowed_origin(self, client):
        with patch.object(get_redis, '__call__', return_value=None):
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://evil-site.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert "access-control-allow-origin" not in response.headers

    def test_cors_blocks_random_subdomain(self, client):
        with patch.object(get_redis, '__call__', return_value=None):
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:9999",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert "access-control-allow-origin" not in response.headers

    def test_cors_allowed_methods_restricted(self, client):
        with patch.object(get_redis, '__call__', return_value=None):
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "TRACE",
                },
            )
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "TRACE" not in allow_methods

    def test_cors_allows_standard_methods(self, client):
        with patch.object(get_redis, '__call__', return_value=None):
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods
        assert "GET" in allow_methods

    def test_cors_credentials_allowed_for_whitelisted(self, client):
        with patch.object(get_redis, '__call__', return_value=None):
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert response.headers.get("access-control-allow-credentials") == "true"


class TestCORSConfig:
    def test_cors_origins_list_parses_correctly(self):
        from src.core.config import settings
        origins = settings.cors_origins_list
        assert "http://localhost:3000" in origins
        assert "http://localhost:8080" in origins
        assert len(origins) >= 2

    def test_cors_origins_no_wildcard(self):
        from src.core.config import settings
        origins = settings.cors_origins_list
        assert "*" not in origins
