"""
批注与讨论模型 - 多态关联
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Comment(Base):
    """批注/讨论"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)

    # 多态关联: resource_type + resource_id
    resource_type = Column(String(50), nullable=False, index=True, comment="资源类型: manager/product/project/portfolio")
    resource_id = Column(Integer, nullable=False, index=True, comment="资源ID")

    content = Column(Text, nullable=False, comment="评论内容")
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True, comment="父评论ID(用于回复)")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="评论人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", lazy="joined")
    replies = relationship("Comment", backref="parent", remote_side="Comment.id", lazy="joined")

    def __repr__(self):
        return f"<Comment {self.id}: {self.resource_type}/{self.resource_id}>"
