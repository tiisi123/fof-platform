import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User, UserCreate, UserUpdate, UserListParams } from '@/types'
import { userApi } from '@/api/user'
import { ElMessage } from 'element-plus'

/**
 * 用户管理Store
 * 管理用户数据和操作（区别于认证用的userStore）
 */
export const useUserManagementStore = defineStore('userManagement', () => {
  // 状态
  const users = ref<User[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentUser = ref<User | null>(null)

  /**
   * 获取用户列表
   */
  const fetchUsers = async (params?: UserListParams) => {
    loading.value = true
    try {
      const response = await userApi.getList(params)
      users.value = response.items
      total.value = response.total
      return response
    } catch (error) {
      console.error('获取用户列表失败:', error)
      ElMessage.error('获取用户列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取用户详情
   */
  const fetchUserById = async (id: number) => {
    loading.value = true
    try {
      const user = await userApi.getById(id)
      currentUser.value = user
      return user
    } catch (error) {
      console.error('获取用户详情失败:', error)
      ElMessage.error('获取用户详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建用户
   */
  const createUser = async (data: UserCreate) => {
    loading.value = true
    try {
      const user = await userApi.create(data)
      ElMessage.success('创建用户成功')
      return user
    } catch (error) {
      console.error('创建用户失败:', error)
      ElMessage.error('创建用户失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新用户
   */
  const updateUser = async (id: number, data: UserUpdate) => {
    loading.value = true
    try {
      const user = await userApi.update(id, data)
      ElMessage.success('更新用户成功')
      return user
    } catch (error) {
      console.error('更新用户失败:', error)
      ElMessage.error('更新用户失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除用户
   */
  const deleteUser = async (id: number) => {
    loading.value = true
    try {
      await userApi.delete(id)
      ElMessage.success('删除用户成功')
    } catch (error) {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 修改密码
   */
  const changePassword = async (id: number, oldPassword: string, newPassword: string) => {
    loading.value = true
    try {
      void id
      await userApi.changePassword({
        current_password: oldPassword,
        new_password: newPassword
      })
      ElMessage.success('修改密码成功')
    } catch (error) {
      console.error('修改密码失败:', error)
      ElMessage.error('修改密码失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置状态
   */
  const reset = () => {
    users.value = []
    total.value = 0
    loading.value = false
    currentUser.value = null
  }

  return {
    // 状态
    users,
    total,
    loading,
    currentUser,

    // 方法
    fetchUsers,
    fetchUserById,
    createUser,
    updateUser,
    deleteUser,
    changePassword,
    reset
  }
})
