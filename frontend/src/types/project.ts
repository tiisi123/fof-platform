/**
 * 一级项目相关类型定义
 */

import type { PaginationParams, PaginationResponse } from './api'

// 项目阶段
export type ProjectStage = 'sourcing' | 'screening' | 'due_diligence' | 'ic' | 'post_investment' | 'exit' | 'rejected'

// 项目行业
export type ProjectIndustry = 'tmt' | 'healthcare' | 'consumer' | 'manufacturing' | 'energy' | 'finance' | 'real_estate' | 'other'

// 跟进记录
export interface ProjectFollowUp {
  id: number
  project_id: number
  follow_date: string
  follow_type?: string
  content: string
  next_plan?: string
  follow_user_id?: number
  follow_user_name?: string
  created_at: string
}

// 阶段变更记录
export interface ProjectStageChange {
  id: number
  project_id: number
  from_stage?: ProjectStage
  to_stage: ProjectStage
  reason?: string
  operator_id?: number
  operator_name?: string
  created_at: string
}

// 项目
export interface Project {
  id: number
  project_code: string
  project_name: string
  short_name?: string
  industry?: ProjectIndustry
  sub_industry?: string
  source?: string
  source_channel?: string
  stage: ProjectStage
  assigned_user_id?: number
  assigned_user_name?: string
  // Sourcing
  initial_intro?: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  // 初筛
  screening_date?: string
  screening_result?: string
  screening_notes?: string
  // 尽调
  dd_start_date?: string
  dd_end_date?: string
  dd_conclusion?: string
  // 投决
  ic_date?: string
  ic_result?: string
  investment_amount?: number
  valuation?: number
  shareholding_ratio?: number
  // 投后
  investment_date?: string
  board_seat?: boolean
  // 退出
  exit_method?: string
  exit_date?: string
  exit_amount?: number
  irr?: number
  moic?: number
  remark?: string
  created_at: string
  updated_at: string
  follow_ups?: ProjectFollowUp[]
  stage_changes?: ProjectStageChange[]
}


// 创建项目请求
export interface ProjectCreate {
  project_code: string
  project_name: string
  short_name?: string
  industry?: ProjectIndustry
  sub_industry?: string
  source?: string
  source_channel?: string
  stage?: ProjectStage
  assigned_user_id?: number
  initial_intro?: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  remark?: string
}

// 更新项目请求
export interface ProjectUpdate extends Partial<Omit<ProjectCreate, 'project_code'>> {
  screening_date?: string
  screening_result?: string
  screening_notes?: string
  dd_start_date?: string
  dd_end_date?: string
  dd_conclusion?: string
  ic_date?: string
  ic_result?: string
  investment_amount?: number
  valuation?: number
  shareholding_ratio?: number
  investment_date?: string
  board_seat?: boolean
  exit_method?: string
  exit_date?: string
  exit_amount?: number
  irr?: number
  moic?: number
}

// 项目列表查询参数
export interface ProjectListParams extends PaginationParams {
  keyword?: string
  stages?: string
  industries?: string
  assigned_user_ids?: string
  sort_by?: string
  sort_order?: string
}

// 项目列表响应
export interface ProjectListResponse extends PaginationResponse<Project> {}

// 阶段流转请求
export interface StageTransfer {
  to_stage: ProjectStage
  reason?: string
}

// 跟进记录创建
export interface ProjectFollowUpCreate {
  follow_date: string
  follow_type?: string
  content: string
  next_plan?: string
}

// 项目统计
export interface ProjectStats {
  total: number
  by_stage: Record<string, number>
  by_industry: Record<string, number>
  total_investment: number
}

// 项目阶段选项
export const PROJECT_STAGE_OPTIONS = [
  { label: 'Sourcing', value: 'sourcing', color: '#909399' },
  { label: '初筛', value: 'screening', color: '#409EFF' },
  { label: '尽调', value: 'due_diligence', color: '#E6A23C' },
  { label: '投决', value: 'ic', color: '#F56C6C' },
  { label: '投后', value: 'post_investment', color: '#67C23A' },
  { label: '退出', value: 'exit', color: '#303133' },
  { label: '已否决', value: 'rejected', color: '#C0C4CC' }
] as const

// 项目行业选项
export const PROJECT_INDUSTRY_OPTIONS = [
  { label: 'TMT', value: 'tmt' },
  { label: '医疗健康', value: 'healthcare' },
  { label: '消费', value: 'consumer' },
  { label: '先进制造', value: 'manufacturing' },
  { label: '新能源', value: 'energy' },
  { label: '金融', value: 'finance' },
  { label: '房地产', value: 'real_estate' },
  { label: '其他', value: 'other' }
] as const

// 跟进方式选项
export const FOLLOW_TYPE_OPTIONS = [
  { label: '电话', value: '电话' },
  { label: '会议', value: '会议' },
  { label: '邮件', value: '邮件' },
  { label: '现场', value: '现场' },
  { label: '其他', value: '其他' }
] as const

// 退出方式选项
export const EXIT_METHOD_OPTIONS = [
  { label: 'IPO', value: 'IPO' },
  { label: '并购', value: '并购' },
  { label: '回购', value: '回购' },
  { label: '转让', value: '转让' },
  { label: '清算', value: '清算' },
  { label: '其他', value: '其他' }
] as const
