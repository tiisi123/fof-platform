"""
审计中间件 - 自动记录所有非GET请求
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
import json
import re

from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
from app.core.logger import logger


# 路径到资源类型的映射
RESOURCE_TYPE_MAP = {
    "/managers": "manager",
    "/products": "product",
    "/portfolios": "portfolio",
    "/projects": "project",
    "/nav": "nav",
    "/documents": "document",
    "/users": "user",
    "/ai-reports": "report",
    "/alerts": "alert",
    "/auth": "auth",
    "/tasks": "task",
}

# 方法到操作类型的映射
METHOD_ACTION_MAP = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

# 不需要记录的路径
EXCLUDED_PATHS = {
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/health",
    "/",
}


def _get_resource_type(path: str) -> str:
    """从请求路径推断资源类型"""
    for prefix, resource_type in RESOURCE_TYPE_MAP.items():
        if prefix in path:
            return resource_type
    return "other"


def _get_action(method: str, path: str) -> str:
    """从请求方法和路径推断操作类型"""
    # 登录/登出特殊处理
    if "/auth/login" in path:
        return "login"
    if "/auth/logout" in path:
        return "logout"
    if "/upload" in path or "/import" in path:
        return "import"
    if "/export" in path or "/download" in path:
        return "export"
    return METHOD_ACTION_MAP.get(method, "other")


def _get_resource_id(path: str) -> int | None:
    """从路径中提取资源ID"""
    # 匹配 /xxx/123 或 /xxx/123/yyy 格式
    match = re.search(r'/(\d+)(?:/|$)', path)
    if match:
        return int(match.group(1))
    return None


def _get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _get_user_info(request: Request) -> tuple:
    """从请求状态中获取用户信息"""
    user_id = getattr(request.state, "user_id", None)
    username = getattr(request.state, "username", None)
    return user_id, username


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 跳过不需要记录的请求
        if request.method == "GET":
            return await call_next(request)

        path = request.url.path
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        # 跳过非API请求
        if not path.startswith("/api/"):
            return await call_next(request)

        # 执行请求
        response: Response = await call_next(request)

        # 异步记录审计日志(不影响正常响应)
        try:
            user_id, username = _get_user_info(request)
            action = _get_action(request.method, path)
            resource_type = _get_resource_type(path)
            resource_id = _get_resource_id(path)

            db: Session = SessionLocal()
            try:
                log = AuditLog(
                    user_id=user_id,
                    username=username,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=_get_client_ip(request),
                    user_agent=request.headers.get("user-agent", "")[:500],
                    request_method=request.method,
                    request_path=path[:500],
                    status_code=response.status_code,
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"审计日志记录失败: {e}")

        return response
