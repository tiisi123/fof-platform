"""
一级项目Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class ProjectStage(str, Enum):
    """项目阶段"""
    SOURCING = "sourcing"
    SCREENING = "screening"
    DUE_DILIGENCE = "due_diligence"
    IC = "ic"
    POST_INVESTMENT = "post_investment"
    EXIT = "exit"
    REJECTED = "rejected"


class ProjectIndustry(str, Enum):
    """项目行业"""
    TMT = "tmt"
    HEALTHCARE = "healthcare"
    CONSUMER = "consumer"
    MANUFACTURING = "manufacturing"
    ENERGY = "energy"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


# ========== 跟进记录 ==========
class ProjectFollowUpBase(BaseModel):
    follow_date: date = Field(..., description="跟进日期")
    follow_type: Optional[str] = Field(None, description="跟进方式")
    content: str = Field(..., description="跟进内容")
    next_plan: Optional[str] = Field(None, description="下一步计划")


class ProjectFollowUpCreate(ProjectFollowUpBase):
    pass


class ProjectFollowUpResponse(ProjectFollowUpBase):
    id: int
    project_id: int
    follow_user_id: Optional[int]
    follow_user_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 阶段变更 ==========
class ProjectStageChangeResponse(BaseModel):
    id: int
    project_id: int
    from_stage: Optional[ProjectStage]
    to_stage: ProjectStage
    reason: Optional[str]
    operator_id: Optional[int]
    operator_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== 项目 ==========
class ProjectBase(BaseModel):
    project_code: str = Field(..., description="项目编号")
    project_name: str = Field(..., description="项目名称")
    short_name: Optional[str] = Field(None, description="项目简称")
    industry: Optional[ProjectIndustry] = Field(None, description="行业")
    sub_industry: Optional[str] = Field(None, description="细分领域")
    source: Optional[str] = Field(None, description="项目来源")
    source_channel: Optional[str] = Field(None, description="来源渠道")
    stage: Optional[ProjectStage] = Field(ProjectStage.SOURCING, description="项目阶段")
    assigned_user_id: Optional[int] = Field(None, description="负责人ID")
    
    # Sourcing
    initial_intro: Optional[str] = Field(None, description="初步介绍")
    contact_name: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    
    # 初筛
    screening_date: Optional[date] = None
    screening_result: Optional[str] = None
    screening_notes: Optional[str] = None
    
    # 尽调
    dd_start_date: Optional[date] = None
    dd_end_date: Optional[date] = None
    dd_conclusion: Optional[str] = None
    
    # 投决
    ic_date: Optional[date] = None
    ic_result: Optional[str] = None
    investment_amount: Optional[float] = None
    valuation: Optional[float] = None
    shareholding_ratio: Optional[float] = None
    
    # 投后
    investment_date: Optional[date] = None
    board_seat: Optional[bool] = False
    
    # 退出
    exit_method: Optional[str] = None
    exit_date: Optional[date] = None
    exit_amount: Optional[float] = None
    irr: Optional[float] = None
    moic: Optional[float] = None
    
    remark: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    short_name: Optional[str] = None
    industry: Optional[ProjectIndustry] = None
    sub_industry: Optional[str] = None
    source: Optional[str] = None
    source_channel: Optional[str] = None
    assigned_user_id: Optional[int] = None
    initial_intro: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    screening_date: Optional[date] = None
    screening_result: Optional[str] = None
    screening_notes: Optional[str] = None
    dd_start_date: Optional[date] = None
    dd_end_date: Optional[date] = None
    dd_conclusion: Optional[str] = None
    ic_date: Optional[date] = None
    ic_result: Optional[str] = None
    investment_amount: Optional[float] = None
    valuation: Optional[float] = None
    shareholding_ratio: Optional[float] = None
    investment_date: Optional[date] = None
    board_seat: Optional[bool] = None
    exit_method: Optional[str] = None
    exit_date: Optional[date] = None
    exit_amount: Optional[float] = None
    irr: Optional[float] = None
    moic: Optional[float] = None
    remark: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    assigned_user_name: Optional[str] = None
    follow_ups: List[ProjectFollowUpResponse] = []
    stage_changes: List[ProjectStageChangeResponse] = []
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    id: int
    project_code: str
    project_name: str
    short_name: Optional[str]
    industry: Optional[ProjectIndustry]
    stage: Optional[ProjectStage]
    assigned_user_id: Optional[int]
    assigned_user_name: Optional[str] = None
    investment_amount: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class StageTransfer(BaseModel):
    """阶段流转"""
    to_stage: ProjectStage = Field(..., description="目标阶段")
    reason: Optional[str] = Field(None, description="流转原因")


class ProjectStats(BaseModel):
    """项目统计"""
    total: int
    by_stage: dict
    by_industry: dict
    total_investment: float
