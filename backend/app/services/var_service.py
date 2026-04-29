"""
VaR与风险归因服务
"""
import numpy as np
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.logger import logger
from app.models.portfolio import Portfolio, PortfolioNav, PortfolioComponent
from app.models.nav import NavData


def calculate_portfolio_var(
    portfolio_id: int,
    db: Session,
    confidence_level: float = 0.95,
    holding_period: int = 1,
    method: str = "historical",
) -> Dict[str, Any]:
    """
    计算组合VaR

    Args:
        portfolio_id: 组合ID
        confidence_level: 置信水平 (0.95 或 0.99)
        holding_period: 持有期(天)
        method: 方法 historical/parametric

    Returns:
        {var_95, var_99, es_95, daily_returns_stats, ...}
    """
    # 获取组合净值序列
    navs = db.query(PortfolioNav).filter(
        PortfolioNav.portfolio_id == portfolio_id
    ).order_by(asc(PortfolioNav.nav_date)).all()

    if len(navs) < 20:
        return {"error": "净值数据不足(至少需要20个数据点)", "var_95": None, "var_99": None}

    # 计算日收益率
    nav_values = [float(n.unit_nav) for n in navs]
    returns = np.diff(nav_values) / nav_values[:-1]

    if method == "parametric":
        # 参数法: 假设正态分布
        mu = np.mean(returns)
        sigma = np.std(returns, ddof=1)
        var_95 = -(mu - 1.645 * sigma) * np.sqrt(holding_period)
        var_99 = -(mu - 2.326 * sigma) * np.sqrt(holding_period)
    else:
        # 历史模拟法
        sorted_returns = np.sort(returns)
        var_95 = -np.percentile(sorted_returns, (1 - 0.95) * 100) * np.sqrt(holding_period)
        var_99 = -np.percentile(sorted_returns, (1 - 0.99) * 100) * np.sqrt(holding_period)

    # Expected Shortfall (CVaR)
    sorted_returns = np.sort(returns)
    cutoff_95 = int(len(sorted_returns) * 0.05)
    es_95 = -np.mean(sorted_returns[:max(cutoff_95, 1)]) * np.sqrt(holding_period)

    return {
        "var_95": round(float(var_95), 6),
        "var_99": round(float(var_99), 6),
        "es_95": round(float(es_95), 6),
        "confidence_level": confidence_level,
        "holding_period": holding_period,
        "method": method,
        "data_points": len(returns),
        "daily_return_stats": {
            "mean": round(float(np.mean(returns)), 6),
            "std": round(float(np.std(returns, ddof=1)), 6),
            "min": round(float(np.min(returns)), 6),
            "max": round(float(np.max(returns)), 6),
            "skew": round(float(_skewness(returns)), 4),
            "kurtosis": round(float(_kurtosis(returns)), 4),
        },
    }


def calculate_risk_attribution(portfolio_id: int, db: Session) -> Dict[str, Any]:
    """
    组合风险归因 - 计算各成分对组合风险的贡献

    Returns:
        {total_volatility, components: [{name, weight, volatility, risk_contribution, ...}]}
    """
    # 获取组合成分
    components = db.query(PortfolioComponent).filter(
        PortfolioComponent.portfolio_id == portfolio_id
    ).all()

    if not components:
        return {"error": "组合无成分", "total_volatility": None, "components": []}

    result_components = []
    returns_matrix = []
    weights = []

    for comp in components:
        # 获取成分产品的净值
        navs = db.query(NavData).filter(
            NavData.product_id == comp.product_id
        ).order_by(asc(NavData.nav_date)).limit(252).all()

        if len(navs) < 10:
            continue

        nav_values = [float(n.unit_nav) for n in navs]
        rets = list(np.diff(nav_values) / nav_values[:-1])
        returns_matrix.append(rets)
        weights.append(float(comp.weight or 0) / 100.0)

        vol = float(np.std(rets, ddof=1)) * np.sqrt(252)
        result_components.append({
            "product_id": comp.product_id,
            "product_name": comp.product.product_name if comp.product else str(comp.product_id),
            "weight": round(float(comp.weight or 0), 2),
            "annualized_volatility": round(vol, 6),
        })

    if not returns_matrix:
        return {"error": "成分净值数据不足", "total_volatility": None, "components": result_components}

    # 截断到相同长度
    min_len = min(len(r) for r in returns_matrix)
    returns_matrix = [r[:min_len] for r in returns_matrix]

    # 协方差矩阵
    cov_matrix = np.cov(returns_matrix) * 252
    w = np.array(weights[:len(returns_matrix)])

    portfolio_var = float(w @ cov_matrix @ w)
    portfolio_vol = np.sqrt(portfolio_var) if portfolio_var > 0 else 0

    # 边际风险贡献
    if portfolio_vol > 0:
        marginal = cov_matrix @ w / portfolio_vol
        risk_contributions = w * marginal
        for i, comp in enumerate(result_components[:len(w)]):
            comp["risk_contribution"] = round(float(risk_contributions[i]), 6)
            comp["risk_contribution_pct"] = round(float(risk_contributions[i]) / portfolio_vol * 100, 2)

    return {
        "total_volatility": round(portfolio_vol, 6),
        "total_variance": round(portfolio_var, 6),
        "components": result_components,
    }


def _skewness(x):
    n = len(x)
    if n < 3:
        return 0
    m = np.mean(x)
    s = np.std(x, ddof=1)
    if s == 0:
        return 0
    return (n / ((n - 1) * (n - 2))) * np.sum(((x - m) / s) ** 3)


def _kurtosis(x):
    n = len(x)
    if n < 4:
        return 0
    m = np.mean(x)
    s = np.std(x, ddof=1)
    if s == 0:
        return 0
    return ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(((x - m) / s) ** 4) - (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
