import request from '@/utils/request'
import type { ApiResponse, LoginRequest, LoginResponse, User } from '@/types/auth'

/** 用户登录 */
export const login = (data: LoginRequest) =>
  request.post<any, ApiResponse<LoginResponse>>('/auth/login', data)

/** 获取当前用户信息 */
export const getCurrentUser = () =>
  request.get<any, ApiResponse<User>>('/auth/me')
