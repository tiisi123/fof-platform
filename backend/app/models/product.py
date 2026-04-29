"""
产品模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.types import Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProductStatus(str, enum.Enum):
    """产品状态"""
    ACTIVE = "active"  # 运行中
    LIQUIDATED = "liquidated"  # 已清盘
    SUSPENDED = "suspended"  # 暂停


class Product(Base):
    """产品表"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True, comment="产品ID")
    product_code = Column(String(50), unique=True, nullable=False, index=True, comment="产品代码")
    product_name = Column(String(200), nullable=False, comment="产品名称")
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, comment="管理人ID")
    strategy_type = Column(String(50), comment="策略类型")
    established_date = Column(Date, comment="成立日期")
    liquidation_date = Column(Date, comment="清盘日期")
    management_fee = Column(Numeric(5, 2), comment="管理费率(%)")
    performance_fee = Column(Numeric(5, 2), comment="业绩报酬(%)")
    benchmark_code = Column(String(50), comment="基准代码")
    benchmark_name = Column(String(100), comment="基准名称")
    is_invested = Column(Boolean, default=False, comment="是否在投")
    status = Column(String(20), default="active", comment="状态")
    remark = Column(String(1000), comment="备注")
    analysis_data = Column(Text, nullable=True, comment="分析数据（回撤、胜率、滚动分析等）JSON格式")
    attribution_data = Column(Text, nullable=True, comment="风格归因数据JSON格式")
    last_analysis_update = Column(DateTime, nullable=True, comment="分析数据最后更新时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    manager = relationship("Manager", back_populates="products")
    nav_data = relationship("NavData", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, code='{self.product_code}', name='{self.product_name}')>"
