"""入口文件 —— 启动 uvicorn 即可"""
import uvicorn

from backend.main import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
