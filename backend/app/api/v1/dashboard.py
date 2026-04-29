"""
Dashboard API - 总览页面聚合接口

优化：一次请求获取所有Dashboard数据，减少请求次数
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.manager import Manager
from app.models.product import Product
from app.models.project import Project
from app.models.portfolio import Portfolio, PortfolioNav
from app.models.task import Task, TaskStatus
from app.services import manager_service, product_service, project_service

router = APIRouter()


@router.get("/summary", summary="获取Dashboard汇总数据")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    一次性获取Dashboard所有数据，减少请求次数
    
    包括：
    - 管理人统计
    - 产品统计
    - 项目统计
    - 组合列表（含最新净值）
    - 任务统计
    
    优化：
    - 使用单次查询获取统计数据
    - 避免N+1查询问题
    - 返回预处理好的数据
    """
    
    # 1. 管理人统计（优化：使用单次查询）
    manager_stats_raw = db.query(
        func.count(Manager.id).label('total'),
        func.sum(case((Manager.pool_category == 'invested', 1), else_=0)).label('invested'),
        func.sum(case((Manager.pool_category == 'key_tracking', 1), else_=0)).label('key_tracking'),
        func.sum(case((Manager.pool_category == 'observation', 1), else_=0)).label('observation'),
    ).filter(Manager.is_deleted == False).first()
    
    # 策略统计
    strategy_stats = db.query(
        Manager.primary_strategy,
        func.count(Manager.id)
    ).filter(Manager.is_deleted == False).group_by(Manager.primary_strategy).all()
    
    manager_stats = {
        "total": manager_stats_raw.total or 0,
        "by_pool": [
            {"category": "invested", "count": manager_stats_raw.invested or 0},
            {"category": "key_tracking", "count": manager_stats_raw.key_tracking or 0},
            {"category": "observation", "count": manager_stats_raw.observation or 0},
        ],
        "by_strategy": {s: c for s, c in strategy_stats if s}
    }
    
    # 2. 产品统计
    product_stats = product_service.get_product_statistics(db)
    
    # 3. 项目统计
    project_stats = project_service.get_project_statistics(db)
    
    # 4. 组合列表（只查询基本信息和最新净值）
    portfolios_query = db.query(Portfolio).filter(
        Portfolio.status == 'active'
    ).limit(10).all()
    
    portfolios = []
    for pf in portfolios_query:
        # 获取最新净值
        latest_nav = db.query(PortfolioNav).filter(
            PortfolioNav.portfolio_id == pf.id
        ).order_by(PortfolioNav.nav_date.desc()).first()
        
        # 获取成分数量
        from app.models.portfolio import PortfolioHolding
        component_count = db.query(func.count(func.distinct(PortfolioHolding.product_id))).filter(
            PortfolioHolding.portfolio_id == pf.id
        ).scalar() or 0
        
        portfolios.append({
            "id": pf.id,
            "name": pf.name,
            "portfolio_type": pf.portfolio_type,
            "latest_nav": float(latest_nav.unit_nav) if latest_nav else None,
            "total_return": float(latest_nav.cumulative_return) if latest_nav else None,
            "component_count": component_count
        })
    
    # 5. 任务统计（直接查询）
    from sqlalchemy import or_
    from datetime import date
    
    total_tasks = db.query(Task).count()
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
    
    # 我的待办
    my_pending = db.query(Task).filter(
        or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id),
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
    ).count()
    
    # 逾期任务
    overdue = db.query(Task).filter(
        Task.due_date < date.today(),
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
    ).count()
    
    task_stats = {
        "total": total_tasks,
        "pending": pending_tasks,
        "in_progress": in_progress_tasks,
        "completed": completed_tasks,
        "my_pending": my_pending,
        "overdue": overdue
    }
    
    # 6. 预警摘要（简化版，只返回数量）
    # TODO: 实现预警系统后补充
    alert_summary = {
        "by_level": {
            "critical": 0,
            "warning": 0,
            "info": 0
        },
        "alerts": []
    }
    
    return {
        "manager_stats": manager_stats,
        "product_stats": product_stats,
        "project_stats": project_stats,
        "portfolios": portfolios,
        "task_stats": task_stats,
        "alert_summary": alert_summary,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/portfolio-nav-compare", summary="组合净值对比（优化版）")
async def get_portfolio_nav_compare(
    period: str = Query('6m', description="时间周期: 3m, 6m, 1y, inception"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    一次性获取所有组合的净值对比数据
    
    优化：
    1. 使用单次SQL查询获取所有组合净值
    2. 在内存中计算绩效指标
    3. 返回预处理好的图表数据
    """
    from app.core.logger import logger
    logger.info(f"获取组合净值对比，周期: {period}")
    
    # 获取所有活跃组合
    portfolios = db.query(Portfolio).filter(
        Portfolio.status == 'active'
    ).limit(10).all()
    
    logger.info(f"找到 {len(portfolios)} 个活跃组合")
    
    if not portfolios:
        return {
            "portfolios": [],
            "nav_series": {},
            "performance": {},
            "timestamp": datetime.now().isoformat()
        }
    
    # 计算起始日期
    start_date = _get_period_start_date(period)
    logger.info(f"起始日期: {start_date}")
    
    # 一次性查询所有组合的净值数据
    portfolio_ids = [p.id for p in portfolios]
    nav_data = db.query(PortfolioNav).filter(
        PortfolioNav.portfolio_id.in_(portfolio_ids)
    )
    
    if start_date:
        nav_data = nav_data.filter(PortfolioNav.nav_date >= start_date)
    
    nav_data = nav_data.order_by(
        PortfolioNav.portfolio_id,
        PortfolioNav.nav_date
    ).all()
    
    logger.info(f"查询到 {len(nav_data)} 条净值数据")
    
    # 组织数据
    nav_series = {}
    performance = {}
    
    for pf in portfolios:
        pf_navs = [n for n in nav_data if n.portfolio_id == pf.id]
        
        if not pf_navs:
            continue
        
        # 净值序列
        dates = [n.nav_date.strftime('%Y-%m-%d') for n in pf_navs]
        values = [float(n.unit_nav) for n in pf_navs]
        
        nav_series[pf.id] = {
            "name": pf.name,
            "dates": dates,
            "values": values
        }
        
        # 计算绩效指标
        perf = _calculate_performance(pf_navs, period)
        performance[pf.id] = {
            "name": pf.name,
            "type": pf.portfolio_type,
            "nav": f"{values[-1]:.4f}" if values else None,
            "total_return": perf["total_return"],
            "annualized_return": perf["annualized_return"],
            "volatility": perf["volatility"],
            "max_drawdown": perf["max_drawdown"],
            "sharpe": perf["sharpe"]
        }
    
    return {
        "portfolios": [{"id": p.id, "name": p.name, "type": p.portfolio_type} for p in portfolios],
        "nav_series": nav_series,
        "performance": performance,
        "timestamp": datetime.now().isoformat()
    }


def _get_period_start_date(period: str) -> Optional[datetime]:
    """计算周期起始日期"""
    if period == 'inception':
        return None
    
    today = datetime.now()
    if period == '3m':
        return today - timedelta(days=90)
    elif period == '6m':
        return today - timedelta(days=180)
    elif period == '1y':
        return today - timedelta(days=365)
    else:
        return today - timedelta(days=180)  # 默认6个月


def _calculate_performance(nav_list: list, period: str) -> dict:
    """计算绩效指标"""
    import numpy as np
    
    if not nav_list or len(nav_list) < 2:
        return {
            "total_return": None,
            "annualized_return": None,
            "volatility": None,
            "max_drawdown": None,
            "sharpe": None
        }
    
    # 提取净值和收益率
    navs = [float(n.unit_nav) for n in nav_list]
    returns = [float(n.daily_return) if n.daily_return else 0 for n in nav_list[1:]]
    
    # 累计收益率
    total_return = (navs[-1] / navs[0] - 1) if navs[0] > 0 else 0
    
    # 年化收益率
    days = (nav_list[-1].nav_date - nav_list[0].nav_date).days
    if days > 0:
        annualized_return = (1 + total_return) ** (365 / days) - 1
    else:
        annualized_return = 0
    
    # 波动率（年化）
    if len(returns) > 1:
        volatility = np.std(returns) * np.sqrt(252)
    else:
        volatility = 0
    
    # 最大回撤
    max_drawdown = 0
    peak = navs[0]
    for nav in navs:
        if nav > peak:
            peak = nav
        drawdown = (peak - nav) / peak if peak > 0 else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # 夏普比率（假设无风险利率2%）
    risk_free_rate = 0.02
    if volatility > 0:
        sharpe = (annualized_return - risk_free_rate) / volatility
    else:
        sharpe = 0
    
    return {
        "total_return": round(total_return, 6),
        "annualized_return": round(annualized_return, 6),
        "volatility": round(volatility, 6),
        "max_drawdown": round(max_drawdown, 6),
        "sharpe": round(sharpe, 2)
    }
