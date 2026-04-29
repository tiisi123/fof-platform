"""
管理人编辑历史模型 - 版本追踪
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ManagerEditHistory(Base):
    """管理人编辑历史表"""
    __tablename__ = "manager_edit_history"

    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, index=True, comment="管理人ID")
    field_name = Column(String(100), nullable=False, comment="字段名")
    field_label = Column(String(100), comment="字段中文名")
    old_value = Column(Text, comment="旧值")
    new_value = Column(Text, comment="新值")
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    batch_id = Column(String(50), comment="批次ID，同一次编辑共享")
    created_at = Column(DateTime, server_default=func.now(), comment="操作时间")

    operator = relationship("User", foreign_keys=[operator_id])
