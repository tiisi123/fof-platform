/**
 * 管理人API V2
 */
import request from './request'
import type {
  Manager,
  ManagerCreate,
  ManagerUpdate,
  ManagerListParams,
  ManagerListResponse,
  ManagerStatistics,
  ManagerContact,
  ManagerTeam,
  PoolTransfer,
  PoolTransferCreate
} from '@/types'

export const managerApi = {
  /**
   * 获取管理人列表
   */
  getList(params?: ManagerListParams): Promise<ManagerListResponse> {
    return request({
      url: '/managers',
      method: 'get',
      params
    })
  },

  /**
   * 获取管理人详情
   */
  getById(id: number): Promise<Manager> {
    return request({
      url: `/managers/${id}`,
      method: 'get'
    })
  },

  /**
   * 创建管理人
   */
  create(data: ManagerCreate): Promise<Manager> {
    return request({
      url: '/managers',
      method: 'post',
      data
    })
  },

  /**
   * 更新管理人
   */
  update(id: number, data: ManagerUpdate): Promise<Manager> {
    return request({
      url: `/managers/${id}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除管理人
   */
  delete(id: number): Promise<{ message: string }> {
    return request({
      url: `/managers/${id}`,
      method: 'delete'
    })
  },

  /**
   * 获取管理人统计信息
   */
  getStatistics(): Promise<ManagerStatistics> {
    return request({
      url: '/managers/statistics/summary',
      method: 'get'
    })
  },

  // ========== 联系人 ==========
  /**
   * 添加联系人
   */
  addContact(managerId: number, data: Omit<ManagerContact, 'id' | 'manager_id' | 'created_at'>): Promise<ManagerContact> {
    return request({
      url: `/managers/${managerId}/contacts`,
      method: 'post',
      data
    })
  },

  /**
   * 更新联系人
   */
  updateContact(contactId: number, data: Omit<ManagerContact, 'id' | 'manager_id' | 'created_at'>): Promise<ManagerContact> {
    return request({
      url: `/managers/contacts/${contactId}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除联系人
   */
  deleteContact(contactId: number): Promise<{ message: string }> {
    return request({
      url: `/managers/contacts/${contactId}`,
      method: 'delete'
    })
  },

  // ========== 核心团队 ==========
  /**
   * 添加团队成员
   */
  addTeamMember(managerId: number, data: Omit<ManagerTeam, 'id' | 'manager_id' | 'created_at'>): Promise<ManagerTeam> {
    return request({
      url: `/managers/${managerId}/team`,
      method: 'post',
      data
    })
  },

  /**
   * 删除团队成员
   */
  deleteTeamMember(memberId: number): Promise<{ message: string }> {
    return request({
      url: `/managers/team/${memberId}`,
      method: 'delete'
    })
  },

  // ========== 跟踪池流转 ==========
  /**
   * 跟踪池流转
   */
  transferPool(managerId: number, data: PoolTransferCreate): Promise<PoolTransfer> {
    return request({
      url: `/managers/${managerId}/transfer`,
      method: 'post',
      data
    })
  },

  /**
   * 获取流转历史
   */
  getPoolTransfers(managerId: number): Promise<PoolTransfer[]> {
    return request({
      url: `/managers/${managerId}/transfers`,
      method: 'get'
    })
  },

  /**
   * 批量流转
   */
  batchTransferPool(managerIds: number[], data: PoolTransferCreate): Promise<{ message: string }> {
    return request({
      url: '/managers/batch-transfer',
      method: 'post',
      data: {
        manager_ids: managerIds,
        ...data
      }
    })
  },

  // ========== 导入导出 ==========
  /**
   * 批量导入
   */
  import(file: File): Promise<{ success_count: number; fail_count: number; errors: any[] }> {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: '/managers/import',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 导出Excel
   */
  export(managerIds?: number[]): Promise<Blob> {
    return request({
      url: '/managers/export/excel',
      method: 'get',
      params: managerIds ? { manager_ids: managerIds.join(',') } : {},
      responseType: 'blob'
    })
  },

  /**
   * 下载导入模板
   */
  downloadTemplate(): Promise<Blob> {
    return request({
      url: '/managers/export/template',
      method: 'get',
      responseType: 'blob'
    })
  },

  // ========== 旗下产品 ==========
  getProducts(managerId: number): Promise<import('@/types').ManagerProductInfo[]> {
    return request({
      url: `/managers/${managerId}/products`,
      method: 'get'
    })
  },

  // ========== 业绩汇总 ==========
  getPerformanceSummary(managerId: number): Promise<import('@/types').ManagerPerformanceSummary> {
    return request({
      url: `/managers/${managerId}/performance-summary`,
      method: 'get'
    })
  },

  // ========== 尽调资料 ==========
  getDocuments(managerId: number, params?: { category?: string; keyword?: string; skip?: number; limit?: number }): Promise<{ total: number; items: import('@/types').ManagerDocument[] }> {
    return request({
      url: `/managers/${managerId}/documents`,
      method: 'get',
      params
    })
  },

  uploadDocument(managerId: number, file: File, options?: { category?: string; title?: string; description?: string }): Promise<{ id: number; filename: string; message: string }> {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: `/managers/${managerId}/documents`,
      method: 'post',
      data: formData,
      params: options,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // ========== 标签 ==========
  getAllTags(tagType?: string): Promise<{ tag_type: string; tag_name: string; tag_color: string; count: number }[]> {
    return request({
      url: '/managers/tags/all',
      method: 'get',
      params: tagType ? { tag_type: tagType } : {}
    })
  },

  getTags(managerId: number): Promise<import('@/types').ManagerTag[]> {
    return request({
      url: `/managers/${managerId}/tags`,
      method: 'get'
    })
  },

  addTag(managerId: number, data: import('@/types').ManagerTagCreate): Promise<import('@/types').ManagerTag> {
    return request({
      url: `/managers/${managerId}/tags`,
      method: 'post',
      data
    })
  },

  deleteTag(tagId: number): Promise<{ message: string }> {
    return request({
      url: `/managers/tags/${tagId}`,
      method: 'delete'
    })
  }
}
