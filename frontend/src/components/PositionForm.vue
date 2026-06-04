<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { Position, PositionCreate } from '@/types/position'
import { usePositionStore } from '@/stores/positionStore'

const props = defineProps<{
  visible: boolean
  editData?: Position | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
}>()

const store = usePositionStore()
const formRef = ref<FormInstance>()
const form = ref<PositionCreate>({
  title: '',
  responsibilities: '',
  requirements: '',
  bonus: '',
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入岗位名称', trigger: 'blur' }],
  responsibilities: [{ required: true, message: '请输入岗位职责', trigger: 'blur' }],
  requirements: [{ required: true, message: '请输入任职要求', trigger: 'blur' }],
}

watch(
  () => props.visible,
  (val) => {
    if (val && props.editData) {
      form.value = {
        title: props.editData.title,
        responsibilities: props.editData.responsibilities,
        requirements: props.editData.requirements,
        bonus: props.editData.bonus || '',
      }
    } else if (val) {
      form.value = { title: '', responsibilities: '', requirements: '', bonus: '' }
    }
  },
)

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (props.editData) {
      await store.editPosition(props.editData.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await store.addPosition(form.value)
      ElMessage.success('创建成功')
    }
    emit('update:visible', false)
    emit('saved')
  } catch {
    // 错误已在 request 拦截器中处理
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    :title="editData ? '编辑岗位' : '新增岗位'"
    width="600px"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="岗位名称" prop="title">
        <el-input v-model="form.title" placeholder="请输入岗位名称" />
      </el-form-item>
      <el-form-item label="岗位职责" prop="responsibilities">
        <el-input
          v-model="form.responsibilities"
          type="textarea"
          :rows="4"
          placeholder="请输入岗位职责"
        />
      </el-form-item>
      <el-form-item label="任职要求" prop="requirements">
        <el-input
          v-model="form.requirements"
          type="textarea"
          :rows="4"
          placeholder="请输入任职要求"
        />
      </el-form-item>
      <el-form-item label="加分项">
        <el-input
          v-model="form.bonus"
          type="textarea"
          :rows="3"
          placeholder="请输入加分项（可选）"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit">
        {{ editData ? '保存修改' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>
