/**
 * 组合管理API
 */
import request from './request'
import type {
  Portfolio,
  PortfolioCreate,
  PortfolioUpdate,
  PortfolioListParams,
  PortfolioListResponse,
  PortfolioComponent,
  ComponentCreate,
  ComponentUpdate,
  PortfolioNavResponse,
  PortfolioContribution,
  PortfolioPerformance,
  PortfolioAdjustment,
  AdjustmentCreate
} from '@/types/portfolio'

export const portfolioApi = {
  /**
   * 获取组合列表
   */
  getList(params?: PortfolioListParams): Promise<PortfolioListResponse> {
    return request({
      url: '/portfolios',
      method: 'get',
      params
    })
  },

  /**
   * 获取组合详情
   */
  getById(id: number): Promise<Portfolio> {
    return request({
      url: `/portfolios/${id}`,
      method: 'get'
    })
  },

  /**
   * 创建组合
   */
  create(data: PortfolioCreate): Promise<Portfolio> {
    return request({
      url: '/portfolios',
      method: 'post',
      data
    })
  },

  /**
   * 更新组合
   */
  update(id: number, data: PortfolioUpdate): Promise<Portfolio> {
    return request({
      url: `/portfolios/${id}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除组合
   */
  delete(id: number): Promise<{ message: string }> {
    return request({
      url: `/portfolios/${id}`,
      method: 'delete'
    })
  },

  /**
   * 添加成分
   */
  addComponent(portfolioId: number, data: ComponentCreate): Promise<PortfolioComponent> {
    return request({
      url: `/portfolios/${portfolioId}/components`,
      method: 'post',
      data
    })
  },

  /**
   * 更新成分
   */
  updateComponent(componentId: number, data: ComponentUpdate): Promise<PortfolioComponent> {
    return request({
      url: `/portfolios/components/${componentId}`,
      method: 'put',
      data
    })
  },

  /**
   * 移除成分
   */
  removeComponent(componentId: number, exitDate?: string): Promise<{ message: string }> {
    return request({
      url: `/portfolios/components/${componentId}`,
      method: 'delete',
      params: exitDate ? { exit_date: exitDate } : undefined
    })
  },

  /**
   * 批量设置成分
   */
  setComponents(portfolioId: number, components: ComponentCreate[]): Promise<{ message: string; count: number }> {
    return request({
      url: `/portfolios/${portfolioId}/components/batch`,
      method: 'put',
      data: components
    })
  },

  /**
   * 获取组合净值序列
   */
  getNav(portfolioId: number, startDate?: string, endDate?: string): Promise<PortfolioNavResponse> {
    return request({
      url: `/portfolios/${portfolioId}/nav`,
      method: 'get',
      params: {
        start_date: startDate,
        end_date: endDate
      }
    })
  },

  /**
   * 获取成分贡献分析
   */
  getContribution(portfolioId: number, startDate?: string, endDate?: string): Promise<PortfolioContribution> {
    return request({
      url: `/portfolios/${portfolioId}/contribution`,
      method: 'get',
      params: {
        start_date: startDate,
        end_date: endDate
      }
    })
  },

  /**
   * 获取组合业绩指标
   */
  getPerformance(portfolioId: number, period: string = '1m'): Promise<PortfolioPerformance> {
    return request({
      url: `/portfolios/${portfolioId}/performance`,
      method: 'get',
      params: { period }
    })
  },

  /**
   * 记录组合调整
   */
  recordAdjustment(portfolioId: number, data: AdjustmentCreate): Promise<PortfolioAdjustment> {
    return request({
      url: `/portfolios/${portfolioId}/adjustments`,
      method: 'post',
      data
    })
  },

  /**
   * 获取调整记录
   */
  getAdjustments(portfolioId: number): Promise<{ items: PortfolioAdjustment[]; total: number }> {
    return request({
      url: `/portfolios/${portfolioId}/adjustments`,
      method: 'get'
    })
  },

  /**
   * Brinson归因分析
   */
  getBrinsonAttribution(portfolioId: number, startDate?: string, endDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/attribution/brinson`,
      method: 'get',
      params: { start_date: startDate, end_date: endDate }
    })
  },

  /**
   * 风险贡献归因
   */
  getRiskContribution(portfolioId: number, startDate?: string, endDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/attribution/risk`,
      method: 'get',
      params: { start_date: startDate, end_date: endDate }
    })
  },

  /**
   * 调仓模拟
   */
  simulateRebalance(portfolioId: number, data: { weights: { product_id: number; weight: number }[]; start_date?: string; end_date?: string }): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/simulate`,
      method: 'post',
      data
    })
  },

  /**
   * 穿透分析
   */
  getLookthrough(portfolioId: number): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/lookthrough`,
      method: 'get'
    })
  },

  /**
   * 获取风险预算配置
   */
  getRiskBudget(portfolioId: number): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/risk-budget`,
      method: 'get'
    })
  },

  /**
   * 更新风险预算配置
   */
  updateRiskBudget(portfolioId: number, data: any): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/risk-budget`,
      method: 'put',
      data
    })
  },

  /**
   * 检查风险预算超限
   */
  checkRiskBudget(portfolioId: number, period?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/risk-budget/check`,
      method: 'get',
      params: { period }
    })
  },

  /**
   * Brinson第3层 管理人归因
   */
  getBrinsonManagerAttribution(portfolioId: number, startDate?: string, endDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/attribution/brinson-manager`,
      method: 'get',
      params: { start_date: startDate, end_date: endDate }
    })
  },

  /**
   * Brinson第4层 个券归因
   */
  getBrinsonSecurityAttribution(portfolioId: number, holdingDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/attribution/brinson-security`,
      method: 'get',
      params: { holding_date: holdingDate }
    })
  },

  /**
   * 多因子分析
   */
  getFactorAnalysis(portfolioId: number, startDate?: string, endDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/factor-analysis`,
      method: 'get',
      params: { start_date: startDate, end_date: endDate }
    })
  },

  /**
   * 获取底层持仓明细
   */
  getHoldingsDetail(portfolioId: number, holdingDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/holdings-detail`,
      method: 'get',
      params: holdingDate ? { holding_date: holdingDate } : undefined
    })
  },

  /**
   * 导入底层持仓明细
   */
  importHoldingsDetail(portfolioId: number, data: { items: any[] }): Promise<{ message: string; count: number }> {
    return request({
      url: `/portfolios/${portfolioId}/holdings-detail`,
      method: 'post',
      data
    })
  },

  /**
   * 四级估值表分析
   */
  getHoldingsDetailAnalysis(portfolioId: number, holdingDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/holdings-detail/analysis`,
      method: 'get',
      params: holdingDate ? { holding_date: holdingDate } : undefined
    })
  },

  /**
   * 获取持仓快照
   */
  getHoldings(portfolioId: number, holdingDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/holdings`,
      method: 'get',
      params: holdingDate ? { holding_date: holdingDate } : undefined
    })
  },

  /**
   * 录入持仓快照
   */
  saveHoldings(portfolioId: number, data: { holding_date: string; holdings: any[] }): Promise<{ message: string; count: number }> {
    return request({
      url: `/portfolios/${portfolioId}/holdings`,
      method: 'post',
      data
    })
  },

  /**
   * 获取持久化净值序列
   */
  getNavHistory(portfolioId: number, startDate?: string, endDate?: string): Promise<any> {
    return request({
      url: `/portfolios/${portfolioId}/nav/history`,
      method: 'get',
      params: { start_date: startDate, end_date: endDate }
    })
  },

  /**
   * 触发净值计算并持久化
   */
  calculateNav(portfolioId: number): Promise<{ message: string; count: number }> {
    return request({
      url: `/portfolios/${portfolioId}/nav/calculate`,
      method: 'post'
    })
  },

  /**
   * Quant provider 鐘舵€?
   */
  getQuantProviders(): Promise<any> {
    return request({
      url: '/quant/providers',
      method: 'get'
    })
  },

  /**
   * OpenBB 鎺ュ叆鐘舵€?
   */
  getOpenBBStatus(): Promise<any> {
    return request({
      url: '/quant/openbb/status',
      method: 'get'
    })
  },

  /**
   * Quant 缁勫悎浼樺寲
   */
  optimizeWithQuant(
    portfolioId: number,
    data: {
      engine?: 'auto' | 'pypfopt' | 'riskfolio' | 'native'
      objective?: 'max_sharpe' | 'min_volatility' | 'risk_budget' | 'cvar_min' | 'target_return'
      risk_free_rate?: number
      start_date?: string
      end_date?: string
      allow_short?: boolean
      target_return?: number
    }
  ): Promise<any> {
    return request({
      url: `/quant/portfolios/${portfolioId}/optimize`,
      method: 'post',
      data
    })
  },

  /**
   * Quant 缁勫悎涓氱哗鎽樿
   */
  getQuantPerformance(
    portfolioId: number,
    params?: {
      engine?: 'auto' | 'quantstats' | 'native'
      start_date?: string
      end_date?: string
      benchmark_code?: string
      benchmark_engine?: 'auto' | 'akshare' | 'openbb' | 'native'
      risk_free_rate?: number
    }
  ): Promise<any> {
    return request({
      url: `/quant/portfolios/${portfolioId}/performance`,
      method: 'get',
      params
    })
  },

  /**
   * Quant 鍩哄噯瀵规瘮/CAPM
   */
  compareQuantBenchmark(
    portfolioId: number,
    params: {
      benchmark_code: string
      engine?: 'auto' | 'akshare' | 'openbb' | 'native'
      start_date?: string
      end_date?: string
      risk_free_rate?: number
    }
  ): Promise<any> {
    return request({
      url: `/quant/portfolios/${portfolioId}/benchmark`,
      method: 'get',
      params
    })
  }
}
