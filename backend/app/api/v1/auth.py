"""
认证相关API
"""
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import Token, UserInfo

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ----------- 登录失败锁定机制 -----------
_MAX_LOGIN_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5分钟
_login_failures: dict[str, list[float]] = defaultdict(list)  # username -> [timestamps]


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if user.status != "active":
        raise HTTPException(status_code=403, detail="用户已被停用")
    
    # 将用户ID注入request.state供审计中间件使用
    if request:
        request.state.user_id = user.id
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    uname = form_data.username

    # 检查是否被临时锁定
    now = time.time()
    recent = [t for t in _login_failures[uname] if now - t < _LOCKOUT_SECONDS]
    _login_failures[uname] = recent
    if len(recent) >= _MAX_LOGIN_ATTEMPTS:
        remaining = int(_LOCKOUT_SECONDS - (now - recent[0]))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，请 {remaining} 秒后重试",
        )

    # 查询用户
    user = db.query(User).filter(User.username == uname).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        _login_failures[uname].append(now)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != "active":
        raise HTTPException(status_code=403, detail="用户已被停用")
    
    # 登录成功，清除失败记录
    _login_failures.pop(uname, None)

    # 更新最后登录时间
    user.last_login_at = datetime.now()
    db.commit()
    
    # 生成Token
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "real_name": current_user.real_name,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    # 这里可以将Token加入黑名单（需要Redis支持）
    return {"message": "登出成功"}
