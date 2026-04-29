"""
用户Service - 业务逻辑层
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from fastapi import HTTPException, status

from app.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[List[User], int]:
    """
    获取用户列表
    
    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        search: 搜索关键词（用户名或邮箱）
        is_active: 是否激活筛选
    
    Returns:
        (用户列表, 总数)
    """
    query = db.query(User)
    
    # 搜索过滤
    if search:
        query = query.filter(
            (User.username.like(f"%{search}%")) |
            (User.email.like(f"%{search}%"))
        )
    
    # 状态过滤
    if is_active is not None:
        status = UserStatus.ACTIVE if is_active else UserStatus.INACTIVE
        query = query.filter(User.status == status)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return users, total


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: UserCreate) -> User:
    """
    创建用户
    
    Args:
        db: 数据库会话
        user: 用户创建数据
    
    Returns:
        创建的用户对象
    
    Raises:
        HTTPException: 如果用户名已存在
    """
    # 检查用户名是否已存在
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户名 {user.username} 已存在"
        )
    
    # 密码强度校验
    from app.core.security import validate_password_strength
    msg = validate_password_strength(user.password)
    if msg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"密码不符合要求: {msg}")

    # 创建用户对象
    db_user = User(
        username=user.username,
        email=user.email,
        real_name=user.real_name,
        password_hash=hash_password(user.password),
        role=user.role or "readonly",
        status=UserStatus.ACTIVE
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_user(
    db: Session,
    user_id: int,
    user_update: UserUpdate
) -> User:
    """
    更新用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        user_update: 更新数据
    
    Returns:
        更新后的用户对象
    
    Raises:
        HTTPException: 如果用户不存在
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    
    # 更新字段（只更新提供的字段）
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user


def change_password(
    db: Session,
    user_id: int,
    old_password: str,
    new_password: str
) -> bool:
    """
    修改密码
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        old_password: 旧密码
        new_password: 新密码
    
    Returns:
        是否修改成功
    
    Raises:
        HTTPException: 如果用户不存在或旧密码错误
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    
    # 验证旧密码
    if not verify_password(old_password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 密码强度校验
    from app.core.security import validate_password_strength
    msg = validate_password_strength(new_password)
    if msg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"新密码不符合要求: {msg}")

    # 更新密码
    db_user.password_hash = hash_password(new_password)
    db.commit()
    
    return True


def delete_user(db: Session, user_id: int) -> bool:
    """
    删除用户（停用）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
    
    Returns:
        是否删除成功
    
    Raises:
        HTTPException: 如果用户不存在
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    
    # 软删除：设置为不激活
    db_user.status = UserStatus.INACTIVE
    db.commit()
    
    return True
