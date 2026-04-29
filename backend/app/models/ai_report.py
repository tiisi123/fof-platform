"""
AI报告持久化模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    """报告状态"""
    DRAFT = "draft"          # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"    # 已归档


class AIReport(Base):
    """AI报告存储"""
    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="报告标题")
    report_type = Column(String(50), nullable=False, comment="报告类型: product/manager/portfolio/market")
    
    # 关联对象
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, comment="关联产品ID")
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=True, comment="关联管理人ID")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, comment="关联组合ID")
    
    # 内容
    summary = Column(Text, comment="报告摘要")
    content = Column(JSON, nullable=False, comment="报告完整内容(JSON)")
    analysis_text = Column(Text, comment="AI分析文本(便于搜索)")
    
    # 元数据
    status = Column(String(20), default=ReportStatus.DRAFT, comment="状态: draft/published/archived")
    version = Column(Integer, default=1, comment="版本号")
    parent_id = Column(Integer, ForeignKey("ai_reports.id"), nullable=True, comment="父版本ID")
    
    # 分享
    share_token = Column(String(64), unique=True, nullable=True, index=True, comment="分享令牌")
    share_password = Column(String(100), nullable=True, comment="分享密码")
    share_expires_at = Column(DateTime, nullable=True, comment="分享过期时间")
    is_shared = Column(Boolean, default=False, comment="是否已分享")
    
    # 用户信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    
    # 时间戳
    report_date = Column(DateTime, server_default=func.now(), comment="报告日期")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    product = relationship("Product", backref="ai_reports", lazy="joined", foreign_keys=[product_id])
    manager = relationship("Manager", backref="ai_reports", lazy="joined", foreign_keys=[manager_id])
    portfolio = relationship("Portfolio", backref="ai_reports", lazy="joined", foreign_keys=[portfolio_id])
    creator = relationship("User", backref="created_reports", lazy="joined", foreign_keys=[created_by])
    updater = relationship("User", backref="updated_reports", lazy="joined", foreign_keys=[updated_by])
    parent = relationship("AIReport", remote_side=[id], backref="versions")

    def __repr__(self):
        return f"<AIReport {self.id}: {self.title}>"
