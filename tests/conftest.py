"""测试配置：Mock 数据库 + TestClient + 认证辅助"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.auth import create_token
from backend.main import app


# ---------- Mock 数据库 ----------


class MockCursor:
    """模拟 pymysql DictCursor"""

    def __init__(self):
        self._results = []
        self._lastrowid = 1
        self._executed = []

    def execute(self, sql, params=None):
        self._executed.append((sql, params))

    def fetchone(self):
        return self._results[0] if self._results else None

    def fetchall(self):
        return self._results

    def set_results(self, results):
        self._results = results if isinstance(results, list) else [results]

    def set_lastrowid(self, val):
        self._lastrowid = val

    @property
    def lastrowid(self):
        return self._lastrowid

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class MockConnection:
    """模拟 pymysql Connection"""

    def __init__(self):
        self.cursor_instance = MockCursor()

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture
def mock_conn():
    """提供一个 MockConnection 实例，可自定义返回数据"""
    conn = MockConnection()
    with patch("backend.routers.positions.get_connection", return_value=conn), \
         patch("backend.routers.auth.get_connection", return_value=conn), \
         patch("backend.routers.statistics.get_connection", return_value=conn):
        yield conn


@pytest.fixture
def client():
    """FastAPI TestClient"""
    return TestClient(app)


# ---------- 认证辅助 ----------


def make_token(user_id: int = 1, username: str = "admin", role: str = "admin") -> str:
    """生成测试用 JWT Token"""
    return create_token(user_id, username, role)


def auth_header(role: str = "admin") -> dict:
    """返回带 Token 的请求头"""
    return {"Authorization": f"Bearer {make_token(role=role)}"}


# ---------- 测试数据 ----------

SAMPLE_POSITION = {
    "id": 1,
    "title": "Python 开发工程师",
    "responsibilities": "负责后端开发",
    "requirements": "熟悉 Python",
    "bonus": "有 FastAPI 经验",
    "status": "DRAFT",
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00",
}

SAMPLE_USER = {
    "id": 1,
    "username": "admin",
    "password_hash": "$2b$12$dummy_hash_for_testing",
    "role": "admin",
}
