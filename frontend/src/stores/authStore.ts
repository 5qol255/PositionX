import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest } from '@/types/auth'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isApprover = computed(
    () => user.value?.role === 'approver' || user.value?.role === 'admin',
  )
  const canEdit = computed(() => user.value?.role === 'admin')
  const canApprove = computed(
    () => user.value?.role === 'admin' || user.value?.role === 'approver',
  )

  /** 初始化：从 localStorage 恢复登录态 */
  const init = () => {
    const saved = localStorage.getItem('user')
    if (saved) {
      user.value = JSON.parse(saved)
    }
  }

  /** 登录 */
  const login = async (data: LoginRequest) => {
    const res = await authApi.login(data)
    token.value = res.data.token
    user.value = res.data.user
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
  }

  /** 登出 */
  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    user,
    token,
    isLoggedIn,
    isAdmin,
    isApprover,
    canEdit,
    canApprove,
    init,
    login,
    logout,
  }
})
