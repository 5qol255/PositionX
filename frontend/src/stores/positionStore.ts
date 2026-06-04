import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  Position,
  PositionCreate,
  PositionUpdate,
  StatusUpdateRequest,
} from '@/types/position'
import * as api from '@/api/positions'

export const usePositionStore = defineStore('position', () => {
  const positions = ref<Position[]>([])
  const statistics = ref({ total: 0, by_status: {} as Record<string, number> })
  const loading = ref(false)
  const error = ref('')
  const keyword = ref('')
  const statusFilter = ref('')

  const fetchPositions = async () => {
    loading.value = true
    error.value = ''
    try {
      const params: Record<string, string> = {}
      if (keyword.value) params.keyword = keyword.value
      if (statusFilter.value) params.status = statusFilter.value
      const res = await api.getPositions(params)
      positions.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  const fetchStatistics = async () => {
    try {
      const res = await api.getStatistics()
      statistics.value = res.data
    } catch (e: any) {
      console.error('获取统计数据失败:', e.message)
    }
  }

  const addPosition = async (data: PositionCreate) => {
    const res = await api.createPosition(data)
    await fetchPositions()
    await fetchStatistics()
    return res.data
  }

  const editPosition = async (id: number, data: PositionUpdate) => {
    const res = await api.updatePosition(id, data)
    await fetchPositions()
    return res.data
  }

  const removePosition = async (id: number) => {
    await api.deletePosition(id)
    await fetchPositions()
    await fetchStatistics()
  }

  const changeStatus = async (id: number, data: StatusUpdateRequest) => {
    const res = await api.updateStatus(id, data)
    await fetchPositions()
    await fetchStatistics()
    return res.data
  }

  const batchImport = async (list: PositionCreate[]) => {
    const res = await api.batchUpload(list)
    await fetchPositions()
    await fetchStatistics()
    return res.data
  }

  const setSearch = (kw: string, status: string) => {
    keyword.value = kw
    statusFilter.value = status
    fetchPositions()
  }

  return {
    positions,
    statistics,
    loading,
    error,
    keyword,
    statusFilter,
    fetchPositions,
    fetchStatistics,
    addPosition,
    editPosition,
    removePosition,
    changeStatus,
    batchImport,
    setSearch,
  }
})
