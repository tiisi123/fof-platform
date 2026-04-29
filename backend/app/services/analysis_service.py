"""
数据分析Service - 计算收益率和风险指标
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal
import math
import pandas as pd
import os

from app.models.nav import NavData
from app.models.product import Product


# 上传文件目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')


def get_nav_from_file(product_code: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
    """
    从文件读取净值数据
    
    Args:
        product_code: 产品代码
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        净值数据列表
    """
    # 查找产品的最新文件
    if not os.path.exists(UPLOAD_DIR):
        return []
    
    files = []
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(f"{product_code}_"):
            files.append(os.path.join(UPLOAD_DIR, filename))
    
    if not files:
        return []
    
    # 使用最新的文件
    latest_file = sorted(files, reverse=True)[0]

    try:
        # 读取Excel文件
        df = pd.read_excel(latest_file)

        # 标准化列名
        df.columns = df.columns.str.strip()
        column_mapping = {
            '产品代码': 'product_code',
            '产品名称': 'product_name',
            '净值日期': 'nav_date',
            '单位净值': 'unit_nav',
            '累计净值': 'cumulative_nav',
            '累计单位净值': 'cumulative_nav'
        }
        df = df.rename(columns=column_mapping)
        
        # 转换日期
        df['nav_date'] = pd.to_datetime(df['nav_date']).dt.date
        
        # 日期过滤
        if start_date:
            df = df[df['nav_date'] >= start_date]
        if end_date:
            df = df[df['nav_date'] <= end_date]
        
        # 排序
        df = df.sort_values('nav_date')
        
        # 转换为字典列表
        result = []
        for _, row in df.iterrows():
            result.append({
                'nav_date': row['nav_date'],
                'unit_nav': float(row['unit_nav']) if pd.notna(row['unit_nav']) else None,
                'cumulative_nav': float(row['cumulative_nav']) if 'cumulative_nav' in row and pd.notna(row['cumulative_nav']) else None
            })
        
        return result
    except Exception as e:
        return []


def get_nav_series(
    db: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[NavData]:
    """
    获取净值序列（优先从文件读取，否则从数据库读取）
    
    Args:
        db: 数据库会话
        product_id: 产品ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        净值数据列表（按日期升序）
    """
    # 获取产品信息
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return []
    
    # 优先从文件读取
    file_data = get_nav_from_file(product.product_code, start_date, end_date)
    if file_data:
        # 将文件数据转换为类似NavData的对象
        class NavDataLike:
            def __init__(self, data):
                self.nav_date = data['nav_date']
                self.unit_nav = data['unit_nav']
                self.cumulative_nav = data['cumulative_nav']
        
        return [NavDataLike(d) for d in file_data if d['unit_nav'] is not None]
    
    # 从数据库读取
    query = db.query(NavData).filter(NavData.product_id == product_id)
    
    if start_date:
        query = query.filter(NavData.nav_date >= start_date)
    if end_date:
        query = query.filter(NavData.nav_date <= end_date)
    
    return query.order_by(NavData.nav_date.asc()).all()


def calculate_return(
    db: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """
    计算收益率
    
    Args:
        db: 数据库会话
        product_id: 产品ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        收益率指标字典
    """
    nav_series = get_nav_series(db, product_id, start_date, end_date)
    
    if len(nav_series) < 2:
        return {
            "total_return": None,
            "annualized_return": None,
            "message": "数据不足，至少需要2个净值数据点"
        }
    
    # 起始和结束净值
    start_nav = float(nav_series[0].unit_nav)
    end_nav = float(nav_series[-1].unit_nav)
    
    # 累计收益率
    total_return = (end_nav - start_nav) / start_nav
    
    # 计算天数
    days = (nav_series[-1].nav_date - nav_series[0].nav_date).days
    
    # 年化收益率
    if days > 0:
        years = days / 365.0
        annualized_return = (1 + total_return) ** (1 / years) - 1
    else:
        annualized_return = None
    
    return {
        "product_id": product_id,
        "start_date": nav_series[0].nav_date,
        "end_date": nav_series[-1].nav_date,
        "days": days,
        "start_nav": start_nav,
        "end_nav": end_nav,
        "total_return": round(total_return * 100, 2),  # 百分比
        "annualized_return": round(annualized_return * 100, 2) if annualized_return else None
    }


def calculate_volatility(
    db: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """
    计算波动率
    
    Args:
        db: 数据库会话
        product_id: 产品ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        波动率指标字典
    """
    nav_series = get_nav_series(db, product_id, start_date, end_date)
    
    if len(nav_series) < 2:
        return {
            "volatility": None,
            "message": "数据不足"
        }
    
    # 计算日收益率
    daily_returns = []
    for i in range(1, len(nav_series)):
        prev_nav = float(nav_series[i-1].unit_nav)
        curr_nav = float(nav_series[i].unit_nav)
        daily_return = (curr_nav - prev_nav) / prev_nav
        daily_returns.append(daily_return)
    
    # 计算标准差
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
    daily_volatility = math.sqrt(variance)
    
    # 年化波动率（假设每年252个交易日）
    annualized_volatility = daily_volatility * math.sqrt(252)
    
    return {
        "product_id": product_id,
        "daily_volatility": round(daily_volatility * 100, 2),
        "annualized_volatility": round(annualized_volatility * 100, 2),
        "data_points": len(nav_series)
    }


def calculate_max_drawdown(
    db: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """
    计算最大回撤
    
    Args:
        db: 数据库会话
        product_id: 产品ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        最大回撤指标字典
    """
    nav_series = get_nav_series(db, product_id, start_date, end_date)
    
    if len(nav_series) < 2:
        return {
            "max_drawdown": None,
            "message": "数据不足"
        }
    
    # 计算最大回撤
    max_drawdown = 0
    peak = float(nav_series[0].unit_nav)
    peak_date = nav_series[0].nav_date
    trough_date = nav_series[0].nav_date
    max_dd_peak_date = peak_date
    max_dd_trough_date = trough_date
    
    for nav_data in nav_series:
        nav_value = float(nav_data.unit_nav)
        
        # 更新峰值
        if nav_value > peak:
            peak = nav_value
            peak_date = nav_data.nav_date
        
        # 计算当前回撤
        drawdown = (peak - nav_value) / peak
        
        # 更新最大回撤
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_dd_peak_date = peak_date
            max_dd_trough_date = nav_data.nav_date
    
    # 计算回撤持续天数
    drawdown_days = (max_dd_trough_date - max_dd_peak_date).days if max_drawdown > 0 else 0
    
    return {
        "product_id": product_id,
        "max_drawdown": round(max_drawdown * 100, 2),  # 百分比
        "peak_date": max_dd_peak_date,
        "trough_date": max_dd_trough_date,
        "drawdown_days": drawdown_days,
        "data_points": len(nav_series)
    }


def calculate_sharpe_ratio(
    db: Session,
    product_id: int,
    risk_free_rate: float = 0.03,  # 无风险利率，默认3%
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """
    计算夏普比率
    
    Args:
        db: 数据库会话
        product_id: 产品ID
        risk_free_rate: 无风险利率（年化）
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        夏普比率字典
    """
    # 获取收益率
    return_data = calculate_return(db, product_id, start_date, end_date)
    if return_data.get("annualized_return") is None:
        return {
            "sharpe_ratio": None,
            "message": "数据不足"
        }
    
    # 获取波动率
    volatility_data = calculate_volatility(db, product_id, start_date, end_date)
    if volatility_data.get("annualized_volatility") is None:
        return {
            "sharpe_ratio": None,
            "message": "数据不足"
        }
    
    # 计算夏普比率
    annualized_return = return_data["annualized_return"] / 100
    annualized_volatility = volatility_data["annualized_volatility"] / 100
    
    if annualized_volatility > 0:
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
    else:
        sharpe_ratio = None
    
    return {
        "product_id": product_id,
        "sharpe_ratio": round(sharpe_ratio, 2) if sharpe_ratio else None,
        "annualized_return": return_data["annualized_return"],
        "annualized_volatility": volatility_data["annualized_volatility"],
        "risk_free_rate": round(risk_free_rate * 100, 2)
    }


def calculate_all_indicators(
    db: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    risk_free_rate: float = 0.03
) -> Dict:
    """
    计算所有指标
    
    Args:
        db: 数据库会话
        product_id: 产品ID
        start_date: 开始日期
        end_date: 结束日期
        risk_free_rate: 无风险利率
    
    Returns:
        所有指标字典（格式与前端期望匹配）
    """
    # 获取产品信息
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "产品不存在"}
    
    # 计算各项指标
    return_data = calculate_return(db, product_id, start_date, end_date)
    volatility_data = calculate_volatility(db, product_id, start_date, end_date)
    drawdown_data = calculate_max_drawdown(db, product_id, start_date, end_date)
    sharpe_data = calculate_sharpe_ratio(db, product_id, risk_free_rate, start_date, end_date)
    
    # 转换百分比为小数（前端会乘以100显示）
    total_return = return_data.get("total_return")
    annualized_return = return_data.get("annualized_return")
    daily_volatility = volatility_data.get("daily_volatility")
    annualized_volatility = volatility_data.get("annualized_volatility")
    max_drawdown = drawdown_data.get("max_drawdown")
    
    # 返回前端期望的数据结构
    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "product_code": product.product_code,
        # 前端期望的格式
        "return_analysis": {
            "cumulative_return": total_return / 100 if total_return is not None else None,
            "annualized_return": annualized_return / 100 if annualized_return is not None else None,
            "period_days": return_data.get("days")
        },
        "volatility_analysis": {
            "volatility": daily_volatility / 100 if daily_volatility is not None else None,
            "annualized_volatility": annualized_volatility / 100 if annualized_volatility is not None else None
        },
        "max_drawdown_analysis": {
            "max_drawdown": max_drawdown / 100 if max_drawdown is not None else None,
            "max_drawdown_start_date": str(drawdown_data.get("peak_date")) if drawdown_data.get("peak_date") else None,
            "max_drawdown_end_date": str(drawdown_data.get("trough_date")) if drawdown_data.get("trough_date") else None,
            "max_drawdown_days": drawdown_data.get("drawdown_days")
        },
        "sharpe_ratio_analysis": {
            "sharpe_ratio": sharpe_data.get("sharpe_ratio"),
            "risk_free_rate": risk_free_rate
        },
        # 保留原有格式以兼容其他调用
        "analysis_period": {
            "start_date": return_data.get("start_date"),
            "end_date": return_data.get("end_date"),
            "days": return_data.get("days")
        },
        "return_indicators": {
            "total_return": total_return,
            "annualized_return": annualized_return
        },
        "risk_indicators": {
            "daily_volatility": daily_volatility,
            "annualized_volatility": annualized_volatility,
            "max_drawdown": max_drawdown,
            "drawdown_peak_date": drawdown_data.get("peak_date"),
            "drawdown_trough_date": drawdown_data.get("trough_date"),
            "drawdown_days": drawdown_data.get("drawdown_days")
        },
        "risk_adjusted_indicators": {
            "sharpe_ratio": sharpe_data.get("sharpe_ratio"),
            "risk_free_rate": sharpe_data.get("risk_free_rate")
        }
    }


def get_chart_data(
    db: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """获取图表数据"""
    nav_series = get_nav_series(db, product_id, start_date, end_date)    
    if not nav_series:
        return {"dates": [], "unit_navs": [], "cumulative_navs": []}
    
    dates = []
    unit_navs = []
    cumulative_navs = []
    
    for nav in nav_series:
        dates.append(nav.nav_date.strftime('%Y-%m-%d'))
        unit_navs.append(float(nav.unit_nav) if nav.unit_nav else None)
        cumulative_navs.append(float(nav.cumulative_nav) if nav.cumulative_nav else None)

    return {"dates": dates, "unit_navs": unit_navs, "cumulative_navs": cumulative_navs}
