/**
 * API通用类型定义
 */

// 通用API响应结构
export interface ApiResponse<T = any> {
  data?: T
  message?: string
  code?: number
}

// 分页参数
export interface PaginationParams {
  skip?: number
  limit?: number
}

// 分页响应
export interface PaginationResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// 日期范围参数
export interface DateRangeParams {
  start_date?: string
  end_date?: string
}

// 搜索参数
export interface SearchParams {
  search?: string
}

// 错误响应
export interface ErrorResponse {
  detail: string
  message?: string
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  token_type: string
}

// 用户信息
export interface UserInfo {
  id: number
  username: string
  email?: string
  real_name?: string
  role: string
}
