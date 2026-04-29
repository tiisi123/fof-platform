"""
管理人模型 V2
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Boolean, Text, ForeignKey
from sqlalchemy.types import Numeric, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class PoolCategory(str, enum.Enum):
    """跟踪池分类"""
    INVESTED = "invested"           # 在投池
    KEY_TRACKING = "key_tracking"   # 重点跟踪池
    OBSERVATION = "observation"     # 观察池
    ELIMINATED = "eliminated"       # 淘汰池
    CONTACTED = "contacted"         # 已看过


class PrimaryStrategy(str, enum.Enum):
    """一级策略"""
    EQUITY_LONG = "equity_long"         # 股票多头
    QUANT_NEUTRAL = "quant_neutral"     # 量化中性
    CTA = "cta"                         # CTA
    ARBITRAGE = "arbitrage"             # 套利
    MULTI_STRATEGY = "multi_strategy"   # 多策略
    BOND = "bond"                       # 债券
    OTHER = "other"                     # 其他


class ManagerStatus(str, enum.Enum):
    """管理人状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Manager(Base):
    """管理人表"""
    __tablename__ = "managers"
    
    id = Column(Integer, primary_key=True, index=True, comment="管理人ID")
    manager_code = Column(String(50), unique=True, nullable=False, index=True, comment="管理人编号")
    manager_name = Column(String(200), nullable=False, comment="管理人名称")
    short_name = Column(String(100), comment="管理人简称")
    registration_no = Column(String(50), comment="协会备案编号")
    established_date = Column(Date, comment="成立日期")
    registered_capital = Column(Numeric(15, 2), comment="注册资本(万元)")
    paid_capital = Column(Numeric(15, 2), comment="实缴资本(万元)")
    aum_range = Column(String(50), comment="管理规模区间")
    employee_count = Column(Integer, comment="员工人数")
    registered_address = Column(Text, comment="注册地址")
    office_address = Column(Text, comment="办公地址")
    website = Column(String(200), comment="官网")
    
    # 策略分类
    primary_strategy = Column(String(50), comment="一级策略")
    secondary_strategy = Column(String(50), comment="二级策略")
    investment_style = Column(JSON, comment="投资风格标签")
    benchmark_index = Column(String(50), comment="基准指数")
    
    # 跟踪池管理
    pool_category = Column(String(50), default="observation", comment="跟踪池分类")
    cooperation_start_date = Column(Date, comment="合作开始日期")
    cooperation_end_date = Column(Date, comment="合作结束日期")
    assigned_user_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    
    # 兼容V1字段
    team_size = Column(Integer, comment="团队规模")
    aum = Column(Numeric(20, 2), comment="AUM（亿元）")
    strategy_type = Column(String(50), comment="策略类型(兼容)")
    rating = Column(String(20), default="unrated", comment="内部评级")
    contact_person = Column(String(100), comment="联系人")
    contact_phone = Column(String(50), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")
    address = Column(String(500), comment="办公地址(兼容)")
    
    # 运营情况
    operation_status = Column(String(50), comment="运营状态: normal/abnormal/warning")
    aum_scale = Column(Numeric(15, 2), comment="管理规模(亿元)精确值")
    fund_count = Column(Integer, comment="在管基金数")
    last_inspection_date = Column(Date, comment="最近尽调/检查日期")
    operation_remark = Column(Text, comment="运营备注")

    # 财务与合规
    compliance_status = Column(String(50), comment="合规状态: compliant/non_compliant/under_review")
    has_penalty = Column(Boolean, default=False, comment="是否有处罚记录")
    penalty_details = Column(Text, comment="处罚详情")
    financial_audit_date = Column(Date, comment="最近财务审计日期")
    compliance_remark = Column(Text, comment="合规备注")

    remark = Column(Text, comment="备注")
    status = Column(String(20), default="active", comment="状态")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    
    # 关联关系
    products = relationship("Product", back_populates="manager")
    contacts = relationship("ManagerContact", back_populates="manager", cascade="all, delete-orphan")
    team_members = relationship("ManagerTeam", back_populates="manager", cascade="all, delete-orphan")
    pool_transfers = relationship("PoolTransfer", back_populates="manager", cascade="all, delete-orphan")
    tags = relationship("ManagerTag", back_populates="manager", cascade="all, delete-orphan")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    
    def __repr__(self):
        return f"<Manager(id={self.id}, name='{self.manager_name}', pool='{self.pool_category}')>"


class ManagerContact(Base):
    """管理人联系人表"""
    __tablename__ = "manager_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="姓名")
    position = Column(String(100), comment="职位")
    phone = Column(String(50), comment="手机")
    email = Column(String(100), comment="邮箱")
    wechat = Column(String(100), comment="微信")
    is_primary = Column(Boolean, default=False, comment="是否主要联系人")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    manager = relationship("Manager", back_populates="contacts")


class ManagerTeam(Base):
    """管理人核心团队表"""
    __tablename__ = "manager_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="姓名")
    position = Column(String(100), nullable=False, comment="职位")
    years_of_experience = Column(Integer, comment="从业年限")
    education = Column(String(200), comment="教育背景")
    work_history = Column(Text, comment="工作经历")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    manager = relationship("Manager", back_populates="team_members")


class PoolTransfer(Base):
    """跟踪池流转记录表"""
    __tablename__ = "pool_transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, index=True)
    from_pool = Column(String(50), comment="原分类")
    to_pool = Column(String(50), nullable=False, comment="新分类")
    reason = Column(Text, nullable=False, comment="流转原因")
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    created_at = Column(DateTime, server_default=func.now(), comment="操作时间")
    
    manager = relationship("Manager", back_populates="pool_transfers")
    operator = relationship("User", foreign_keys=[operator_id])


class ManagerTag(Base):
    """管理人标签表"""
    __tablename__ = "manager_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, index=True)
    tag_type = Column(String(50), nullable=False, comment="标签类型: strategy/progress/custom")
    tag_name = Column(String(100), nullable=False, comment="标签名称")
    tag_color = Column(String(20), default="#409EFF", comment="标签颜色")
    created_at = Column(DateTime, server_default=func.now())
    
    manager = relationship("Manager", back_populates="tags")
