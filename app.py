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

class PositionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="岗位名称")
    responsibilities: Optional[str] = Field(None, min_length=1, description="岗位职责")
    requirements: Optional[str] = Field(None, min_length=1, description="岗位要求")
    bonus: Optional[str] = Field(None, description="加分项")

class PositionResponse(BaseModel):
    id: int
    title: str
    responsibilities: str
    requirements: str
    bonus: str

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

@app.get("/webapi/positions", response_model=dict)
def get_all_positions():
    """获取所有岗位信息"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, responsibilities, requirements, bonus FROM positions ORDER BY id DESC")
            rows = cursor.fetchall()
        return {"data": rows}
    finally:
        conn.close()


@app.get("/webapi/positions/{position_id}", response_model=dict)
def get_position(position_id: int):
    """获取单个岗位信息"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, responsibilities, requirements, bonus FROM positions WHERE id = %s",
                (position_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="岗位不存在")
        return {"data": row}
    finally:
        conn.close()


@app.post("/webapi/positions", status_code=201, response_model=dict)
def create_position(position: PositionCreate):
    """新增岗位"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO positions (title, responsibilities, requirements, bonus) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (position.title, position.responsibilities, position.requirements, position.bonus))
            conn.commit()
            new_id = cursor.lastrowid

        # 查询新建的完整记录
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, responsibilities, requirements, bonus FROM positions WHERE id = %s",
                (new_id,)
            )
            new_row = cursor.fetchone()
        return {"data": new_row}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"新增失败: {str(e)}")
    finally:
        conn.close()


@app.put("/webapi/positions/{position_id}", response_model=dict)
def update_position(position_id: int, position: PositionUpdate):
    """更新岗位信息（支持部分更新）"""
    # 检查岗位是否存在
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM positions WHERE id = %s",
                (position_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="岗位不存在")

        # 构建动态更新 SQL
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
            # 无字段需要更新，直接返回当前记录
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title, description FROM positions WHERE id = %s",
                    (position_id,)
                )
                row = cursor.fetchone()
            return {"data": row}

        sql = f"UPDATE positions SET {', '.join(updates)} WHERE id = %s"
        params.append(position_id)

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()

        # 返回更新后的记录
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, responsibilities, requirements, bonus FROM positions WHERE id = %s",
                (position_id,)
            )
            updated_row = cursor.fetchone()
        return {"data": updated_row}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    finally:
        conn.close()


@app.delete("/webapi/positions/{position_id}", response_model=dict)
def delete_position(position_id: int):
    """删除岗位"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM positions WHERE id = %s",
                (position_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="岗位不存在")

            cursor.execute(
                "DELETE FROM positions WHERE id = %s",
                (position_id,)
            )
            conn.commit()
        return {"message": f"岗位 id={position_id} 删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    finally:
        conn.close()


@app.post("/webapi/positions/batch", status_code=201, response_model=dict)
def batch_upload(request: BatchUploadRequest):
    """批量上传岗位（自动跳过已存在的重复记录）"""
    if not request.positions:
        raise HTTPException(status_code=400, detail="导入数据不能为空")

    conn = get_connection()
    try:
        inserted = 0
        skipped = 0
        with conn.cursor() as cursor:
            for pos in request.positions:
                # 检查是否已存在完全相同的岗位
                cursor.execute(
                    "SELECT id FROM positions WHERE title = %s AND responsibilities = %s AND requirements = %s AND bonus = %s LIMIT 1",
                    (pos.title, pos.responsibilities, pos.requirements, pos.bonus)
                )
                if cursor.fetchone():
                    skipped += 1
                    continue   # 已存在则跳过

                cursor.execute(
                    "INSERT INTO positions (title, responsibilities, requirements, bonus) VALUES (%s, %s, %s, %s)",
                    (pos.title, pos.responsibilities, pos.requirements, pos.bonus)
                )
                inserted += 1

        conn.commit()
        return {
            "message": f"批量导入完成：新增 {inserted} 条，跳过 {skipped} 条（已存在）",
            "count": inserted,
            "skipped": skipped
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")
    finally:
        conn.close()


# ---------- 启动入口 ----------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
