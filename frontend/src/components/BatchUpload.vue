<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import type { PositionCreate } from '@/types/position'
import { usePositionStore } from '@/stores/positionStore'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'done'): void
}>()

const store = usePositionStore()
const fileList = ref<File[]>([])
const previewData = ref<PositionCreate[]>([])
const showPreview = ref(false)
const importing = ref(false)

const handleClose = () => {
  emit('update:visible', false)
  fileList.value = []
  previewData.value = []
  showPreview.value = false
}

const handleFileChange = async (file: File) => {
  try {
    const data = await file.arrayBuffer()
    const workbook = XLSX.read(data)
    const firstSheetName = workbook.SheetNames[0]
    if (!firstSheetName) {
      ElMessage.error('文件中没有工作表')
      return
    }
    const sheet = workbook.Sheets[firstSheetName]!
    const json = XLSX.utils.sheet_to_json<Record<string, string>>(sheet)

    // 验证必须列
    const requiredCols = ['title', 'responsibilities', 'requirements']
    const firstRow = json[0] || {}
    const missing = requiredCols.filter((c) => !(c in firstRow))
    if (missing.length > 0) {
      ElMessage.error(`缺少必需列：${missing.join(', ')}`)
      return
    }

    previewData.value = json.map((row) => ({
      title: row.title || '',
      responsibilities: row.responsibilities || '',
      requirements: row.requirements || '',
      bonus: row.bonus || '',
    }))
    showPreview.value = true
  } catch {
    ElMessage.error('文件解析失败')
  }
}

const handleImport = async () => {
  if (previewData.value.length === 0) return
  importing.value = true
  try {
    const res = await store.batchImport(previewData.value)
    ElMessage.success(`导入完成：新增 ${res.count} 条，跳过 ${res.skipped} 条`)
    emit('update:visible', false)
    emit('done')
  } catch {
    // 错误已在拦截器处理
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <el-dialog :model-value="visible" title="Excel 批量上传" width="700px" @close="handleClose">
    <el-upload
      :auto-upload="false"
      :limit="1"
      accept=".xlsx,.xls"
      :on-change="(f: any) => handleFileChange(f.raw)"
      drag
    >
      <el-icon style="font-size: 40px; color: #c0c4cc">
        <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" fill="currentColor" width="1em" height="1em">
          <path d="M544 864V672h128L512 480 352 672h128v192H320v-1.6c-5.376.32-10.496 1.6-16 1.6A240 240 0 0 1 64 624c0-123.136 93.12-223.488 212.608-237.248A239.808 239.808 0 0 1 512 192a239.872 239.872 0 0 1 235.456 194.752c119.488 13.76 212.48 114.112 212.48 237.248a240 240 0 0 1-240 240c-5.376 0-10.56-1.28-16-1.6v1.6H544z"/>
        </svg>
      </el-icon>
      <div>将 Excel 文件拖到此处，或<em>点击上传</em></div>
      <template #tip>
        <div style="color: #909399; font-size: 12px">
          文件需包含 title、responsibilities、requirements 列，bonus 列可选
        </div>
      </template>
    </el-upload>

    <div v-if="showPreview" style="margin-top: 16px">
      <h4>预览（前 5 条，共 {{ previewData.length }} 条）</h4>
      <el-table :data="previewData.slice(0, 5)" border size="small">
        <el-table-column prop="title" label="岗位名称" />
        <el-table-column prop="responsibilities" label="岗位职责" show-overflow-tooltip />
        <el-table-column prop="requirements" label="任职要求" show-overflow-tooltip />
        <el-table-column prop="bonus" label="加分项" show-overflow-tooltip />
      </el-table>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button
        type="primary"
        :disabled="!showPreview || previewData.length === 0"
        :loading="importing"
        @click="handleImport"
      >
        确认导入 {{ previewData.length }} 条
      </el-button>
    </template>
  </el-dialog>
</template>
