"""
舆情自动爬取服务 — 定时从配置的数据源抓取管理人相关新闻
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import SessionLocal
from app.core.logger import logger
from app.models.manager import Manager
from app.models.news_article import NewsArticle
from app.services.sentiment_service import sentiment_service


# ========== 数据源配置 ==========
# 可后续迁移到数据库或配置文件
NEWS_SOURCES = [
    {
        "name": "东方财富搜索",
        "type": "eastmoney",
        "base_url": "https://search-api-web.eastmoney.com/search/jsonp",
        "enabled": True,
    },
    {
        "name": "新浪财经搜索",
        "type": "sina",
        "base_url": "https://search.sina.com.cn/news",
        "enabled": False,  # 默认关闭，需配置
    },
]

# 爬取间隔（秒）
CRAWL_INTERVAL = 4 * 3600  # 默认4小时
_crawler_task: Optional[asyncio.Task] = None


class SentimentCrawler:
    """舆情爬取器"""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.running = False

    async def _get_client(self) -> httpx.AsyncClient:
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    # ========== 核心爬取 ==========
    async def crawl_for_manager(self, manager_name: str, manager_id: int, db: Session) -> int:
        """为单个管理人爬取新闻，返回新增条数"""
        new_count = 0
        articles = await self._fetch_news(manager_name)

        for article_data in articles:
            # 去重：按标题 + 管理人ID判断
            existing = db.query(NewsArticle).filter(
                NewsArticle.manager_id == manager_id,
                NewsArticle.title == article_data["title"],
            ).first()
            if existing:
                continue

            article = NewsArticle(
                title=article_data["title"],
                content=article_data.get("content", ""),
                source=article_data.get("source", "自动爬取"),
                url=article_data.get("url", ""),
                publish_date=article_data.get("publish_date"),
                manager_id=manager_id,
            )
            db.add(article)
            db.commit()
            db.refresh(article)

            # 自动情感分析
            try:
                sentiment_service.analyze_article(article, db)
            except Exception as e:
                logger.warning(f"自动分析失败 article={article.id}: {e}")

            new_count += 1

        return new_count

    async def _fetch_news(self, keyword: str) -> List[Dict[str, Any]]:
        """从配置的数据源获取新闻"""
        results: List[Dict[str, Any]] = []

        for source in NEWS_SOURCES:
            if not source["enabled"]:
                continue
            try:
                if source["type"] == "eastmoney":
                    items = await self._fetch_eastmoney(keyword)
                    results.extend(items)
                # 可扩展更多数据源
            except Exception as e:
                logger.warning(f"爬取 {source['name']} 失败: {e}")

        return results[:10]  # 每次最多10条

    async def _fetch_eastmoney(self, keyword: str) -> List[Dict[str, Any]]:
        """东方财富搜索API"""
        client = await self._get_client()
        try:
            params = {
                "cb": "",
                "param": f'{{"uid":"","keyword":"{keyword}","type":["cmsArticleWebOld"],"client":"web","clientType":"web","clientVersion":"curr","param":{{"cmsArticleWebOld":{{"searchScope":"default","sort":"default","pageIndex":1,"pageSize":5}}}}}}',
            }
            resp = await client.get(
                "https://search-api-web.eastmoney.com/search/jsonp",
                params=params,
            )
            if resp.status_code != 200:
                return []

            # 解析JSONP响应
            text = resp.text.strip()
            if text.startswith("("):
                text = text[1:]
            if text.endswith(")"):
                text = text[:-1]

            import json
            data = json.loads(text)
            result = data.get("result") if isinstance(data, dict) else {}
            if not isinstance(result, dict):
                result = {}
            cms = result.get("cmsArticleWebOld") if isinstance(result, dict) else {}
            if not isinstance(cms, dict):
                cms = {}
            items = cms.get("list", []) if isinstance(cms, dict) else []

            results = []
            for item in items:
                pub_date = None
                if item.get("date"):
                    try:
                        pub_date = datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass

                results.append({
                    "title": item.get("title", "").replace("<em>", "").replace("</em>", ""),
                    "content": item.get("content", "")[:2000],
                    "source": "东方财富",
                    "url": item.get("url", ""),
                    "publish_date": pub_date,
                })

            return results
        except Exception as e:
            logger.warning(f"东方财富API调用失败: {e}")
            return []

    # ========== 全量爬取 ==========
    async def crawl_all(self) -> Dict[str, int]:
        """为所有活跃管理人爬取舆情"""
        db = SessionLocal()
        try:
            managers = db.query(Manager).filter(
                Manager.is_deleted == False,
                Manager.status == "active",
            ).all()

            summary = {"total_managers": len(managers), "new_articles": 0, "errors": 0}

            for mgr in managers:
                try:
                    name = mgr.short_name or mgr.manager_name
                    count = await self.crawl_for_manager(name, mgr.id, db)
                    summary["new_articles"] += count
                    if count > 0:
                        logger.info(f"爬取 {mgr.manager_name}: 新增{count}条")
                except Exception as e:
                    summary["errors"] += 1
                    logger.error(f"爬取 {mgr.manager_name} 失败: {e}")

                # 间隔避免被封
                await asyncio.sleep(1)

            logger.info(f"舆情爬取完成: {summary}")
            return summary
        finally:
            db.close()

    async def crawl_single(self, manager_id: int) -> Dict[str, int]:
        """为单个管理人爬取"""
        db = SessionLocal()
        try:
            mgr = db.query(Manager).filter(Manager.id == manager_id).first()
            if not mgr:
                return {"error": "管理人不存在", "new_articles": 0}

            name = mgr.short_name or mgr.manager_name
            count = await self.crawl_for_manager(name, mgr.id, db)
            return {"manager_name": mgr.manager_name, "new_articles": count}
        finally:
            db.close()


# 全局单例
sentiment_crawler = SentimentCrawler()


# ========== 定时任务 ==========
async def _crawl_loop():
    """后台定时爬取循环"""
    logger.info(f"舆情定时爬取已启动，间隔 {CRAWL_INTERVAL}s")
    # 启动后延迟30秒再开始首次爬取
    await asyncio.sleep(30)
    while True:
        try:
            result = await sentiment_crawler.crawl_all()
            logger.info(f"定时爬取结果: {result}")
        except Exception as e:
            logger.error(f"定时爬取异常: {e}")
        await asyncio.sleep(CRAWL_INTERVAL)


def start_crawler():
    """启动爬取定时任务"""
    global _crawler_task
    if _crawler_task is None or _crawler_task.done():
        _crawler_task = asyncio.create_task(_crawl_loop())
        logger.info("舆情爬取后台任务已创建")


def stop_crawler():
    """停止爬取定时任务"""
    global _crawler_task
    if _crawler_task and not _crawler_task.done():
        _crawler_task.cancel()
        logger.info("舆情爬取后台任务已停止")
    _crawler_task = None
