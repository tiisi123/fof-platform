/**
 * 组合管理类型定义
 */

// 组合成分
export interface PortfolioComponent {
  id: number
  portfolio_id: number
  product_id: number
  weight: number
  join_date: string | null
  exit_date: string | null
  is_active: boolean
  product_code: string | null
  product_name: string | null
  manager_name: string | null
}

export interface ComponentCreate {
  product_id: number
  weight: number
  join_date?: string
}

export interface ComponentUpdate {
  weight?: number
  exit_date?: string
  is_active?: boolean
}

// 组合
export type PortfolioType = 'invested' | 'simulated'
export type PortfolioStatus = 'draft' | 'active' | 'archived'

export interface Portfolio {
  id: number
  portfolio_code: string | null
  name: string
  portfolio_type: PortfolioType
  description: string | null
  status: PortfolioStatus
  benchmark_code: string | null
  benchmark_name: string | null
  start_date: string | null
  initial_amount: number | null
  created_by: number | null
  created_at: string
  updated_at: string
  components: PortfolioComponent[]
}

export interface PortfolioListItem {
  id: number
  portfolio_code: string | null
  name: string
  portfolio_type: PortfolioType
  description: string | null
  status: PortfolioStatus
  start_date: string | null
  component_count: number
  total_weight: number
  latest_nav: number | null
  total_return: number | null
  created_at: string
}

export interface PortfolioCreate {
  name: string
  portfolio_code?: string
  portfolio_type?: PortfolioType
  description?: string
  benchmark_code?: string
  benchmark_name?: string
  start_date?: string
  initial_amount?: number
  components?: ComponentCreate[]
}

export interface PortfolioUpdate {
  name?: string
  portfolio_code?: string
  portfolio_type?: PortfolioType
  description?: string
  status?: PortfolioStatus
  benchmark_code?: string
  benchmark_name?: string
  start_date?: string
  initial_amount?: number
}

export const PORTFOLIO_TYPE_OPTIONS = [
  { value: 'invested', label: '已投组合', color: '#3b82f6' },
  { value: 'simulated', label: '模拟组合', color: '#8b5cf6' }
] as const

export const PORTFOLIO_STATUS_OPTIONS = [
  { value: 'draft', label: '草稿', color: '#909399' },
  { value: 'active', label: '生效', color: '#67c23a' },
  { value: 'archived', label: '归档', color: '#e6a23c' }
] as const

// 持仓快照
export interface PortfolioHolding {
  id: number
  portfolio_id: number
  product_id: number
  holding_date: string
  shares: number
  market_value: number
  weight: number
  cost: number
  pnl: number
  pnl_ratio: number
  product_code: string | null
  product_name: string | null
  manager_name: string | null
}

export interface HoldingsResponse {
  items: PortfolioHolding[]
  total: number
  holding_date: string | null
  total_market_value: number
  total_pnl: number
  available_dates: string[]
}

// 组合净值记录
export interface PortfolioNavRecord {
  nav_date: string
  total_nav: number | null
  unit_nav: number | null
  daily_return: number
  cumulative_return: number
}

// 组合净值
export interface PortfolioNavPoint {
  date: string
  nav: number
  daily_return: number
}

export interface PortfolioNavQuality {
  effective_dates: number
  calculated_dates: number
  skipped_dates: number
  coverage_ratio: number
  avg_weight_coverage: number
  partial_weight_dates: number
  carry_forward_dates: number
  carry_forward_component_days: number
  stale_component_days: number
  missing_component_days: number
  max_carry_forward_days: number
}

export interface PortfolioNavResponse {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  nav_series: PortfolioNavPoint[]
  initial_nav: number
  latest_nav: number
  total_return: number
  nav_quality?: PortfolioNavQuality
}

// 成分贡献
export interface ComponentContribution {
  product_id: number
  product_code: string
  product_name: string
  weight: number
  period_return: number
  contribution: number
  contribution_pct: number
}

export interface PortfolioContribution {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  portfolio_return: number
  contributions: ComponentContribution[]
}

// 组合业绩
export interface PortfolioPerformance {
  portfolio_id: number
  portfolio_name: string
  period: string
  total_return: number
  annualized_return: number
  volatility: number
  max_drawdown: number
  sharpe_ratio: number
  calmar_ratio: number
}

// 调整记录
export type AdjustmentType = 'rebalance' | 'add' | 'remove' | 'weight_change'

export interface AdjustmentCreate {
  adjust_date: string
  adjust_type: AdjustmentType
  description?: string
  components: ComponentCreate[]
}

export interface PortfolioAdjustment {
  id: number
  portfolio_id: number
  adjust_date: string
  adjust_type: AdjustmentType
  description: string | null
  before_weights: string | null
  after_weights: string | null
  created_at: string
}

export const ADJUSTMENT_TYPE_OPTIONS = [
  { value: 'rebalance', label: '再平衡' },
  { value: 'add', label: '新增成分' },
  { value: 'remove', label: '移除成分' },
  { value: 'weight_change', label: '权重调整' }
] as const

// Brinson归因
export interface BrinsonStrategyAttribution {
  strategy: string
  portfolio_weight: number
  benchmark_weight: number
  portfolio_return: number
  benchmark_return: number
  allocation_effect: number
  selection_effect: number
  interaction_effect: number
  total_effect: number
}

export interface BrinsonAttributionResponse {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  portfolio_return: number
  benchmark_return: number
  excess_return: number
  total_allocation_effect: number
  total_selection_effect: number
  total_interaction_effect: number
  attributions: BrinsonStrategyAttribution[]
}

// 风险贡献归因
export interface RiskContributionItem {
  product_id: number
  product_code: string
  product_name: string
  weight: number
  mctr: number
  cctr: number
  risk_contribution_pct: number
}

export interface RiskContributionResponse {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  portfolio_volatility: number
  data_points: number
  contributions: RiskContributionItem[]
}

// 调仓模拟
export interface SimulateWeightItem {
  product_id: number
  weight: number
}

export interface SimulateRequest {
  weights: SimulateWeightItem[]
  start_date?: string
  end_date?: string
}

export interface SimulateNavPoint {
  date: string
  nav: number
  daily_return: number
}

export interface SimulateMetrics {
  total_return: number
  volatility: number
  max_drawdown: number
  sharpe_ratio: number
}

export interface SimulateResponse {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  original_weights: Record<string, number>
  simulated_weights: Record<string, number>
  original_nav: SimulateNavPoint[]
  simulated_nav: SimulateNavPoint[]
  original_metrics: SimulateMetrics
  simulated_metrics: SimulateMetrics
}

// 穿透分析
export interface LookthroughProduct {
  product_id: number
  product_name: string
  weight: number
}

export interface LookthroughGroup {
  name: string
  weight: number
  count: number
  products: LookthroughProduct[]
}

export interface LookthroughResponse {
  portfolio_id: number
  portfolio_name: string
  total_components: number
  by_strategy: LookthroughGroup[]
  by_manager: LookthroughGroup[]
}

// 风险预算
export interface RiskBudgetConfig {
  max_drawdown?: number
  volatility?: number
  sharpe_min?: number
  max_single_weight?: number
}

export interface RiskAlert {
  metric: string
  label: string
  threshold: number
  current: number
  severity: 'danger' | 'warning'
}

export interface RiskBudgetCheckResponse {
  portfolio_id: number
  period: string
  config: RiskBudgetConfig
  metrics: Record<string, number>
  alerts: RiskAlert[]
  has_breach: boolean
}

// Brinson 第3层 管理人归因
export interface BrinsonManagerItem {
  manager_name: string
  strategy: string
  portfolio_weight: number
  benchmark_weight: number
  portfolio_return: number
  benchmark_return: number
  selection_effect: number
}

export interface BrinsonManagerResponse {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  total_selection_effect: number
  attributions: BrinsonManagerItem[]
}

// Brinson 第4层 个券归因
export interface BrinsonSecurityItem {
  security_code: string
  security_name: string
  product_name: string
  weight: number
  return_rate: number
  sector_return: number
  stock_selection_effect: number
  sector_allocation_effect: number
}

export interface BrinsonSecurityResponse {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  total_stock_selection: number
  total_sector_allocation: number
  attributions: BrinsonSecurityItem[]
}

// 多因子分析
export interface FactorExposure {
  factor_name: string
  factor_label: string
  exposure: number
  factor_return: number
  contribution: number
}

export interface ProductFactorDetail {
  product_id: number
  product_name: string
  alpha: number
  residual: number
  r_squared: number
  exposures: FactorExposure[]
}

export interface MultiFactorResponse {
  portfolio_id: number
  portfolio_name: string
  start_date: string
  end_date: string
  portfolio_exposures: FactorExposure[]
  product_details: ProductFactorDetail[]
}

// 底层持仓明细 (四级估值表)
export interface HoldingsDetailItem {
  id: number
  product_id: number
  product_name: string | null
  holding_date: string
  security_code: string
  security_name: string | null
  security_type: string | null
  quantity: number
  market_value: number
  cost: number
  weight: number
  industry_l1: string | null
  industry_l2: string | null
  market_cap_type: string | null
}

export interface HoldingsDetailCreate {
  product_id: number
  holding_date: string
  security_code: string
  security_name?: string
  security_type?: string
  quantity?: number
  market_value?: number
  cost?: number
  weight?: number
  industry_l1?: string
  industry_l2?: string
  market_cap_type?: string
}

// 四级估值表分析
export interface IndustryDistItem {
  industry: string
  weight: number
  count: number
  market_value: number
}

export interface ConcentrationMetrics {
  top5_weight: number
  top10_weight: number
  top20_weight: number
  hhi: number
}

export interface MarketCapDistItem {
  cap_type: string
  cap_label: string
  weight: number
  count: number
}

export interface HoldingsAnalysisResponse {
  portfolio_id: number
  portfolio_name: string
  holding_date: string
  total_securities: number
  industry_l1: IndustryDistItem[]
  industry_l2: IndustryDistItem[]
  concentration: ConcentrationMetrics
  market_cap_dist: MarketCapDistItem[]
  security_type_dist: { type: string; label: string; weight: number; count: number }[]
}

// 列表参数
export interface PortfolioListParams {
  skip?: number
  limit?: number
  status?: PortfolioStatus
  search?: string
}

export interface PortfolioListResponse {
  items: PortfolioListItem[]
  total: number
  skip: number
  limit: number
}

// 基准选项
export const BENCHMARK_OPTIONS = [
  { value: '000300.SH', label: '沪深300' },
  { value: '000905.SH', label: '中证500' },
  { value: '000852.SH', label: '中证1000' },
  { value: '932000.CSI', label: '中证2000' },
  { value: '000510.SH', label: '中证A500' },
  { value: '399006.SZ', label: '创业板指' },
  { value: '000688.SH', label: '科创50' }
] as const

// 周期选项
export const PERIOD_OPTIONS = [
  { value: '1w', label: '近1周' },
  { value: '1m', label: '近1月' },
  { value: '3m', label: '近3月' },
  { value: '6m', label: '近6月' },
  { value: '1y', label: '近1年' },
  { value: 'ytd', label: '今年以来' },
  { value: 'inception', label: '成立以来' }
] as const
