"""
尽调工作流模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class DDStatus(str, enum.Enum):
    """尽调状态"""
    DRAFT = "draft"           # 草稿
    IN_PROGRESS = "in_progress"  # 进行中
    REVIEW = "review"         # 评审中
    APPROVED = "approved"     # 已通过
    REJECTED = "rejected"     # 已否决


class DueDiligenceFlow(Base):
    """尽调工作流"""
    __tablename__ = "due_diligence_flows"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="尽调标题")

    # 关联对象
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=True, index=True, comment="关联管理人")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True, comment="关联项目")

    # 状态
    status = Column(String(20), default=DDStatus.DRAFT, index=True, comment="状态")
    dd_type = Column(String(50), comment="尽调类型: initial/follow_up/annual")

    # 日期
    start_date = Column(Date, comment="计划开始日期")
    end_date = Column(Date, comment="计划结束日期")
    actual_end_date = Column(Date, comment="实际结束日期")

    # 内容
    checklist = Column(JSON, default=list, comment="尽调清单 [{item, completed, remark}]")
    conclusion = Column(Text, comment="尽调结论")
    risk_points = Column(Text, comment="风险点")

    # 人员
    lead_user_id = Column(Integer, ForeignKey("users.id"), comment="负责人")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="评审人")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    manager = relationship("Manager", backref="due_diligences", foreign_keys=[manager_id])
    project = relationship("Project", backref="due_diligences", foreign_keys=[project_id])
    lead_user = relationship("User", foreign_keys=[lead_user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<DueDiligenceFlow {self.id}: {self.title}>"
