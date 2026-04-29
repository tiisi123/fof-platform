"""
用户上下文中间件 - 从JWT Token中提取用户信息注入 request.state
供审计中间件等使用
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_token


class UserContextMiddleware(BaseHTTPMiddleware):
    """从Authorization头解析JWT，将用户信息注入request.state"""

    async def dispatch(self, request: Request, call_next):
        # 初始化
        request.state.user_id = None
        request.state.username = None

        # 尝试从 Authorization 头解析用户
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
                if payload:
                    request.state.username = payload.get("sub")
                    # user_id 需要在 get_current_user 中设置
                    # 这里先通过 username 标识
            except Exception:
                pass

        response = await call_next(request)
        return response
