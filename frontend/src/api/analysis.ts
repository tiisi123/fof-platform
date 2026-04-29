/**
 * 数据分析API - V2升级版
 * 支持多周期业绩分析
 */
import request from './request'

export interface AnalysisParams {
  product_id: number
  start_date?: string
  end_date?: string
}

export interface ReturnAnalysis {
  cumulative_return: number
  annualized_return: number
  period_days: number
}

export interface VolatilityAnalysis {
  volatility: number
  annualized_volatility: number
}

export interface MaxDrawdownAnalysis {
  max_drawdown: number
  max_drawdown_start_date: string
  max_drawdown_end_date: string
  max_drawdown_days: number
}

export interface SharpeRatioAnalysis {
  sharpe_ratio: number
  risk_free_rate: number
}

export interface AllIndicators {
  return_analysis: ReturnAnalysis
  volatility_analysis: VolatilityAnalysis
  max_drawdown_analysis: MaxDrawdownAnalysis
  sharpe_ratio_analysis: SharpeRatioAnalysis
}

export interface ChartDataPoint {
  date: string
  unit_nav: number
  cumulative_nav?: number
}

export interface ChartData {
  dates: string[]
  unit_navs: number[]
  cumulative_navs: number[]
}

// V2 多周期业绩类型
export interface PeriodPerformance {
  period: string
  period_name: string
  start_date?: string
  end_date?: string
  days?: number
  data_points: number
  has_data: boolean
  // 收益指标
  total_return?: number | null
  annualized_return?: number | null
  // 风险指标
  daily_volatility?: number | null
  annualized_volatility?: number | null
  downside_volatility?: number | null
  max_drawdown?: number | null
  drawdown_peak_date?: string | null
  drawdown_trough_date?: string | null
  drawdown_days?: number | null
  recovery_days?: number | null
  // 风险调整收益
  sharpe_ratio?: number | null
  calmar_ratio?: number | null
  sortino_ratio?: number | null
  // 其他
  win_rate?: number | null
}

export interface MultiPeriodPerformance {
  product_id: number
  product_code: string
  product_name: string
  latest_nav?: number
  latest_cumulative_nav?: number | null
  latest_nav_date?: string
  risk_free_rate: number
  periods: Record<string, PeriodPerformance>
  error?: string
}

export interface PerformanceSummary {
  product_id: number
  product_code: string
  product_name: string
  latest_nav?: number
  latest_cumulative_nav?: number | null
  latest_nav_date?: string
  total_return?: number | null
  annualized_return?: number | null
  annualized_volatility?: number | null
  max_drawdown?: number | null
  sharpe_ratio?: number | null
  calmar_ratio?: number | null
  returns_by_period: Record<string, number | null>
}

export const analysisApi = {
  /**
   * 获取收益率分析
   */
  getReturn(params: AnalysisParams): Promise<ReturnAnalysis> {
    return request({
      url: `/analysis/${params.product_id}/return`,
      method: 'get',
      params: {
        start_date: params.start_date,
        end_date: params.end_date
      }
    })
  },

  /**
   * 获取波动率分析
   */
  getVolatility(params: AnalysisParams): Promise<VolatilityAnalysis> {
    return request({
      url: `/analysis/${params.product_id}/volatility`,
      method: 'get',
      params: {
        start_date: params.start_date,
        end_date: params.end_date
      }
    })
  },

  /**
   * 获取最大回撤分析
   */
  getMaxDrawdown(params: AnalysisParams): Promise<MaxDrawdownAnalysis> {
    return request({
      url: `/analysis/${params.product_id}/max-drawdown`,
      method: 'get',
      params: {
        start_date: params.start_date,
        end_date: params.end_date
      }
    })
  },

  /**
   * 获取夏普比率分析
   */
  getSharpeRatio(params: AnalysisParams): Promise<SharpeRatioAnalysis> {
    return request({
      url: `/analysis/${params.product_id}/sharpe-ratio`,
      method: 'get',
      params: {
        start_date: params.start_date,
        end_date: params.end_date
      }
    })
  },

  /**
   * 获取所有指标
   */
  getAllIndicators(params: AnalysisParams): Promise<AllIndicators> {
    return request({
      url: `/analysis/${params.product_id}/all`,
      method: 'get',
      params: {
        start_date: params.start_date,
        end_date: params.end_date
      },
      timeout: 60000
    })
  },

  /**
   * 获取图表数据
   */
  getChartData(params: AnalysisParams): Promise<ChartData> {
    return request({
      url: `/analysis/${params.product_id}/chart-data`,
      method: 'get',
      params: {
        start_date: params.start_date,
        end_date: params.end_date
      }
    })
  },

  // ============ V2 多周期业绩分析接口 ============

  /**
   * 获取多周期业绩指标
   */
  getMultiPeriodPerformance(
    productId: number,
    periods?: string[],
    riskFreeRate: number = 0.03
  ): Promise<MultiPeriodPerformance> {
    return request({
      url: `/analysis/performance/${productId}`,
      method: 'get',
      params: {
        periods: periods?.join(','),
        risk_free_rate: riskFreeRate
      },
      timeout: 60000
    })
  },

  /**
   * 获取业绩摘要
   */
  getPerformanceSummary(
    productId: number,
    riskFreeRate: number = 0.03
  ): Promise<PerformanceSummary> {
    return request({
      url: `/analysis/performance/${productId}/summary`,
      method: 'get',
      params: {
        risk_free_rate: riskFreeRate
      }
    })
  },

  /**
   * 获取单周期业绩指标
   */
  getPeriodPerformance(
    productId: number,
    period: string,
    riskFreeRate: number = 0.03
  ): Promise<PeriodPerformance> {
    return request({
      url: `/analysis/performance/${productId}/period/${period}`,
      method: 'get',
      params: {
        risk_free_rate: riskFreeRate
      }
    })
  },

  /**
   * 比较多产品业绩
   */
  compareProducts(
    productIds: number[],
    period: string = 'inception',
    riskFreeRate: number = 0.03
  ): Promise<PeriodPerformance[]> {
    return request({
      url: '/analysis/performance/compare',
      method: 'post',
      data: productIds,
      params: {
        period,
        risk_free_rate: riskFreeRate
      }
    })
  },

  // ============ V2 市场排名与分位数接口 ============

  /**
   * 获取产品市场排名
   */
  getProductRanking(
    productId: number,
    period: string = '1y',
    riskFreeRate: number = 0.03
  ): Promise<ProductRanking> {
    return request({
      url: `/analysis/ranking/${productId}`,
      method: 'get',
      params: {
        period,
        risk_free_rate: riskFreeRate
      }
    })
  },

  /**
   * 获取策略排行榜
   */
  getStrategyRankingList(
    strategyType: string,
    period: string = '1y',
    indicator: string = 'annualized_return',
    limit: number = 20,
    riskFreeRate: number = 0.03
  ): Promise<StrategyRankingList> {
    return request({
      url: `/analysis/ranking/strategy/${encodeURIComponent(strategyType)}`,
      method: 'get',
      params: {
        period,
        indicator,
        limit,
        risk_free_rate: riskFreeRate
      }
    })
  },

  /**
   * 获取滚动分位数走势
   */
  getRollingPercentile(
    productId: number,
    indicator: string = 'annualized_return',
    window: number = 252,
    riskFreeRate: number = 0.03
  ): Promise<RollingPercentile> {
    return request({
      url: `/analysis/ranking/${productId}/rolling`,
      method: 'get',
      params: {
        indicator,
        window,
        risk_free_rate: riskFreeRate
      }
    })
  },

  /**
   * 获取策略指标分布
   */
  getStrategyDistribution(
    strategyType: string,
    indicator: string = 'annualized_return',
    period: string = '1y',
    riskFreeRate: number = 0.03
  ): Promise<StrategyDistribution> {
    return request({
      url: `/analysis/distribution/${encodeURIComponent(strategyType)}`,
      method: 'get',
      params: {
        indicator,
        period,
        risk_free_rate: riskFreeRate
      }
    })
  }
}

// 排名相关类型
export interface RankingIndicator {
  value: number
  rank: number
  percentile: number
  total: number
}

export interface ProductRanking {
  product_id: number
  product_code: string
  product_name: string
  strategy_type: string
  strategy_name: string
  period: string
  period_name: string
  end_date: string
  peer_count: number
  indicators: {
    annualized_return?: RankingIndicator
    annualized_volatility?: RankingIndicator | null
    max_drawdown?: RankingIndicator | null
    sharpe_ratio?: RankingIndicator | null
    calmar_ratio?: RankingIndicator | null
  }
  message?: string
  error?: string
}

export interface StrategyRankingItem {
  product_id: number
  product_code: string
  product_name: string
  manager_name?: string
  total_return?: number
  annualized_return?: number
  annualized_volatility?: number
  max_drawdown?: number
  sharpe_ratio?: number
  calmar_ratio?: number
  rank: number
  percentile: number
}

export interface StrategyRankingList {
  strategy_type: string
  period: string
  period_name: string
  indicator: string
  end_date: string
  items: StrategyRankingItem[]
  total: number
}

export interface RollingPercentilePoint {
  date: string
  percentile: number
  value: number
  peer_count: number
}

export interface RollingPercentile {
  product_id: number
  product_code: string
  product_name: string
  strategy_type: string
  indicator: string
  series: RollingPercentilePoint[]
  error?: string
}

export interface DistributionStatistics {
  mean: number
  median: number
  std: number
  min: number
  max: number
  q25: number
  q75: number
}

export interface StrategyDistribution {
  strategy_type: string
  period: string
  indicator: string
  end_date: string
  count: number
  statistics: DistributionStatistics
  distribution: Array<{
    product_id: number
    product_name: string
    value: number
  }>
}
