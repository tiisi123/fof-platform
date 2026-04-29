/**
 * 用户API
 */
import request from './request'
import type {
  User,
  UserCreate,
  UserUpdate,
  UserListParams,
  UserListResponse
} from '@/types'

export const userApi = {
  /**
   * 获取用户列表
   */
  getList(params?: UserListParams): Promise<UserListResponse> {
    return request({
      url: '/users',
      method: 'get',
      params
    })
  },

  /**
   * 获取用户详情
   */
  getById(id: number): Promise<User> {
    return request({
      url: `/users/${id}`,
      method: 'get'
    })
  },

  /**
   * 创建用户
   */
  create(data: UserCreate): Promise<User> {
    return request({
      url: '/users',
      method: 'post',
      data
    })
  },

  /**
   * 更新用户
   */
  update(id: number, data: UserUpdate): Promise<User> {
    return request({
      url: `/users/${id}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除用户
   */
  delete(id: number): Promise<{ message: string }> {
    return request({
      url: `/users/${id}`,
      method: 'delete'
    })
  },

  /**
   * 修改密码
   */
  changePassword(data: { current_password: string; new_password: string }): Promise<{ message: string }> {
    return request({
      url: '/users/me/change-password',
      method: 'post',
      data
    })
  },

  /**
   * 更新当前用户信息
   */
  updateProfile(data: { real_name?: string; email?: string }): Promise<User> {
    return request({
      url: '/users/me',
      method: 'put',
      data
    })
  },

  /**
   * 获取当前用户信息
   */
  getMe(): Promise<User> {
    return request({
      url: '/users/me',
      method: 'get'
    })
  }
}
