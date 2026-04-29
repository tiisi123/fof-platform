/**
 * 产品相关类型定义
 */

import type { PaginationParams, PaginationResponse, SearchParams } from './api'

// 产品状态
export type ProductStatus = 'active' | 'liquidated' | 'suspended'

// 产品基础信息
export interface Product {
  id: number
  product_code: string
  product_name: string
  manager_id: number
  manager_name?: string
  strategy_type?: string
  established_date?: string
  liquidation_date?: string
  management_fee?: number
  performance_fee?: number
  benchmark_code?: string
  benchmark_name?: string
  is_invested?: boolean
  status: ProductStatus
  remark?: string
  created_at: string
  updated_at: string
  // 兼容别名
  code?: string
  name?: string
}

// 创建产品请求
export interface ProductCreate {
  product_code: string
  product_name: string
  manager_id: number
  strategy_type?: string
  established_date?: string
  liquidation_date?: string
  management_fee?: number
  performance_fee?: number
  benchmark_code?: string
  benchmark_name?: string
  is_invested?: boolean
  status?: ProductStatus
  remark?: string
}

// 更新产品请求
export interface ProductUpdate {
  product_code?: string
  product_name?: string
  manager_id?: number
  strategy_type?: string
  established_date?: string
  liquidation_date?: string
  management_fee?: number
  performance_fee?: number
  benchmark_code?: string
  benchmark_name?: string
  is_invested?: boolean
  status?: ProductStatus
  remark?: string
}

// 产品列表查询参数
export interface ProductListParams extends PaginationParams, SearchParams {
  manager_id?: number
  strategy_type?: string
  status?: string
}

// 产品列表响应
export interface ProductListResponse extends PaginationResponse<Product> {}

// 产品统计信息
export interface ProductStatistics {
  total: number
  by_status: Record<string, number>
  by_strategy: Record<string, number>
}

// 产品状态选项
export const PRODUCT_STATUS_OPTIONS = [
  { label: '运行中', value: 'active' },
  { label: '已清盘', value: 'liquidated' },
  { label: '暂停', value: 'suspended' }
] as const

// 产品状态颜色映射
export const PRODUCT_STATUS_COLOR: Record<ProductStatus, string> = {
  'active': 'success',
  'liquidated': 'danger',
  'suspended': 'warning'
}

// 产品状态中文映射
export const PRODUCT_STATUS_TEXT: Record<ProductStatus, string> = {
  'active': '运行中',
  'liquidated': '已清盘',
  'suspended': '暂停'
}
