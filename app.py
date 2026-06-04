from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import pymysql
import uvicorn
from db_config import DB_CONFIG

# ---------- 数据库配置 ----------


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

# ---------- API 路由 ----------

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
