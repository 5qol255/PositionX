<script setup lang="ts">
import type { PositionStatus } from '@/types/position'

const props = defineProps<{ status: PositionStatus }>()

const statusMap: Record<PositionStatus, { label: string; type: string }> = {
  DRAFT: { label: '草稿', type: 'info' },
  PENDING: { label: '待审批', type: 'warning' },
  PUBLISHED: { label: '已发布', type: 'success' },
  CLOSED: { label: '已关闭', type: 'danger' },
}
</script>

<template>
  <el-tag :type="statusMap[props.status]?.type as any" size="small">
    {{ statusMap[props.status]?.label }}
  </el-tag>
</template>
