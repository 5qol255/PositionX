# 招聘岗位管理系统

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

## 测试指南

### 1. 公开页面测试

访问 <http://localhost>（Docker）或 <http://localhost:5173>（本地开发）

- 搜索框输入关键词，点击搜索
- 状态筛选下拉框切换不同状态
- 点击「查看详情」查看岗位完整信息
- 点击「← 返回」回到列表

### 2. 登录测试

访问 <http://localhost/admin/login>

- 输入错误密码 → 提示「用户名或密码错误」
- 用 admin/admin123 登录 → 跳转管理后台
- 用 hr/hr123 登录 → 跳转管理后台

### 3. 岗位管理测试（admin 角色）

登录后在管理后台：

**创建岗位：**

- 点击「新增岗位」，填写表单，提交
- 新岗位状态为「草稿」

**编辑岗位：**

- 草稿状态的岗位，点击「编辑」修改内容
- 非草稿状态的岗位，没有编辑按钮

**提交审批：**

- 草稿状态的岗位，点击「提交审批」
- 状态变为「待审批」

**审批岗位：**

- 待审批状态的岗位，点击「审批」
- 弹窗选择「通过」或「驳回」
- 通过 → 状态变为「已发布」
- 驳回 → 状态变回「草稿」

**关闭岗位：**

- 已发布的岗位，点击「关闭」
- 状态变为「已关闭」

**删除岗位：**

- 草稿或已关闭的岗位，点击「删除」
- 其他状态的岗位，没有删除按钮

### 4. 权限测试（hr 角色）

用 hr/hr123 登录：

- 能看到「编辑」「提交审批」「删除」按钮（草稿状态）
- 看不到「审批」按钮（待审批状态）
- 看不到「关闭」按钮（已发布状态）
- 尝试直接调用审批接口 → 返回 403 权限不足

### 5. 批量导入测试

- 点击「批量导入」按钮
- 上传 Excel 文件（需包含 title, responsibilities, requirements 列）
- 预览数据，确认后导入
- 重复数据自动跳过

### 6. API 接口测试

使用 curl 或 Postman 测试：

```bash
# 获取岗位列表
curl http://localhost/webapi/positions

# 登录获取 Token
curl -X POST http://localhost/webapi/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 用 Token 访问需要认证的接口
curl http://localhost/webapi/auth/me \
  -H "Authorization: Bearer <你的token>"

# 创建岗位
curl -X POST http://localhost/webapi/positions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <你的token>" \
  -d '{"title":"测试岗位","responsibilities":"职责","requirements":"要求"}'

# 变更状态
curl -X PATCH http://localhost/webapi/positions/1/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <你的token>" \
  -d '{"action":"submit"}'
```

### 7. 异常场景测试

- 未登录访问管理后台 → 跳转登录页
- Token 过期后操作 → 提示重新登录
- 非草稿状态编辑岗位 → 返回 400
- hr 角色调用审批接口 → 返回 403
- 删除不存在的岗位 → 返回 404
