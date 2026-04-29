/**
 * 一级项目API
 */
import request from './request'
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectListParams,
  ProjectListResponse,
  ProjectStats,
  ProjectFollowUp,
  ProjectFollowUpCreate,
  ProjectStageChange,
  StageTransfer
} from '@/types'

export const projectApi = {
  /**
   * 获取项目列表
   */
  getList(params?: ProjectListParams): Promise<ProjectListResponse> {
    return request({
      url: '/projects',
      method: 'get',
      params
    })
  },

  /**
   * 获取项目详情
   */
  getById(id: number): Promise<Project> {
    return request({
      url: `/projects/${id}`,
      method: 'get'
    })
  },

  /**
   * 创建项目
   */
  create(data: ProjectCreate): Promise<Project> {
    return request({
      url: '/projects',
      method: 'post',
      data
    })
  },

  /**
   * 更新项目
   */
  update(id: number, data: ProjectUpdate): Promise<Project> {
    return request({
      url: `/projects/${id}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除项目
   */
  delete(id: number): Promise<{ message: string }> {
    return request({
      url: `/projects/${id}`,
      method: 'delete'
    })
  },

  /**
   * 获取项目统计
   */
  getStatistics(): Promise<ProjectStats> {
    return request({
      url: '/projects/statistics',
      method: 'get'
    })
  },

  // ========== 阶段流转 ==========
  /**
   * 阶段流转
   */
  transferStage(projectId: number, data: StageTransfer): Promise<ProjectStageChange> {
    return request({
      url: `/projects/${projectId}/transfer`,
      method: 'post',
      data
    })
  },

  /**
   * 获取阶段变更历史
   */
  getStageChanges(projectId: number): Promise<ProjectStageChange[]> {
    return request({
      url: `/projects/${projectId}/stage-changes`,
      method: 'get'
    })
  },

  // ========== 跟进记录 ==========
  /**
   * 添加跟进记录
   */
  addFollowUp(projectId: number, data: ProjectFollowUpCreate): Promise<ProjectFollowUp> {
    return request({
      url: `/projects/${projectId}/follow-ups`,
      method: 'post',
      data
    })
  },

  /**
   * 获取跟进记录
   */
  getFollowUps(projectId: number): Promise<ProjectFollowUp[]> {
    return request({
      url: `/projects/${projectId}/follow-ups`,
      method: 'get'
    })
  },

  /**
   * 删除跟进记录
   */
  deleteFollowUp(followUpId: number): Promise<{ message: string }> {
    return request({
      url: `/projects/follow-ups/${followUpId}`,
      method: 'delete'
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
      url: '/projects/import',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 下载导入模板
   */
  downloadTemplate(): Promise<Blob> {
    return request({
      url: '/projects/export/template',
      method: 'get',
      responseType: 'blob'
    })
  }
}
