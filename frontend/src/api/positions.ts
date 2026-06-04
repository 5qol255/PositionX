import request from '@/utils/request'
import type {
  Position,
  PositionCreate,
  PositionUpdate,
  StatusUpdateRequest,
  ApiResponse,
  BatchResult,
  Statistics,
} from '@/types/position'

/** 获取岗位列表（支持搜索/过滤） */
export const getPositions = (params?: { keyword?: string; status?: string }) =>
  request.get<any, ApiResponse<Position[]>>('/positions', { params })

/** 获取单个岗位 */
export const getPosition = (id: number) =>
  request.get<any, ApiResponse<Position>>(`/positions/${id}`)

/** 创建岗位 */
export const createPosition = (data: PositionCreate) =>
  request.post<any, ApiResponse<Position>>('/positions', data)

/** 更新岗位 */
export const updatePosition = (id: number, data: PositionUpdate) =>
  request.put<any, ApiResponse<Position>>(`/positions/${id}`, data)

/** 删除岗位 */
export const deletePosition = (id: number) =>
  request.delete<any, ApiResponse<null>>(`/positions/${id}`)

/** 变更岗位状态 */
export const updateStatus = (id: number, data: StatusUpdateRequest) =>
  request.patch<any, ApiResponse<Position>>(`/positions/${id}/status`, data)

/** 批量上传 */
export const batchUpload = (positions: PositionCreate[]) =>
  request.post<any, ApiResponse<BatchResult>>('/positions/batch', { positions })

/** 获取统计数据 */
export const getStatistics = () =>
  request.get<any, ApiResponse<Statistics>>('/statistics')
