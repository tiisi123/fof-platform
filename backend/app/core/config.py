"""
应用配置
"""
import os
import secrets
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


# backend 目录（确保数据库路径固定在 backend/fof.db）
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BACKEND_DIR, "fof.db")


def _generate_secret(length: int = 32) -> str:
    """生成随机安全密钥（仅作开发fallback，生产环境必须通过.env配置）"""
    return secrets.token_hex(length)


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    APP_NAME: str = "FOF管理平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = _generate_secret()
    
    # 数据库配置 - 默认使用SQLite（固定指向 backend/fof.db，除非通过 .env 覆盖）
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"
    DATABASE_ECHO: bool = False
    
    # JWT配置
    JWT_SECRET_KEY: str = _generate_secret()
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:8507",
        "http://127.0.0.1:8507",
        "http://47.116.187.192:8507",
        "http://47.116.187.192",
        "*"  # 临时允许所有来源，生产环境应该限制
    ]
    
    # 默认管理员密码（生产环境务必通过 .env 修改）
    ADMIN_DEFAULT_PASSWORD: str = "admin123"
    
    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 100  # MB
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # LLM 配置（DeepSeek）
    LLM_API_KEY: str = ""  # DeepSeek API Key
    LLM_MODEL: str = "deepseek-chat"  # 模型: deepseek-chat, deepseek-reasoner
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"  # OpenAI兼容接口
    LLM_TIMEOUT: int = 60  # 请求超时(秒)
    LLM_ENABLED: bool = True  # 是否启用LLM(关闭则使用规则引擎)

    # Copilot 可选模型通道（OpenAI Codex 兼容接口）
    LLM_CODEX_API_KEY: str = ""
    LLM_CODEX_MODEL: str = "gpt-5.5"
    LLM_CODEX_BASE_URL: str = "https://cc.maya.today/api/v1"
    LLM_CODEX_TIMEOUT: int = 120
    
    # 钉钉推送配置
    DINGTALK_WEBHOOK_URL: str = ""  # 钉钉群机器人Webhook URL
    DINGTALK_SECRET: str = ""  # 加签密钥(可选)
    DINGTALK_ENABLED: bool = False  # 是否启用钉钉推送
    
    # 舆情爬虫配置
    ENABLE_SENTIMENT_CRAWLER: bool = False  # 是否启用舆情定时爬取（默认禁用）
    SENTIMENT_CRAWLER_INTERVAL: int = 14400  # 爬取间隔(秒)，默认4小时

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "dev", "development"}:
                return True
        return value
    
    class Config:
        env_file = ".env"  # .env文件在backend目录
        case_sensitive = True
        extra = "allow"


# 创建全局配置实例
settings = Settings()
