<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPosition } from '@/api/positions'
import StatusTag from '@/components/StatusTag.vue'
import type { Position } from '@/types/position'

const route = useRoute()
const router = useRouter()
const position = ref<Position | null>(null)
const loading = ref(false)

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

const formatTime = (val: string) => {
  if (!val) return '-'
  return val.replace('T', ' ').slice(0, 19)
}

onMounted(async () => {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const res = await getPosition(id)
    position.value = res.data
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div style="max-width: 900px; margin: 0 auto; padding: 20px">
    <el-button @click="goBack" style="margin-bottom: 16px">
      ← 返回
    </el-button>

    <el-empty v-if="!loading && !position" description="岗位不存在" />

    <el-card v-else v-loading="loading">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <h2 style="margin: 0">{{ position?.title }}</h2>
          <StatusTag v-if="position" :status="position.status" />
        </div>
      </template>

      <el-descriptions v-if="position" :column="1" border>
        <el-descriptions-item label="岗位名称">
          {{ position.title }}
        </el-descriptions-item>
        <el-descriptions-item label="岗位职责">
          <div style="white-space: pre-wrap; line-height: 1.8">{{ position.responsibilities }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="任职要求">
          <div style="white-space: pre-wrap; line-height: 1.8">{{ position.requirements }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="加分项">
          <div style="white-space: pre-wrap; line-height: 1.8">{{ position.bonus || '无' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatTime(position.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatTime(position.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>
