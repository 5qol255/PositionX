<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/authStore'
import { usePositionStore } from '@/stores/positionStore'
import type { Position } from '@/types/position'
import StatisticsPanel from '@/components/StatisticsPanel.vue'
import PositionTable from '@/components/PositionTable.vue'
import PositionForm from '@/components/PositionForm.vue'
import ApprovalDialog from '@/components/ApprovalDialog.vue'
import BatchUpload from '@/components/BatchUpload.vue'
import DeleteConfirm from '@/components/DeleteConfirm.vue'

const router = useRouter()
const authStore = useAuthStore()
const store = usePositionStore()

// 搜索
const searchKeyword = ref('')
const searchStatus = ref('')

// 弹窗状态
const formVisible = ref(false)
const approvalVisible = ref(false)
const batchVisible = ref(false)
const deleteVisible = ref(false)
const editData = ref<Position | null>(null)
const approvalTarget = ref<Position | null>(null)
const deleteTarget = ref<Position | null>(null)
const batchDeleteIds = ref<number[]>([])

// 角色
const userRole = ref<'admin' | 'hr' | 'viewer'>(
  (authStore.user?.role as any) || 'viewer',
)

onMounted(async () => {
  await Promise.all([store.fetchPositions(), store.fetchStatistics()])
})

const handleSearch = () => {
  store.setSearch(searchKeyword.value, searchStatus.value)
}

const handleAdd = () => {
  editData.value = null
  formVisible.value = true
}

const handleEdit = (row: Position) => {
  editData.value = row
  formVisible.value = true
}

const handleSubmit = async (row: Position) => {
  try {
    await store.changeStatus(row.id, { action: 'submit' })
    ElMessage.success('已提交审批')
  } catch {
    // 错误已在拦截器处理
  }
}

const handleApprove = (row: Position) => {
  approvalTarget.value = row
  approvalVisible.value = true
}

const handleClose = async (row: Position) => {
  try {
    await store.changeStatus(row.id, { action: 'close' })
    ElMessage.success('已关闭')
  } catch {
    // 错误已在拦截器处理
  }
}

const handleDelete = (row: Position) => {
  deleteTarget.value = row
  batchDeleteIds.value = []
  deleteVisible.value = true
}

const handleBatchDelete = (ids: number[]) => {
  batchDeleteIds.value = ids
  deleteTarget.value = null
  deleteVisible.value = true
}

const handleLogout = () => {
  authStore.logout()
  router.push('/admin/login')
}
</script>

<template>
  <div style="max-width: 1400px; margin: 0 auto; padding: 20px">
    <!-- 顶部栏 -->
    <el-card style="margin-bottom: 20px" body-style="padding: 12px 20px">
      <div style="display: flex; align-items: center; justify-content: space-between">
        <h2 style="margin: 0">📋 PositionX 管理后台</h2>
        <div style="display: flex; align-items: center; gap: 16px">
          <span style="color: #606266">
            欢迎，<strong>{{ authStore.user?.username }}</strong>
            <el-tag size="small" style="margin-left: 8px">{{ authStore.user?.role }}</el-tag>
          </span>
          <el-button type="danger" size="small" plain @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计面板 -->
    <StatisticsPanel />

    <!-- 工具栏 -->
    <el-card style="margin-bottom: 20px">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索岗位名称"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
        />
        <el-select v-model="searchStatus" placeholder="状态筛选" clearable style="width: 140px">
          <el-option label="全部" value="" />
          <el-option label="草稿" value="DRAFT" />
          <el-option label="待审批" value="PENDING" />
          <el-option label="已发布" value="PUBLISHED" />
          <el-option label="已关闭" value="CLOSED" />
        </el-select>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <div style="flex: 1" />
        <el-button v-if="authStore.canEdit" type="success" @click="handleAdd">
          + 新增岗位
        </el-button>
        <el-button v-if="authStore.canEdit" @click="batchVisible = true">
          📤 批量上传
        </el-button>
        <el-tag v-if="authStore.isAdmin" type="danger" size="small" style="margin-left: 8px">
          有审批权限
        </el-tag>
      </div>
    </el-card>

    <!-- 岗位表格 -->
    <el-card>
      <PositionTable
        :positions="store.positions"
        :loading="store.loading"
        :user-role="userRole"
        @edit="handleEdit"
        @delete="handleDelete"
        @submit="handleSubmit"
        @approve="handleApprove"
        @close="handleClose"
        @batch-delete="handleBatchDelete"
      />
      <el-empty
        v-if="!store.loading && store.positions.length === 0"
        description="暂无岗位数据"
      />
    </el-card>

    <!-- 弹窗 -->
    <PositionForm
      v-model:visible="formVisible"
      :edit-data="editData"
      @saved="handleSearch"
    />
    <ApprovalDialog
      v-model:visible="approvalVisible"
      :position="approvalTarget"
      @done="handleSearch"
    />
    <BatchUpload v-model:visible="batchVisible" @done="handleSearch" />
    <DeleteConfirm
      v-model:visible="deleteVisible"
      :position-id="deleteTarget?.id ?? null"
      :position-title="deleteTarget?.title ?? ''"
      :batch-ids="batchDeleteIds"
      @done="handleSearch"
    />
  </div>
</template>
