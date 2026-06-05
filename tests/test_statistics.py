"""统计接口测试"""


class TestStatistics:
    """GET /webapi/statistics"""

    def test_get_statistics(self, client, mock_conn):
        """获取统计数据"""
        # 模拟两次查询：COUNT(*) 和 GROUP BY
        cursor = mock_conn.cursor_instance
        cursor.set_results({"total": 10})

        # 第一次 fetchone 返回 total，第二次 fetchall 返回分组
        results_sequence = [
            {"total": 10},  # COUNT(*) fetchone
            [              # GROUP BY fetchall
                {"status": "DRAFT", "cnt": 5},
                {"status": "PUBLISHED", "cnt": 3},
                {"status": "PENDING", "cnt": 2},
            ],
        ]
        call_count = [0]

        original_fetchone = cursor.fetchone
        original_fetchall = cursor.fetchall

        def mock_fetchone():
            return results_sequence[0]

        def mock_fetchall():
            return results_sequence[1]

        cursor.fetchone = mock_fetchone
        cursor.fetchall = mock_fetchall

        r = client.get("/webapi/statistics")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total"] == 10
        assert data["by_status"]["DRAFT"] == 5
        assert data["by_status"]["PUBLISHED"] == 3

    def test_get_statistics_empty(self, client, mock_conn):
        """空数据统计"""
        cursor = mock_conn.cursor_instance

        cursor.fetchone = lambda: {"total": 0}
        cursor.fetchall = lambda: []

        r = client.get("/webapi/statistics")
        assert r.status_code == 200
        assert r.json()["data"]["total"] == 0
