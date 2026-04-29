"""
用户Schema - 数据验证模型
"""
from pydantic import BaseModel, Field, EmailStr, field_serializer
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, description="邮箱")
    real_name: Optional[str] = Field(None, description="真实姓名", max_length=100)
    role: Optional[str] = Field("readonly", description="角色")
    status: str = Field("active", description="状态")


class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    password: str = Field(..., description="密码", min_length=6, max_length=100)
    email: Optional[EmailStr] = Field(None, description="邮箱")
    real_name: Optional[str] = Field(None, description="真实姓名", max_length=100)
    role: Optional[str] = Field("readonly", description="角色")


class UserUpdate(BaseModel):
    """更新用户（所有字段可选）"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    real_name: Optional[str] = Field(None, description="真实姓名", max_length=100)
    role: Optional[str] = Field(None, description="角色")
    status: Optional[str] = Field(None, description="状态")


class UserChangePassword(BaseModel):
    """修改密码"""
    old_password: Optional[str] = Field(None, description="旧密码")
    current_password: Optional[str] = Field(None, description="当前密码（old_password别名）")
    new_password: str = Field(..., description="新密码", min_length=6, max_length=100)


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    real_name: Optional[str] = Field(None, description="真实姓名")
    role: str = Field(..., description="角色")
    status: str = Field(..., description="状态")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt: Optional[datetime], _info):
        """序列化datetime为字符串"""
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int = Field(..., description="总数")
    items: list[UserResponse] = Field(..., description="用户列表")
