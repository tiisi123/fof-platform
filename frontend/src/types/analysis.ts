/**
 * 分析相关类型定义
 */

import type { DateRangeParams } from './api'

// 收益率分析
export interface ReturnAnalysis {
  cumulative_return: number
  annualized_return: number
  period_days: number
}

// 波动率分析
export interface VolatilityAnalysis {
  daily_volatility: number
  annualized_volatility: number
}

// 最大回撤分析
export interface MaxDrawdownAnalysis {
  max_drawdown: number
  max_drawdown_pct: number
  peak_date: string
  trough_date: string
}

// 夏普比率分析
export interface SharpeRatioAnalysis {
  sharpe_ratio: number
  risk_free_rate: number
}

// 所有指标
export interface AllIndicators {
  return: ReturnAnalysis
  volatility: VolatilityAnalysis
  max_drawdown: MaxDrawdownAnalysis
  sharpe_ratio: SharpeRatioAnalysis
}

// 分析查询参数
export interface AnalysisParams extends DateRangeParams {
  product_id: number
}

// 净值曲线数据点
export interface NavChartData {
  date: string
  nav_value: number
  accumulated_nav?: number
}

// 指标卡片配置
export interface MetricCard {
  title: string
  value: string | number
  unit?: string
  icon: string
  color: string
  description?: string
}

// 指标类型
export type MetricType = 'return' | 'volatility' | 'drawdown' | 'sharpe'

// 指标配置
export const METRIC_CONFIGS: Record<MetricType, Omit<MetricCard, 'value'>> = {
  return: {
    title: '累计收益率',
    unit: '%',
    icon: 'TrendCharts',
    color: '#67C23A',
    description: '产品成立以来的总收益'
  },
  volatility: {
    title: '年化波动率',
    unit: '%',
    icon: 'DataLine',
    color: '#E6A23C',
    description: '收益率的标准差，衡量风险'
  },
  drawdown: {
    title: '最大回撤',
    unit: '%',
    icon: 'Bottom',
    color: '#F56C6C',
    description: '从峰值到谷底的最大跌幅'
  },
  sharpe: {
    title: '夏普比率',
    unit: '',
    icon: 'Medal',
    color: '#409EFF',
    description: '风险调整后的收益指标'
  }
}

// 日期范围预设
export const DATE_RANGE_PRESETS = [
  { label: '近1个月', value: 30 },
  { label: '近3个月', value: 90 },
  { label: '近6个月', value: 180 },
  { label: '近1年', value: 365 },
  { label: '今年以来', value: 'ytd' },
  { label: '全部', value: 'all' }
] as const
