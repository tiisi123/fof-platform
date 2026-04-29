/**
 * 净值数据API - V2升级版
 * 支持4种格式智能识别、预览、批量导入
 */
import request from './request'
import type { NavData, NavDataListParams, NavDataListResponse } from '@/types'

export interface NavImportParams {
  file: File
  product_id?: number
  product_code?: string
  skip_duplicates?: boolean
  update_existing?: boolean
  auto_detect_product?: boolean
}

export interface NavImportResult {
  success: boolean
  message: string
  format_detected?: string
  total_rows: number
  imported_rows: number
  updated_rows?: number
  skipped_rows: number
  error_rows: number
  errors: string[]
  warnings?: string[]
  date_range?: {
    start: string | null
    end: string | null
  }
  saved_file?: string
}

export interface NavPreviewItem {
  nav_date: string | null
  unit_nav: number | null
  cumulative_nav: number | null
  product_code?: string | null
  product_name?: string | null
}

export interface NavPreviewResult {
  success: boolean
  format_detected?: string
  total_rows?: number
  columns?: string[]
  date_range?: {
    start: string | null
    end: string | null
  }
  product_codes?: string[]
  product_names?: string[]
  warnings?: string[]
  errors?: string[]
  preview_data?: NavPreviewItem[]
}

export interface BatchImportResult {
  success: boolean
  total_files: number
  successful_files: number
  failed_files: number
  total_imported_rows: number
  results: Array<{
    filename: string
    success: boolean
    imported_rows: number
    message: string
  }>
}

export const navApi = {
  /**
   * 获取净值数据列表
   */
  getList(params?: NavDataListParams): Promise<NavDataListResponse> {
    return request({
      url: '/nav',
      method: 'get',
      params
    })
  },

  /**
   * 获取净值数据详情
   */
  getById(id: number): Promise<NavData> {
    return request({
      url: `/nav/${id}`,
      method: 'get'
    })
  },

  /**
   * 预览净值文件（不导入）
   */
  preview(file: File, previewRows: number = 10): Promise<NavPreviewResult> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('preview_rows', previewRows.toString())

    return request({
      url: '/nav/preview',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 30000
    })
  },

  /**
   * 导入净值数据
   */
  import(params: NavImportParams): Promise<NavImportResult> {
    const formData = new FormData()
    formData.append('file', params.file)
    
    if (params.product_id) {
      formData.append('product_id', params.product_id.toString())
    }
    if (params.product_code) {
      formData.append('product_code', params.product_code)
    }
    if (params.skip_duplicates !== undefined) {
      formData.append('skip_duplicates', params.skip_duplicates.toString())
    }
    if (params.update_existing !== undefined) {
      formData.append('update_existing', params.update_existing.toString())
    }
    if (params.auto_detect_product !== undefined) {
      formData.append('auto_detect_product', params.auto_detect_product.toString())
    }

    return request({
      url: '/nav/import',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 120000
    })
  },

  /**
   * 批量导入净值文件
   */
  batchImport(files: File[], options?: {
    skip_duplicates?: boolean
    update_existing?: boolean
    auto_detect_product?: boolean
  }): Promise<BatchImportResult> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    if (options?.skip_duplicates !== undefined) {
      formData.append('skip_duplicates', options.skip_duplicates.toString())
    }
    if (options?.update_existing !== undefined) {
      formData.append('update_existing', options.update_existing.toString())
    }
    if (options?.auto_detect_product !== undefined) {
      formData.append('auto_detect_product', options.auto_detect_product.toString())
    }

    return request({
      url: '/nav/batch-import',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000 // 批量导入5分钟超时
    })
  },

  /**
   * 删除净值数据
   */
  delete(id: number): Promise<{ message: string }> {
    return request({
      url: `/nav/${id}`,
      method: 'delete'
    })
  },

  /**
   * 获取产品净值统计
   */
  getStatistics(productId: number): Promise<{
    product_id: number
    product_name: string
    total_records: number
    start_date: string | null
    end_date: string | null
    latest_unit_nav: number | null
    latest_cumulative_nav: number | null
    latest_nav_date: string | null
  }> {
    return request({
      url: `/nav/statistics/${productId}`,
      method: 'get'
    })
  }
}
