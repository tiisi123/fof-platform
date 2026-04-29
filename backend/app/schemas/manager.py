"""
管理人Schema V2
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class PoolCategory(str, Enum):
    """跟踪池分类"""
    INVESTED = "invested"
    KEY_TRACKING = "key_tracking"
    OBSERVATION = "observation"
    ELIMINATED = "eliminated"
    CONTACTED = "contacted"


class PrimaryStrategy(str, Enum):
    """一级策略"""
    EQUITY_LONG = "equity_long"
    STOCK_LONG = "stock_long"
    QUANT_NEUTRAL = "quant_neutral"
    CTA = "cta"
    ARBITRAGE = "arbitrage"
    MULTI_STRATEGY = "multi_strategy"
    BOND = "bond"
    OTHER = "other"


# ========== 联系人 ==========
class ManagerContactBase(BaseModel):
    name: str = Field(..., description="姓名")
    position: Optional[str] = Field(None, description="职位")
    phone: Optional[str] = Field(None, description="手机")
    email: Optional[str] = Field(None, description="邮箱")
    wechat: Optional[str] = Field(None, description="微信")
    is_primary: bool = Field(False, description="是否主要联系人")
    remark: Optional[str] = None


class ManagerContactCreate(ManagerContactBase):
    pass


class ManagerContactResponse(ManagerContactBase):
    id: int
    manager_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 核心团队 ==========
class ManagerTeamBase(BaseModel):
    name: str = Field(..., description="姓名")
    position: str = Field(..., description="职位")
    years_of_experience: Optional[int] = Field(None, description="从业年限")
    education: Optional[str] = Field(None, description="教育背景")
    work_history: Optional[str] = Field(None, description="工作经历")
    remark: Optional[str] = None


class ManagerTeamCreate(ManagerTeamBase):
    pass


class ManagerTeamResponse(ManagerTeamBase):
    id: int
    manager_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 跟踪池流转 ==========
class PoolTransferBase(BaseModel):
    to_pool: PoolCategory = Field(..., description="新分类")
    reason: str = Field(..., description="流转原因")


class PoolTransferCreate(PoolTransferBase):
    pass


class PoolTransferResponse(BaseModel):
    id: int
    manager_id: int
    from_pool: Optional[PoolCategory]
    to_pool: PoolCategory
    reason: str
    operator_id: Optional[int]
    operator_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 管理人 ==========
class ManagerBase(BaseModel):
    manager_code: str = Field(..., description="管理人编号")
    manager_name: str = Field(..., description="管理人名称")
    short_name: Optional[str] = Field(None, description="管理人简称")
    registration_no: Optional[str] = Field(None, description="协会备案编号")
    established_date: Optional[date] = Field(None, description="成立日期")
    registered_capital: Optional[float] = Field(None, description="注册资本(万元)")
    paid_capital: Optional[float] = Field(None, description="实缴资本(万元)")
    aum_range: Optional[str] = Field(None, description="管理规模区间")
    employee_count: Optional[int] = Field(None, description="员工人数")
    registered_address: Optional[str] = Field(None, description="注册地址")
    office_address: Optional[str] = Field(None, description="办公地址")
    website: Optional[str] = Field(None, description="官网")
    
    # 策略分类
    primary_strategy: Optional[PrimaryStrategy] = Field(None, description="一级策略")
    secondary_strategy: Optional[str] = Field(None, description="二级策略")
    investment_style: Optional[List[str]] = Field(None, description="投资风格标签")
    benchmark_index: Optional[str] = Field(None, description="基准指数")
    
    # 跟踪池
    pool_category: Optional[PoolCategory] = Field(PoolCategory.OBSERVATION, description="跟踪池分类")
    cooperation_start_date: Optional[date] = Field(None, description="合作开始日期")
    cooperation_end_date: Optional[date] = Field(None, description="合作结束日期")
    assigned_user_id: Optional[int] = Field(None, description="负责人ID")
    
    # 兼容V1
    team_size: Optional[int] = Field(None, description="团队规模")
    aum: Optional[float] = Field(None, description="AUM(亿元)")
    strategy_type: Optional[str] = Field(None, description="策略类型")
    rating: Optional[str] = Field("unrated", description="内部评级")
    contact_person: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    
    remark: Optional[str] = Field(None, description="备注")


class ManagerCreate(ManagerBase):
    contacts: Optional[List[ManagerContactCreate]] = Field(None, description="联系人列表")
    team_members: Optional[List[ManagerTeamCreate]] = Field(None, description="核心团队")


class ManagerUpdate(BaseModel):
    manager_name: Optional[str] = None
    short_name: Optional[str] = None
    registration_no: Optional[str] = None
    established_date: Optional[date] = None
    registered_capital: Optional[float] = None
    paid_capital: Optional[float] = None
    aum_range: Optional[str] = None
    employee_count: Optional[int] = None
    registered_address: Optional[str] = None
    office_address: Optional[str] = None
    website: Optional[str] = None
    primary_strategy: Optional[PrimaryStrategy] = None
    secondary_strategy: Optional[str] = None
    investment_style: Optional[List[str]] = None
    benchmark_index: Optional[str] = None
    cooperation_start_date: Optional[date] = None
    cooperation_end_date: Optional[date] = None
    assigned_user_id: Optional[int] = None
    team_size: Optional[int] = None
    aum: Optional[float] = None
    strategy_type: Optional[str] = None
    rating: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    remark: Optional[str] = None


class ManagerResponse(ManagerBase):
    id: int
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    contacts: List[ManagerContactResponse] = []
    team_members: List[ManagerTeamResponse] = []
    assigned_user_name: Optional[str] = None
    product_count: int = 0
    
    class Config:
        from_attributes = True


class ManagerListResponse(BaseModel):
    """管理人列表响应"""
    id: int
    manager_code: str
    manager_name: str
    short_name: Optional[str]
    primary_strategy: Optional[PrimaryStrategy]
    secondary_strategy: Optional[str]
    pool_category: Optional[PoolCategory]
    aum_range: Optional[str]
    aum: Optional[float]
    rating: Optional[str]
    assigned_user_id: Optional[int]
    assigned_user_name: Optional[str] = None
    contact_person: Optional[str]
    contact_phone: Optional[str]
    product_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class ManagerListParams(BaseModel):
    """管理人列表查询参数"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=1000)
    keyword: Optional[str] = Field(None, description="关键词搜索")
    pool_categories: Optional[List[PoolCategory]] = Field(None, description="跟踪池分类")
    primary_strategies: Optional[List[PrimaryStrategy]] = Field(None, description="一级策略")
    assigned_user_ids: Optional[List[int]] = Field(None, description="负责人")
    tag_names: Optional[List[str]] = Field(None, description="标签名称筛选（包含区域标签）")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")


class ManagerBatchImport(BaseModel):
    """批量导入管理人"""
    managers: List[ManagerCreate]


class PoolCategoryStats(BaseModel):
    """跟踪池统计"""
    category: PoolCategory
    count: int
    
    
class ManagerStats(BaseModel):
    """管理人统计"""
    total: int
    by_pool: List[PoolCategoryStats]
    by_strategy: dict


# ========== 管理人旗下产品信息 ==========
class ManagerProductInfo(BaseModel):
    """管理人旗下产品信息（含最新净值和绩效）"""
    id: int
    product_code: str
    product_name: str
    strategy_type: Optional[str] = None
    established_date: Optional[date] = None
    status: Optional[str] = None
    latest_nav: Optional[float] = None
    latest_nav_date: Optional[date] = None
    cumulative_nav: Optional[float] = None
    cumulative_return: Optional[float] = None
    annualized_return: Optional[float] = None
    nav_count: int = 0

    class Config:
        from_attributes = True


class ProductPerformanceComparison(BaseModel):
    """产品绩效对比"""
    product_name: str
    cumulative_return: Optional[float] = None
    annualized_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    volatility: Optional[float] = None


class ManagerPerformanceSummary(BaseModel):
    """管理人业绩汇总"""
    manager_id: int
    manager_name: str
    total_products: int = 0
    active_products: int = 0
    # 加权平均指标
    weighted_cumulative_return: Optional[float] = None
    weighted_annualized_return: Optional[float] = None
    avg_max_drawdown: Optional[float] = None
    avg_sharpe_ratio: Optional[float] = None
    avg_volatility: Optional[float] = None
    # 各产品对比
    products_comparison: List[ProductPerformanceComparison] = []
    # 综合净值曲线数据
    nav_dates: List[str] = []
    nav_values: List[Optional[float]] = []


# ========== 标签 ==========
class ManagerTagCreate(BaseModel):
    """创建标签"""
    tag_type: str = Field(..., description="标签类型: strategy/progress/custom")
    tag_name: str = Field(..., description="标签名称")
    tag_color: str = Field("#409EFF", description="标签颜色")


class ManagerTagResponse(BaseModel):
    """标签响应"""
    id: int
    manager_id: int
    tag_type: str
    tag_name: str
    tag_color: str
    created_at: datetime

    class Config:
        from_attributes = True
