# 招聘岗位管理系统 — 详细实施方案

## 一、项目概述

基于现有 FastAPI + Streamlit 项目，扩展为满足需求规格说明书的完整招聘岗位管理系统。  
后端继续使用 FastAPI (Python)，前端迁移至 Vue 3 + Element Plus。

### 技术栈总览

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端框架 | FastAPI | 0.115+ | RESTful API |
| 数据库 | MySQL | 8.x | 关系型存储 |
| 数据库驱动 | PyMySQL | 1.1+ | Python MySQL 连接器 |
| 前端框架 | Vue 3 | 3.5+ | Composition API |
| UI 组件库 | Element Plus | 2.x | 表格、表单、弹窗、上传 |
| 状态管理 | Pinia | 3.x | 全局状态 |
| HTTP 客户端 | Axios | 1.x | 请求封装 |
| Excel 解析 | SheetJS (xlsx) | -- | 前端解析 Excel |
| 构建工具 | Vite | 8.x | 开发热更新 + 生产构建 |
| 认证方式 | JWT (python-jose) | -- | Token 无状态认证 |
| 密码加密 | passlib + bcrypt | -- | 密码哈希存储 |
| 容器化 | Docker Compose | -- | MySQL + 后端 + 前端一键部署 |

---

## 二、Docker 部署架构

### 2.1 容器规划

```yaml
services:
  db:       # MySQL 8.0 — 数据库
  backend:  # FastAPI — 后端 API
  frontend: # Nginx + Vue 3 — 前端静态文件 + 反向代理
```

### 2.2 网络与端口

```
浏览器 → localhost:80 ──→ frontend (Nginx)
                              ├── /              → Vue SPA 静态文件
                              └── /webapi/*       → 反向代理 → backend:8080
                                                        ↓
                                                   backend → db:3306 (MySQL)
```

| 容器 | 对外端口 | 内部端口 | 说明 |
|------|---------|---------|------|
| frontend | 80 | 80 | Nginx，对外入口 |
| backend | 不暴露 | 8080 | 仅内部网络可访问 |
| db | 不暴露 | 3306 | 仅内部网络可访问 |

### 2.3 文件结构

```
project/
├── docker-compose.yml          # 编排文件
├── .env                        # 环境变量（JWT_SECRET、MySQL 密码等）
├── backend.Dockerfile          # 后端镜像
├── frontend.Dockerfile         # 前端镜像（多阶段构建）
├── nginx.conf                  # Nginx 配置（反向代理）
├── db_init.sql                 # 数据库初始化脚本（建表 + 预置数据）
├── app.py
├── db_config.py
├── ...
└── frontend/
    ├── ...
    └── vite.config.ts
```

### 2.4 docker-compose.yml

```yaml
version: "3.8"

services:
  db:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root}
      MYSQL_DATABASE: recruitment
      MYSQL_CHARSET: utf8mb4
    volumes:
      - mysql_data:/var/lib/mysql
      - ./db_init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend.Dockerfile
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      DB_HOST: db
      DB_PORT: 3306
      DB_USER: root
      DB_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root}
      DB_NAME: recruitment
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production}

  frontend:
    build:
      context: .
      dockerfile: frontend.Dockerfile
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "80:80"

volumes:
  mysql_data:
```

### 2.5 后端 Dockerfile (backend.Dockerfile)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2.6 前端 Dockerfile (frontend.Dockerfile)

多阶段构建：Node 编译 → Nginx 托管。

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 2.7 Nginx 配置 (nginx.conf)

```nginx
server {
    listen 80;
    server_name localhost;

    # 前端 SPA
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反向代理
    location /webapi/ {
        proxy_pass http://backend:8080/webapi/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 2.8 环境变量 (.env)

```env
MYSQL_ROOT_PASSWORD=root
JWT_SECRET=recruitment-jwt-secret-2024
```

### 2.9 db_config.py 改造

数据库配置改为从环境变量读取，兼容 Docker 和本地开发：

```python
import os
import pymysql

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "recruitment"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}
```

---

## 三、系统架构（应用层）

### 2.1 双页面架构

系统分为两个独立页面，普通访客无法感知管理后台的存在：

```
浏览器访问
├── /                    → 公开页面（PublicView）
│   └── 仅展示已发布(PUBLISHED)的岗位列表
│   └── 无需登录，任何人都可访问
│   └── 只读，无任何管理操作
│
└── /admin               → 管理后台（AdminView）
    ├── /admin/login     → 登录页（LoginView）
    └── /admin/dashboard → 管理面板（DashboardView）
        └── 岗位 CRUD、审批、批量上传、统计
        └── 需要登录，未登录自动跳转到 /admin/login
```

**设计要点**：
- 公开页面（`/`）与管理后台（`/admin`）完全独立
- 管理后台 URL 不在公开页面中出现或链接
- 管理后台使用 JWT Token 认证，Token 存储在 localStorage
- 前端路由守卫：访问 `/admin/dashboard` 时检查 Token，无效则跳转登录

### 2.2 角色设计

| 角色 | 说明 | 权限 |
|------|------|------|
| admin | 管理员 | 所有操作：CRUD、审批、批量导入、关闭 |
| approver | 审批人 | 审批操作（通过/驳回），查看所有岗位 |
| viewer | 只读管理员 | 查看所有岗位（含草稿/待审批），无修改权限 |

预置账号（写入数据库初始化脚本）：

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | admin | 超级管理员 |
| approver | approver123 | approver | 审批人 |

> ⚠️ 以上为开发/演示用默认密码，生产环境应强制修改。

---

## 三、数据库设计

### 3.1 positions 表变更

在现有 `positions` 表基础上新增 3 个字段：

```sql
ALTER TABLE positions
  ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'DRAFT' COMMENT '岗位状态' AFTER bonus,
  ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';
```

### 2.2 最终表结构

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT / BIGINT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| title | VARCHAR(200) | NOT NULL | 岗位名称 |
| responsibilities | TEXT | NOT NULL | 岗位职责 |
| requirements | TEXT | NOT NULL | 任职要求 |
| bonus | TEXT | DEFAULT '' | 加分项 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'DRAFT' | 岗位状态 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 3.2 新增 users 表

```sql
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希（bcrypt）',
  role VARCHAR(20) NOT NULL DEFAULT 'viewer' COMMENT '角色：admin/approver/viewer',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员用户表';

-- 预置账号（密码为 bcrypt 哈希值，明文分别为 admin123 / approver123）
INSERT INTO users (username, password_hash, role) VALUES
('admin',    '$2b$12$<运行时生成的哈希值>', 'admin'),
('approver', '$2b$12$<运行时生成的哈希值>', 'approver');
```

> 实际开发中，哈希值由 Python 脚本生成：
> ```python
> from passlib.context import CryptContext
> pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
> print(pwd.hash("admin123"))
> ```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 密码哈希 |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'viewer' | 角色 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 3.3 状态枚举

| 值 | 含义 | 说明 |
|----|------|------|
| DRAFT | 草稿 | 新建岗位的默认状态 |
| PENDING | 待审批 | 已提交，等待审批人处理 |
| PUBLISHED | 已发布 | 审批通过，对外可见 |
| CLOSED | 已关闭 | 手动关闭，不可再变更 |

### 2.4 状态流转规则

```
DRAFT ──提交审批──→ PENDING
PENDING ──审批通过──→ PUBLISHED
PENDING ──审批驳回──→ DRAFT
PUBLISHED ──关闭──→ CLOSED
CLOSED ──（终态，不可变更）
```

**约束**：
- 只有 DRAFT 状态可以提交审批
- 只有 PENDING 状态可以审批（通过或驳回）
- 只有 PUBLISHED 状态可以关闭
- 已发布的岗位不可直接删除，需先关闭
- 已关闭的岗位不可删除、不可修改

---

## 四、后端 API 设计

### 4.1 统一返回格式

**成功响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**错误响应**：
```json
{
  "code": 400,
  "message": "岗位不存在",
  "data": null
}
```

### 4.2 接口清单

#### 4.2.0 认证接口（新增）

| 方法 | URL | 说明 | 认证 |
|------|-----|------|------|
| POST | `/webapi/auth/login` | 用户登录，返回 JWT Token | 否 |
| GET | `/webapi/auth/me` | 获取当前登录用户信息 | 是 |
| POST | `/webapi/auth/logout` | 登出（前端清除 Token 即可，此接口可选） | 是 |

**POST /webapi/auth/login**

请求体：
```json
{
  "username": "admin",
  "password": "admin123"
}
```

成功响应：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "role": "admin"
    }
  }
}
```

失败响应（用户名或密码错误）：
```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

**GET /webapi/auth/me**

请求头：`Authorization: Bearer <token>`

成功响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

Token 过期或无效 → 返回 401。

**JWT 配置**：
- 密钥：配置在 `db_config.py` 中的 `JWT_SECRET`
- 过期时间：24 小时
- 算法：HS256

**认证中间件**：
- 后端新增依赖函数 `get_current_user(request)`，从 `Authorization: Bearer <token>` 中解析用户
- 需要认证的接口注入该依赖，未认证返回 401
- 各角色权限校验在具体接口中实现

**角色权限矩阵**：

| 操作 | admin | approver | viewer |
|------|-------|----------|--------|
| 查看所有岗位（含草稿） | ✅ | ✅ | ✅ |
| 创建/编辑岗位 | ✅ | ❌ | ❌ |
| 删除岗位 | ✅ | ❌ | ❌ |
| 提交审批 | ✅ | ❌ | ❌ |
| 审批（通过/驳回） | ✅ | ✅ | ❌ |
| 关闭岗位 | ✅ | ❌ | ❌ |
| 批量导入 | ✅ | ❌ | ❌ |
| 查看统计 | ✅ | ✅ | ✅ |

#### 4.2.1 岗位 CRUD（已有，需改造）

| 方法 | URL | 说明 | 变更 |
|------|-----|------|------|
| GET | `/webapi/positions` | 获取岗位列表 | 增加 `keyword`、`status` 查询参数；返回值增加 `status`、`created_at`、`updated_at`；返回格式改为 `{code, message, data}` |
| GET | `/webapi/positions/{id}` | 获取单个岗位 | 返回值增加新字段；返回格式统一 |
| POST | `/webapi/positions` | 创建新岗位 | 请求体可选 `status`（默认 DRAFT）；返回格式统一；新增岗位默认 DRAFT 状态 |
| PUT | `/webapi/positions/{id}` | 更新岗位 | 只允许 DRAFT 状态的岗位被编辑；返回格式统一 |
| DELETE | `/webapi/positions/{id}` | 删除岗位 | 只允许删除 DRAFT 或 CLOSED 状态的岗位；返回格式统一 |

#### 4.2.2 搜索与过滤（新增）

```
GET /webapi/positions?keyword=Java&status=PUBLISHED
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按岗位名称模糊搜索 (LIKE %keyword%) |
| status | string | 否 | 按状态精确过滤 (DRAFT/PENDING/PUBLISHED/CLOSED) |

两个参数可组合使用，均不传则返回全部。

#### 4.2.3 状态变更接口（新增）

```
PATCH /webapi/positions/{id}/status
```

**请求体**：
```json
{
  "action": "submit" | "approve" | "reject" | "close",
  "comment": "审批意见（可选）"
}
```

**action 与状态流转对应关系**：

| action | 说明 | 前置状态 | 目标状态 |
|--------|------|---------|---------|
| submit | 提交审批 | DRAFT | PENDING |
| approve | 审批通过 | PENDING | PUBLISHED |
| reject | 审批驳回 | PENDING | DRAFT |
| close | 关闭岗位 | PUBLISHED | CLOSED |

**返回**：更新后的岗位完整信息。

**错误情况**：
- 岗位不存在 → 404
- 状态不允许该操作 → 400（如对 PUBLISHED 状态执行 submit）

#### 4.2.4 统计接口（新增）

```
GET /webapi/statistics
```

**返回**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 25,
    "by_status": {
      "DRAFT": 5,
      "PENDING": 3,
      "PUBLISHED": 15,
      "CLOSED": 2
    }
  }
}
```

#### 4.2.5 批量上传（已有，需改造）

```
POST /webapi/positions/batch
```

- 返回格式统一为 `{code, message, data}`
- 批量导入的岗位默认状态为 DRAFT
- Excel 模板列名：`title`（必填）、`responsibilities`（必填）、`requirements`（必填）、`bonus`（可选）

### 4.3 后端代码结构变更

`app.py` 中需要修改/新增的内容：

```
app.py
├── Pydantic 模型
│   ├── PositionCreate          # 增加 status 可选字段
│   ├── PositionUpdate          # 不变
│   ├── PositionResponse        # 增加 status, created_at, updated_at
│   ├── StatusUpdateRequest     # 新增：action + comment
│   ├── BatchUploadRequest      # 不变
│   ├── UserLogin               # 新增：username + password
│   └── UserResponse            # 新增：id + username + role
├── 工具函数
│   ├── success_response(data, message)   # 新增：统一成功返回
│   ├── error_response(code, message)     # 新增：统一错误返回
│   ├── create_token(user)                # 新增：生成 JWT
│   └── get_current_user(request)         # 新增：解析 JWT 依赖
├── API 路由
│   ├── POST /webapi/auth/login           # 新增：登录
│   ├── GET  /webapi/auth/me              # 新增：当前用户信息
│   ├── GET  /webapi/positions            # 改造：加搜索/过滤参数
│   ├── GET  /webapi/positions/{id}       # 改造：返回格式统一
│   ├── POST /webapi/positions            # 改造：返回格式统一 + 认证
│   ├── PUT  /webapi/positions/{id}       # 改造：加状态校验 + 认证
│   ├── DELETE /webapi/positions/{id}     # 改造：加状态校验 + 认证
│   ├── PATCH /webapi/positions/{id}/status  # 新增：状态变更 + 认证
│   ├── POST /webapi/positions/batch      # 改造：返回格式统一 + 认证
│   └── GET  /webapi/statistics           # 新增：统计接口
└── 启动入口
```

**认证规则**：
- `GET /webapi/positions`、`GET /webapi/positions/{id}`、`GET /webapi/statistics` — **无需认证**（公开页面也需要）
- 其余写操作接口 — **需要认证**，且按角色权限校验

---

## 五、前端设计

### 5.1 目录结构

```
frontend/src/
├── api/
│   ├── positions.ts              # 岗位 API 调用层
│   └── auth.ts                   # 认证 API 调用层
├── types/
│   ├── position.ts               # 岗位 TypeScript 类型
│   └── auth.ts                   # 认证 TypeScript 类型
├── utils/
│   └── request.ts                # Axios 实例 + 拦截器（自动附加 Token）
├── stores/
│   ├── positionStore.ts          # 岗位状态管理
│   └── authStore.ts              # 认证状态管理（登录态、用户信息）
├── components/
│   ├── PositionForm.vue          # 新增/编辑表单
│   ├── PositionTable.vue         # 岗位列表表格（管理后台用，含操作列）
│   ├── PublicPositionTable.vue   # 公开岗位列表（只读，仅显示已发布）
│   ├── BatchUpload.vue           # Excel 批量上传
│   ├── DeleteConfirm.vue         # 删除确认弹窗
│   ├── StatusTag.vue             # 状态标签（彩色 Tag）
│   ├── ApprovalDialog.vue        # 审批弹窗
│   └── StatisticsPanel.vue       # 统计面板
├── views/
│   ├── PublicView.vue            # 公开页面（/）
│   ├── LoginView.vue             # 登录页面（/admin/login）
│   └── DashboardView.vue         # 管理面板（/admin/dashboard）
├── router/
│   └── index.ts                  # 路由配置 + 导航守卫
├── App.vue
└── main.ts
```

### 5.2 类型定义

**types/position.ts** — 岗位相关类型：

```typescript
/** 岗位状态枚举 */
export type PositionStatus = 'DRAFT' | 'PENDING' | 'PUBLISHED' | 'CLOSED'

/** 岗位信息（完整） */
export interface Position {
  id: number
  title: string
  responsibilities: string
  requirements: string
  bonus: string
  status: PositionStatus
  created_at: string       // ISO 8601 格式
  updated_at: string
}

/** 创建岗位请求体 */
export interface PositionCreate {
  title: string
  responsibilities: string
  requirements: string
  bonus?: string
  status?: PositionStatus  // 默认 DRAFT
}

/** 更新岗位请求体 */
export interface PositionUpdate {
  title?: string
  responsibilities?: string
  requirements?: string
  bonus?: string
}

/** 状态变更请求体 */
export interface StatusUpdateRequest {
  action: 'submit' | 'approve' | 'reject' | 'close'
  comment?: string
}

/** 统一 API 响应 */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

/** 批量上传结果 */
export interface BatchResult {
  message: string
  count: number
  skipped: number
}

/** 统计数据 */
export interface Statistics {
  total: number
  by_status: Record<PositionStatus, number>
}
```

**types/auth.ts** — 认证相关类型：

```typescript
/** 用户角色 */
export type UserRole = 'admin' | 'approver' | 'viewer'

/** 用户信息 */
export interface User {
  id: number
  username: string
  role: UserRole
}

/** 登录请求体 */
export interface LoginRequest {
  username: string
  password: string
}

/** 登录响应 */
export interface LoginResponse {
  token: string
  user: User
}
```

### 5.3 请求封装 (utils/request.ts)

```typescript
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/webapi',
  timeout: 10000,
})

// 请求拦截器：自动附加 Token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const status = err.response?.status
    const msg = err.response?.data?.message || err.message || '请求失败'

    if (status === 401) {
      // Token 过期或无效，清除登录态并跳转登录页
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (router.currentRoute.value.path.startsWith('/admin')) {
        router.push('/admin/login')
      }
      ElMessage.error('登录已过期，请重新登录')
    } else if (status === 403) {
      ElMessage.warning('权限不足')
    } else if (status === 404) {
      ElMessage.error('请求的资源不存在')
    } else if (status === 400) {
      ElMessage.warning(msg)
    } else if (status === 500) {
      ElMessage.error('服务器内部错误')
    } else {
      ElMessage.error(msg)
    }

    return Promise.reject(new Error(msg))
  }
)

export default request
```

### 5.4 API 调用层

**api/auth.ts** — 认证接口：

```typescript
import request from '@/utils/request'
import type { ApiResponse, LoginRequest, LoginResponse, User } from '@/types/auth'

/** 用户登录 */
export const login = (data: LoginRequest) =>
  request.post<any, ApiResponse<LoginResponse>>('/auth/login', data)

/** 获取当前用户信息 */
export const getCurrentUser = () =>
  request.get<any, ApiResponse<User>>('/auth/me')
```

**api/positions.ts** — 岗位接口：

```typescript
import request from '@/utils/request'
import type {
  Position, PositionCreate, PositionUpdate,
  StatusUpdateRequest, ApiResponse, BatchResult, Statistics
} from '@/types/position'

/** 获取岗位列表（支持搜索/过滤） */
export const getPositions = (params?: { keyword?: string; status?: string }) =>
  request.get<any, ApiResponse<Position[]>>('/positions', { params })

/** 获取单个岗位 */
export const getPosition = (id: number) =>
  request.get<any, ApiResponse<Position>>(`/positions/${id}`)

/** 创建岗位 */
export const createPosition = (data: PositionCreate) =>
  request.post<any, ApiResponse<Position>>('/positions', data)

/** 更新岗位 */
export const updatePosition = (id: number, data: PositionUpdate) =>
  request.put<any, ApiResponse<Position>>(`/positions/${id}`, data)

/** 删除岗位 */
export const deletePosition = (id: number) =>
  request.delete<any, ApiResponse<null>>(`/positions/${id}`)

/** 变更岗位状态 */
export const updateStatus = (id: number, data: StatusUpdateRequest) =>
  request.patch<any, ApiResponse<Position>>(`/positions/${id}/status`, data)

/** 批量上传 */
export const batchUpload = (positions: PositionCreate[]) =>
  request.post<any, ApiResponse<BatchResult>>('/positions/batch', { positions })

/** 获取统计数据 */
export const getStatistics = () =>
  request.get<any, ApiResponse<Statistics>>('/statistics')
```

### 5.5 Pinia 状态管理

**stores/authStore.ts** — 认证状态：

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest } from '@/types/auth'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string>(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isApprover = computed(() => user.value?.role === 'approver' || user.value?.role === 'admin')
  const canEdit = computed(() => user.value?.role === 'admin')
  const canApprove = computed(() => user.value?.role === 'admin' || user.value?.role === 'approver')

  /** 初始化：从 localStorage 恢复登录态 */
  const init = async () => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      user.value = JSON.parse(savedUser)
    }
    // 可选：调用 /auth/me 验证 Token 是否仍然有效
  }

  /** 登录 */
  const login = async (data: LoginRequest) => {
    const res = await authApi.login(data)
    token.value = res.data.token
    user.value = res.data.user
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
  }

  /** 登出 */
  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    user, token, isLoggedIn, isAdmin, isApprover, canEdit, canApprove,
    init, login, logout
  }
})
```

**stores/positionStore.ts** — 岗位状态：

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Position, PositionCreate, PositionUpdate, StatusUpdateRequest } from '@/types/position'
import * as api from '@/api/positions'

export const usePositionStore = defineStore('position', () => {
  // ---- 状态 ----
  const positions = ref<Position[]>([])
  const statistics = ref<{ total: number; by_status: Record<string, number> }>({
    total: 0, by_status: {}
  })
  const loading = ref(false)
  const error = ref('')

  // 搜索/过滤条件
  const keyword = ref('')
  const statusFilter = ref('')

  // ---- 计算属性 ----
  const filteredPositions = computed(() => positions.value)

  // ---- 操作方法 ----

  /** 获取岗位列表 */
  const fetchPositions = async () => {
    loading.value = true
    error.value = ''
    try {
      const params: Record<string, string> = {}
      if (keyword.value) params.keyword = keyword.value
      if (statusFilter.value) params.status = statusFilter.value
      const res = await api.getPositions(params)
      positions.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  /** 获取统计数据 */
  const fetchStatistics = async () => {
    try {
      const res = await api.getStatistics()
      statistics.value = res.data
    } catch (e: any) {
      console.error('获取统计数据失败:', e.message)
    }
  }

  /** 创建岗位 */
  const addPosition = async (data: PositionCreate) => {
    const res = await api.createPosition(data)
    await fetchPositions()
    await fetchStatistics()
    return res.data
  }

  /** 更新岗位 */
  const editPosition = async (id: number, data: PositionUpdate) => {
    const res = await api.updatePosition(id, data)
    await fetchPositions()
    return res.data
  }

  /** 删除岗位 */
  const removePosition = async (id: number) => {
    await api.deletePosition(id)
    await fetchPositions()
    await fetchStatistics()
  }

  /** 变更状态 */
  const changeStatus = async (id: number, data: StatusUpdateRequest) => {
    const res = await api.updateStatus(id, data)
    await fetchPositions()
    await fetchStatistics()
    return res.data
  }

  /** 批量导入 */
  const batchImport = async (list: PositionCreate[]) => {
    const res = await api.batchUpload(list)
    await fetchPositions()
    await fetchStatistics()
    return res.data
  }

  /** 设置搜索条件并刷新 */
  const setSearch = (kw: string, status: string) => {
    keyword.value = kw
    statusFilter.value = status
    fetchPositions()
  }

  return {
    positions, statistics, loading, error,
    keyword, statusFilter, filteredPositions,
    fetchPositions, fetchStatistics,
    addPosition, editPosition, removePosition,
    changeStatus, batchImport, setSearch
  }
})
```

### 5.6 组件设计

#### 5.6.1 StatusTag.vue — 状态标签

根据 status 值显示不同颜色的 Element Plus Tag：

| 状态 | 颜色 | 文字 |
|------|------|------|
| DRAFT | info (灰) | 草稿 |
| PENDING | warning (橙) | 待审批 |
| PUBLISHED | success (绿) | 已发布 |
| CLOSED | danger (红) | 已关闭 |

#### 5.6.2 StatisticsPanel.vue — 统计面板

顶部显示 4 个数字卡片（el-statistic），分别展示各状态数量和总数。  
页面加载时自动调用 `store.fetchStatistics()`。

布局：
```
┌──────────┬──────────┬──────────┬──────────┐
│  草稿 5  │ 待审批 3 │ 已发布 15│ 已关闭 2 │
└──────────┴──────────┴──────────┴──────────┘
```

#### 5.6.3 PositionTable.vue — 管理后台岗位列表

**顶部工具栏**：
- 搜索输入框（el-input，v-model 绑定 keyword）
- 状态下拉筛选（el-select，选项：全部/草稿/待审批/已发布/已关闭）
- 搜索按钮 → 调用 `store.setSearch()`
- 批量删除按钮（仅选中 DRAFT/CLOSED 状态时可用）

**表格列**：

| 列名 | 字段 | 宽度 | 说明 |
|------|------|------|------|
| ID | id | 60px | -- |
| 岗位名称 | title | 180px | -- |
| 岗位职责 | responsibilities | -- | show-overflow-tooltip |
| 任职要求 | requirements | -- | show-overflow-tooltip |
| 加分项 | bonus | -- | show-overflow-tooltip |
| 状态 | status | 100px | StatusTag 组件 |
| 创建时间 | created_at | 160px | 格式化显示 |
| 操作 | -- | 240px | 按钮组 |

**操作列按钮**（根据状态显示/隐藏）：

| 状态 | 可用操作 |
|------|---------|
| DRAFT | 编辑、提交审批、删除 |
| PENDING | 审批（通过/驳回） |
| PUBLISHED | 关闭 |
| CLOSED | 删除 |

#### 5.6.4 PositionForm.vue — 新增/编辑表单

- 位于页面左侧或通过 el-dialog 弹窗
- 表单字段：岗位名称（el-input）、岗位职责（el-input type=textarea）、任职要求（el-input type=textarea）、加分项（el-input type=textarea）
- 校验规则：title、responsibilities、requirements 必填
- 编辑模式：接收 Position 对象作为初始值
- 保存成功后 emit 事件通知父组件刷新列表

#### 5.6.5 ApprovalDialog.vue — 审批弹窗

- el-dialog 弹窗
- 显示岗位基本信息（只读）
- 审批意见输入框（el-input type=textarea）
- 两个按钮：「通过」（success）、「驳回」（danger）
- 点击后调用 `store.changeStatus(id, { action, comment })`

#### 5.6.6 BatchUpload.vue — 批量上传

- el-upload 组件选择文件
- 使用 xlsx 库在前端解析 Excel
- 列名校验：必须包含 title、responsibilities、requirements
- 数据预览：el-dialog 显示前 5 条数据
- 确认导入按钮 → 调用 `store.batchImport()`
- 结果提示：新增 X 条，跳过 Y 条

#### 5.6.7 DeleteConfirm.vue — 删除确认

- el-dialog 二次确认
- 单条删除：显示岗位名称
- 批量删除：显示已选数量

#### 5.6.8 PublicPositionTable.vue — 公开岗位列表（只读）

- 仅显示 PUBLISHED 状态的岗位
- 无操作列，无多选框
- 支持按名称搜索
- 长文本 show-overflow-tooltip，点击行可展开详情

### 5.7 页面设计

#### 5.7.1 PublicView.vue — 公开页面（`/`）

访客看到的首页，只展示已发布的岗位，无需登录。

```
┌─────────────────────────────────────────────────────────────┐
│  📋 招聘岗位 — 热招岗位                                       │
├─────────────────────────────────────────────────────────────┤
│  搜索栏：[关键词输入] [搜索]                                  │
├─────────────────────────────────────────────────────────────┤
│  PublicPositionTable（只读表格，仅 PUBLISHED 岗位）            │
│  ┌────┬──────┬──────────────────────────────────────┐       │
│  │ ID │ 岗位名称│ 岗位详情（职责/要求/加分项）          │       │
│  ├────┼──────┼──────────────────────────────────────┤       │
│  │ 1  │ Java后端│ 职责：...  要求：...  加分：...      │       │
│  └────┴──────┴──────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

- 调用 `GET /webapi/positions?status=PUBLISHED` 获取数据
- 页面简洁，仅搜索 + 表格
- 无任何管理入口链接

#### 5.7.2 LoginView.vue — 登录页面（`/admin/login`）

```
┌─────────────────────────────────────────┐
│            🔐 管理后台登录               │
│                                         │
│  用户名：[________________]              │
│  密  码：[________________]              │
│                                         │
│         [ 登  录 ]                       │
│                                         │
│  提示：仅管理员可访问                     │
└─────────────────────────────────────────┘
```

- el-card 居中布局
- 用户名 + 密码表单，el-form 校验
- 登录成功后跳转 `/admin/dashboard`
- 登录失败显示错误提示
- 已登录状态访问此页面自动跳转 dashboard

#### 5.7.3 DashboardView.vue — 管理面板（`/admin/dashboard`）

管理员的工作台，包含所有管理功能。

```
┌─────────────────────────────────────────────────────────────┐
│  📋 招聘岗位管理后台           欢迎，admin  [退出登录]         │
├─────────────────────────────────────────────────────────────┤
│  StatisticsPanel（数字卡片 × 4）                              │
├─────────────────────────────────────────────────────────────┤
│  搜索栏：[关键词] [状态下拉] [搜索]  [新增岗位] [批量上传]     │
├─────────────────────────────────────────────────────────────┤
│  PositionTable（含操作列：编辑/审批/删除/关闭）                │
│  ┌────┬──────┬──────┬────┬──────┬──────────┐               │
│  │ ID │ 名称 │ 状态 │ 时间│ 角色限制操作 │ 操作 │               │
│  ├────┼──────┼──────┼────┼──────────┤      │               │
│  │ .. │ ...  │ ...  │ .. │ ...      │ ...  │               │
│  └────┴──────┴──────┴────┴──────────┘      │               │
├─────────────────────────────────────────────────────────────┤
│  弹窗：PositionForm / ApprovalDialog / BatchUpload / Delete  │
└─────────────────────────────────────────────────────────────┘
```

- 顶部显示当前用户名和角色，右侧「退出登录」按钮
- 操作按钮根据**用户角色 + 岗位状态**双重控制显隐
- admin 角色：所有操作可用
- approver 角色：仅审批操作可用，CRUD 按钮隐藏
- viewer 角色：所有操作按钮隐藏，仅查看

### 5.8 路由配置 (router/index.ts)

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'public',
      component: () => import('@/views/PublicView.vue')
    },
    {
      path: '/admin/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue')
    },
    {
      path: '/admin/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 导航守卫：管理后台页面需要登录
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/admin/login')
  } else {
    next()
  }
})

export default router
```

### 5.9 Vite 配置 (vite.config.ts)

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/webapi': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
```

---

## 六、实施步骤

### Step 1：数据库迁移

1. 连接 MySQL，执行 ALTER TABLE 语句为 positions 表新增字段
2. 创建 users 表
3. 生成密码哈希并插入预置账号
4. 验证现有数据的 status 默认值为 DRAFT

### Step 2：后端改造 — 认证系统

1. 安装依赖：`pip install python-jose[cryptography] passlib[bcrypt]`
2. 新增 Pydantic 模型：UserLogin、UserResponse
3. 实现密码哈希工具函数
4. 实现 JWT Token 生成/解析函数：`create_token()`、`get_current_user()`
5. 新增 `POST /webapi/auth/login` 接口
6. 新增 `GET /webapi/auth/me` 接口

### Step 3：后端改造 — 数据模型与统一返回

1. 新增 Pydantic 模型：StatusUpdateRequest
2. 修改 PositionCreate：增加可选 status 字段
3. 修改 PositionResponse：增加 status、created_at、updated_at
4. 新增工具函数 success_response() / error_response()
5. 改造所有现有接口的返回格式为 `{code, message, data}`

### Step 4：后端改造 — 搜索/过滤

1. 修改 `GET /webapi/positions`，增加 keyword 和 status 查询参数
2. 动态构建 SQL WHERE 条件
3. keyword 使用 LIKE 模糊匹配 title
4. status 使用精确匹配

### Step 5：后端新增 — 状态变更接口

1. 新增 `PATCH /webapi/positions/{id}/status`
2. 实现状态流转校验逻辑
3. 添加角色权限校验（仅 admin/approver 可审批）

### Step 6：后端新增 — 统计接口

1. 新增 `GET /webapi/statistics`
2. SQL 按 status 分组 COUNT
3. 返回总数和各状态数量

### Step 7：后端改造 — CRUD 状态校验 + 权限控制

1. PUT 接口：校验只有 DRAFT 状态可编辑，仅 admin 可操作
2. DELETE 接口：校验只有 DRAFT / CLOSED 状态可删除，仅 admin 可操作
3. POST 创建 / 批量上传：仅 admin 可操作
4. 提交审批：仅 admin 可操作

### Step 8：前端 — 基础框架搭建

1. 创建 types/position.ts 和 types/auth.ts
2. 创建 utils/request.ts（含 Token 自动附加 + 401 处理）
3. 创建 api/auth.ts 和 api/positions.ts
4. 创建 stores/authStore.ts 和 stores/positionStore.ts
5. 配置 router/index.ts（含导航守卫）
6. 配置 vite.config.ts 代理
7. main.ts 注册 Element Plus + Pinia + Router

### Step 9：前端 — 公开页面

1. PublicPositionTable.vue（只读表格）
2. PublicView.vue（组装搜索 + 表格）

### Step 10：前端 — 登录页面

1. LoginView.vue（登录表单 + 跳转逻辑）

### Step 11：前端 — 管理后台组件

1. StatusTag.vue
2. StatisticsPanel.vue
3. PositionForm.vue
4. PositionTable.vue（含操作列，按钮按角色/状态显隐）
5. ApprovalDialog.vue
6. BatchUpload.vue
7. DeleteConfirm.vue

### Step 12：前端 — 管理面板组装

1. DashboardView.vue 组装所有管理组件
2. 顶部栏：用户名 + 角色 + 退出登录
3. App.vue 路由出口配置

### Step 13：联调与完善

1. 启动后端 (`python app.py`)
2. 启动前端 (`npm run dev`)
3. 测试公开页面：访问 `/` 看到已发布岗位
4. 测试登录：访问 `/admin/login`，用 admin/admin123 登录
5. 测试管理功能：CRUD、审批、批量导入
6. 测试权限：不同角色看到不同操作按钮
7. 修复 Streamlit 前端适配新字段
8. 异常场景测试（Token 过期、非法操作等）

---

## 七、Streamlit 前端适配

`front.py` 需要同步修改：

1. 表格展示增加「状态」列（彩色标签）
2. 表单增加状态下拉选择（仅新增时可选，默认 DRAFT）
3. 列表增加搜索框和状态过滤
4. 操作按钮根据状态显示/隐藏
5. 新增审批操作区域
6. 统计数字展示

---

## 八、交付物清单

| 序号 | 交付物 | 说明 |
|------|--------|------|
| 1 | 后端源代码 | app.py（含所有新增接口） |
| 2 | 前端源代码 | frontend/ 目录（Vue 3 完整项目） |
| 3 | 数据库脚本 | ALTER TABLE 语句 |
| 4 | 项目依赖配置 | requirements.txt / package.json |
| 5 | 系统运行视频 | 演示所有功能 |
| 6 | 实验报告 | 含 AI 辅助开发过程记录 |
| 7 | 本文档 | 详细实施方案 |

---

## 九、风险与应对

| 风险 | 应对措施 |
|------|---------|
| 数据库迁移影响现有数据 | ALTER TABLE 使用 DEFAULT 值，不影响已有记录 |
| 前后端接口不一致 | 严格按照本文档的接口定义开发，统一返回格式 |
| 状态流转逻辑复杂 | 后端硬编码状态机，前端按钮显隐控制 |
| Vue 前端开发量大 | 优先实现核心组件，统计功能可简化为数字卡片 |
