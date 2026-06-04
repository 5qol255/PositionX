<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Position } from '@/types/position'
import type { UserRole } from '@/types/auth'
import StatusTag from './StatusTag.vue'

const props = defineProps<{
  positions: Position[]
  loading: boolean
  userRole: UserRole
}>()

const emit = defineEmits<{
  (e: 'edit', row: Position): void
  (e: 'delete', row: Position): void
  (e: 'submit', row: Position): void
  (e: 'approve', row: Position): void
  (e: 'close', row: Position): void
  (e: 'batch-delete', ids: number[]): void
}>()

const selectedIds = ref<number[]>([])

const handleSelectionChange = (rows: Position[]) => {
  selectedIds.value = rows.map((r) => r.id)
}

const canDeleteSelected = computed(() => {
  if (selectedIds.value.length === 0) return false
  const selected = props.positions.filter((p) => selectedIds.value.includes(p.id))
  return selected.every((p) => p.status === 'DRAFT' || p.status === 'CLOSED')
})

const handleBatchDelete = () => {
  emit('batch-delete', selectedIds.value)
}

const formatTime = (val: string) => {
  if (!val) return ''
  return val.replace('T', ' ').slice(0, 19)
}
</script>

<template>
  <div>
    <div v-if="userRole === 'admin'" style="margin-bottom: 12px">
      <el-button
        type="danger"
        size="small"
        :disabled="!canDeleteSelected"
        @click="handleBatchDelete"
      >
        批量删除 ({{ selectedIds.length }})
      </el-button>
    </div>

    <el-table
      :data="positions"
      :loading="loading"
      border
      stripe
      @selection-change="handleSelectionChange"
    >
      <el-table-column v-if="userRole === 'admin'" type="selection" width="45" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="岗位名称" width="180" show-overflow-tooltip />
      <el-table-column prop="responsibilities" label="岗位职责" show-overflow-tooltip />
      <el-table-column prop="requirements" label="任职要求" show-overflow-tooltip />
      <el-table-column prop="bonus" label="加分项" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <!-- admin 操作 -->
          <template v-if="userRole === 'admin'">
            <el-button
              v-if="row.status === 'DRAFT'"
              type="primary"
              size="small"
              link
              @click="emit('edit', row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'DRAFT'"
              type="warning"
              size="small"
              link
              @click="emit('submit', row)"
            >
              提交审批
            </el-button>
            <el-button
              v-if="row.status === 'PENDING'"
              type="success"
              size="small"
              link
              @click="emit('approve', row)"
            >
              审批
            </el-button>
            <el-button
              v-if="row.status === 'DRAFT' || row.status === 'CLOSED'"
              type="danger"
              size="small"
              link
              @click="emit('delete', row)"
            >
              删除
            </el-button>
            <el-button
              v-if="row.status === 'PUBLISHED'"
              type="info"
              size="small"
              link
              @click="emit('close', row)"
            >
              关闭
            </el-button>
          </template>

          <!-- approver 操作 -->
          <template v-if="userRole === 'approver'">
            <el-button
              v-if="row.status === 'PENDING'"
              type="success"
              size="small"
              link
              @click="emit('approve', row)"
            >
              审批
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
