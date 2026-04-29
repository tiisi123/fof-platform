/**
 * 净值数据相关类型定义
 */

import type { PaginationParams, PaginationResponse } from './api'

// 净值数据
export interface NavData {
  id: number
  product_id: number
  product_code?: string
  product_name?: string
  nav_date: string
  unit_nav: number
  cumulative_nav?: number
  created_at: string
  updated_at?: string
}

// 净值数据列表查询参数
export interface NavDataListParams extends PaginationParams {
  product_id?: number
  start_date?: string
  end_date?: string
}

// 净值数据列表响应
export interface NavDataListResponse extends PaginationResponse<NavData> {}

// 净值数据导入响应
export interface NavImportResponse {
  success: number
  failed: number
  errors: string[]
}

// 净值数据统计
export interface NavStatistics {
  total_records: number
  date_range: {
    start: string
    end: string
  }
  latest_nav: number
}

// 导入记录
export interface ImportRecord {
  id: string
  product_id: number
  product_name: string
  file_name: string
  success_count: number
  failed_count: number
  import_time: string
  status: 'success' | 'partial' | 'failed'
}

// 支持的文件格式
export const SUPPORTED_FILE_FORMATS = ['.xls', '.xlsx'] as const

// 文件格式说明
export const FILE_FORMAT_DESCRIPTION = '支持Excel文件格式：.xls、.xlsx'

// 最大文件大小（10MB）
export const MAX_FILE_SIZE = 10 * 1024 * 1024
