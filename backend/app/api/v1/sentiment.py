"""
管理人舆情 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.news_article import NewsArticle, SentimentType
from app.models.manager import Manager
from app.services.sentiment_service import sentiment_service

router = APIRouter(prefix="/sentiment", tags=["舆情分析"])


def _article_to_dict(a: NewsArticle) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "source": a.source,
        "url": a.url,
        "publish_date": a.publish_date.isoformat() if a.publish_date else None,
        "manager_id": a.manager_id,
        "manager_name": a.manager.manager_name if a.manager else None,
        "sentiment": a.sentiment,
        "sentiment_score": a.sentiment_score,
        "keywords": a.keywords or [],
        "events": a.events or [],
        "summary": a.summary,
        "is_alert": a.is_alert,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.get("/articles", summary="获取舆情文章列表")
async def list_articles(
    manager_id: Optional[int] = Query(None),
    sentiment: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    is_alert: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取舆情文章列表"""
    query = db.query(NewsArticle)

    if manager_id:
        query = query.filter(NewsArticle.manager_id == manager_id)
    if sentiment:
        query = query.filter(NewsArticle.sentiment == sentiment)
    if keyword:
        query = query.filter(NewsArticle.title.contains(keyword))
    if is_alert is not None:
        query = query.filter(NewsArticle.is_alert == is_alert)

    total = query.count()
    articles = query.order_by(desc(NewsArticle.publish_date)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_article_to_dict(a) for a in articles],
    }


@router.post("/articles", summary="添加舆情文章")
async def create_article(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    添加舆情文章并自动进行情感分析。
    body: { title, content?, source?, url?, publish_date?, manager_id }
    """
    body = await request.json()

    manager_id = body.get("manager_id")
    if not manager_id:
        raise HTTPException(status_code=400, detail="manager_id 不能为空")

    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="管理人不存在")

    article = NewsArticle(
        title=body.get("title", ""),
        content=body.get("content"),
        source=body.get("source"),
        url=body.get("url"),
        publish_date=body.get("publish_date"),
        manager_id=manager_id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    # 自动情感分析
    try:
        sentiment_service.analyze_article(article, db)
    except Exception:
        pass  # 分析失败不影响创建

    return {"id": article.id, "message": "文章已添加", "sentiment": article.sentiment}


@router.get("/articles/{article_id}", summary="获取文章详情")
async def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return _article_to_dict(article)


@router.delete("/articles/{article_id}", summary="删除文章")
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    db.delete(article)
    db.commit()
    return {"message": "文章已删除"}


@router.post("/articles/{article_id}/analyze", summary="重新分析文章")
async def reanalyze_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发重新情感分析"""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    result = sentiment_service.analyze_article(article, db)
    return {"message": "分析完成", "result": result}


@router.get("/manager/{manager_id}/summary", summary="获取管理人舆情摘要")
async def get_manager_summary(
    manager_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取管理人舆情统计摘要"""
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="管理人不存在")

    summary = sentiment_service.get_manager_sentiment_summary(manager_id, db)
    return summary


@router.get("/manager/{manager_id}/timeline", summary="获取管理人舆情时间轴")
async def get_manager_timeline(
    manager_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取管理人舆情时间轴，按时间排序，提取关键事件
    包括：核心人员变动、产品清盘、监管处罚、规模变化、投资踩雷等
    """
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="管理人不存在")

    # 获取所有舆情文章，按时间排序
    articles = db.query(NewsArticle).filter(
        NewsArticle.manager_id == manager_id
    ).order_by(NewsArticle.publish_date.desc()).all()

    # 提取关键事件
    key_events = []
    for a in articles:
        events = a.events or []
        event_types = []
        
        # 检查关键词提取事件类型
        title_content = (a.title or '') + (a.content or '')
        if any(kw in title_content for kw in ['离职', '连任', '变动', '走人']):
            event_types.append('personnel')
        if any(kw in title_content for kw in ['清盘', '清算', '终止']):
            event_types.append('liquidation')
        if any(kw in title_content for kw in ['处罚', '警告', '违规', '监管']):
            event_types.append('penalty')
        if any(kw in title_content for kw in ['规模', '增长', '突破']):
            event_types.append('scale')
        if any(kw in title_content for kw in ['踩雷', '跌停', '暴雷', '地雷']):
            event_types.append('risk')
        if a.is_alert:
            event_types.append('alert')
        
        # 该新闻是关键事件或者已提取事件
        if event_types or events:
            key_events.append({
                "id": a.id,
                "date": str(a.publish_date) if a.publish_date else a.created_at.strftime('%Y-%m-%d') if a.created_at else '',
                "title": a.title,
                "sentiment": a.sentiment,
                "event_types": list(set(event_types + events)),
                "is_alert": a.is_alert,
                "source": a.source,
                "summary": a.summary,
                "url": a.url,
            })
    
    # 事件类型映射
    event_type_labels = {
        'personnel': '人员变动',
        'liquidation': '产品清盘',
        'penalty': '监管处罚',
        'scale': '规模变化',
        'risk': '投资风险',
        'alert': '系统预警',
    }

    return {
        "manager_id": manager_id,
        "manager_name": manager.manager_name,
        "total_events": len(key_events),
        "events": key_events,
        "event_type_labels": event_type_labels,
    }


@router.post("/manager/{manager_id}/batch-analyze", summary="批量分析管理人舆情")
async def batch_analyze(
    manager_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量分析某管理人所有未分析的文章"""
    count = sentiment_service.batch_analyze(manager_id, db)
    return {"message": f"已分析{count}篇文章", "analyzed_count": count}


# ========== 舆情爬取 ==========
@router.post("/crawl/all", summary="手动触发全量舆情爬取")
async def trigger_crawl_all(
    current_user: User = Depends(get_current_user),
):
    """手动触发为所有管理人爬取舆情"""
    from app.services.sentiment_crawler import sentiment_crawler
    result = await sentiment_crawler.crawl_all()
    return {"message": "爬取完成", **result}


@router.post("/crawl/manager/{manager_id}", summary="爬取单个管理人舆情")
async def trigger_crawl_single(
    manager_id: int,
    current_user: User = Depends(get_current_user),
):
    """为指定管理人爬取最新舆情"""
    from app.services.sentiment_crawler import sentiment_crawler
    result = await sentiment_crawler.crawl_single(manager_id)
    return {"message": "爬取完成", **result}
