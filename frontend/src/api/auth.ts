/**
 * 认证相关API
 */

import request from './request'
import type { LoginRequest, LoginResponse, UserInfo } from '@/types'

export const authApi = {
  /**
   * 用户登录
   * @param data 登录信息（用户名和密码）
   * @returns 登录响应（包含access_token）
   */
  login: (data: LoginRequest): Promise<LoginResponse> => {
    // 注意：后端登录接口需要form-data格式
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)
    
    return request.post<LoginResponse, LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },

  /**
   * 获取当前用户信息
   * @returns 用户信息
   */
  getCurrentUser: (): Promise<UserInfo> => {
    return request.get<UserInfo, UserInfo>('/auth/me')
  }
}
