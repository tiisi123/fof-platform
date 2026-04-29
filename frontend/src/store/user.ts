import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, LoginRequest } from '@/types'
import { authApi } from '@/api/auth'

/**
 * 用户Store
 * 管理用户认证状态和用户信息
 */
export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<UserInfo | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => userInfo.value?.role || '')
  const username = computed(() => userInfo.value?.username || '')

  /**
   * 登录
   * @param username 用户名
   * @param password 密码
   */
  const login = async (username: string, password: string) => {
    try {
      const loginData: LoginRequest = { username, password }
      const response = await authApi.login(loginData)
      
      // 保存token
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      
      // 获取用户信息
      await fetchUserInfo()
      
      return true
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  /**
   * 退出登录
   */
  const logout = () => {
    // 清除token和用户信息
    token.value = null
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('currentUser')
  }

  /**
   * 获取当前用户信息
   */
  const fetchUserInfo = async () => {
    try {
      const info = await authApi.getCurrentUser()
      userInfo.value = info
      // Review SDK 权限表当前使用 admin 角色标识，super_admin 映射为 admin
      const sdkRole = info.role === 'super_admin' ? 'admin' : info.role
      // 同步用户信息到 localStorage 供 review-sdk 使用
      localStorage.setItem('currentUser', JSON.stringify({
        id: info.username,
        name: info.username,
        role: sdkRole
      }))
      return info
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，清除token
      logout()
      throw error
    }
  }

  /**
   * 检查用户是否有指定角色
   * @param role 角色名称
   */
  const hasRole = (role: string): boolean => {
    return userInfo.value?.role === role
  }

  /**
   * 检查用户是否有指定角色之一
   * @param roles 角色列表
   */
  const hasAnyRole = (roles: string[]): boolean => {
    return roles.includes(userInfo.value?.role || '')
  }

  /**
   * 检查是否为超级管理员
   */
  const isSuperAdmin = computed(() => hasRole('super_admin'))

  /**
   * 初始化用户信息
   * 如果有token，尝试获取用户信息
   */
  const init = async () => {
    if (token.value) {
      try {
        await fetchUserInfo()
      } catch (error) {
        // 如果token无效，清除
        logout()
      }
    }
  }

  return {
    // 状态
    token,
    userInfo,
    
    // 计算属性
    isLoggedIn,
    userRole,
    username,
    isSuperAdmin,
    
    // 方法
    login,
    logout,
    fetchUserInfo,
    hasRole,
    hasAnyRole,
    init
  }
})
