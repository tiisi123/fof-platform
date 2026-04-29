"""
项目现金流模型 - 用于IRR/MOIC计算
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class CashflowType(str, enum.Enum):
    """现金流类型"""
    INVESTMENT = "investment"    # 投入
    DISTRIBUTION = "distribution"  # 分配/回收
    FEE = "fee"                 # 费用
    OTHER = "other"             # 其他


class ProjectCashflow(Base):
    """项目现金流"""
    __tablename__ = "project_cashflows"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True, comment="关联项目")
    cashflow_date = Column(Date, nullable=False, comment="现金流日期")
    cashflow_type = Column(String(20), default=CashflowType.INVESTMENT, comment="类型: investment/distribution/fee/other")
    amount = Column(Numeric(15, 2), nullable=False, comment="金额(万元), 投入为负, 回收为正")
    description = Column(Text, comment="说明")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    project = relationship("Project", backref="cashflows", foreign_keys=[project_id])

    def __repr__(self):
        return f"<ProjectCashflow {self.id}: {self.cashflow_date} {self.amount}>"
