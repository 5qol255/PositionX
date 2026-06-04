/** 用户角色类型 */
export type UserRole = 'admin' | 'hr' | 'viewer'

/** 统一 API 响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 用户信息 */
export interface User {
  id: number
  username: string
  role: UserRole
}

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
}

/** 登录响应 */
export interface LoginResponse {
  token: string
  user: User
}
