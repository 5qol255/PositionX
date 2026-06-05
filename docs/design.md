# PositionX 系统设计方案 v2

> 基于当前代码状态的完整设计文档，替代过时的 v1 规划。

---

## 一、项目概述

**PositionX** 是一个招聘岗位管理系统，采用前后端分离架构，支持岗位发布、审批流转、批量导入等功能。

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI + PyMySQL | RESTful API，Python 3.12 |
| 前端 | Vue 3 + TypeScript + Element Plus | Composition API，Pinia 状态管理 |
| 数据库 | MySQL 8.0 | 关系型存储 |
| 认证 | JWT (python-jose) + bcrypt | 无状态 Token 认证 |
| 部署 | Docker Compose | MySQL + FastAPI + Nginx |

---

## 二、系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   浏览器     │────→│  Nginx      │────→│  Vue SPA    │
└─────────────┘     │  (frontend) │     │  (static)   │
                    └──────┬──────┘     └─────────────┘
                           │
                           │ /webapi/*
                           ↓
                    ┌─────────────┐     ┌─────────────┐
                    │ FastAPI     │────→│  MySQL 8.0  │
                    │ :8080       │     │  :3306      │
                    │ (backend)   │     │  (db)       │
                    └─────────────┘     └─────────────┘
```

- **Nginx**：托管前端静态文件，反向代理 `/webapi/` 到后端
- **FastAPI**：不对外暴露端口，仅内部网络可访问
- **MySQL**：不对外暴露端口，数据持久化通过 `mysql_data` volume

---

## 三、目录结构

```
PositionX/
├── backend/                    # FastAPI 后端
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用初始化 + CORS + 路由挂载
│   ├── auth.py                 # JWT 生成/解析、角色校验依赖
│   ├── db.py                   # 数据库连接配置（环境变量驱动）
│   ├── models.py               # Pydantic 请求/响应模型
│   └── routers/
│       ├── auth.py             # POST /auth/login, GET /auth/me
│       ├── positions.py        # 岗位 CRUD + 状态变更 + 批量上传
│       └── statistics.py       # GET /statistics
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/                # Axios 接口封装
│   │   │   ├── auth.ts
│   │   │   └── positions.ts
│   │   ├── components/         # 通用组件
│   │   │   ├── ApprovalDialog.vue
│   │   │   ├── BatchUpload.vue
│   │   │   ├── DeleteConfirm.vue
│   │   │   ├── PositionForm.vue
│   │   │   ├── PositionTable.vue
│   │   │   ├── PublicPositionTable.vue
│   │   │   ├── StatisticsPanel.vue
│   │   │   └── StatusTag.vue
│   │   ├── router/
│   │   │   └── index.ts        # 路由配置 + 导航守卫
│   │   ├── stores/
│   │   │   ├── authStore.ts    # Pinia：登录态 + 用户信息
│   │   │   └── positionStore.ts # Pinia：岗位列表 + 统计 + 搜索
│   │   ├── types/
│   │   │   ├── auth.ts         # TS 类型：User, LoginRequest...
│   │   │   └── position.ts     # TS 类型：Position, PositionCreate...
│   │   ├── utils/
│   │   │   └── request.ts      # Axios 实例 + 拦截器（Token/401处理）
│   │   ├── views/
│   │   │   ├── DashboardView.vue   # 管理后台
│   │   │   ├── LoginView.vue       # 登录页
│   │   │   ├── PositionDetailView.vue # 岗位详情
│   │   │   └── PublicView.vue      # 公开页面（热招岗位）
│   │   ├── App.vue
│   │   └── main.ts
│   └── ...
│
├── tests/                      # pytest 测试（Mock 数据库）
│   ├── conftest.py             # MockCursor, MockConnection, fixtures
│   ├── test_auth.py            # 登录 + Token 校验
│   ├── test_positions.py       # CRUD + 搜索/过滤
│   ├── test_status.py          # 状态流转
│   ├── test_permissions.py     # 角色权限边界
│   ├── test_batch.py           # 批量导入
│   └── test_statistics.py      # 统计接口
│
├── docker/                     # Docker 配置
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── default.conf            # Nginx 反向代理配置
│
├── data/                       # 样例数据（gitignored）
│   ├── positions_sample.csv
│   └── positions_sample.xlsx
│
├── docker-compose.yml
├── db_init.sql                 # 数据库初始化（建表 + 预置账号）
├── requirements.txt
├── pytest.ini                  # pythonpath = .
└── README.md
```

---

## 四、数据库设计

### 4.1 岗位表 `positions`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| title | VARCHAR(200) | NOT NULL | 岗位名称 |
| responsibilities | TEXT | NOT NULL | 岗位职责 |
| requirements | TEXT | NOT NULL | 岗位要求 |
| bonus | TEXT | — | 加分项 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'DRAFT' | 状态 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL DEFAULT ... ON UPDATE ... | 更新时间 |

### 4.2 用户表 `users`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| role | VARCHAR(20) | NOT NULL DEFAULT 'viewer' | admin / hr / viewer |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4.3 预置账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | admin |
| hr | hr123 | hr |

---

## 五、后端设计

### 5.1 模块职责

| 模块 | 职责 |
|------|------|
| `backend.main` | FastAPI 实例创建、CORS、路由挂载 |
| `backend.auth` | JWT 密钥配置、`create_token`、`get_current_user`、`require_role` |
| `backend.db` | `DB_CONFIG` 字典（环境变量驱动）、`get_connection()` |
| `backend.models` | 所有 Pydantic 模型（PositionCreate, PositionUpdate, StatusUpdateRequest, BatchUploadRequest, UserLogin） |
| `backend.routers.auth` | 登录、获取当前用户 |
| `backend.routers.positions` | 岗位 CRUD、状态变更、批量上传 |
| `backend.routers.statistics` | 统计查询 |

### 5.2 状态机设计

岗位生命周期：

```
DRAFT ──submit──→ PENDING ──approve──→ PUBLISHED ──close──→ CLOSED
              └─reject──┘                              （终态）
```

| 当前状态 | 允许操作 | 目标状态 |
|----------|----------|----------|
| DRAFT | submit | PENDING |
| PENDING | approve | PUBLISHED |
| PENDING | reject | DRAFT |
| PUBLISHED | close | CLOSED |
| CLOSED | （无） | — |

### 5.3 角色权限矩阵

| 操作 | admin | hr | viewer |
|------|-------|----|--------|
| 查看岗位（公开） | ✅ | ✅ | ✅ |
| 创建岗位 | ✅ | ✅ | ❌ |
| 编辑岗位（仅 DRAFT） | ✅ | ✅ | ❌ |
| 删除岗位（仅 DRAFT/CLOSED） | ✅ | ✅ | ❌ |
| 提交审批 | ✅ | ✅ | ❌ |
| 审批通过/驳回 | ✅ | ❌ | ❌ |
| 关闭岗位 | ✅ | ❌ | ❌ |
| 批量导入 | ✅ | ✅ | ❌ |

### 5.4 API 清单

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /webapi/auth/login | 登录，返回 JWT | 否 |
| GET | /webapi/auth/me | 当前用户信息 | 是 |
| GET | /webapi/positions | 岗位列表（keyword, status 过滤） | 否 |
| GET | /webapi/positions/:id | 岗位详情 | 否 |
| POST | /webapi/positions | 创建岗位 | admin/hr |
| PUT | /webapi/positions/:id | 更新岗位（仅 DRAFT） | admin/hr |
| DELETE | /webapi/positions/:id | 删除岗位（仅 DRAFT/CLOSED） | admin/hr |
| PATCH | /webapi/positions/:id/status | 变更状态 | admin/hr |
| POST | /webapi/positions/batch | 批量导入 | admin/hr |
| GET | /webapi/statistics | 统计数据 | 否 |

---

## 六、前端设计

### 6.1 路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | PublicView | 公开页面，展示已发布岗位 |
| `/positions/:id` | PositionDetailView | 岗位详情（长文本完整展示） |
| `/admin/login` | LoginView | 登录页 |
| `/admin/dashboard` | DashboardView | 管理后台（需登录） |

路由守卫：`/admin/dashboard` 未登录自动跳 `/admin/login`。

### 6.2 组件职责

| 组件 | 职责 |
|------|------|
| `PositionTable` | 管理后台表格，含操作列（编辑/提交/审批/关闭/删除） |
| `PublicPositionTable` | 公开页表格，只读，含"查看详情"按钮 |
| `PositionForm` | 新增/编辑弹窗表单 |
| `ApprovalDialog` | 审批弹窗（通过/驳回） |
| `BatchUpload` | Excel/CSV 批量上传 + 预览 |
| `DeleteConfirm` | 删除二次确认（支持单条/批量） |
| `StatisticsPanel` | 统计数字卡片 |
| `StatusTag` | 状态彩色标签 |

### 6.3 状态管理

**authStore**：
- `user`, `token`, `isLoggedIn`
- `isAdmin`, `canEdit`
- `login()`, `logout()`, `init()`

**positionStore**：
- `positions`, `statistics`, `loading`
- `fetchPositions()`, `fetchStatistics()`
- `addPosition()`, `editPosition()`, `removePosition()`
- `changeStatus()`, `batchImport()`, `setSearch()`

---

## 七、测试设计

### 7.1 测试策略

- **Mock 数据库**：`MockCursor` / `MockConnection`，不依赖真实 MySQL
- **FastAPI TestClient**：端到端 API 测试
- **覆盖率**：10 个接口，45 个测试用例

### 7.2 测试分类

| 测试文件 | 用例数 | 覆盖范围 |
|----------|--------|----------|
| `test_auth.py` | 7 | 登录成功/失败/空体、Token 校验 |
| `test_positions.py` | 14 | CRUD、搜索过滤、状态校验、字段缺失 |
| `test_status.py` | 6 | 提交/审批/驳回/关闭、无效流转、终态锁定 |
| `test_permissions.py` | 10 | admin/hr/viewer 的权限边界 |
| `test_batch.py` | 4 | 成功导入、去重、空列表、未认证 |
| `test_statistics.py` | 2 | 正常统计、空数据 |

---

## 八、部署

### 8.1 Docker Compose

```bash
docker compose up --build
```

服务：
- `db`：MySQL 8.0，自动执行 `db_init.sql`
- `backend`：FastAPI，`uvicorn backend.main:app`
- `frontend`：Nginx，代理 `/webapi/` → backend:8080

### 8.2 本地开发

```bash
# 后端
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8080

# 前端
cd frontend
npm install
npm run dev
```

### 8.3 环境变量（.env）

```env
MYSQL_ROOT_PASSWORD=root
JWT_SECRET=your-secret-key
```

---

## 九、变更记录（v1 → v2）

| 变更项 | v1 | v2 |
|--------|----|----|
| 后端入口 | `app.py` 单体 496 行 | 拆分为 `backend/` 包，入口 `backend.main:app` |
| 角色设计 | admin / approver / viewer | admin / hr / viewer |
| 前端视图 | `HomeView.vue` | `DashboardView.vue` |
| 前端公开页 | 表格内嵌在 dashboard | 独立 `PublicView.vue` + `PositionDetailView.vue` |
| Docker 配置 | 散放在根目录 | 集中到 `docker/` 目录 |
| 测试 | 无 | 45 个 pytest 用例，Mock 数据库 |
| 启动方式 | `python app.py` | `uvicorn backend.main:app` |
