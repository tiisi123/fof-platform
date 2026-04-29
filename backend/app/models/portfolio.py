"""
组合管理模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.types import Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class PortfolioStatus(str, enum.Enum):
    """组合状态"""
    DRAFT = "draft"  # 草稿
    ACTIVE = "active"  # 生效
    ARCHIVED = "archived"  # 归档


class PortfolioType(str, enum.Enum):
    """组合类型"""
    INVESTED = "invested"      # 已投组合（实盘）
    SIMULATED = "simulated"    # 模拟组合


class Portfolio(Base):
    """组合表"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True, comment="组合ID")
    portfolio_code = Column(String(50), unique=True, nullable=True, index=True, comment="组合代码")
    name = Column(String(200), nullable=False, comment="组合名称")
    portfolio_type = Column(String(20), default="invested", comment="类型: invested/simulated")
    description = Column(Text, comment="组合描述")
    status = Column(String(20), default="active", comment="状态: draft/active/archived")
    benchmark_code = Column(String(50), comment="基准代码")
    benchmark_name = Column(String(100), comment="基准名称")
    start_date = Column(Date, comment="组合起始日期")
    initial_amount = Column(Numeric(20, 2), comment="初始金额")
    risk_budget = Column(Text, comment="风险预算配置(JSON)")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    
    # 关联关系
    components = relationship("PortfolioComponent", back_populates="portfolio", cascade="all, delete-orphan")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    nav_history = relationship("PortfolioNav", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, code='{self.portfolio_code}', name='{self.name}')>"


class PortfolioComponent(Base):
    """组合成分表"""
    __tablename__ = "portfolio_components"
    
    id = Column(Integer, primary_key=True, index=True, comment="成分ID")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, comment="组合ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="产品ID")
    weight = Column(Numeric(10, 4), nullable=False, comment="权重(小数，如0.25表示25%)")
    join_date = Column(Date, comment="加入日期")
    exit_date = Column(Date, comment="退出日期")
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    portfolio = relationship("Portfolio", back_populates="components")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<PortfolioComponent(portfolio_id={self.portfolio_id}, product_id={self.product_id}, weight={self.weight})>"


class PortfolioHolding(Base):
    """组合持仓快照表 —— 按日期记录每只子基金的份额、市值、盈亏"""
    __tablename__ = "portfolio_holdings"
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'product_id', 'holding_date', name='uq_holding_snapshot'),
    )
    
    id = Column(Integer, primary_key=True, index=True, comment="持仓ID")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True, comment="组合ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="产品ID")
    holding_date = Column(Date, nullable=False, index=True, comment="持仓日期")
    shares = Column(Numeric(20, 4), default=0, comment="持有份额")
    market_value = Column(Numeric(20, 2), default=0, comment="市值")
    weight = Column(Numeric(10, 6), default=0, comment="权重")
    cost = Column(Numeric(20, 2), default=0, comment="成本")
    pnl = Column(Numeric(20, 2), default=0, comment="浮动盈亏")
    pnl_ratio = Column(Numeric(10, 6), default=0, comment="盈亏比例")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    portfolio = relationship("Portfolio", back_populates="holdings")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<PortfolioHolding(portfolio={self.portfolio_id}, product={self.product_id}, date={self.holding_date})>"


class PortfolioNav(Base):
    """组合净值表 —— 持久化组合净值序列"""
    __tablename__ = "portfolio_nav"
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'nav_date', name='uq_portfolio_nav'),
    )
    
    id = Column(Integer, primary_key=True, index=True, comment="净值ID")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True, comment="组合ID")
    nav_date = Column(Date, nullable=False, index=True, comment="净值日期")
    total_nav = Column(Numeric(20, 2), comment="组合总净值(总市值)")
    unit_nav = Column(Numeric(10, 6), comment="单位净值")
    daily_return = Column(Numeric(10, 6), comment="日收益率")
    cumulative_return = Column(Numeric(10, 6), comment="累计收益率")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    portfolio = relationship("Portfolio", back_populates="nav_history")
    
    def __repr__(self):
        return f"<PortfolioNav(portfolio={self.portfolio_id}, date={self.nav_date}, unit_nav={self.unit_nav})>"


class PortfolioAdjustment(Base):
    """组合调仓记录表"""
    __tablename__ = "portfolio_adjustments"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, comment="组合ID")
    adjust_date = Column(Date, nullable=False, comment="调仓日期")
    adjust_type = Column(String(50), comment="调整类型: rebalance/add/remove/weight_change")
    description = Column(Text, comment="调仓说明")
    before_weights = Column(Text, comment="调仓前快照(JSON)")
    after_weights = Column(Text, comment="调仓后快照(JSON)")
    created_by = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<PortfolioAdjustment(portfolio_id={self.portfolio_id}, date={self.adjust_date})>"
