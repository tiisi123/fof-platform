"""
数据分析相关API - V2升级版
支持多周期业绩分析、市场排名与分位数
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services import analysis_service
from app.services import performance_service
from app.services import ranking_service

router = APIRouter()


@router.get("/return/{product_id}", summary="计算收益率")
async def calculate_return(
    product_id: int = Path(..., description="产品ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算产品收益率
    
    - **product_id**: 产品ID
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    
    返回指标：
    - 累计收益率
    - 年化收益率
    """
    return analysis_service.calculate_return(db, product_id, start_date, end_date)


@router.get("/volatility/{product_id}", summary="计算波动率")
async def calculate_volatility(
    product_id: int = Path(..., description="产品ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算产品波动率
    
    - **product_id**: 产品ID
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    
    返回指标：
    - 日波动率
    - 年化波动率
    """
    return analysis_service.calculate_volatility(db, product_id, start_date, end_date)


@router.get("/drawdown/{product_id}", summary="计算最大回撤")
async def calculate_max_drawdown(
    product_id: int = Path(..., description="产品ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算产品最大回撤
    
    - **product_id**: 产品ID
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    
    返回指标：
    - 最大回撤
    - 回撤峰值日期
    - 回撤谷底日期
    - 回撤持续天数
    """
    return analysis_service.calculate_max_drawdown(db, product_id, start_date, end_date)


@router.get("/sharpe/{product_id}", summary="计算夏普比率")
async def calculate_sharpe_ratio(
    product_id: int = Path(..., description="产品ID"),
    risk_free_rate: float = Query(0.03, description="无风险利率（年化）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算产品夏普比率
    
    - **product_id**: 产品ID
    - **risk_free_rate**: 无风险利率（默认3%）
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    
    返回指标：
    - 夏普比率
    - 年化收益率
    - 年化波动率
    """
    return analysis_service.calculate_sharpe_ratio(
        db, product_id, risk_free_rate, start_date, end_date
    )


@router.get("/all/{product_id}", summary="计算所有指标")
async def calculate_all_indicators(
    product_id: int = Path(..., description="产品ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    risk_free_rate: float = Query(0.03, description="无风险利率（年化）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算产品所有分析指标
    
    - **product_id**: 产品ID
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    - **risk_free_rate**: 无风险利率（默认3%）
    
    返回所有指标：
    - 收益率指标（累计收益率、年化收益率）
    - 风险指标（波动率、最大回撤）
    - 风险调整收益指标（夏普比率）
    """
    return analysis_service.calculate_all_indicators(
        db, product_id, start_date, end_date, risk_free_rate
    )


# 兼容前端请求格式的路由
@router.get("/{product_id}/all", summary="计算所有指标(兼容)")
async def calculate_all_indicators_v2(
    product_id: int = Path(..., description="产品ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    risk_free_rate: float = Query(0.03, description="无风险利率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """计算产品所有分析指标"""
    return analysis_service.calculate_all_indicators(
        db, product_id, start_date, end_date, risk_free_rate
    )


@router.get("/{product_id}/chart-data", summary="获取图表数据")
async def get_chart_data(
    product_id: int = Path(..., description="产品ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取产品净值图表数据"""
    return analysis_service.get_chart_data(db, product_id, start_date, end_date)


# ============ V2 多周期业绩分析接口 ============

@router.get("/performance/{product_id}", summary="获取多周期业绩指标")
async def get_multi_period_performance(
    product_id: int = Path(..., description="产品ID"),
    periods: Optional[str] = Query(None, description="周期列表，逗号分隔，如: 1w,1m,3m,6m,1y,ytd,inception"),
    risk_free_rate: float = Query(0.03, description="无风险利率（年化）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品多周期业绩指标
    
    - **product_id**: 产品ID
    - **periods**: 周期列表（可选），支持: 1w(近1周), 1m(近1月), 3m(近3月), 6m(近6月), 1y(近1年), ytd(今年以来), inception(成立以来)
    - **risk_free_rate**: 无风险利率（默认3%）
    
    返回每个周期的指标：
    - 收益率（累计、年化）
    - 波动率（日、年化、下行）
    - 最大回撤
    - 夏普比率、卡玛比率、索提诺比率
    - 胜率
    """
    period_list = periods.split(',') if periods else None
    return performance_service.calculate_multi_period_performance(
        db, product_id, period_list, risk_free_rate
    )


@router.get("/performance/{product_id}/summary", summary="获取业绩摘要")
async def get_performance_summary(
    product_id: int = Path(..., description="产品ID"),
    risk_free_rate: float = Query(0.03, description="无风险利率（年化）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品业绩摘要（用于卡片展示）
    
    返回关键指标：
    - 最新净值
    - 成立以来收益率、年化收益率
    - 年化波动率、最大回撤
    - 夏普比率、卡玛比率
    - 各周期收益率
    """
    return performance_service.get_performance_summary(db, product_id, risk_free_rate)


@router.get("/performance/{product_id}/period/{period}", summary="获取单周期业绩指标")
async def get_period_performance(
    product_id: int = Path(..., description="产品ID"),
    period: str = Path(..., description="周期: 1w/1m/3m/6m/1y/ytd/inception"),
    risk_free_rate: float = Query(0.03, description="无风险利率（年化）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品单个周期的业绩指标
    """
    return performance_service.calculate_period_performance(
        db, product_id, period, risk_free_rate=risk_free_rate
    )


@router.post("/performance/compare", summary="比较多产品业绩")
async def compare_products_performance(
    product_ids: List[int],
    period: str = Query('inception', description="比较周期"),
    risk_free_rate: float = Query(0.03, description="无风险利率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    比较多个产品的业绩
    
    - **product_ids**: 产品ID列表
    - **period**: 比较周期（默认成立以来）
    
    返回按年化收益率排序的产品业绩列表
    """
    return performance_service.compare_products_performance(
        db, product_ids, period, risk_free_rate
    )


# ============ V2 市场排名与分位数接口 ============

@router.get("/ranking/{product_id}", summary="获取产品市场排名")
async def get_product_ranking(
    product_id: int = Path(..., description="产品ID"),
    period: str = Query('1y', description="周期: 1w/1m/3m/6m/1y/ytd/inception"),
    risk_free_rate: float = Query(0.03, description="无风险利率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品在同策略中的排名和分位数
    
    - **product_id**: 产品ID
    - **period**: 计算周期
    
    返回各指标的排名、分位数和同策略产品数量
    """
    return ranking_service.get_product_ranking(db, product_id, period, risk_free_rate)


@router.get("/ranking/strategy/{strategy_type}", summary="获取策略排行榜")
async def get_strategy_ranking_list(
    strategy_type: str = Path(..., description="策略类型"),
    period: str = Query('1y', description="周期"),
    indicator: str = Query('annualized_return', description="排序指标: annualized_return/sharpe_ratio/max_drawdown"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    risk_free_rate: float = Query(0.03, description="无风险利率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取策略排行榜
    
    - **strategy_type**: 策略类型（如：股票多头、量化对冲等）
    - **period**: 计算周期
    - **indicator**: 排序指标
    - **limit**: 返回数量
    
    返回按指定指标排序的产品列表
    """
    return ranking_service.get_strategy_ranking_list(
        db, strategy_type, period, indicator, limit, risk_free_rate
    )


@router.get("/ranking/{product_id}/rolling", summary="获取滚动分位数走势")
async def get_rolling_percentile(
    product_id: int = Path(..., description="产品ID"),
    indicator: str = Query('annualized_return', description="指标"),
    window: int = Query(252, description="滚动窗口（交易日数）"),
    risk_free_rate: float = Query(0.03, description="无风险利率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品滚动分位数走势
    
    - **product_id**: 产品ID
    - **indicator**: 计算指标
    - **window**: 滚动窗口大小
    
    返回每个时间点的分位数序列
    """
    return ranking_service.get_rolling_percentile(
        db, product_id, indicator, window, risk_free_rate
    )


@router.get("/distribution/{strategy_type}", summary="获取策略指标分布")
async def get_strategy_distribution(
    strategy_type: str = Path(..., description="策略类型"),
    indicator: str = Query('annualized_return', description="指标"),
    period: str = Query('1y', description="周期"),
    risk_free_rate: float = Query(0.03, description="无风险利率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取策略内指标分布统计
    
    - **strategy_type**: 策略类型
    - **indicator**: 统计指标
    - **period**: 计算周期
    
    返回分布统计（均值、中位数、标准差、四分位等）和所有产品列表
    """
    return ranking_service.get_strategy_distribution(
        db, strategy_type, indicator, period, risk_free_rate
    )
