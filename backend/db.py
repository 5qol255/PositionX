import os

import pymysql
from dbutils.pooled_db import PooledDB

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "recruitment"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

_pool = PooledDB(creator=pymysql, maxconnections=int(os.getenv("DB_MAX_CONNECTIONS", 10)), **DB_CONFIG)


def get_connection():
    """从连接池获取数据库连接"""
    return _pool.connection()
