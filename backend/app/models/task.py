"""
待办任务模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TaskPriority(str, enum.Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"        # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"    # 已完成
    CANCELLED = "cancelled"    # 已取消


class Task(Base):
    """待办任务"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, comment="任务描述")
    
    # 状态
    status = Column(String(20), default=TaskStatus.PENDING, index=True, comment="状态")
    priority = Column(String(20), default=TaskPriority.MEDIUM, comment="优先级")
    
    # 关联(可选)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, comment="关联产品")
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=True, comment="关联管理人")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, comment="关联组合")
    
    # 分配
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, comment="指派给")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人")
    
    # 时间
    due_date = Column(Date, nullable=True, comment="截止日期")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    product = relationship("Product", backref="tasks", lazy="joined", foreign_keys=[product_id])
    manager = relationship("Manager", backref="tasks", lazy="joined", foreign_keys=[manager_id])
    portfolio = relationship("Portfolio", backref="tasks", lazy="joined", foreign_keys=[portfolio_id])
    assignee = relationship("User", backref="assigned_tasks", lazy="joined", foreign_keys=[assigned_to])
    creator = relationship("User", backref="created_tasks", lazy="joined", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Task {self.id}: {self.title}>"
