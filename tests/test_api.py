def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_openapi_schema(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

def test_register_user(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "new_user_for_api_test",
        "email": "new_api_test@example.com",
        "password": "Password@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["username"] == "new_user_for_api_test"

def test_login_user(client):
    response = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "access_token" in data["data"]

def test_get_me(client):
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin_test",
        "password": "Admin@123"
    })
    token = login_resp.json()["data"]["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "admin_test"
