"""
组合管理Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ============ 组合成分 ============
class ComponentBase(BaseModel):
    """成分基础"""
    product_id: int = Field(..., description="产品ID")
    weight: Decimal = Field(..., ge=0, le=1, description="权重(0-1)")
    join_date: Optional[date] = Field(None, description="加入日期")


class ComponentCreate(ComponentBase):
    """创建成分"""
    pass


class ComponentUpdate(BaseModel):
    """更新成分"""
    weight: Optional[Decimal] = Field(None, ge=0, le=1, description="权重")
    exit_date: Optional[date] = Field(None, description="退出日期")
    is_active: Optional[bool] = Field(None, description="是否有效")


class ComponentResponse(BaseModel):
    """成分响应"""
    id: int
    portfolio_id: int
    product_id: int
    weight: float
    join_date: Optional[date] = None
    exit_date: Optional[date] = None
    is_active: bool = True
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    manager_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ 组合 ============
class PortfolioBase(BaseModel):
    """组合基础"""
    name: str = Field(..., min_length=1, max_length=200, description="组合名称")
    portfolio_code: Optional[str] = Field(None, max_length=50, description="组合代码")
    portfolio_type: Optional[str] = Field("invested", pattern="^(invested|simulated)$", description="类型")
    description: Optional[str] = Field(None, description="组合描述")
    benchmark_code: Optional[str] = Field(None, description="基准代码")
    benchmark_name: Optional[str] = Field(None, description="基准名称")
    start_date: Optional[date] = Field(None, description="组合起始日期")
    initial_amount: Optional[Decimal] = Field(None, description="初始金额")


class PortfolioCreate(PortfolioBase):
    """创建组合"""
    components: Optional[List[ComponentCreate]] = Field(None, description="组合成分")


class PortfolioUpdate(BaseModel):
    """更新组合"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    portfolio_code: Optional[str] = Field(None, max_length=50)
    portfolio_type: Optional[str] = Field(None, pattern="^(invested|simulated)$")
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")
    benchmark_code: Optional[str] = None
    benchmark_name: Optional[str] = None
    start_date: Optional[date] = None
    initial_amount: Optional[Decimal] = None


class PortfolioResponse(PortfolioBase):
    """组合响应"""
    id: int
    status: str = "active"
    initial_amount: Optional[float] = None  # override Decimal -> float for JSON
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    components: List[ComponentResponse] = []
    
    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """组合列表响应"""
    id: int
    portfolio_code: Optional[str] = None
    name: str
    portfolio_type: str = "invested"
    description: Optional[str] = None
    status: str
    start_date: Optional[date] = None
    component_count: int = 0
    total_weight: float = 0.0
    latest_nav: Optional[float] = None
    total_return: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ 组合分析 ============
class PortfolioNavPoint(BaseModel):
    """组合净值点"""
    date: date
    nav: float
    daily_return: Optional[float] = None


class PortfolioNavResponse(BaseModel):
    """组合净值响应"""
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    nav_series: List[PortfolioNavPoint]
    initial_nav: float = 1.0
    latest_nav: float
    total_return: float


class ComponentContribution(BaseModel):
    """成分贡献"""
    product_id: int
    product_code: str
    product_name: str
    weight: float
    period_return: float
    contribution: float  # 贡献度 = 权重 * 收益率
    contribution_pct: float  # 贡献占比


class PortfolioContributionResponse(BaseModel):
    """组合贡献分析响应"""
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    portfolio_return: float
    contributions: List[ComponentContribution]


class PortfolioPerformance(BaseModel):
    """组合业绩"""
    portfolio_id: int
    portfolio_name: str
    period: str
    total_return: float
    annualized_return: Optional[float] = None
    volatility: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None


# ============ 持仓快照 ============
class HoldingCreate(BaseModel):
    """录入持仓"""
    product_id: int = Field(..., description="产品ID")
    holding_date: date = Field(..., description="持仓日期")
    shares: Decimal = Field(default=Decimal("0"), description="持有份额")
    market_value: Decimal = Field(default=Decimal("0"), description="市值")
    cost: Decimal = Field(default=Decimal("0"), description="成本")


class HoldingResponse(BaseModel):
    """持仓响应"""
    id: int
    portfolio_id: int
    product_id: int
    holding_date: date
    shares: float
    market_value: float
    weight: float
    cost: float
    pnl: float
    pnl_ratio: float
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    manager_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class HoldingsBatchCreate(BaseModel):
    """批量录入持仓"""
    holding_date: date = Field(..., description="持仓日期")
    holdings: List[HoldingCreate] = Field(..., description="持仓列表")


# ============ 组合净值记录 ============
class PortfolioNavRecord(BaseModel):
    """组合净值记录"""
    nav_date: date
    total_nav: float
    unit_nav: float
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None
    
    class Config:
        from_attributes = True


# ============ 调仓记录 ============
class AdjustmentCreate(BaseModel):
    """创建调仓记录"""
    adjust_date: date
    adjust_type: str = Field(..., pattern="^(rebalance|add|remove|weight_change)$")
    description: Optional[str] = None
    components: List[ComponentCreate]  # 调仓后的成分


class AdjustmentResponse(BaseModel):
    """调仓记录响应"""
    id: int
    portfolio_id: int
    adjust_date: date
    adjust_type: str
    description: Optional[str] = None
    before_weights: Optional[str] = None
    after_weights: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Brinson归因 ============
class BrinsonStrategyAttribution(BaseModel):
    """单策略Brinson归因"""
    strategy: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    total_effect: float


class BrinsonAttributionResponse(BaseModel):
    """Brinson归因响应"""
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    portfolio_return: float
    benchmark_return: float
    excess_return: float
    total_allocation_effect: float
    total_selection_effect: float
    total_interaction_effect: float
    attributions: List[BrinsonStrategyAttribution]


# ============ 风险贡献 ============
class RiskContributionItem(BaseModel):
    """单成分风险贡献"""
    product_id: int
    product_code: str
    product_name: str
    weight: float
    mctr: float
    cctr: float
    risk_contribution_pct: float


class RiskContributionResponse(BaseModel):
    """风险贡献响应"""
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    portfolio_volatility: float
    data_points: int
    contributions: List[RiskContributionItem]


# ============ 调仓模拟 ============
class SimulateWeightItem(BaseModel):
    """模拟权重项"""
    product_id: int
    weight: Decimal = Field(..., ge=0, le=1)


class SimulateRequest(BaseModel):
    """调仓模拟请求"""
    weights: List[SimulateWeightItem]
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ============ 风险预算 ============
class RiskBudgetConfig(BaseModel):
    """风险预算配置"""
    max_drawdown: Optional[float] = Field(None, description="最大回撒阈值(0.1=10%)")
    volatility: Optional[float] = Field(None, description="波动率阈值")
    sharpe_min: Optional[float] = Field(None, description="最低夏普比率")
    max_single_weight: Optional[float] = Field(None, description="单一成分最大权重")


# ============ Brinson 第3层 管理人归因 ============
class BrinsonManagerItem(BaseModel):
    """单管理人 Brinson 归因"""
    manager_name: str
    strategy: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    selection_effect: float


class BrinsonManagerResponse(BaseModel):
    """管理人层归因响应"""
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    total_selection_effect: float
    attributions: List[BrinsonManagerItem]


# ============ Brinson 第4层 个券归因 ============
class BrinsonSecurityItem(BaseModel):
    """单个券归因"""
    security_code: str
    security_name: str
    product_name: str
    weight: float
    return_rate: float
    sector_return: float
    stock_selection_effect: float
    sector_allocation_effect: float


class BrinsonSecurityResponse(BaseModel):
    """个券层归因响应"""
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    total_stock_selection: float
    total_sector_allocation: float
    attributions: List[BrinsonSecurityItem]


# ============ 多因子分析 ============
class FactorExposure(BaseModel):
    """单因子暴露"""
    factor_name: str
    factor_label: str
    exposure: float
    factor_return: float
    contribution: float


class ProductFactorDetail(BaseModel):
    """单产品因子明细"""
    product_id: int
    product_name: str
    alpha: float
    residual: float
    r_squared: float
    exposures: List[FactorExposure]


class MultiFactorResponse(BaseModel):
    """多因子分析响应"""
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    portfolio_exposures: List[FactorExposure]
    product_details: List[ProductFactorDetail]


# ============ 四级估值表分析 ============
class HoldingsDetailCreate(BaseModel):
    """导入底层持仓明细"""
    product_id: int
    holding_date: date
    security_code: str
    security_name: Optional[str] = None
    security_type: Optional[str] = None
    quantity: Optional[Decimal] = Decimal("0")
    market_value: Optional[Decimal] = Decimal("0")
    cost: Optional[Decimal] = Decimal("0")
    weight: Optional[Decimal] = Decimal("0")
    industry_l1: Optional[str] = None
    industry_l2: Optional[str] = None
    market_cap_type: Optional[str] = None


class HoldingsDetailBatchCreate(BaseModel):
    """批量导入底层持仓"""
    items: List[HoldingsDetailCreate]


class HoldingsDetailResponse(BaseModel):
    """底层持仓明细响应"""
    id: int
    product_id: int
    product_name: Optional[str] = None
    holding_date: date
    security_code: str
    security_name: Optional[str] = None
    security_type: Optional[str] = None
    quantity: float
    market_value: float
    cost: float
    weight: float
    industry_l1: Optional[str] = None
    industry_l2: Optional[str] = None
    market_cap_type: Optional[str] = None

    class Config:
        from_attributes = True


class IndustryDistItem(BaseModel):
    """行业分布项"""
    industry: str
    weight: float
    count: int
    market_value: float


class ConcentrationMetrics(BaseModel):
    """集中度指标"""
    top5_weight: float
    top10_weight: float
    top20_weight: float
    hhi: float


class MarketCapDistItem(BaseModel):
    """市值分布项"""
    cap_type: str
    cap_label: str
    weight: float
    count: int


class HoldingsAnalysisResponse(BaseModel):
    """四级估值表分析响应"""
    portfolio_id: int
    portfolio_name: str
    holding_date: date
    total_securities: int
    industry_l1: List[IndustryDistItem]
    industry_l2: List[IndustryDistItem]
    concentration: ConcentrationMetrics
    market_cap_dist: List[MarketCapDistItem]
    security_type_dist: List[dict]
