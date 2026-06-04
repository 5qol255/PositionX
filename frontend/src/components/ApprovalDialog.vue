<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { Position } from '@/types/position'
import { usePositionStore } from '@/stores/positionStore'

const props = defineProps<{
  visible: boolean
  position: Position | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'done'): void
}>()

const store = usePositionStore()
const comment = ref('')
const submitting = ref(false)

const handleClose = () => {
  emit('update:visible', false)
  comment.value = ''
}

const handleAction = async (action: 'approve' | 'reject') => {
  if (!props.position) return
  submitting.value = true
  try {
    await store.changeStatus(props.position.id, { action, comment: comment.value })
    ElMessage.success(action === 'approve' ? '审批通过' : '已驳回')
    emit('update:visible', false)
    emit('done')
  } catch {
    // 错误已在拦截器处理
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="岗位审批"
    width="500px"
    @close="handleClose"
  >
    <div v-if="position" style="margin-bottom: 16px">
      <p><strong>岗位名称：</strong>{{ position.title }}</p>
      <p><strong>岗位职责：</strong>{{ position.responsibilities }}</p>
      <p><strong>任职要求：</strong>{{ position.requirements }}</p>
      <p v-if="position.bonus"><strong>加分项：</strong>{{ position.bonus }}</p>
    </div>
    <el-input
      v-model="comment"
      type="textarea"
      :rows="3"
      placeholder="审批意见（可选）"
    />
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="danger" :loading="submitting" @click="handleAction('reject')">
        驳回
      </el-button>
      <el-button type="success" :loading="submitting" @click="handleAction('approve')">
        通过
      </el-button>
    </template>
  </el-dialog>
</template>
