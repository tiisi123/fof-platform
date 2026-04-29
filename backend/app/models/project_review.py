"""
项目评审意见模型 - 投决会评审
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ReviewResult(str, enum.Enum):
    """评审结果"""
    APPROVE = "approve"             # 通过
    REJECT = "reject"               # 否决
    CONDITIONAL = "conditional"     # 有条件通过
    ABSTAIN = "abstain"             # 弃权


class ProjectReview(Base):
    """项目评审意见表"""
    __tablename__ = "project_reviews"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True, comment="项目ID")

    # 评审信息
    review_type = Column(String(50), default="ic", comment="评审类型: screening/dd/ic")
    meeting_date = Column(Date, comment="会议日期")
    reviewer_name = Column(String(100), nullable=False, comment="评审人")
    reviewer_role = Column(String(100), comment="评审人角色/职位")
    result = Column(String(20), nullable=False, comment="评审结果: approve/reject/conditional/abstain")
    opinion = Column(Text, comment="评审意见")
    conditions = Column(Text, comment="附加条件（有条件通过时）")
    risk_notes = Column(Text, comment="风险提示")

    # 操作人
    created_by = Column(Integer, ForeignKey("users.id"), comment="录入人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关系
    project = relationship("Project", backref="reviews")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ProjectReview {self.id}: {self.reviewer_name} -> {self.result}>"
