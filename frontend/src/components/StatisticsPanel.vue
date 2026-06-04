<script setup lang="ts">
import { usePositionStore } from '@/stores/positionStore'

const store = usePositionStore()
</script>

<template>
  <el-row :gutter="20" style="margin-bottom: 20px">
    <el-col :span="6">
      <el-card shadow="hover" body-style="padding: 16px; text-align: center">
        <div style="font-size: 14px; color: #909399">全部岗位</div>
        <div style="font-size: 28px; font-weight: bold; color: #303133">
          {{ store.statistics.total }}
        </div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card shadow="hover" body-style="padding: 16px; text-align: center">
        <div style="font-size: 14px; color: #909399">草稿</div>
        <div style="font-size: 28px; font-weight: bold; color: #909399">
          {{ store.statistics.by_status['DRAFT'] || 0 }}
        </div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card shadow="hover" body-style="padding: 16px; text-align: center">
        <div style="font-size: 14px; color: #e6a23c">待审批</div>
        <div style="font-size: 28px; font-weight: bold; color: #e6a23c">
          {{ store.statistics.by_status['PENDING'] || 0 }}
        </div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card shadow="hover" body-style="padding: 16px; text-align: center">
        <div style="font-size: 14px; color: #67c23a">已发布</div>
        <div style="font-size: 28px; font-weight: bold; color: #67c23a">
          {{ store.statistics.by_status['PUBLISHED'] || 0 }}
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>
