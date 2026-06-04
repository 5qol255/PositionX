# Vue 3 前端重构方案

## 一、技术栈

| 层级 | 选型 | 说明 |
|------|------|------|
| 框架 | Vue 3.4+ | Composition API |
| 语言 | TypeScript 5.x | 全项目类型安全 |
| 构建 | Vite 5.x | 热更新快 |
| UI 库 | Element Plus 2.x | 表格、表单、弹窗、上传 |
| 状态 | Pinia 2.x | 全局岗位列表状态 |
| 请求 | Axios 1.x | 统一封装拦截器 |
| Excel 解析 | xlsx (sheetjs) | 前端解析 .xlsx/.csv |
| 路由 | Vue Router 4.x | 单页面，预留扩展 |

---

## 二、目录结构

```
frontend/
├── public/
├── src/
│   ├── api/positions.ts          # 后端接口封装
│   ├── types/position.ts         # TS 类型定义
│   ├── utils/request.ts          # Axios 实例 + 拦截器
│   ├── stores/positionStore.ts   # Pinia：岗位状态 + 操作方法
│   ├── components/
│   │   ├── PositionForm.vue      # 新增/编辑表单（侧边栏）
│   │   ├── PositionTable.vue     # 岗位列表表格
│   │   ├── BatchUpload.vue       # Excel/CSV 批量上传
│   │   └── DeleteConfirm.vue     # 删除确认弹窗
│   ├── views/HomeView.vue        # 主页面（组装所有组件）
│   ├── App.vue
│   └── main.ts
├── .env.development              # VITE_API_BASE_URL=http://localhost:8080/webapi
├── .env.production
├── vite.config.ts
└── package.json
```

---

## 三、实现步骤（按优先级）

### Step 0：环境准备
```bash
npm create vue@latest frontend
# 勾选：TypeScript + Vite + Pinia + Vue Router
cd frontend
npm install element-plus axios xlsx
npm run dev
```

### Step 1：类型定义（types/position.ts）

与后端 Pydantic 模型对齐：

```typescript
export interface Position {
  id: number
  title: string
  responsibilities: string
  requirements: string
  bonus: string
}

export interface PositionCreate {
  title: string
  responsibilities: string
  requirements: string
  bonus?: string
}

export interface PositionUpdate {
  title?: string
  responsibilities?: string
  requirements?: string
  bonus?: string
}
```

### Step 2：请求封装（utils/request.ts）

```typescript
import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
})

request.interceptors.response.use(
  res => res.data,
  err => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default request
```

### Step 3：API 层（api/positions.ts）

```typescript
import request from '@/utils/request'
import type { PositionCreate, PositionUpdate, Position, BatchResult } from '@/types/position'

export const getPositions = () =>
  request.get('/positions').then(r => r.data.data)

export const createPosition = (data: PositionCreate) =>
  request.post('/positions', data).then(r => r.data.data)

export const updatePosition = (id: number, data: PositionUpdate) =>
  request.put(`/positions/${id}`, data).then(r => r.data.data)

export const deletePosition = (id: number) =>
  request.delete(`/positions/${id}`).then(r => r.data.message)

export const batchUpload = (positions: PositionCreate[]) =>
  request.post('/positions/batch', { positions }).then(r => r.data)
```

### Step 4：Pinia 状态管理（stores/positionStore.ts）

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Position, PositionCreate, PositionUpdate } from '@/types/position'
import * as api from '@/api/positions'

export const usePositionStore = defineStore('position', () => {
  const positions = ref<Position[]>([])
  const loading = ref(false)
  const error = ref('')

  const fetchPositions = async () => {
    loading.value = true
    error.value = ''
    try {
      positions.value = await api.getPositions()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  const addPosition = async (data: PositionCreate) => {
    const newPos = await api.createPosition(data)
    positions.value.unshift(newPos)
  }

  const editPosition = async (id: number, data: PositionUpdate) => {
    const updated = await api.updatePosition(id, data)
    const idx = positions.value.findIndex(p => p.id === id)
    if (idx !== -1) positions.value[idx] = updated
  }

  const removePosition = async (id: number) => {
    await api.deletePosition(id)
    positions.value = positions.value.filter(p => p.id !== id)
  }

  const batchImport = async (list: PositionCreate[]) => {
    const res = await api.batchUpload(list)
    await fetchPositions()
    return res
  }

  return {
    positions, loading, error,
    fetchPositions, addPosition, editPosition, removePosition, batchImport
  }
})
```

**设计要点**：
- 列表数据只维护一处，任何操作后自动同步
- 组件只管调用 Store 方法，不用手动更新表格

### Step 5：主页面布局（HomeView.vue）

左右分栏：
- 左侧（380px）：PositionForm（新增/编辑）
- 右侧：PositionTable + BatchUpload

响应式：768px 以下切换为上下堆叠布局。

### Step 6：表单组件（PositionForm.vue）

- 接收 `editData?: Position` prop，有值则为编辑模式
- `el-form` + `rules` 校验：`title`、`responsibilities`、`requirements` 必填
- 编辑模式顶部显示当前 `id`，提供"取消编辑"按钮
- 保存成功后 `ElMessage.success('保存成功')` + 重置表单

### Step 7：表格组件（PositionTable.vue）

- `el-table`：ID、岗位名称、岗位职责、岗位要求、加分项、操作
- 长文本用 `show-overflow-tooltip`
- 顶部工具栏：多选 + 批量删除
- 操作列：编辑（emit 给父组件传值到表单）、删除（弹窗确认）

编辑通信链：`PositionTable` emit('edit', row) -> `HomeView` -> `PositionForm`

### Step 8：批量上传组件（BatchUpload.vue）

流程：
1. `el-upload` / `<input type="file">` 选择文件
2. `xlsx` 库解析：
   ```typescript
   import * as XLSX from 'xlsx'
   const workbook = XLSX.read(await file.arrayBuffer())
   const json = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]])
   ```
3. 列名校验：必须含 `title`、`responsibilities`、`requirements`；`bonus` 可选
4. 数据清洗：空值处理、缺失必填标红
5. `el-dialog` 预览前 5 条
6. 确认导入 -> 组装 `PositionCreate[]` -> `store.batchImport()`
7. 显示结果："新增 X 条，跳过 Y 条"

### Step 9：删除确认（DeleteConfirm.vue）

单条删除用 `el-dialog` 二次确认。批量删除顶部显示"已选 X 条" + 批量删除按钮。

### Step 10：部署

**开发代理**（vite.config.ts）：
```typescript
server: {
  proxy: {
    '/webapi': { target: 'http://localhost:8080', changeOrigin: true }
  }
}
```

**生产构建**：`npm run build` -> 输出 `frontend/dist/`

**部署方式**：
- A. FastAPI 挂载静态目录：`app.mount("/", StaticFiles(directory="frontend/dist", html=True))`
- B. Nginx 托管前端 + 反向代理 `/webapi`
- C. Vercel/Netlify 托管前端，FastAPI 独立部署

---

## 四、与后端对接要点

| 后端现状 | 前端处理 |
|---------|---------|
| CORS 已开 | 开发时直接调 localhost:8080 |
| 返回 `{ data: ... }` | API 层 `r.data.data` 解包 |
| 异常 `{ detail: "..." }` | Axios 拦截器提取 detail |

---

## 五、样式规范

- 主色：Element Plus 默认蓝 `#409EFF`
- 侧边栏背景：`#f5f7fa`
- 表单标签宽：`100px`
- 表格行高：`48px`
- 响应式断点：`768px`

---

## 六、扩展预留

| 未来功能 | 预留设计 |
|---------|---------|
| 登录 | request.ts 拦截器加 `Authorization: Bearer token` |
| 分页 | getPositions 加 query 参数，表格加 `el-pagination` |
| 搜索 | Store 加 keyword 状态，顶部加搜索栏 |
| 详情页 | Vue Router 加 `/position/:id` 路由 |
| 富文本 | `responsibilities` 等用 wangEditor 替换 textarea |
