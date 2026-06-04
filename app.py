import os
from datetime import datetime, timedelta, timezone

import pymysql
import uvicorn
from db_config import DB_CONFIG
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import List, Optional

# ---------- 数据库配置 ----------


# ---------- JWT / 密码配置 ----------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(user_id: int, username: str, role: str) -> str:
    """生成 JWT Token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(request: Request) -> dict:
    """从 Authorization: Bearer <token> 解析当前用户，作为 FastAPI 依赖使用"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "id": int(payload["sub"]),
            "username": payload["username"],
            "role": payload["role"],
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")


def require_role(*roles: str):
    """返回一个依赖函数，校验当前用户是否具有指定角色之一"""
    def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return checker


# ---------- 数据库连接函数 ----------
def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# ---------- Pydantic 数据模型 ----------
class PositionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="岗位名称")
    responsibilities: str = Field(..., min_length=1, description="岗位职责")
    requirements: str = Field(..., min_length=1, description="岗位要求")
    bonus: str = Field(default="", description="加分项")
    status: Optional[str] = Field(None, description="岗位状态（默认 DRAFT）")


class PositionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="岗位名称")
    responsibilities: Optional[str] = Field(None, min_length=1, description="岗位职责")
    requirements: Optional[str] = Field(None, min_length=1, description="岗位要求")
    bonus: Optional[str] = Field(None, description="加分项")


class StatusUpdateRequest(BaseModel):
    action: str = Field(..., description="操作：submit/approve/reject/close")
    comment: str = Field(default="", description="审批意见（可选）")


class BatchUploadRequest(BaseModel):
    positions: List[PositionCreate]


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

# ---------- FastAPI 应用 ----------
app = FastAPI(
    title="招聘岗位发布系统",
    description="提供岗位信息的增删改查及批量上传接口",
    version="1.0.0",
)

# 配置 CORS，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 生产环境请限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 认证 API ----------

@app.post("/webapi/auth/login", response_model=dict)
def login(body: UserLogin):
    """用户登录，返回 JWT Token"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = %s",
                (body.username,),
            )
            user = cursor.fetchone()

        if not user or not pwd_context.verify(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        token = create_token(user["id"], user["username"], user["role"])
        return {
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                },
            },
        }
    finally:
        conn.close()


@app.get("/webapi/auth/me", response_model=dict)
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"code": 200, "message": "success", "data": current_user}


# ---------- 岗位 API ----------

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


@app.get("/webapi/positions", response_model=dict)
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

        # 将 datetime 转为字符串
        for row in rows:
            if row.get("created_at"):
                row["created_at"] = str(row["created_at"])
            if row.get("updated_at"):
                row["updated_at"] = str(row["updated_at"])

        return {"code": 200, "message": "success", "data": rows}
    finally:
        conn.close()


@app.get("/webapi/positions/{position_id}", response_model=dict)
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

        if row.get("created_at"):
            row["created_at"] = str(row["created_at"])
        if row.get("updated_at"):
            row["updated_at"] = str(row["updated_at"])

        return {"code": 200, "message": "success", "data": row}
    finally:
        conn.close()


@app.post("/webapi/positions", status_code=201, response_model=dict)
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

        if new_row.get("created_at"):
            new_row["created_at"] = str(new_row["created_at"])
        if new_row.get("updated_at"):
            new_row["updated_at"] = str(new_row["updated_at"])

        return {"code": 201, "message": "创建成功", "data": new_row}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"新增失败: {str(e)}")
    finally:
        conn.close()


@app.put("/webapi/positions/{position_id}", response_model=dict)
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
            return {"code": 200, "message": "无需更新", "data": existing}

        sql = f"UPDATE positions SET {', '.join(updates)} WHERE id = %s"
        params.append(position_id)

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT {POSITION_COLUMNS} FROM positions WHERE id = %s", (position_id,))
            updated_row = cursor.fetchone()

        if updated_row.get("created_at"):
            updated_row["created_at"] = str(updated_row["created_at"])
        if updated_row.get("updated_at"):
            updated_row["updated_at"] = str(updated_row["updated_at"])

        return {"code": 200, "message": "更新成功", "data": updated_row}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    finally:
        conn.close()


@app.delete("/webapi/positions/{position_id}", response_model=dict)
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


@app.patch("/webapi/positions/{position_id}/status", response_model=dict)
def update_position_status(
    position_id: int,
    body: StatusUpdateRequest,
    current_user: dict = Depends(require_role("admin", "hr")),
):
    """变更岗位状态（admin 可审批/关闭，hr 只能提交）"""
    action = body.action

    # hr 角色只能执行 submit 操作
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

        if updated_row.get("created_at"):
            updated_row["created_at"] = str(updated_row["created_at"])
        if updated_row.get("updated_at"):
            updated_row["updated_at"] = str(updated_row["updated_at"])

        return {"code": 200, "message": f"状态已变更为 {new_status}", "data": updated_row}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"状态变更失败: {str(e)}")
    finally:
        conn.close()


@app.get("/webapi/statistics", response_model=dict)
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


@app.post("/webapi/positions/batch", status_code=201, response_model=dict)
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


# ---------- 启动入口 ----------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
