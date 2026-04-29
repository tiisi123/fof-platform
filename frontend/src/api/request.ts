import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

// 创建Axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000, // 增加到60秒，适应大文件上传和数据处理
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    
    // 如果token存在，添加到请求头
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error: AxiosError) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 直接返回响应数据
    return response.data
  },
  (error: AxiosError) => {
    // 处理错误响应
    if (error.response) {
      const status = error.response.status
      const data = error.response.data as any
      
      switch (status) {
        case 401:
          // 未授权 - Token过期或无效
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          window.location.href = '/login'
          break

        case 403:
          ElMessage.error(data?.detail || '权限不足，无法执行此操作')
          break

        case 404:
          ElMessage.error('请求的资源不存在')
          break

        case 429:
          // 请求频率限制（登录锁定等）
          ElMessage.warning(data?.detail || '操作过于频繁，请稍后重试')
          break

        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
          
        default: {
          const message = data?.detail || data?.message || '请求失败'
          ElMessage.error(message)
        }
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('网络连接失败，请检查网络设置')
    } else {
      // 请求配置出错
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

// 导出request实例
export default request

// 导出类型定义，方便其他模块使用
export type { AxiosRequestConfig, AxiosResponse }
