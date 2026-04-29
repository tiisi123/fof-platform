"""
审计日志 API
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["审计日志"])

# 操作类型映射
ACTION_LABELS = {
    "create": "新增",
    "update": "修改",
    "delete": "删除",
    "login": "登录",
    "logout": "登出",
    "import": "导入",
    "export": "导出/下载",
    "other": "其他",
}

# 资源类型映射
RESOURCE_LABELS = {
    "manager": "管理人",
    "product": "产品",
    "portfolio": "组合",
    "project": "项目",
    "nav": "净值",
    "document": "资料",
    "user": "用户",
    "report": "报告",
    "alert": "预警",
    "auth": "认证",
    "task": "任务",
    "other": "其他",
}


@router.get("", summary="查询审计日志")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询审计日志列表

    支持按用户、操作类型、资源类型、时间范围、关键词筛选
    """
    service = AuditService(db)
    logs, total = service.get_logs(
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword,
    )

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username or (log.user.real_name if log.user else None) or "系统",
            "action": log.action,
            "action_label": ACTION_LABELS.get(log.action, log.action),
            "resource_type": log.resource_type,
            "resource_type_label": RESOURCE_LABELS.get(log.resource_type, log.resource_type or ""),
            "resource_id": log.resource_id,
            "resource_name": log.resource_name,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "request_method": log.request_method,
            "request_path": log.request_path,
            "status_code": log.status_code,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/statistics", summary="审计统计")
async def get_audit_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取审计日志统计信息"""
    service = AuditService(db)
    return service.get_statistics()


@router.get("/actions", summary="获取操作类型列表")
async def get_action_types(
    current_user: User = Depends(get_current_user),
):
    """获取所有操作类型"""
    return [{"key": k, "label": v} for k, v in ACTION_LABELS.items()]


@router.get("/resource-types", summary="获取资源类型列表")
async def get_resource_types(
    current_user: User = Depends(get_current_user),
):
    """获取所有资源类型"""
    return [{"key": k, "label": v} for k, v in RESOURCE_LABELS.items()]
