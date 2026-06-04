from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth, positions, statistics

app = FastAPI(
    title="招聘岗位发布系统",
    description="提供岗位信息的增删改查及批量上传接口",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/webapi")
app.include_router(positions.router, prefix="/webapi")
app.include_router(statistics.router, prefix="/webapi")
