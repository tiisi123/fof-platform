"""
市场排名与分位数API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.ranking_service import (
    get_product_ranking,
    get_strategy_ranking_list,
    get_rolling_percentile,
    get_strategy_distribution
)

router = APIRouter()


@router.get("/product/{product_id}")
async def get_product_ranking_api(
    product_id: int,
    period: str = Query("1y", description="分析周期: 1m/3m/6m/1y/ytd/inception"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品在同策略中的排名和分位数
    """
    result = get_product_ranking(db, product_id, period)
    return result


@router.get("/strategy/{strategy_type}")
async def get_strategy_ranking_api(
    strategy_type: str,
    period: str = Query("1y", description="分析周期"),
    indicator: str = Query("annualized_return", description="排名指标"),
    limit: int = Query(50, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取策略排行榜
    """
    result = get_strategy_ranking_list(
        db, strategy_type, period, indicator, limit
    )
    return result


@router.get("/rolling/{product_id}")
async def get_rolling_percentile_api(
    product_id: int,
    indicator: str = Query("annualized_return", description="指标"),
    window: int = Query(252, description="滚动窗口"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取滚动分位数走势
    """
    result = get_rolling_percentile(db, product_id, indicator, window)
    return result


@router.get("/distribution/{strategy_type}")
async def get_distribution_api(
    strategy_type: str,
    period: str = Query("1y", description="分析周期"),
    indicator: str = Query("annualized_return", description="指标"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取策略内指标分布
    """
    result = get_strategy_distribution(db, strategy_type, indicator, period)
    return result


@router.get("/strategies")
async def get_strategy_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有策略类型列表
    """
    from app.models.product import Product
    from sqlalchemy import distinct
    
    strategies = db.query(distinct(Product.strategy_type)).filter(
        Product.strategy_type != None,
        Product.status != "liquidated"
    ).all()
    
    strategy_list = [s[0] for s in strategies if s[0]]
    
    # 策略名称映射
    strategy_names = {
        'equity_long': '股票多头',
        'equity_hedge': '股票对冲',
        'quant_neutral': '量化中性',
        'cta': 'CTA策略',
        'bond': '债券策略',
        'multi_strategy': '多策略',
        'macro': '宏观策略',
        'event_driven': '事件驱动',
        'fof': 'FOF',
        'arbitrage': '套利策略',
        'other': '其他'
    }
    
    return {
        'strategies': [
            {
                'value': s,
                'label': strategy_names.get(s, s)
            }
            for s in strategy_list
        ]
    }
