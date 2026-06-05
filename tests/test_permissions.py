"""角色权限测试"""

from conftest import SAMPLE_POSITION, auth_header


class TestHrPermissions:
    """hr 角色权限限制"""

    def test_hr_can_submit(self, client, mock_conn):
        """hr 可以提交审批"""
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "submit"},
            headers=auth_header("hr"),
        )
        assert r.status_code == 200

    def test_hr_cannot_approve(self, client, mock_conn):
        """hr 不能审批"""
        position = {**SAMPLE_POSITION, "status": "PENDING"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "approve"},
            headers=auth_header("hr"),
        )
        assert r.status_code == 403

    def test_hr_cannot_close(self, client, mock_conn):
        """hr 不能关闭岗位"""
        position = {**SAMPLE_POSITION, "status": "PUBLISHED"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "close"},
            headers=auth_header("hr"),
        )
        assert r.status_code == 403

    def test_hr_can_create(self, client, mock_conn):
        """hr 可以创建岗位"""
        mock_conn.cursor_instance.set_lastrowid(1)
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)

        r = client.post(
            "/webapi/positions",
            json={"title": "测试", "responsibilities": "职责", "requirements": "要求"},
            headers=auth_header("hr"),
        )
        assert r.status_code == 201

    def test_hr_can_delete_draft(self, client, mock_conn):
        """hr 可以删除草稿"""
        mock_conn.cursor_instance.set_results({"id": 1, "status": "DRAFT"})

        r = client.delete("/webapi/positions/1", headers=auth_header("hr"))
        assert r.status_code == 200


class TestViewerPermissions:
    """viewer 角色（无权限）"""

    def test_viewer_cannot_create(self, client, mock_conn):
        """viewer 不能创建岗位"""
        r = client.post(
            "/webapi/positions",
            json={"title": "测试", "responsibilities": "职责", "requirements": "要求"},
            headers=auth_header("viewer"),
        )
        assert r.status_code == 403

    def test_viewer_cannot_delete(self, client, mock_conn):
        """viewer 不能删除岗位"""
        r = client.delete("/webapi/positions/1", headers=auth_header("viewer"))
        assert r.status_code == 403


class TestAdminPermissions:
    """admin 角色（全权限）"""

    def test_admin_can_approve(self, client, mock_conn):
        """admin 可以审批"""
        position = {**SAMPLE_POSITION, "status": "PENDING"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "approve"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 200

    def test_admin_can_close(self, client, mock_conn):
        """admin 可以关闭"""
        position = {**SAMPLE_POSITION, "status": "PUBLISHED"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "close"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 200
