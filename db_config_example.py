import os
import pymysql

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "your_password_here"),
    "database": os.getenv("DB_NAME", "recruitment"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,  # 返回字典格式
}