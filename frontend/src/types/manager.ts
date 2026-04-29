/**
 * 管理人相关类型定义 V2
 */

import type { PaginationParams, PaginationResponse } from './api'

// 管理人状态
export type ManagerStatus = 'active' | 'inactive'

// 跟踪池分类
export type PoolCategory = 'invested' | 'key_tracking' | 'observation' | 'eliminated' | 'contacted'

// 一级策略
export type PrimaryStrategy = 'equity_long' | 'quant_neutral' | 'cta' | 'arbitrage' | 'multi_strategy' | 'bond' | 'other'

// 联系人
export interface ManagerContact {
  id: number
  manager_id: number
  name: string
  position?: string
  phone?: string
  email?: string
  wechat?: string
  is_primary: boolean
  remark?: string
  created_at: string
}

// 核心团队成员
export interface ManagerTeam {
  id: number
  manager_id: number
  name: string
  position: string
  years_of_experience?: number
  education?: string
  work_history?: string
  remark?: string
  created_at: string
}

// 跟踪池流转记录
export interface PoolTransfer {
  id: number
  manager_id: number
  from_pool?: PoolCategory
  to_pool: PoolCategory
  reason: string
  operator_id?: number
  operator_name?: string
  created_at: string
}

// 管理人基础信息
export interface Manager {
  id: number
  manager_code: string
  manager_name: string
  short_name?: string
  registration_no?: string
  established_date?: string
  registered_capital?: number
  paid_capital?: number
  aum_range?: string
  employee_count?: number
  registered_address?: string
  office_address?: string
  website?: string
  primary_strategy?: PrimaryStrategy
  secondary_strategy?: string
  investment_style?: string[]
  benchmark_index?: string
  pool_category?: PoolCategory
  cooperation_start_date?: string
  cooperation_end_date?: string
  assigned_user_id?: number
  assigned_user_name?: string
  // 兼容V1
  team_size?: number
  aum?: number
  strategy_type?: string
  rating?: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  address?: string
  remark?: string
  status: ManagerStatus
  created_at: string
  updated_at: string
  contacts?: ManagerContact[]
  team_members?: ManagerTeam[]
  product_count?: number
}


// 创建管理人请求
export interface ManagerCreate {
  manager_code: string
  manager_name: string
  short_name?: string
  registration_no?: string
  established_date?: string
  registered_capital?: number
  paid_capital?: number
  aum_range?: string
  employee_count?: number
  registered_address?: string
  office_address?: string
  website?: string
  primary_strategy?: PrimaryStrategy
  secondary_strategy?: string
  investment_style?: string[]
  benchmark_index?: string
  pool_category?: PoolCategory
  cooperation_start_date?: string
  cooperation_end_date?: string
  assigned_user_id?: number
  team_size?: number
  aum?: number
  strategy_type?: string
  rating?: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  remark?: string
  contacts?: Omit<ManagerContact, 'id' | 'manager_id' | 'created_at'>[]
  team_members?: Omit<ManagerTeam, 'id' | 'manager_id' | 'created_at'>[]
}

// 更新管理人请求
export interface ManagerUpdate extends Partial<Omit<ManagerCreate, 'manager_code' | 'contacts' | 'team_members'>> {}

// 管理人列表查询参数
export interface ManagerListParams extends PaginationParams {
  keyword?: string
  pool_categories?: string
  primary_strategies?: string
  assigned_user_ids?: string
  sort_by?: string
  sort_order?: string
  // 兼容V1
  search?: string
  strategy_type?: string
  status?: string
  rating?: string
}

// 管理人列表响应
export interface ManagerListResponse extends PaginationResponse<Manager> {}

// 跟踪池统计
export interface PoolCategoryStats {
  category: PoolCategory
  count: number
}

// 管理人统计信息
export interface ManagerStatistics {
  total: number
  by_pool: PoolCategoryStats[]
  by_strategy: Record<string, number>
  // 兼容V1
  active?: number
  inactive?: number
}

// 跟踪池流转请求
export interface PoolTransferCreate {
  to_pool: PoolCategory
  reason: string
}

// 跟踪池分类选项
export const POOL_CATEGORY_OPTIONS = [
  { label: '在投池', value: 'invested', color: '#67C23A' },
  { label: '重点跟踪池', value: 'key_tracking', color: '#E6A23C' },
  { label: '观察池', value: 'observation', color: '#409EFF' },
  { label: '淘汰池', value: 'eliminated', color: '#F56C6C' },
  { label: '已看过', value: 'contacted', color: '#909399' }
] as const

// 一级策略选项
export const PRIMARY_STRATEGY_OPTIONS = [
  { label: '股票多头', value: 'equity_long' },
  { label: '量化中性', value: 'quant_neutral' },
  { label: 'CTA', value: 'cta' },
  { label: '套利', value: 'arbitrage' },
  { label: '多策略', value: 'multi_strategy' },
  { label: '债券', value: 'bond' },
  { label: '其他', value: 'other' }
] as const

// 二级策略选项（根据一级策略）
export const SECONDARY_STRATEGY_OPTIONS: Record<PrimaryStrategy, { label: string; value: string }[]> = {
  equity_long: [
    { label: '价值型', value: '价值型' },
    { label: '成长型', value: '成长型' },
    { label: '行业主题', value: '行业主题' },
    { label: 'GARP', value: 'GARP' },
    { label: '小盘', value: '小盘' },
    { label: '大盘', value: '大盘' },
    { label: '灵活配置', value: '灵活配置' }
  ],
  quant_neutral: [
    { label: '指数增强', value: '指数增强' },
    { label: '市场中性', value: '市场中性' },
    { label: '统计套利', value: '统计套利' },
    { label: '多因子', value: '多因子' }
  ],
  cta: [
    { label: '趋势跟踪', value: '趋势跟踪' },
    { label: '套利', value: '套利' },
    { label: '高频', value: '高频' },
    { label: '混合', value: '混合' }
  ],
  arbitrage: [
    { label: '期现套利', value: '期现套利' },
    { label: '跨期套利', value: '跨期套利' },
    { label: '跨品种套利', value: '跨品种套利' },
    { label: '事件套利', value: '事件套利' }
  ],
  multi_strategy: [
    { label: '宏观对冲', value: '宏观对冲' },
    { label: 'FOF', value: 'FOF' },
    { label: '多策略混合', value: '多策略混合' }
  ],
  bond: [
    { label: '纯债', value: '纯债' },
    { label: '转债', value: '转债' },
    { label: '信用债', value: '信用债' }
  ],
  other: [
    { label: '其他', value: '其他' }
  ]
}

// 评级选项
export const RATING_OPTIONS = [
  { label: 'S', value: 'S' },
  { label: 'A', value: 'A' },
  { label: 'B', value: 'B' },
  { label: 'C', value: 'C' },
  { label: 'D', value: 'D' },
  { label: '未评级', value: 'unrated' }
] as const

// 管理规模选项
export const AUM_RANGE_OPTIONS = [
  { label: '0-10亿', value: '0-10亿' },
  { label: '10-20亿', value: '10-20亿' },
  { label: '20-50亿', value: '20-50亿' },
  { label: '50-100亿', value: '50-100亿' },
  { label: '100亿以上', value: '100亿以上' }
] as const

// 基准指数选项
export const MANAGER_BENCHMARK_OPTIONS = [
  { label: '沪深300', value: '沪深300' },
  { label: '中证500', value: '中证500' },
  { label: '中证1000', value: '中证1000' },
  { label: '无风险利率', value: '无风险利率' }
] as const


// 管理人旗下产品信息
export interface ManagerProductInfo {
  id: number
  product_code: string
  product_name: string
  strategy_type?: string
  established_date?: string
  status?: string
  latest_nav?: number
  latest_nav_date?: string
  cumulative_nav?: number
  cumulative_return?: number
  annualized_return?: number
  nav_count: number
}

// 产品绩效对比
export interface ProductPerformanceComparison {
  product_name: string
  cumulative_return?: number
  annualized_return?: number
  max_drawdown?: number
  sharpe_ratio?: number
  volatility?: number
}

// 管理人业绩汇总
export interface ManagerPerformanceSummary {
  manager_id: number
  manager_name: string
  total_products: number
  active_products: number
  weighted_cumulative_return?: number
  weighted_annualized_return?: number
  avg_max_drawdown?: number
  avg_sharpe_ratio?: number
  avg_volatility?: number
  products_comparison: ProductPerformanceComparison[]
  nav_dates: string[]
  nav_values: (number | null)[]
}

// 管理人标签
export interface ManagerTag {
  id: number
  manager_id: number
  tag_type: string
  tag_name: string
  tag_color: string
  created_at: string
}

// 创建标签请求
export interface ManagerTagCreate {
  tag_type: string
  tag_name: string
  tag_color?: string
}

// 尽调资料
export interface ManagerDocument {
  id: number
  filename: string
  file_size: number
  file_type: string
  category: string
  title: string
  description?: string
  uploaded_by: number
  uploaded_at: string
}

// 标签类型选项
export const TAG_TYPE_OPTIONS = [
  { label: '策略标签', value: 'strategy', color: '#409EFF' },
  { label: '进展标签', value: 'progress', color: '#67C23A' },
  { label: '自定义', value: 'custom', color: '#E6A23C' }
] as const

// 尽调资料分类选项
export const DOCUMENT_CATEGORY_OPTIONS = [
  { label: '尽调报告', value: 'dd_report' },
  { label: '法律文件', value: 'legal' },
  { label: '财务资料', value: 'financial' },
  { label: '合同协议', value: 'contract' },
  { label: '路演材料', value: 'presentation' },
  { label: '会议纪要', value: 'meeting' },
  { label: '其他', value: 'other' }
] as const


// 兼容V1的导出
export const STRATEGY_TYPES = PRIMARY_STRATEGY_OPTIONS.map(s => ({
  label: s.label,
  value: s.label  // V1使用中文作为value
}))

export const STATUS_OPTIONS = [
  { label: '活跃', value: 'active' },
  { label: '停用', value: 'inactive' }
] as const
