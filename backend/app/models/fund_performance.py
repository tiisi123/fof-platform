"""
基金业绩数据模型
存储从火富牛等数据源获取的完整业绩指标
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class FundPerformance(Base):
    """基金业绩数据表"""
    __tablename__ = "fund_performance"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="产品ID")
    
    # 数据来源
    data_source = Column(String(50), default="huofuniu", comment="数据来源")
    source_fund_id = Column(String(100), comment="数据源基金ID")
    update_date = Column(Date, comment="数据更新日期")
    
    # 收益率指标
    return_1w = Column(Float, comment="近1周收益率")
    return_1m = Column(Float, comment="近1月收益率")
    return_3m = Column(Float, comment="近3月收益率")
    return_6m = Column(Float, comment="近6月收益率")
    return_1y = Column(Float, comment="近1年收益率")
    return_2y = Column(Float, comment="近2年收益率")
    return_3y = Column(Float, comment="近3年收益率")
    return_5y = Column(Float, comment="近5年收益率")
    return_ytd = Column(Float, comment="今年以来收益率")
    return_inception = Column(Float, comment="成立以来收益率")
    
    # 风险指标
    volatility_1y = Column(Float, comment="近1年波动率")
    max_drawdown_1y = Column(Float, comment="近1年最大回撤")
    sharpe_ratio_1y = Column(Float, comment="近1年夏普比率")
    calmar_ratio_1y = Column(Float, comment="近1年卡玛比率")
    sortino_ratio_1y = Column(Float, comment="近1年索提诺比率")
    
    # 年度收益
    annual_returns = Column(JSON, comment="年度收益率列表")
    
    # 原始数据（JSON格式保存所有字段）
    raw_data = Column(JSON, comment="原始数据")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    product = relationship("Product", foreign_keys=[product_id])
    
    def __repr__(self):
        return f"<FundPerformance(product_id={self.product_id}, return_1y={self.return_1y})>"


class FundExtendedInfo(Base):
    """基金扩展信息表"""
    __tablename__ = "fund_extended_info"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True, index=True, comment="产品ID")
    
    # 火富牛字段
    hfn_fund_id = Column(String(100), comment="火富牛基金ID")
    hfn_company_id = Column(String(100), comment="火富牛管理人ID")
    fund_short_name = Column(String(200), comment="基金简称")
    fund_state = Column(Integer, comment="基金状态")
    
    # 净值信息
    latest_nav = Column(Float, comment="最新单位净值")
    latest_cumulative_nav = Column(Float, comment="最新累计净值")
    latest_nav_date = Column(Date, comment="最新净值日期")
    
    # 策略分类
    strategy_level1 = Column(String(100), comment="一级策略")
    strategy_level2 = Column(String(100), comment="二级策略")
    
    # 规模信息
    aum = Column(Float, comment="管理规模（亿元）")
    aum_date = Column(Date, comment="规模更新日期")
    
    # 其他信息
    min_investment = Column(Float, comment="最低投资额")
    management_fee = Column(Float, comment="管理费率")
    performance_fee = Column(Float, comment="业绩报酬")
    
    # 完整原始数据
    raw_data = Column(JSON, comment="完整原始数据")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    product = relationship("Product", foreign_keys=[product_id])
    
    def __repr__(self):
        return f"<FundExtendedInfo(product_id={self.product_id}, fund_short_name='{self.fund_short_name}')>"
