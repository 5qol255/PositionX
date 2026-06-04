from fastapi import APIRouter, Depends, HTTPException

from backend.auth import create_token, get_current_user, pwd_context
from backend.db import get_connection
from backend.models import UserLogin

router = APIRouter(tags=["认证"])


@router.post("/auth/login", response_model=dict)
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


@router.get("/auth/me", response_model=dict)
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"code": 200, "message": "success", "data": current_user}
