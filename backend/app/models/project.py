"""
一级项目模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Boolean, Text, ForeignKey
from sqlalchemy.types import Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProjectStage(str, enum.Enum):
    """项目阶段"""
    SOURCING = "sourcing"           # Sourcing
    SCREENING = "screening"         # 初筛
    DUE_DILIGENCE = "due_diligence" # 尽调
    IC = "ic"                       # 投决
    POST_INVESTMENT = "post_investment"  # 投后
    EXIT = "exit"                   # 退出
    REJECTED = "rejected"           # 已否决


class ProjectIndustry(str, enum.Enum):
    """项目行业"""
    TMT = "tmt"                     # TMT
    HEALTHCARE = "healthcare"       # 医疗健康
    CONSUMER = "consumer"           # 消费
    MANUFACTURING = "manufacturing" # 先进制造
    ENERGY = "energy"               # 新能源
    FINANCE = "finance"             # 金融
    REAL_ESTATE = "real_estate"     # 房地产
    OTHER = "other"                 # 其他


class Project(Base):
    """一级项目表"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True, comment="项目编号")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    short_name = Column(String(100), comment="项目简称")
    industry = Column(Enum(ProjectIndustry), comment="行业")
    sub_industry = Column(String(100), comment="细分领域")
    source = Column(String(100), comment="项目来源")
    source_channel = Column(String(100), comment="来源渠道")
    
    # 阶段管理
    stage = Column(Enum(ProjectStage), default=ProjectStage.SOURCING, comment="项目阶段")
    assigned_user_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    
    # Sourcing阶段
    initial_intro = Column(Text, comment="初步介绍")
    contact_name = Column(String(100), comment="项目联系人")
    contact_phone = Column(String(50), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")

    # 初筛阶段
    screening_date = Column(Date, comment="初筛日期")
    screening_result = Column(String(50), comment="初筛结果")
    screening_notes = Column(Text, comment="初筛备注")
    
    # 尽调阶段
    dd_start_date = Column(Date, comment="尽调开始日期")
    dd_end_date = Column(Date, comment="尽调结束日期")
    dd_conclusion = Column(Text, comment="尽调结论")
    
    # 投决阶段
    ic_date = Column(Date, comment="投决日期")
    ic_result = Column(String(50), comment="投决结果")
    investment_amount = Column(Numeric(15, 2), comment="投资金额(万元)")
    valuation = Column(Numeric(15, 2), comment="估值(万元)")
    shareholding_ratio = Column(Numeric(5, 2), comment="持股比例(%)")
    
    # 投后阶段
    investment_date = Column(Date, comment="投资日期")
    board_seat = Column(Boolean, default=False, comment="是否有董事席位")
    
    # 退出阶段
    exit_method = Column(String(50), comment="退出方式")
    exit_date = Column(Date, comment="退出日期")
    exit_amount = Column(Numeric(15, 2), comment="退出金额(万元)")
    irr = Column(Numeric(10, 4), comment="IRR")
    moic = Column(Numeric(10, 4), comment="MOIC")
    
    remark = Column(Text, comment="备注")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    follow_ups = relationship("ProjectFollowUp", back_populates="project", cascade="all, delete-orphan")
    stage_changes = relationship("ProjectStageChange", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', stage='{self.stage}')>"


class ProjectFollowUp(Base):
    """项目跟进记录表"""
    __tablename__ = "project_follow_ups"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    follow_date = Column(Date, nullable=False, comment="跟进日期")
    follow_type = Column(String(50), comment="跟进方式")  # 电话/会议/邮件/现场
    content = Column(Text, nullable=False, comment="跟进内容")
    next_plan = Column(Text, comment="下一步计划")
    follow_user_id = Column(Integer, ForeignKey("users.id"), comment="跟进人ID")
    created_at = Column(DateTime, server_default=func.now())
    
    project = relationship("Project", back_populates="follow_ups")
    follow_user = relationship("User", foreign_keys=[follow_user_id])


class ProjectStageChange(Base):
    """项目阶段变更记录表"""
    __tablename__ = "project_stage_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    from_stage = Column(Enum(ProjectStage), comment="原阶段")
    to_stage = Column(Enum(ProjectStage), nullable=False, comment="新阶段")
    reason = Column(Text, comment="变更原因")
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    created_at = Column(DateTime, server_default=func.now())
    
    project = relationship("Project", back_populates="stage_changes")
    operator = relationship("User", foreign_keys=[operator_id])
