from typing import List, Optional

from pydantic import BaseModel, Field


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


class StatusUpdateRequest(BaseModel):
    action: str = Field(..., description="操作：submit/approve/reject/close")


class BatchUploadRequest(BaseModel):
    positions: List[PositionCreate]


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
