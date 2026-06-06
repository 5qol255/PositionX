/** 岗位状态枚举 */
export type PositionStatus = 'DRAFT' | 'PENDING' | 'PUBLISHED' | 'CLOSED'

/** 岗位信息 */
export interface Position {
  id: number
  title: string
  responsibilities: string
  requirements: string
  bonus: string
  status: PositionStatus
  created_at: string
  updated_at: string
}

/** 创建岗位请求体 */
export interface PositionCreate {
  title: string
  responsibilities: string
  requirements: string
  bonus?: string
}

/** 更新岗位请求体 */
export interface PositionUpdate {
  title?: string
  responsibilities?: string
  requirements?: string
  bonus?: string
}

/** 状态变更请求体 */
export interface StatusUpdateRequest {
  action: 'submit' | 'approve' | 'reject' | 'close'
}

/** 统一 API 响应 */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

/** 批量上传结果 */
export interface BatchResult {
  count: number
  skipped: number
}

/** 统计数据 */
export interface Statistics {
  total: number
  by_status: Record<PositionStatus, number>
}
