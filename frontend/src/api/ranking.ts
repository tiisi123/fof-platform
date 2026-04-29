/**
 * 市场排名与分位数API
 */
import request from '@/api/request'

// 获取产品在同策略中的排名
export function getProductRanking(productId: number, period: string = '1y') {
  return request.get(`/ranking/product/${productId}`, {
    params: { period }
  })
}

// 获取策略排行榜
export function getStrategyRanking(
  strategyType: string,
  period: string = '1y',
  indicator: string = 'annualized_return',
  limit: number = 50
) {
  return request.get(`/ranking/strategy/${strategyType}`, {
    params: { period, indicator, limit }
  })
}

// 获取滚动分位数走势
export function getRollingPercentile(
  productId: number,
  indicator: string = 'annualized_return',
  window: number = 252
) {
  return request.get(`/ranking/rolling/${productId}`, {
    params: { indicator, window }
  })
}

// 获取策略内指标分布
export function getStrategyDistribution(
  strategyType: string,
  period: string = '1y',
  indicator: string = 'annualized_return'
) {
  return request.get(`/ranking/distribution/${strategyType}`, {
    params: { period, indicator }
  })
}

// 获取所有策略类型
export function getStrategyTypes() {
  return request.get('/ranking/strategies')
}

// 指标选项
export const INDICATOR_OPTIONS = [
  { value: 'annualized_return', label: '年化收益率' },
  { value: 'total_return', label: '累计收益率' },
  { value: 'annualized_volatility', label: '年化波动率' },
  { value: 'max_drawdown', label: '最大回撤' },
  { value: 'sharpe_ratio', label: '夏普比率' },
  { value: 'calmar_ratio', label: '卡玛比率' }
]

// 周期选项
export const PERIOD_OPTIONS = [
  { value: '1m', label: '近1月' },
  { value: '3m', label: '近3月' },
  { value: '6m', label: '近6月' },
  { value: '1y', label: '近1年' },
  { value: 'ytd', label: '今年以来' },
  { value: 'inception', label: '成立以来' }
]
