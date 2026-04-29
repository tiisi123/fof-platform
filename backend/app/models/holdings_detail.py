"""
持仓明细模型 - 四级估值表
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class HoldingsDetail(Base):
    """持仓明细 - 四级估值表"""
    __tablename__ = "holdings_details"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="关联产品")
    holding_date = Column(Date, nullable=False, index=True, comment="持仓日期")

    # 持仓信息
    security_type = Column(String(50), comment="证券类别: stock/bond/fund/futures/cash/other")
    security_code = Column(String(50), comment="证券代码")
    security_name = Column(String(200), comment="证券名称")
    market = Column(String(50), comment="交易市场")

    # 数量和金额
    quantity = Column(Numeric(15, 4), comment="持有数量")
    cost_price = Column(Numeric(15, 4), comment="成本价")
    market_price = Column(Numeric(15, 4), comment="市场价")
    market_value = Column(Numeric(15, 2), comment="市值(元)")
    cost = Column(Numeric(15, 2), comment="成本(元)")

    # 占比
    weight = Column(Numeric(8, 4), comment="占净值比例")
    pnl = Column(Numeric(15, 2), comment="浮动盈亏(元)")
    pnl_ratio = Column(Numeric(8, 4), comment="盈亏比例")

    # 分类标签
    industry_l1 = Column(String(50), comment="申万一级行业")
    industry_l2 = Column(String(50), comment="申万二级行业")
    market_cap_type = Column(String(20), comment="市值类型: large/mid/small")

    # 层级(用于穿透)
    level = Column(Integer, default=1, comment="穿透层级 1-4")
    parent_id = Column(Integer, ForeignKey("holdings_details.id"), nullable=True, comment="上层持仓ID")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关系
    product = relationship("Product", backref="holdings_details", foreign_keys=[product_id])

    def __repr__(self):
        return f"<HoldingsDetail {self.id}: {self.security_name}>"
