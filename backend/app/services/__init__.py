"""
服务层模块 V2
"""
from app.services import manager_service
from app.services import product_service
from app.services import nav_service
from app.services import user_service
from app.services import analysis_service
from app.services import project_service

__all__ = [
    "manager_service",
    "product_service",
    "nav_service",
    "user_service",
    "analysis_service",
    "project_service",
]
