"""
日历事件模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CalendarEvent(Base):
    """日历事件"""
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="事件标题")
    description = Column(Text, comment="事件描述")
    event_type = Column(String(50), comment="类型: meeting/deadline/review/report/other")
    event_date = Column(Date, nullable=False, index=True, comment="事件日期")
    start_time = Column(String(10), comment="开始时间 HH:MM")
    end_time = Column(String(10), comment="结束时间 HH:MM")
    is_all_day = Column(Boolean, default=True, comment="是否全天事件")
    color = Column(String(20), default="#409EFF", comment="显示颜色")

    # 关联(可选)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=True, comment="关联管理人")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, comment="关联项目")

    # 创建人
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", lazy="joined")

    def __repr__(self):
        return f"<CalendarEvent {self.id}: {self.title}>"
