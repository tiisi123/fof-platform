"""
操作审计日志服务
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """审计日志服务"""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        detail: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> AuditLog:
        """记录一条审计日志"""
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            status_code=status_code,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[AuditLog], int]:
        """查询审计日志"""
        query = self.db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(AuditLog.created_at <= datetime.combine(end_date + timedelta(days=1), datetime.min.time()))
        if keyword:
            query = query.filter(
                or_(
                    AuditLog.username.contains(keyword),
                    AuditLog.resource_name.contains(keyword),
                    AuditLog.request_path.contains(keyword),
                )
            )

        total = query.count()
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        return logs, total

    def get_statistics(self) -> Dict[str, Any]:
        """获取审计统计"""
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())

        total = self.db.query(func.count(AuditLog.id)).scalar() or 0
        today_count = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.created_at >= today_start
        ).scalar() or 0

        # 按操作类型统计
        by_action = {}
        rows = self.db.query(
            AuditLog.action, func.count(AuditLog.id)
        ).group_by(AuditLog.action).all()
        for action, count in rows:
            by_action[action] = count

        # 按资源类型统计
        by_resource = {}
        rows = self.db.query(
            AuditLog.resource_type, func.count(AuditLog.id)
        ).filter(AuditLog.resource_type.isnot(None)).group_by(AuditLog.resource_type).all()
        for rt, count in rows:
            by_resource[rt] = count

        return {
            "total": total,
            "today": today_count,
            "by_action": by_action,
            "by_resource": by_resource,
        }
