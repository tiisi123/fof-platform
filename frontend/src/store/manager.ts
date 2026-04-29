import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Manager, ManagerCreate, ManagerUpdate, ManagerListParams } from '@/types'
import { managerApi } from '@/api/manager'
import { ElMessage } from 'element-plus'

/**
 * 管理人Store
 * 管理管理人数据和操作
 */
export const useManagerStore = defineStore('manager', () => {
  // 状态
  const managers = ref<Manager[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentManager = ref<Manager | null>(null)

  /**
   * 获取管理人列表
   */
  const fetchManagers = async (params?: ManagerListParams) => {
    loading.value = true
    try {
      const response = await managerApi.getList(params)
      managers.value = response.items
      total.value = response.total
      return response
    } catch (error) {
      console.error('获取管理人列表失败:', error)
      ElMessage.error('获取管理人列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取管理人详情
   */
  const fetchManagerById = async (id: number) => {
    loading.value = true
    try {
      const manager = await managerApi.getById(id)
      currentManager.value = manager
      return manager
    } catch (error) {
      console.error('获取管理人详情失败:', error)
      ElMessage.error('获取管理人详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建管理人
   */
  const createManager = async (data: ManagerCreate) => {
    loading.value = true
    try {
      const manager = await managerApi.create(data)
      ElMessage.success('创建管理人成功')
      return manager
    } catch (error) {
      console.error('创建管理人失败:', error)
      ElMessage.error('创建管理人失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新管理人
   */
  const updateManager = async (id: number, data: ManagerUpdate) => {
    loading.value = true
    try {
      const manager = await managerApi.update(id, data)
      ElMessage.success('更新管理人成功')
      return manager
    } catch (error) {
      console.error('更新管理人失败:', error)
      ElMessage.error('更新管理人失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除管理人
   */
  const deleteManager = async (id: number) => {
    loading.value = true
    try {
      await managerApi.delete(id)
      ElMessage.success('删除管理人成功')
    } catch (error) {
      console.error('删除管理人失败:', error)
      ElMessage.error('删除管理人失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置状态
   */
  const reset = () => {
    managers.value = []
    total.value = 0
    loading.value = false
    currentManager.value = null
  }

  return {
    // 状态
    managers,
    total,
    loading,
    currentManager,

    // 方法
    fetchManagers,
    fetchManagerById,
    createManager,
    updateManager,
    deleteManager,
    reset
  }
})
