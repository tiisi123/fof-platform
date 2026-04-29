"""
用户管理相关API
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserChangePassword,
    UserResponse,
    UserListResponse
)
from app.services import user_service

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """仅允许 super_admin / director 角色访问用户管理接口"""
    if current_user.role not in ("super_admin", "director"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可执行此操作"
        )
    return current_user


# ===== 当前用户相关接口（必须放在 /{user_id} 之前） =====

@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的信息
    """
    return current_user


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新当前登录用户的信息
    
    - **real_name**: 姓名
    - **email**: 邮箱
    """
    return user_service.update_user(db, current_user.id, user_update)


@router.post("/me/change-password", summary="修改当前用户密码")
async def change_current_user_password(
    password_data: UserChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    修改当前登录用户的密码
    
    - **old_password / current_password**: 当前密码
    - **new_password**: 新密码
    """
    old_pwd = password_data.old_password or password_data.current_password
    user_service.change_password(
        db,
        current_user.id,
        old_pwd,
        password_data.new_password
    )
    return {"message": "密码修改成功"}


# ===== 用户管理接口 =====

@router.get("", response_model=UserListResponse, summary="获取用户列表")
async def get_users(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词（用户名或邮箱）"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户列表
    
    - **skip**: 跳过的记录数（分页）
    - **limit**: 返回的记录数（分页）
    - **search**: 搜索关键词，支持用户名和邮箱
    - **is_active**: 按激活状态筛选
    """
    users, total = user_service.get_users(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active
    )
    
    return {
        "total": total,
        "items": users
    }


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int = Path(..., description="用户ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据ID获取用户详情
    
    - **user_id**: 用户ID
    """
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    
    return user


@router.post("", response_model=UserResponse, status_code=201, summary="创建用户")
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    创建新用户（仅管理员）
    
    - **username**: 用户名（必填，唯一）
    - **password**: 密码（必填）
    - **email**: 邮箱（可选）
    - **full_name**: 全名（可选）
    - **is_active**: 是否激活（默认true）
    """
    return user_service.create_user(db, user)


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: int = Path(..., description="用户ID"),
    user_update: UserUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新用户信息
    
    - **user_id**: 用户ID
    - 只需提供要更新的字段
    """
    return user_service.update_user(db, user_id, user_update)


@router.post("/{user_id}/change-password", summary="修改密码")
async def change_password(
    user_id: int = Path(..., description="用户ID"),
    password_data: UserChangePassword = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    修改用户密码
    
    - **user_id**: 用户ID
    - **old_password**: 旧密码
    - **new_password**: 新密码
    """
    user_service.change_password(
        db,
        user_id,
        password_data.old_password,
        password_data.new_password
    )
    return {"message": "密码修改成功"}


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int = Path(..., description="用户ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    删除用户（停用）
    
    - **user_id**: 用户ID
    """
    user_service.delete_user(db, user_id)
    return {"message": "用户删除成功"}
