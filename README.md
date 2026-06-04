# PositionX — 招聘岗位管理系统

一个基于 FastAPI + Vue 3 + Element Plus 的招聘岗位管理系统，支持岗位发布、审批流程、批量导入等功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI (Python 3.12) + PyMySQL |
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia |
| 数据库 | MySQL 8.0 |
| 认证 | JWT (python-jose + bcrypt) |
| 部署 | Docker Compose (Nginx + FastAPI + MySQL) |

## 功能特性

- 岗位 CRUD（创建、编辑、删除）
- 岗位状态流转：草稿 → 待审批 → 已发布 → 已关闭
- 角色权限控制（管理员 / 招聘管理）
- Excel 批量导入
- 关键词搜索 + 状态筛选
- 统计面板（按状态分组）
- 公开页面（仅展示已发布岗位）

## 快速启动

### Docker Compose（推荐）

```bash
docker compose up --build
```

访问 http://localhost

### 本地开发

```bash
# 后端
pip install -r requirements.txt
python app.py

# 前端
cd frontend
npm install
npm run dev
```

前端开发服务器：http://localhost:5173
后端 API：http://localhost:8080

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员（可审批、关闭岗位） |
| hr | hr123 | 招聘管理（可创建、编辑、提交岗位） |

## 项目结构

```
project/
├── app.py                    # 入口文件
├── backend/
│   ├── main.py               # FastAPI 应用初始化
│   ├── auth.py               # JWT 认证
│   ├── models.py             # Pydantic 数据模型
│   ├── db.py                 # 数据库连接
│   └── routers/
│       ├── auth.py           # 登录接口
│       ├── positions.py      # 岗位 CRUD + 状态变更
│       └── statistics.py     # 统计接口
├── frontend/
│   └── src/
│       ├── views/            # 页面组件
│       ├── components/       # 通用组件
│       ├── stores/           # Pinia 状态管理
│       ├── api/              # API 调用
│       ├── types/            # TypeScript 类型
│       ├── router/           # 路由配置
│       └── utils/            # 工具函数
├── docker-compose.yml
├── backend.Dockerfile
├── frontend.Dockerfile
├── nginx/default.conf
├── db_init.sql
├── requirements.txt
└── .env                      # 环境变量（已 gitignore）
```

## API 接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /webapi/auth/login | 登录 | 公开 |
| GET | /webapi/auth/me | 当前用户信息 | 登录 |
| GET | /webapi/positions | 岗位列表 | 公开 |
| GET | /webapi/positions/:id | 岗位详情 | 公开 |
| POST | /webapi/positions | 创建岗位 | admin/hr |
| PUT | /webapi/positions/:id | 更新岗位 | admin/hr |
| DELETE | /webapi/positions/:id | 删除岗位 | admin/hr |
| PATCH | /webapi/positions/:id/status | 变更状态 | admin/hr |
| POST | /webapi/positions/batch | 批量导入 | admin/hr |
| GET | /webapi/statistics | 统计数据 | 公开 |

## 角色权限

| 功能 | admin | hr |
|------|-------|-----|
| 查看岗位 | ✅ | ✅ |
| 创建/编辑 | ✅ | ✅ |
| 提交审批 | ✅ | ✅ |
| 审批通过/驳回 | ✅ | ❌ |
| 关闭岗位 | ✅ | ❌ |
| 删除岗位 | ✅ | ✅ |
| 批量导入 | ✅ | ✅ |

## 运行测试

```bash
# 安装测试依赖
pip install pytest httpx

# 运行全部测试
pytest tests/ -v
```
