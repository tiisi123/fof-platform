"""
操作审计日志模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """操作审计日志"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作用户ID")
    username = Column(String(100), comment="操作用户名(冗余)")
    action = Column(String(50), nullable=False, comment="操作类型: create/update/delete/login/logout/export/import")
    resource_type = Column(String(50), comment="资源类型: manager/product/portfolio/project/nav/document/user/report")
    resource_id = Column(Integer, comment="资源ID")
    resource_name = Column(String(200), comment="资源名称(冗余,方便展示)")
    detail = Column(JSON, comment="操作详情(JSON)")
    ip_address = Column(String(50), comment="客户端IP")
    user_agent = Column(String(500), comment="User-Agent")
    request_method = Column(String(10), comment="请求方法")
    request_path = Column(String(500), comment="请求路径")
    status_code = Column(Integer, comment="响应状态码")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="操作时间")

    # 关系
    user = relationship("User", backref="audit_logs", lazy="joined")

    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type} by {self.username}>"
