"""
舆情分析服务
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.logger import logger
from app.models.news_article import NewsArticle, SentimentType
from app.services.llm_service import llm_service


class SentimentService:
    """管理人舆情分析服务"""

    def analyze_article(self, article: NewsArticle, db: Session) -> Dict[str, Any]:
        """对文章进行情感分析并更新"""
        text = f"{article.title}\n{article.content or ''}"
        result = llm_service.analyze_sentiment(text)

        article.sentiment = result.get("sentiment", "neutral")
        article.sentiment_score = result.get("score", 0.5)
        article.keywords = result.get("keywords", [])
        article.events = result.get("events", [])
        article.summary = result.get("summary", "")

        # 负面且强度高于阈值，标记为预警
        if article.sentiment == SentimentType.NEGATIVE and article.sentiment_score < 0.3:
            article.is_alert = 1

        db.commit()
        logger.info(f"舆情分析完成: article={article.id}, sentiment={article.sentiment}, score={article.sentiment_score}")
        return result

    def batch_analyze(self, manager_id: int, db: Session) -> int:
        """批量分析某管理人未分析的文章"""
        articles = db.query(NewsArticle).filter(
            NewsArticle.manager_id == manager_id,
            NewsArticle.summary.is_(None),
        ).all()

        count = 0
        for article in articles:
            try:
                self.analyze_article(article, db)
                count += 1
            except Exception as e:
                logger.error(f"分析文章{article.id}失败: {e}")

        return count

    def get_manager_sentiment_summary(self, manager_id: int, db: Session) -> Dict[str, Any]:
        """获取管理人舆情摘要"""
        articles = db.query(NewsArticle).filter(
            NewsArticle.manager_id == manager_id
        ).order_by(desc(NewsArticle.publish_date)).limit(50).all()

        positive = sum(1 for a in articles if a.sentiment == SentimentType.POSITIVE)
        negative = sum(1 for a in articles if a.sentiment == SentimentType.NEGATIVE)
        neutral = sum(1 for a in articles if a.sentiment == SentimentType.NEUTRAL)
        total = len(articles)

        avg_score = sum(a.sentiment_score or 0.5 for a in articles) / total if total else 0.5

        # 收集所有关键词
        all_keywords: Dict[str, int] = {}
        for a in articles:
            for kw in (a.keywords or []):
                all_keywords[kw] = all_keywords.get(kw, 0) + 1

        top_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "avg_score": round(avg_score, 3),
            "top_keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
            "alert_count": sum(1 for a in articles if a.is_alert),
        }


# 全局单例
sentiment_service = SentimentService()
