"""状态流转测试"""

from conftest import SAMPLE_POSITION, auth_header


class TestStatusTransition:
    """PATCH /webapi/positions/{id}/status"""

    def test_submit_draft_to_pending(self, client, mock_conn):
        """草稿 → 提交审批 → 待审批"""
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "submit"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 200
        assert "PENDING" in r.json()["message"]

    def test_approve_pending_to_published(self, client, mock_conn):
        """待审批 → 审批通过 → 已发布"""
        position = {**SAMPLE_POSITION, "status": "PENDING"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "approve"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 200
        assert "PUBLISHED" in r.json()["message"]

    def test_reject_pending_to_draft(self, client, mock_conn):
        """待审批 → 驳回 → 草稿"""
        position = {**SAMPLE_POSITION, "status": "PENDING"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "reject"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 200
        assert "DRAFT" in r.json()["message"]

    def test_close_published_to_closed(self, client, mock_conn):
        """已发布 → 关闭 → 已关闭"""
        position = {**SAMPLE_POSITION, "status": "PUBLISHED"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "close"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 200
        assert "CLOSED" in r.json()["message"]

    def test_invalid_transition(self, client, mock_conn):
        """无效状态流转：草稿不能直接审批"""
        mock_conn.cursor_instance.set_results(SAMPLE_POSITION)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "approve"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 400

    def test_closed_cannot_transition(self, client, mock_conn):
        """已关闭不能再变更"""
        position = {**SAMPLE_POSITION, "status": "CLOSED"}
        mock_conn.cursor_instance.set_results(position)

        r = client.patch(
            "/webapi/positions/1/status",
            json={"action": "submit"},
            headers=auth_header("admin"),
        )
        assert r.status_code == 400
