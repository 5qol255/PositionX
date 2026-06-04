<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Position } from '@/types/position'
import { getPositions } from '@/api/positions'
import PublicPositionTable from '@/components/PublicPositionTable.vue'

const positions = ref<Position[]>([])
const loading = ref(false)
const keyword = ref('')

const fetchPublished = async () => {
  loading.value = true
  try {
    const params: Record<string, string> = { status: 'PUBLISHED' }
    if (keyword.value) params.keyword = keyword.value
    const res = await getPositions(params)
    positions.value = res.data
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchPublished()
}

onMounted(fetchPublished)
</script>

<template>
  <div style="max-width: 1200px; margin: 0 auto; padding: 20px">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <h2 style="margin: 0">📋 PositionX — 热招岗位</h2>
          <div style="display: flex; gap: 8px">
            <el-input
              v-model="keyword"
              placeholder="搜索岗位名称"
              clearable
              style="width: 240px"
              @keyup.enter="handleSearch"
            />
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </div>
        </div>
      </template>
      <PublicPositionTable :positions="positions" :loading="loading" />
      <el-empty v-if="!loading && positions.length === 0" description="暂无已发布的岗位" />
    </el-card>
  </div>
</template>
