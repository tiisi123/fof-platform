"""
API v1版本路由 V2
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth, managers, products, nav, users, analysis,
    projects, portfolio, ranking, email_crawler,
    reports, documents, alerts, ai_reports, attribution,
    audit, tasks, sentiment, comments, due_diligence,
    holdings, calendar, dashboard, review, quant, copilot
)

api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(managers.router, prefix="/managers", tags=["管理人"])
api_router.include_router(products.router, prefix="/products", tags=["产品"])
api_router.include_router(nav.router, prefix="/nav", tags=["净值"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["数据分析"])
api_router.include_router(projects.router, prefix="/projects", tags=["一级项目"])
api_router.include_router(portfolio.router, prefix="/portfolios", tags=["组合管理"])
api_router.include_router(ranking.router, prefix="/ranking", tags=["市场排名"])
api_router.include_router(email_crawler.router)
api_router.include_router(reports.router)
api_router.include_router(documents.router)
api_router.include_router(alerts.router)
api_router.include_router(ai_reports.router)
api_router.include_router(attribution.router)
api_router.include_router(audit.router)
api_router.include_router(tasks.router)
api_router.include_router(sentiment.router)
api_router.include_router(comments.router)
api_router.include_router(due_diligence.router)
api_router.include_router(holdings.router)
api_router.include_router(calendar.router)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(review.router, tags=["Review SDK"])
api_router.include_router(quant.router, prefix="/quant", tags=["Quant"])
api_router.include_router(copilot.router)
