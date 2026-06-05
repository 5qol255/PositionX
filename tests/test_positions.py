"""岗位 CRUD 接口测试"""

from conftest import SAMPLE_POSITION, auth_header


class TestGetPositions:
    """GET /webapi/positions"""

    def test_get_all(self, client, mock_conn):
        """获取岗位列表"""
        mock_conn.cursor_instance.set_results([SAMPLE_POSITION])
        r = client.get("/webapi/positions")
        assert r.status_code == 200
        assert len(r.json()["data"]) == 1

    def test_get_all_empty(self, client, mock_conn):
        """空列表"""
        mock_conn.cursor_instance.set_results([])
        r = client.get("/webapi/positions")
        assert r.status_code == 200
        assert r.json()["data"] == []

    def test_get_all_with_keyword(self, client, mock_conn):
        """关键词搜索"""
        mock_conn.cursor_instance.set_results([SAMPLE_POSITION])
        r = client.get("/webapi/positions", params={"keyword": "Python"})
        assert r.status_code == 200

    def test_get_all_with_status_filter(self, client, mock_conn):
        """状态筛选"""
        mock_conn.cursor_instance.set_results([SAMPLE_POSITION])
        r = client.get("/webapi/positions", params={"status": "DRAFT"})
        assert r.status_code == 200


class TestGetPosition:
    """GET /webapi/positions/{id}"""

    def test_get_one(self, client, mock_conn):
        """获取单个岗位"""
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)
        r = client.get("/webapi/positions/1")
        assert r.status_code == 200
        assert r.json()["data"]["title"] == "Python 开发工程师"

    def test_get_not_found(self, client, mock_conn):
        """岗位不存在"""
        mock_conn.cursor_instance.set_results(None)
        r = client.get("/webapi/positions/999")
        assert r.status_code == 404


class TestCreatePosition:
    """POST /webapi/positions"""

    def test_create_success(self, client, mock_conn):
        """创建岗位成功"""
        mock_conn.cursor_instance.set_lastrowid(1)
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)

        r = client.post(
            "/webapi/positions",
            json={"title": "测试", "responsibilities": "职责", "requirements": "要求"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 201
        assert r.json()["data"]["title"] == "Python 开发工程师"

    def test_create_no_auth(self, client):
        """未登录创建"""
        r = client.post(
            "/webapi/positions",
            json={"title": "测试", "responsibilities": "职责", "requirements": "要求"},
        )
        assert r.status_code == 401

    def test_create_hr_allowed(self, client, mock_conn):
        """hr 角色可以创建"""
        mock_conn.cursor_instance.set_lastrowid(1)
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)

        r = client.post(
            "/webapi/positions",
            json={"title": "测试", "responsibilities": "职责", "requirements": "要求"},
            headers=auth_header("hr"),
        )
        assert r.status_code == 201

    def test_create_missing_fields(self, client):
        """缺少必填字段"""
        r = client.post(
            "/webapi/positions",
            json={"title": "测试"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 422


class TestUpdatePosition:
    """PUT /webapi/positions/{id}"""

    def test_update_draft(self, client, mock_conn):
        """编辑草稿岗位"""
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)

        r = client.put(
            "/webapi/positions/1",
            json={"title": "新标题"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 200

    def test_update_non_draft_rejected(self, client, mock_conn):
        """非草稿不可编辑"""
        position = {**SAMPLE_POSITION, "status": "PUBLISHED"}
        mock_conn.cursor_instance.set_results(position)

        r = client.put(
            "/webapi/positions/1",
            json={"title": "新标题"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 400

    def test_update_not_found(self, client, mock_conn):
        """岗位不存在"""
        mock_conn.cursor_instance.set_results(None)

        r = client.put(
            "/webapi/positions/999",
            json={"title": "新标题"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 404


class TestDeletePosition:
    """DELETE /webapi/positions/{id}"""

    def test_delete_draft(self, client, mock_conn):
        """删除草稿"""
        mock_conn.cursor_instance.set_results({"id": 1, "status": "DRAFT"})

        r = client.delete("/webapi/positions/1", headers=auth_header("admin"))
        assert r.status_code == 200

    def test_delete_closed(self, client, mock_conn):
        """删除已关闭"""
        mock_conn.cursor_instance.set_results({"id": 1, "status": "CLOSED"})

        r = client.delete("/webapi/positions/1", headers=auth_header("admin"))
        assert r.status_code == 200

    def test_delete_published_rejected(self, client, mock_conn):
        """已发布不可删除"""
        mock_conn.cursor_instance.set_results({"id": 1, "status": "PUBLISHED"})

        r = client.delete("/webapi/positions/1", headers=auth_header("admin"))
        assert r.status_code == 400

    def test_delete_not_found(self, client, mock_conn):
        """岗位不存在"""
        mock_conn.cursor_instance.set_results(None)

        r = client.delete("/webapi/positions/999", headers=auth_header("admin"))
        assert r.status_code == 404
