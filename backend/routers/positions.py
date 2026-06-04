from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.auth import require_role
from backend.db import get_connection
from backend.models import BatchUploadRequest, PositionCreate, PositionUpdate, StatusUpdateRequest

router = APIRouter(tags=["岗位"])

POSITION_COLUMNS = "id, title, responsibilities, requirements, bonus, status, created_at, updated_at"

# 状态流转规则：(当前状态, action) -> 目标状态
STATUS_TRANSITIONS = {
    ("DRAFT", "submit"): "PENDING",
    ("PENDING", "approve"): "PUBLISHED",
    ("PENDING", "reject"): "DRAFT",
    ("PUBLISHED", "close"): "CLOSED",
}

# 各状态允许的操作
ALLOWED_ACTIONS = {
    "DRAFT": ["submit"],
    "PENDING": ["approve", "reject"],
    "PUBLISHED": ["close"],
}


def _format_row(row: dict) -> dict:
    """将 datetime 字段转为字符串"""
    if row.get("created_at"):
        row["created_at"] = str(row["created_at"])
    if row.get("updated_at"):
        row["updated_at"] = str(row["updated_at"])
    return row


@router.get("/positions", response_model=dict)
def get_all_positions(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
):
    """获取岗位列表（支持搜索/过滤）"""
    conn = get_connection()
    try:
        conditions = []
        params = []
        if keyword:
            conditions.append("title LIKE %s")
            params.append(f"%{keyword}%")
        if status:
            conditions.append("status = %s")
            params.append(status)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {POSITION_COLUMNS} FROM positions{where} ORDER BY id DESC",
                params,
            )
            rows = cursor.fetchall()

        rows = [_format_row(row) for row in rows]
        return {"code": 200, "message": "success", "data": rows}
    finally:
        conn.close()


@router.get("/positions/{position_id}", response_model=dict)
def get_position(position_id: int):
    """获取单个岗位信息"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {POSITION_COLUMNS} FROM positions WHERE id = %s",
                (position_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="岗位不存在")

        return {"code": 200, "message": "success", "data": _format_row(row)}
    finally:
        conn.close()


@router.post("/positions", status_code=201, response_model=dict)
def create_position(
    position: PositionCreate,
    current_user: dict = Depends(require_role("admin", "hr")),
):
    """新增岗位（admin/hr）"""
    conn = get_connection()
    try:
        status = position.status or "DRAFT"
        with conn.cursor() as cursor:
            sql = "INSERT INTO positions (title, responsibilities, requirements, bonus, status) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (position.title, position.responsibilities, position.requirements, position.bonus, status))
            conn.commit()
            new_id = cursor.lastrowid

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT {POSITION_COLUMNS} FROM positions WHERE id = %s", (new_id,))
            new_row = cursor.fetchone()

        return {"code": 201, "message": "创建成功", "data": _format_row(new_row)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"新增失败: {str(e)}")
    finally:
        conn.close()


@router.put("/positions/{position_id}", response_model=dict)
def update_position(
    position_id: int,
    position: PositionUpdate,
    current_user: dict = Depends(require_role("admin", "hr")),
):
    """更新岗位信息（admin/hr，且仅 DRAFT 状态可编辑）"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {POSITION_COLUMNS} FROM positions WHERE id = %s",
                (position_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="岗位不存在")
            if existing["status"] != "DRAFT":
                raise HTTPException(status_code=400, detail="只有草稿状态的岗位可以编辑")

        updates = []
        params = []
        if position.title is not None:
            updates.append("title = %s")
            params.append(position.title)
        if position.responsibilities is not None:
            updates.append("responsibilities = %s")
            params.append(position.responsibilities)
        if position.requirements is not None:
            updates.append("requirements = %s")
            params.append(position.requirements)
        if position.bonus is not None:
            updates.append("bonus = %s")
            params.append(position.bonus)

        if not updates:
            return {"code": 200, "message": "无需更新", "data": _format_row(existing)}

        sql = f"UPDATE positions SET {', '.join(updates)} WHERE id = %s"
        params.append(position_id)

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT {POSITION_COLUMNS} FROM positions WHERE id = %s", (position_id,))
            updated_row = cursor.fetchone()

        return {"code": 200, "message": "更新成功", "data": _format_row(updated_row)}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    finally:
        conn.close()


@router.delete("/positions/{position_id}", response_model=dict)
def delete_position(
    position_id: int,
    current_user: dict = Depends(require_role("admin", "hr")),
):
    """删除岗位（admin/hr，且仅 DRAFT/CLOSED 状态可删除）"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, status FROM positions WHERE id = %s",
                (position_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="岗位不存在")
            if existing["status"] not in ("DRAFT", "CLOSED"):
                raise HTTPException(status_code=400, detail="只有草稿或已关闭的岗位可以删除")

            cursor.execute("DELETE FROM positions WHERE id = %s", (position_id,))
            conn.commit()

        return {"code": 200, "message": f"岗位 id={position_id} 删除成功", "data": None}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    finally:
        conn.close()


@router.patch("/positions/{position_id}/status", response_model=dict)
def update_position_status(
    position_id: int,
    body: StatusUpdateRequest,
    current_user: dict = Depends(require_role("admin", "hr")),
):
    """变更岗位状态（admin 可审批/关闭，hr 只能提交）"""
    action = body.action

    if current_user["role"] == "hr" and action != "submit":
        raise HTTPException(status_code=403, detail="权限不足：仅管理员可审批")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {POSITION_COLUMNS} FROM positions WHERE id = %s",
                (position_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="岗位不存在")

        current_status = existing["status"]
        allowed = ALLOWED_ACTIONS.get(current_status, [])
        if action not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"当前状态 {current_status} 不允许执行 {action} 操作",
            )

        new_status = STATUS_TRANSITIONS[(current_status, action)]

        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE positions SET status = %s WHERE id = %s",
                (new_status, position_id),
            )
            conn.commit()

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT {POSITION_COLUMNS} FROM positions WHERE id = %s", (position_id,))
            updated_row = cursor.fetchone()

        return {"code": 200, "message": f"状态已变更为 {new_status}", "data": _format_row(updated_row)}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"状态变更失败: {str(e)}")
    finally:
        conn.close()


@router.post("/positions/batch", status_code=201, response_model=dict)
def batch_upload(
    request: BatchUploadRequest,
    current_user: dict = Depends(require_role("admin", "hr")),
):
    """批量上传岗位（admin/hr，默认 DRAFT 状态）"""
    if not request.positions:
        raise HTTPException(status_code=400, detail="导入数据不能为空")

    conn = get_connection()
    try:
        inserted = 0
        skipped = 0
        with conn.cursor() as cursor:
            for pos in request.positions:
                cursor.execute(
                    "SELECT id FROM positions WHERE title = %s AND responsibilities = %s AND requirements = %s AND bonus = %s LIMIT 1",
                    (pos.title, pos.responsibilities, pos.requirements, pos.bonus),
                )
                if cursor.fetchone():
                    skipped += 1
                    continue

                cursor.execute(
                    "INSERT INTO positions (title, responsibilities, requirements, bonus, status) VALUES (%s, %s, %s, %s, 'DRAFT')",
                    (pos.title, pos.responsibilities, pos.requirements, pos.bonus),
                )
                inserted += 1

        conn.commit()
        return {
            "code": 201,
            "message": f"批量导入完成：新增 {inserted} 条，跳过 {skipped} 条（已存在）",
            "data": {"count": inserted, "skipped": skipped},
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")
    finally:
        conn.close()
