"""
用户模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"  # 超级管理员
    DIRECTOR = "director"  # 投资总监
    MANAGER = "manager"  # 投资经理
    RISK = "risk"  # 风控人员
    OPERATOR = "operator"  # 运营人员
    READONLY = "readonly"  # 只读用户


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"  # 激活
    INACTIVE = "inactive"  # 停用
    LOCKED = "locked"  # 锁定


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(100), comment="真实姓名")
    email = Column(String(100), comment="邮箱")
    role = Column(String(20), nullable=False, default="readonly", comment="角色")
    status = Column(String(20), nullable=False, default="active", comment="状态")
    last_login_at = Column(DateTime, comment="最后登录时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
