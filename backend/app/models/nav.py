"""
净值数据模型
"""
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.types import Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class NavData(Base):
    """净值数据表"""
    __tablename__ = "nav_data"
    __table_args__ = (
        UniqueConstraint('product_id', 'nav_date', name='uk_product_date'),
    )
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="净值ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="产品ID")
    nav_date = Column(Date, nullable=False, index=True, comment="净值日期")
    unit_nav = Column(Numeric(10, 4), comment="单位净值")
    cumulative_nav = Column(Numeric(10, 4), comment="累计净值")
    adjusted_nav = Column(Numeric(10, 4), comment="复权净值")
    dividend_adjusted_nav = Column(Numeric(10, 4), comment="分红调整后净值")
    data_source = Column(String(50), comment="数据来源")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    product = relationship("Product", back_populates="nav_data")
    
    def __repr__(self):
        return f"<NavData(product_id={self.product_id}, date='{self.nav_date}', nav={self.unit_nav})>"
