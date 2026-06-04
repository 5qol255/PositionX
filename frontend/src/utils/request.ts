import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/webapi',
  timeout: 10000,
})

// 请求拦截器：自动附加 Token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const status = err.response?.status
    const msg = err.response?.data?.detail || err.message || '请求失败'

    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (router.currentRoute.value.path.startsWith('/admin')) {
        router.push('/admin/login')
      }
      ElMessage.error('登录已过期，请重新登录')
    } else if (status === 403) {
      ElMessage.warning('权限不足')
    } else if (status === 404) {
      ElMessage.error('请求的资源不存在')
    } else if (status === 400) {
      ElMessage.warning(msg)
    } else if (status === 500) {
      ElMessage.error('服务器内部错误')
    } else {
      ElMessage.error(msg)
    }

    return Promise.reject(new Error(msg))
  },
)

export default request
