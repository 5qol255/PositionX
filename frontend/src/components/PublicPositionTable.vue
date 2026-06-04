<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Position } from '@/types/position'

defineProps<{
  positions: Position[]
  loading: boolean
}>()

const router = useRouter()

const viewDetail = (id: number) => {
  router.push(`/positions/${id}`)
}

const formatTime = (val: string) => {
  if (!val) return ''
  return val.replace('T', ' ').slice(0, 19)
}
</script>

<template>
  <el-table :data="positions" :loading="loading" border stripe>
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="title" label="岗位名称" min-width="150" show-overflow-tooltip />
    <el-table-column prop="responsibilities" label="岗位职责" min-width="200" show-overflow-tooltip />
    <el-table-column prop="requirements" label="任职要求" min-width="200" show-overflow-tooltip />
    <el-table-column prop="bonus" label="加分项" min-width="150" show-overflow-tooltip />
    <el-table-column label="发布时间" width="170">
      <template #default="{ row }">
        {{ formatTime(row.updated_at) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="100" fixed="right">
      <template #default="{ row }">
        <el-button type="primary" link @click="viewDetail(row.id)">
          查看详情
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>
