<script setup lang="ts">
import type { Position } from '@/types/position'

defineProps<{
  positions: Position[]
  loading: boolean
}>()

const formatTime = (val: string) => {
  if (!val) return ''
  return val.replace('T', ' ').slice(0, 19)
}
</script>

<template>
  <el-table :data="positions" :loading="loading" border stripe>
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="title" label="岗位名称" width="180" show-overflow-tooltip />
    <el-table-column prop="responsibilities" label="岗位职责" show-overflow-tooltip />
    <el-table-column prop="requirements" label="任职要求" show-overflow-tooltip />
    <el-table-column prop="bonus" label="加分项" show-overflow-tooltip />
    <el-table-column label="发布时间" width="170">
      <template #default="{ row }">
        {{ formatTime(row.updated_at) }}
      </template>
    </el-table-column>
  </el-table>
</template>
