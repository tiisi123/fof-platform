"""
业绩指标计算服务 - V2升级版
支持多周期计算、完整的风险指标
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import math
import numpy as np
from collections import OrderedDict

from app.models.nav import NavData
from app.models.product import Product


# 时间周期定义
PERIODS = OrderedDict([
    ('1w', {'name': '近1周', 'days': 7}),
    ('1m', {'name': '近1月', 'days': 30}),
    ('3m', {'name': '近3月', 'days': 90}),
    ('6m', {'name': '近6月', 'days': 180}),
    ('1y', {'name': '近1年', 'days': 365}),
    ('ytd', {'name': '今年以来', 'days': None}),  # 特殊处理
    ('inception', {'name': '成立以来', 'days': None}),  # 特殊处理
])


def get_nav_series(
    db: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[NavData]:
    """获取净值序列"""
    query = db.query(NavData).filter(NavData.product_id == product_id)
    
    if start_date:
        query = query.filter(NavData.nav_date >= start_date)
    if end_date:
        query = query.filter(NavData.nav_date <= end_date)
    
    return query.order_by(NavData.nav_date.asc()).all()


def get_period_start_date(end_date: date, period: str) -> Optional[date]:
    """根据周期获取开始日期"""
    if period == 'ytd':
        return date(end_date.year, 1, 1)
    elif period == 'inception':
        return None  # 返回None表示从最早数据开始
    elif period in PERIODS:
        days = PERIODS[period]['days']
        return end_date - timedelta(days=days)
    return None


def calculate_return(nav_series: List[NavData]) -> Dict[str, Any]:
    """计算收益率"""
    if len(nav_series) < 2:
        return {'total_return': None, 'annualized_return': None}
    
    start_nav = float(nav_series[0].unit_nav)
    end_nav = float(nav_series[-1].unit_nav)
    
    if start_nav <= 0:
        return {'total_return': None, 'annualized_return': None}
    
    total_return = (end_nav - start_nav) / start_nav
    days = (nav_series[-1].nav_date - nav_series[0].nav_date).days
    
    if days > 0:
        years = days / 365.0
        annualized_return = (1 + total_return) ** (1 / years) - 1
    else:
        annualized_return = total_return
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'days': days
    }


def calculate_daily_returns(nav_series: List[NavData]) -> List[float]:
    """计算日收益率序列"""
    if len(nav_series) < 2:
        return []
    
    returns = []
    for i in range(1, len(nav_series)):
        prev_nav = float(nav_series[i-1].unit_nav)
        curr_nav = float(nav_series[i].unit_nav)
        if prev_nav > 0:
            returns.append((curr_nav - prev_nav) / prev_nav)
    return returns


def calculate_volatility(daily_returns: List[float]) -> Dict[str, Any]:
    """计算波动率"""
    if len(daily_returns) < 2:
        return {'daily_volatility': None, 'annualized_volatility': None}
    
    returns_array = np.array(daily_returns)
    daily_vol = np.std(returns_array, ddof=1)  # 样本标准差
    annualized_vol = daily_vol * np.sqrt(252)
    
    return {
        'daily_volatility': float(daily_vol),
        'annualized_volatility': float(annualized_vol)
    }


def calculate_downside_volatility(daily_returns: List[float], threshold: float = 0) -> float:
    """计算下行波动率"""
    if len(daily_returns) < 2:
        return None
    
    downside_returns = [r for r in daily_returns if r < threshold]
    if len(downside_returns) < 2:
        return 0.0
    
    returns_array = np.array(downside_returns)
    downside_vol = np.std(returns_array, ddof=1)
    return float(downside_vol * np.sqrt(252))


def calculate_max_drawdown(nav_series: List[NavData]) -> Dict[str, Any]:
    """计算最大回撤"""
    if len(nav_series) < 2:
        return {
            'max_drawdown': None,
            'peak_date': None,
            'trough_date': None,
            'drawdown_days': None,
            'recovery_date': None,
            'recovery_days': None
        }
    
    max_drawdown = 0
    peak = float(nav_series[0].unit_nav)
    peak_date = nav_series[0].nav_date
    trough_date = nav_series[0].nav_date
    max_dd_peak_date = peak_date
    max_dd_trough_date = trough_date
    
    # 用于计算回撤修复
    drawdown_periods = []
    current_dd_start = None
    current_dd_peak = None
    
    for nav_data in nav_series:
        nav_value = float(nav_data.unit_nav)
        
        if nav_value > peak:
            # 新高，记录之前的回撤周期
            if current_dd_start is not None:
                drawdown_periods.append({
                    'start': current_dd_start,
                    'end': nav_data.nav_date,
                    'peak': current_dd_peak
                })
            peak = nav_value
            peak_date = nav_data.nav_date
            current_dd_start = None
            current_dd_peak = None
        else:
            if current_dd_start is None:
                current_dd_start = peak_date
                current_dd_peak = peak
        
        drawdown = (peak - nav_value) / peak
        
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_dd_peak_date = peak_date
            max_dd_trough_date = nav_data.nav_date
    
    # 计算回撤持续天数
    drawdown_days = (max_dd_trough_date - max_dd_peak_date).days if max_drawdown > 0 else 0
    
    # 查找回撤修复日期
    recovery_date = None
    recovery_days = None
    if max_drawdown > 0:
        max_dd_peak_value = None
        for nav_data in nav_series:
            if nav_data.nav_date == max_dd_peak_date:
                max_dd_peak_value = float(nav_data.unit_nav)
            elif nav_data.nav_date > max_dd_trough_date and max_dd_peak_value:
                if float(nav_data.unit_nav) >= max_dd_peak_value:
                    recovery_date = nav_data.nav_date
                    recovery_days = (recovery_date - max_dd_trough_date).days
                    break
    
    return {
        'max_drawdown': max_drawdown,
        'peak_date': max_dd_peak_date,
        'trough_date': max_dd_trough_date,
        'drawdown_days': drawdown_days,
        'recovery_date': recovery_date,
        'recovery_days': recovery_days
    }


def calculate_sharpe_ratio(annualized_return: float, annualized_volatility: float, 
                          risk_free_rate: float = 0.03) -> Optional[float]:
    """计算夏普比率"""
    if annualized_volatility is None or annualized_volatility <= 0:
        return None
    if annualized_return is None:
        return None
    return (annualized_return - risk_free_rate) / annualized_volatility


def calculate_calmar_ratio(annualized_return: float, max_drawdown: float) -> Optional[float]:
    """计算卡玛比率"""
    if max_drawdown is None or max_drawdown <= 0:
        return None
    if annualized_return is None:
        return None
    return annualized_return / max_drawdown


def calculate_sortino_ratio(annualized_return: float, downside_volatility: float,
                           risk_free_rate: float = 0.03) -> Optional[float]:
    """计算索提诺比率"""
    if downside_volatility is None or downside_volatility <= 0:
        return None
    if annualized_return is None:
        return None
    return (annualized_return - risk_free_rate) / downside_volatility


def calculate_win_rate(daily_returns: List[float]) -> Optional[float]:
    """计算胜率（正收益天数占比）"""
    if not daily_returns:
        return None
    positive_days = sum(1 for r in daily_returns if r > 0)
    return positive_days / len(daily_returns)


def calculate_period_performance(
    db: Session,
    product_id: int,
    period: str,
    end_date: Optional[date] = None,
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """
    计算单个周期的业绩指标
    """
    if end_date is None:
        # 获取最新净值日期
        latest = db.query(func.max(NavData.nav_date)).filter(
            NavData.product_id == product_id
        ).scalar()
        end_date = latest if latest else date.today()
    
    start_date = get_period_start_date(end_date, period)
    nav_series = get_nav_series(db, product_id, start_date, end_date)
    
    if len(nav_series) < 2:
        return {
            'period': period,
            'period_name': PERIODS.get(period, {}).get('name', period),
            'data_points': len(nav_series),
            'has_data': False
        }
    
    # 计算各项指标
    return_data = calculate_return(nav_series)
    daily_returns = calculate_daily_returns(nav_series)
    volatility_data = calculate_volatility(daily_returns)
    drawdown_data = calculate_max_drawdown(nav_series)
    downside_vol = calculate_downside_volatility(daily_returns)
    
    annualized_return = return_data.get('annualized_return')
    annualized_vol = volatility_data.get('annualized_volatility')
    max_dd = drawdown_data.get('max_drawdown')
    
    return {
        'period': period,
        'period_name': PERIODS.get(period, {}).get('name', period),
        'start_date': str(nav_series[0].nav_date),
        'end_date': str(nav_series[-1].nav_date),
        'days': return_data.get('days'),
        'data_points': len(nav_series),
        'has_data': True,
        # 收益指标
        'total_return': return_data.get('total_return'),
        'annualized_return': annualized_return,
        # 风险指标
        'daily_volatility': volatility_data.get('daily_volatility'),
        'annualized_volatility': annualized_vol,
        'downside_volatility': downside_vol,
        'max_drawdown': max_dd,
        'drawdown_peak_date': str(drawdown_data.get('peak_date')) if drawdown_data.get('peak_date') else None,
        'drawdown_trough_date': str(drawdown_data.get('trough_date')) if drawdown_data.get('trough_date') else None,
        'drawdown_days': drawdown_data.get('drawdown_days'),
        'recovery_days': drawdown_data.get('recovery_days'),
        # 风险调整收益
        'sharpe_ratio': calculate_sharpe_ratio(annualized_return, annualized_vol, risk_free_rate),
        'calmar_ratio': calculate_calmar_ratio(annualized_return, max_dd),
        'sortino_ratio': calculate_sortino_ratio(annualized_return, downside_vol, risk_free_rate),
        # 其他指标
        'win_rate': calculate_win_rate(daily_returns)
    }


def calculate_multi_period_performance(
    db: Session,
    product_id: int,
    periods: List[str] = None,
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """
    计算多周期业绩指标
    """
    if periods is None:
        periods = list(PERIODS.keys())
    
    # 获取产品信息
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {'error': '产品不存在'}
    
    # 获取最新净值日期
    latest_nav = db.query(NavData).filter(
        NavData.product_id == product_id
    ).order_by(NavData.nav_date.desc()).first()
    
    if not latest_nav:
        return {
            'product_id': product_id,
            'product_code': product.product_code,
            'product_name': product.product_name,
            'error': '无净值数据'
        }
    
    end_date = latest_nav.nav_date
    
    # 计算各周期指标
    period_data = {}
    for period in periods:
        period_data[period] = calculate_period_performance(
            db, product_id, period, end_date, risk_free_rate
        )
    
    return {
        'product_id': product_id,
        'product_code': product.product_code,
        'product_name': product.product_name,
        'latest_nav': float(latest_nav.unit_nav),
        'latest_cumulative_nav': float(latest_nav.cumulative_nav) if latest_nav.cumulative_nav else None,
        'latest_nav_date': str(latest_nav.nav_date),
        'risk_free_rate': risk_free_rate,
        'periods': period_data
    }


def get_performance_summary(
    db: Session,
    product_id: int,
    risk_free_rate: float = 0.03
) -> Dict[str, Any]:
    """
    获取业绩摘要（用于产品卡片展示）
    """
    result = calculate_multi_period_performance(
        db, product_id, 
        periods=['1m', '3m', '6m', '1y', 'inception'],
        risk_free_rate=risk_free_rate
    )
    
    if 'error' in result and result.get('error') == '产品不存在':
        return result
    
    # 提取关键指标用于展示
    inception_data = result.get('periods', {}).get('inception', {})
    
    summary = {
        'product_id': result.get('product_id'),
        'product_code': result.get('product_code'),
        'product_name': result.get('product_name'),
        'latest_nav': result.get('latest_nav'),
        'latest_cumulative_nav': result.get('latest_cumulative_nav'),
        'latest_nav_date': result.get('latest_nav_date'),
        # 成立以来的关键指标
        'total_return': inception_data.get('total_return'),
        'annualized_return': inception_data.get('annualized_return'),
        'annualized_volatility': inception_data.get('annualized_volatility'),
        'max_drawdown': inception_data.get('max_drawdown'),
        'sharpe_ratio': inception_data.get('sharpe_ratio'),
        'calmar_ratio': inception_data.get('calmar_ratio'),
        # 各周期收益率
        'returns_by_period': {
            period: data.get('total_return')
            for period, data in result.get('periods', {}).items()
            if data.get('has_data')
        }
    }
    
    return summary


def compare_products_performance(
    db: Session,
    product_ids: List[int],
    period: str = 'inception',
    risk_free_rate: float = 0.03
) -> List[Dict[str, Any]]:
    """
    比较多个产品的业绩
    """
    results = []
    for product_id in product_ids:
        perf = calculate_period_performance(db, product_id, period, risk_free_rate=risk_free_rate)
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            perf['product_code'] = product.product_code
            perf['product_name'] = product.product_name
        
        results.append(perf)
    
    # 按年化收益率排序
    results.sort(key=lambda x: x.get('annualized_return') or -999, reverse=True)
    
    return results
