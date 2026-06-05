"""认证接口测试"""

from conftest import SAMPLE_USER, auth_header


class TestLogin:
    """POST /webapi/auth/login"""

    def test_login_success(self, client, mock_conn):
        """登录成功"""
        from passlib.context import CryptContext

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd.hash("admin123")

        user = {**SAMPLE_USER, "password_hash": hashed}
        mock_conn.cursor_instance.set_results(user)

        r = client.post("/webapi/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        data = r.json()
        assert data["code"] == 200
        assert "token" in data["data"]
        assert data["data"]["user"]["username"] == "admin"

    def test_login_wrong_password(self, client, mock_conn):
        """密码错误"""
        from passlib.context import CryptContext

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd.hash("correct_password")

        user = {**SAMPLE_USER, "password_hash": hashed}
        mock_conn.cursor_instance.set_results(user)

        r = client.post("/webapi/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401

    def test_login_user_not_found(self, client, mock_conn):
        """用户不存在"""
        mock_conn.cursor_instance.set_results(None)

        r = client.post("/webapi/auth/login", json={"username": "nobody", "password": "123"})
        assert r.status_code == 401

    def test_login_empty_body(self, client):
        """空请求体"""
        r = client.post("/webapi/auth/login", json={})
        assert r.status_code == 422


class TestGetMe:
    """GET /webapi/auth/me"""

    def test_get_me_success(self, client):
        """获取当前用户信息"""
        r = client.get("/webapi/auth/me", headers=auth_header("admin"))
        assert r.status_code == 200
        assert r.json()["data"]["role"] == "admin"

    def test_get_me_no_token(self, client):
        """未登录"""
        r = client.get("/webapi/auth/me")
        assert r.status_code == 401

    def test_get_me_invalid_token(self, client):
        """无效 Token"""
        r = client.get("/webapi/auth/me", headers={"Authorization": "Bearer invalid"})
        assert r.status_code == 401
