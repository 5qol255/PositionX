from fastapi import APIRouter

from backend.db import get_connection

router = APIRouter(tags=["统计"])


@router.get("/statistics", response_model=dict)
def get_statistics():
    """统计数据（按状态分组）"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM positions")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT status, COUNT(*) as cnt FROM positions GROUP BY status")
            rows = cursor.fetchall()
            by_status = {row["status"]: row["cnt"] for row in rows}

        return {
            "code": 200,
            "message": "success",
            "data": {"total": total, "by_status": by_status},
        }
    finally:
        conn.close()
