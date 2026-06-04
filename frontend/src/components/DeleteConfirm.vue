<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { usePositionStore } from '@/stores/positionStore'

const props = defineProps<{
  visible: boolean
  positionId: number | null
  positionTitle: string
  batchIds: number[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'done'): void
}>()

const store = usePositionStore()

const handleClose = () => {
  emit('update:visible', false)
}

const handleConfirm = async () => {
  try {
    if (props.batchIds.length > 0) {
      for (const id of props.batchIds) {
        await store.removePosition(id)
      }
      ElMessage.success(`成功删除 ${props.batchIds.length} 个岗位`)
    } else if (props.positionId) {
      await store.removePosition(props.positionId)
      ElMessage.success('删除成功')
    }
    emit('update:visible', false)
    emit('done')
  } catch {
    // 错误已在拦截器处理
  }
}
</script>

<template>
  <el-dialog :model-value="visible" title="确认删除" width="400px" @close="handleClose">
    <p v-if="batchIds.length > 0">确定删除选中的 {{ batchIds.length }} 个岗位？此操作不可恢复。</p>
    <p v-else>确定删除岗位「{{ positionTitle }}」？此操作不可恢复。</p>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="danger" @click="handleConfirm">确认删除</el-button>
    </template>
  </el-dialog>
</template>
