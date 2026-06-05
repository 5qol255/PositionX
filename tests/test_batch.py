"""批量导入测试"""

from conftest import auth_header


class TestBatchUpload:
    """POST /webapi/positions/batch"""

    def test_batch_success(self, client, mock_conn):
        """批量导入成功"""
        # 第一次 fetchone 返回 None（不重复），第二次返回 None（不重复）
        mock_conn.cursor_instance.set_results(None)

        r = client.post(
            "/webapi/positions/batch",
            json={
                "positions": [
                    {"title": "岗位A", "responsibilities": "职责A", "requirements": "要求A"},
                    {"title": "岗位B", "responsibilities": "职责B", "requirements": "要求B"},
                ]
            },
            headers=auth_header("admin"),
        )
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["count"] == 2
        assert data["skipped"] == 0

    def test_batch_skip_duplicates(self, client, mock_conn):
        """重复数据跳过"""
        # 模拟每个岗位都已存在（fetchone 返回非 None）
        mock_conn.cursor_instance.set_results({"id": 1})

        r = client.post(
            "/webapi/positions/batch",
            json={
                "positions": [
                    {"title": "已存在", "responsibilities": "职责", "requirements": "要求"},
                ]
            },
            headers=auth_header("admin"),
        )
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["count"] == 0
        assert data["skipped"] == 1

    def test_batch_empty_list(self, client):
        """空列表"""
        r = client.post(
            "/webapi/positions/batch",
            json={"positions": []},
            headers=auth_header("admin"),
        )
        assert r.status_code == 400

    def test_batch_no_auth(self, client):
        """未登录"""
        r = client.post(
            "/webapi/positions/batch",
            json={"positions": [{"title": "A", "responsibilities": "B", "requirements": "C"}]},
        )
        assert r.status_code == 401
