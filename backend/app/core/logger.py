"""
日志配置
"""
import sys
import os
from loguru import logger
from app.core.config import settings

# 确保日志目录存在
log_dir = os.path.dirname(settings.LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 移除默认的日志处理器
logger.remove()

# 添加控制台输出
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True
)

# 添加文件输出
logger.add(
    settings.LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL,
    rotation="10 MB",      # 日志文件达到10MB时轮转
    retention="30 days",   # 保留30天的日志
    compression="zip",     # 压缩旧日志
    encoding="utf-8"
)

# 导出 logger 供其他模块使用
__all__ = ["logger"]
