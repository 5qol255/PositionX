import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "your username",
    "password": "your password",
    "database": "your database name",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,  # 返回字典格式
}