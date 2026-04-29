/**
 * 用户相关类型定义
 */

import type { PaginationParams, PaginationResponse, SearchParams } from './api'

// 用户角色
export type UserRole = 'readonly' | 'manager' | 'director' | 'super_admin'

// 用户状态
export type UserStatus = 'active' | 'inactive'

// 用户基础信息
export interface User {
  id: number
  username: string
  email?: string
  real_name?: string
  role: UserRole
  status: UserStatus
  created_at: string
  updated_at: string
}

// 创建用户请求
export interface UserCreate {
  username: string
  email?: string
  real_name?: string
  password: string
  role: UserRole
  status?: UserStatus
}

// 更新用户请求
export interface UserUpdate {
  email?: string
  real_name?: string
  role?: UserRole
  status?: UserStatus
}

// 修改密码请求
export interface PasswordChange {
  old_password: string
  new_password: string
}

// 用户列表查询参数
export interface UserListParams extends PaginationParams, SearchParams {
  role?: string
  status?: string
}

// 用户列表响应
export interface UserListResponse extends PaginationResponse<User> {}

// 角色选项
export const ROLE_OPTIONS = [
  { label: '只读', value: 'readonly' },
  { label: '经理', value: 'manager' },
  { label: '总监', value: 'director' },
  { label: '超级管理员', value: 'super_admin' }
] as const

// 角色权限说明
export const ROLE_DESCRIPTIONS: Record<UserRole, string> = {
  readonly: '只能查看数据，不能修改',
  manager: '可以管理管理人和产品',
  director: '可以管理所有数据',
  super_admin: '拥有所有权限，包括用户管理'
}

// 用户状态选项
export const USER_STATUS_OPTIONS = [
  { label: '活跃', value: 'active' },
  { label: '停用', value: 'inactive' }
] as const
