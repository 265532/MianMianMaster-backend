from src.api.deps import _is_super_admin, SUPER_ADMIN_ROLE
from src.models.user import User, Role


class TestRBACPermissions:
    def test_super_admin_detected_by_role(self):
        admin_role = Role(name="admin", description="Admin")
        user = User(
            username="any_admin_name",
            email="admin@example.com",
            hashed_password="xxx",
            is_active=True,
        )
        user.roles.append(admin_role)
        assert _is_super_admin(user) is True

    def test_non_admin_not_super_admin(self):
        student_role = Role(name="student", description="Student")
        user = User(
            username="student1",
            email="student@example.com",
            hashed_password="xxx",
            is_active=True,
        )
        user.roles.append(student_role)
        assert _is_super_admin(user) is False

    def test_admin_username_without_role_not_super(self):
        student_role = Role(name="student", description="Student")
        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="xxx",
            is_active=True,
        )
        user.roles.append(student_role)
        assert _is_super_admin(user) is False

    def test_super_admin_role_constant(self):
        assert SUPER_ADMIN_ROLE == "admin"

    def test_user_with_no_roles_not_super_admin(self):
        user = User(
            username="noroles",
            email="noroles@example.com",
            hashed_password="xxx",
            is_active=True,
        )
        assert _is_super_admin(user) is False

    def test_user_with_multiple_roles_including_admin(self):
        admin_role = Role(name="admin", description="Admin")
        student_role = Role(name="student", description="Student")
        user = User(
            username="multi_role",
            email="multi@example.com",
            hashed_password="xxx",
            is_active=True,
        )
        user.roles.append(student_role)
        user.roles.append(admin_role)
        assert _is_super_admin(user) is True


class TestRBACAPI:
    def test_student_can_login(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "student_test",
            "password": "Student@123"
        })
        login_data = login_resp.json()
        assert login_data["code"] == 200

    def test_student_cannot_access_admin_endpoint(self, client):
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "student_test",
            "password": "Student@123"
        })
        login_data = login_resp.json()
        assert login_data["code"] == 200
        token = login_data["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/rbac/roles", headers=headers)
        assert response.json()["code"] == 403

    def test_no_username_hardcoded_bypass(self):
        import inspect
        from src.api.deps import check_permissions
        source = inspect.getsource(check_permissions)
        assert 'username == "admin"' not in source
        assert "username != \"admin\"" not in source
