"""
认证相关Schema
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据"""
    username: Optional[str] = None


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    status: str
    
    class Config:
        from_attributes = True
