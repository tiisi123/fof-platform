"""
FastAPI应用主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.logger import logger
from app.api.v1 import api_router
from app.core.audit_middleware import AuditMiddleware
from app.core.user_context_middleware import UserContextMiddleware

# 确保所有模型在 create_all 前注册到 Base
import app.models  # noqa: F401


def init_admin_user():
    """确保管理员用户存在"""
    from app.models.user import User
    from app.core.security import hash_password
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_pwd = settings.ADMIN_DEFAULT_PASSWORD
            admin = User(
                username="admin",
                password_hash=hash_password(admin_pwd),
                real_name="系统管理员",
                role="super_admin",
                status="active"
            )
            db.add(admin)
            db.commit()
            logger.info("已创建默认管理员账户 (密码请查看 .env 配置)")
    except Exception as e:
        db.rollback()
        logger.warning(f"初始化管理员账户失败: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    # 初始化数据库表
    Base.metadata.create_all(bind=engine)
    # 初始化管理员用户
    init_admin_user()
    logger.info("FOF管理平台启动中...")
    logger.info(f"应用名称: {settings.APP_NAME}")
    logger.info(f"版本: {settings.APP_VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"日志文件: {settings.LOG_FILE}")

    # 安全检查: 生产环境警告
    if not settings.DEBUG:
        if settings.ADMIN_DEFAULT_PASSWORD == "admin123":
            logger.warning("⚠️  检测到使用默认管理员密码，请在 .env 中修改 ADMIN_DEFAULT_PASSWORD")
        if settings.DEBUG is False and "47.116.187.192" not in str(settings.CORS_ORIGINS):
            logger.info("✅  CORS 已限制为指定域名")
    
    # 启动舆情定时爬取（可通过环境变量控制）
    # 默认禁用，因为数据源可能失效且会产生大量日志噪音
    # 如需启用，在 .env 中设置 ENABLE_SENTIMENT_CRAWLER=true
    enable_crawler = getattr(settings, 'ENABLE_SENTIMENT_CRAWLER', False)
    if enable_crawler:
        from app.services.sentiment_crawler import start_crawler, stop_crawler
        start_crawler()
        logger.info("✅  舆情爬虫已启动")
    else:
        logger.info("ℹ️  舆情爬虫已禁用（如需启用，设置 ENABLE_SENTIMENT_CRAWLER=true）")
        stop_crawler = None  # 避免关闭时报错
    
    yield
    
    # 关闭时执行
    if stop_crawler:
        stop_crawler()
    logger.info("FOF管理平台关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FOF运营管理分析平台API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    redirect_slashes=False
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册中间件(顺序重要: 先添加的后执行)
app.add_middleware(AuditMiddleware)
app.add_middleware(UserContextMiddleware)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理，记录所有未捕获的异常"""
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Exception: {type(exc).__name__}: {str(exc)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    # 生产环境不返回内部错误详情
    content = {"detail": "服务器内部错误"}
    if settings.DEBUG:
        content["error"] = str(exc)
    return JSONResponse(status_code=500, content=content)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "FOF管理平台API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8506,
        reload=settings.DEBUG,
        access_log=False,  # 关闭默认 access log，减少控制台输出
        log_level="warning",  # uvicorn 自身仅输出 warning 以上
    )
