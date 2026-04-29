"""
市场排名与分位数服务
计算产品在同策略中的排名和分位数
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from collections import defaultdict
import numpy as np

from app.models.nav import NavData
from app.models.product import Product
from app.models.manager import Manager
from app.services.performance_service import (
    get_nav_series, calculate_return, calculate_daily_returns,
    calculate_volatility, calculate_max_drawdown, calculate_sharpe_ratio,
    calculate_calmar_ratio, get_period_start_date, PERIODS
)


def get_products_by_strategy(db: Session, strategy_type: str = None) -> List[Product]:
    """获取同策略产品列表"""
    query = db.query(Product)
    if strategy_type:
        query = query.filter(Product.strategy_type == strategy_type)
    return query.all()


def calculate_product_indicators(
    db: Session,
    product_id: int,
    end_date: date,
    period: str = '1y',
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """计算单个产品的指标"""
    start_date = get_period_start_date(end_date, period)
    nav_series = get_nav_series(db, product_id, start_date, end_date)
    
    if len(nav_series) < 10:  # 至少需要10个数据点
        return None
    
    return_data = calculate_return(nav_series)
    daily_returns = calculate_daily_returns(nav_series)
    volatility_data = calculate_volatility(daily_returns)
    drawdown_data = calculate_max_drawdown(nav_series)
    
    annualized_return = return_data.get('annualized_return')
    annualized_vol = volatility_data.get('annualized_volatility')
    max_dd = drawdown_data.get('max_drawdown')
    
    if annualized_return is None:
        return None
    
    return {
        'product_id': product_id,
        'total_return': return_data.get('total_return'),
        'annualized_return': annualized_return,
        'annualized_volatility': annualized_vol,
        'max_drawdown': max_dd,
        'sharpe_ratio': calculate_sharpe_ratio(annualized_return, annualized_vol, risk_free_rate),
        'calmar_ratio': calculate_calmar_ratio(annualized_return, max_dd),
        'data_points': len(nav_series)
    }


def calculate_percentile(value: float, all_values: List[float], higher_is_better: bool = True) -> float:
    """
    计算分位数
    
    Args:
        value: 当前值
        all_values: 所有值的列表
        higher_is_better: 值越高越好（收益率），否则值越低越好（回撤）
    
    Returns:
        分位数（0-100，100表示最好）
    """
    if not all_values:
        return None
    
    sorted_values = sorted(all_values)
    n = len(sorted_values)
    
    # 找到value在排序后列表中的位置
    count_below = sum(1 for v in sorted_values if v < value)
    
    if higher_is_better:
        # 值越高，排名越靠前
        percentile = (count_below / n) * 100
    else:
        # 值越低，排名越靠前
        percentile = ((n - count_below - 1) / n) * 100
    
    return round(percentile, 2)


def calculate_rank(value: float, all_values: List[float], higher_is_better: bool = True) -> int:
    """
    计算排名
    
    Args:
        value: 当前值
        all_values: 所有值的列表
        higher_is_better: 值越高越好
    
    Returns:
        排名（1表示第一）
    """
    if not all_values:
        return None
    
    sorted_values = sorted(all_values, reverse=higher_is_better)
    
    for i, v in enumerate(sorted_values):
        if abs(v - value) < 1e-10:  # 浮点数比较
            return i + 1
    
    return len(sorted_values)  # 如果没找到，返回最后


def get_product_ranking(
    db: Session,
    product_id: int,
    period: str = '1y',
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """
    获取产品在同策略中的排名和分位数
    """
    # 获取产品信息
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {'error': '产品不存在'}
    
    # 获取最新净值日期
    latest_nav = db.query(NavData).filter(
        NavData.product_id == product_id
    ).order_by(NavData.nav_date.desc()).first()
    
    if not latest_nav:
        return {'error': '无净值数据'}
    
    end_date = latest_nav.nav_date
    
    # 获取同策略产品
    same_strategy_products = get_products_by_strategy(db, product.strategy_type)
    
    if len(same_strategy_products) < 2:
        return {
            'product_id': product_id,
            'product_name': product.product_name,
            'strategy_type': product.strategy_type,
            'message': '同策略产品数量不足，无法计算排名',
            'peer_count': len(same_strategy_products)
        }
    
    # 计算所有同策略产品的指标
    peer_indicators = []
    target_indicators = None
    
    for p in same_strategy_products:
        indicators = calculate_product_indicators(db, p.id, end_date, period, risk_free_rate)
        if indicators:
            indicators['product_name'] = p.product_name
            indicators['product_code'] = p.product_code
            peer_indicators.append(indicators)
            if p.id == product_id:
                target_indicators = indicators
    
    if not target_indicators:
        return {'error': '目标产品无足够数据'}
    
    if len(peer_indicators) < 2:
        return {
            'product_id': product_id,
            'product_name': product.product_name,
            'strategy_type': product.strategy_type,
            'message': '有效同策略产品数量不足',
            'peer_count': len(peer_indicators)
        }
    
    # 提取各指标值列表
    returns = [p['annualized_return'] for p in peer_indicators if p['annualized_return'] is not None]
    volatilities = [p['annualized_volatility'] for p in peer_indicators if p['annualized_volatility'] is not None]
    drawdowns = [p['max_drawdown'] for p in peer_indicators if p['max_drawdown'] is not None]
    sharpes = [p['sharpe_ratio'] for p in peer_indicators if p['sharpe_ratio'] is not None]
    calmars = [p['calmar_ratio'] for p in peer_indicators if p['calmar_ratio'] is not None]
    
    # 计算排名和分位数
    result = {
        'product_id': product_id,
        'product_code': product.product_code,
        'product_name': product.product_name,
        'strategy_type': product.strategy_type,
        'strategy_name': product.strategy_type,  # 可以添加策略名称映射
        'period': period,
        'period_name': PERIODS.get(period, {}).get('name', period),
        'end_date': str(end_date),
        'peer_count': len(peer_indicators),
        'indicators': {
            'annualized_return': {
                'value': target_indicators['annualized_return'],
                'rank': calculate_rank(target_indicators['annualized_return'], returns, True),
                'percentile': calculate_percentile(target_indicators['annualized_return'], returns, True),
                'total': len(returns)
            },
            'annualized_volatility': {
                'value': target_indicators['annualized_volatility'],
                'rank': calculate_rank(target_indicators['annualized_volatility'], volatilities, False),
                'percentile': calculate_percentile(target_indicators['annualized_volatility'], volatilities, False),
                'total': len(volatilities)
            } if target_indicators['annualized_volatility'] else None,
            'max_drawdown': {
                'value': target_indicators['max_drawdown'],
                'rank': calculate_rank(target_indicators['max_drawdown'], drawdowns, False),
                'percentile': calculate_percentile(target_indicators['max_drawdown'], drawdowns, False),
                'total': len(drawdowns)
            } if target_indicators['max_drawdown'] else None,
            'sharpe_ratio': {
                'value': target_indicators['sharpe_ratio'],
                'rank': calculate_rank(target_indicators['sharpe_ratio'], sharpes, True),
                'percentile': calculate_percentile(target_indicators['sharpe_ratio'], sharpes, True),
                'total': len(sharpes)
            } if target_indicators['sharpe_ratio'] else None,
            'calmar_ratio': {
                'value': target_indicators['calmar_ratio'],
                'rank': calculate_rank(target_indicators['calmar_ratio'], calmars, True),
                'percentile': calculate_percentile(target_indicators['calmar_ratio'], calmars, True),
                'total': len(calmars)
            } if target_indicators['calmar_ratio'] else None,
        }
    }
    
    return result


def get_strategy_ranking_list(
    db: Session,
    strategy_type: str,
    period: str = '1y',
    indicator: str = 'annualized_return',
    limit: int = 20,
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """
    获取策略排行榜
    """
    # 获取同策略产品
    products = get_products_by_strategy(db, strategy_type)
    
    if not products:
        return {
            'strategy_type': strategy_type,
            'items': [],
            'total': 0
        }
    
    # 获取最新有数据的日期
    latest_date = db.query(func.max(NavData.nav_date)).scalar()
    if not latest_date:
        return {
            'strategy_type': strategy_type,
            'items': [],
            'total': 0
        }
    
    # 计算所有产品指标
    indicators_list = []
    for p in products:
        indicators = calculate_product_indicators(db, p.id, latest_date, period, risk_free_rate)
        if indicators and indicators.get(indicator) is not None:
            indicators['product_name'] = p.product_name
            indicators['product_code'] = p.product_code
            # 获取管理人名称
            manager = db.query(Manager).filter(Manager.id == p.manager_id).first()
            indicators['manager_name'] = manager.manager_name if manager else None
            indicators_list.append(indicators)
    
    # 排序（收益率和夏普比率越高越好，回撤和波动率越低越好）
    higher_is_better = indicator in ['annualized_return', 'total_return', 'sharpe_ratio', 'calmar_ratio']
    indicators_list.sort(key=lambda x: x.get(indicator) or -999, reverse=higher_is_better)
    
    # 添加排名
    for i, item in enumerate(indicators_list):
        item['rank'] = i + 1
        # 计算分位数
        all_values = [x.get(indicator) for x in indicators_list if x.get(indicator) is not None]
        item['percentile'] = calculate_percentile(item.get(indicator), all_values, higher_is_better)
    
    return {
        'strategy_type': strategy_type,
        'period': period,
        'period_name': PERIODS.get(period, {}).get('name', period),
        'indicator': indicator,
        'end_date': str(latest_date),
        'items': indicators_list[:limit],
        'total': len(indicators_list)
    }


def get_rolling_percentile(
    db: Session,
    product_id: int,
    indicator: str = 'annualized_return',
    window: int = 252,  # 滚动窗口（交易日数）
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """
    获取滚动分位数走势
    计算产品在每个时间点的同策略分位数
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {'error': '产品不存在'}
    
    # 获取产品净值序列
    nav_series = db.query(NavData).filter(
        NavData.product_id == product_id
    ).order_by(NavData.nav_date).all()
    
    if len(nav_series) < window:
        return {
            'product_id': product_id,
            'product_name': product.product_name,
            'error': '数据不足',
            'required_points': window,
            'actual_points': len(nav_series)
        }
    
    # 获取同策略产品
    same_strategy_products = get_products_by_strategy(db, product.strategy_type)
    
    if len(same_strategy_products) < 2:
        return {
            'product_id': product_id,
            'product_name': product.product_name,
            'error': '同策略产品不足'
        }
    
    # 计算每个时间点的分位数
    percentile_series = []
    
    # 每月计算一次分位数
    check_dates = []
    for i in range(window, len(nav_series), 21):  # 约每月一次
        check_dates.append(nav_series[i].nav_date)
    
    for end_date in check_dates:
        start_date = end_date - timedelta(days=365)  # 用近1年数据
        
        # 计算目标产品指标
        target_nav = get_nav_series(db, product_id, start_date, end_date)
        if len(target_nav) < 20:
            continue
        
        return_data = calculate_return(target_nav)
        target_value = return_data.get('annualized_return') if indicator == 'annualized_return' else return_data.get('total_return')
        
        if target_value is None:
            continue
        
        # 计算同策略所有产品的指标
        all_values = []
        for p in same_strategy_products:
            peer_nav = get_nav_series(db, p.id, start_date, end_date)
            if len(peer_nav) < 20:
                continue
            peer_return = calculate_return(peer_nav)
            peer_value = peer_return.get('annualized_return') if indicator == 'annualized_return' else peer_return.get('total_return')
            if peer_value is not None:
                all_values.append(peer_value)
        
        if len(all_values) < 2:
            continue
        
        percentile = calculate_percentile(target_value, all_values, True)
        
        percentile_series.append({
            'date': str(end_date),
            'percentile': percentile,
            'value': target_value,
            'peer_count': len(all_values)
        })
    
    return {
        'product_id': product_id,
        'product_code': product.product_code,
        'product_name': product.product_name,
        'strategy_type': product.strategy_type,
        'indicator': indicator,
        'series': percentile_series
    }


def get_strategy_distribution(
    db: Session,
    strategy_type: str,
    indicator: str = 'annualized_return',
    period: str = '1y',
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """
    获取策略内指标分布（用于分布图）
    """
    products = get_products_by_strategy(db, strategy_type)
    
    if not products:
        return {
            'strategy_type': strategy_type,
            'indicator': indicator,
            'distribution': []
        }
    
    latest_date = db.query(func.max(NavData.nav_date)).scalar()
    if not latest_date:
        return {
            'strategy_type': strategy_type,
            'indicator': indicator,
            'distribution': []
        }
    
    # 收集所有值
    values = []
    for p in products:
        indicators = calculate_product_indicators(db, p.id, latest_date, period, risk_free_rate)
        if indicators and indicators.get(indicator) is not None:
            values.append({
                'product_id': p.id,
                'product_name': p.product_name,
                'value': indicators[indicator]
            })
    
    if not values:
        return {
            'strategy_type': strategy_type,
            'indicator': indicator,
            'distribution': []
        }
    
    # 计算分布统计
    all_values = [v['value'] for v in values]
    
    return {
        'strategy_type': strategy_type,
        'period': period,
        'indicator': indicator,
        'end_date': str(latest_date),
        'count': len(all_values),
        'statistics': {
            'mean': float(np.mean(all_values)),
            'median': float(np.median(all_values)),
            'std': float(np.std(all_values)),
            'min': float(np.min(all_values)),
            'max': float(np.max(all_values)),
            'q25': float(np.percentile(all_values, 25)),
            'q75': float(np.percentile(all_values, 75))
        },
        'distribution': sorted(values, key=lambda x: x['value'], reverse=True)
    }

