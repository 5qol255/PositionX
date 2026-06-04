-- 招聘岗位管理系统 — 数据库初始化脚本
-- 由 Docker MySQL 容器在首次启动时自动执行

CREATE DATABASE IF NOT EXISTS recruitment
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE recruitment;

-- 岗位表
CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '岗位名称',
    responsibilities TEXT NOT NULL COMMENT '岗位职责',
    requirements TEXT NOT NULL COMMENT '岗位要求',
    bonus TEXT COMMENT '加分项',
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
        COMMENT '岗位状态: DRAFT/PENDING/PUBLISHED/CLOSED',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='招聘岗位表';

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希（bcrypt）',
    role VARCHAR(20) NOT NULL DEFAULT 'viewer'
        COMMENT '角色: admin/hr/viewer',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 预置账号（密码均为 bcrypt 哈希）
INSERT IGNORE INTO users (username, password_hash, role) VALUES
    ('admin', '$2b$12$tYCny/aGPUfKii4LVImJUOpD.AR8ZrjRi6ikMulkKmMSF7GM510hK', 'admin'),
    ('hr',    '$2b$12$/d2NkwfqMtKEjHxvJi/YQ.ki6dIbmusPGGxzqhGtwzDi.xZFLMKKu', 'hr');
