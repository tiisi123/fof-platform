"""
舆情新闻文章模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class SentimentType(str, enum.Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class NewsArticle(Base):
    """舆情新闻"""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, comment="新闻标题")
    content = Column(Text, comment="新闻内容")
    source = Column(String(200), comment="来源")
    url = Column(String(1000), comment="原文链接")
    publish_date = Column(DateTime, comment="发布时间")

    # 关联管理人
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, index=True, comment="关联管理人")

    # 情感分析结果
    sentiment = Column(String(20), default=SentimentType.NEUTRAL, index=True, comment="情感: positive/neutral/negative")
    sentiment_score = Column(Float, default=0.5, comment="情感分数 0-1")
    keywords = Column(JSON, default=list, comment="关键词列表")
    events = Column(JSON, default=list, comment="核心事件")
    summary = Column(String(500), comment="AI摘要")

    # 是否已处理
    is_alert = Column(Integer, default=0, comment="是否触发预警 0/1")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    manager = relationship("Manager", backref="news_articles", lazy="joined", foreign_keys=[manager_id])

    def __repr__(self):
        return f"<NewsArticle {self.id}: {self.title[:30]}>"
