/** 用户角色 */
export type UserRole = 'admin' | 'hr' | 'viewer'

/** 用户信息 */
export interface User {
  id: number
  username: string
  role: UserRole
}

/** 登录请求体 */
export interface LoginRequest {
  username: string
  password: string
}

/** 登录响应 */
export interface LoginResponse {
  token: string
  user: User
}
