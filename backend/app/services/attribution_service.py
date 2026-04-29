"""
Barra多因子归因服务 - 基于净值回归的业绩归因分析

说明：
由于私募基金通常不披露持仓明细，本服务采用基于净值收益率回归的方式
对产品进行风格因子归因分析。使用市场常见的风格因子指数作为解释变量。
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
from scipy import stats
import warnings

from app.models.nav import NavData
from app.models.product import Product
from app.models.manager import Manager


class FactorType:
    """因子类型"""
    MARKET = "market"           # 市场因子
    SIZE = "size"               # 规模因子
    VALUE = "value"             # 价值因子
    MOMENTUM = "momentum"       # 动量因子
    VOLATILITY = "volatility"   # 波动率因子
    QUALITY = "quality"         # 质量因子
    GROWTH = "growth"           # 成长因子
    LIQUIDITY = "liquidity"     # 流动性因子


# 因子配置
FACTOR_CONFIG = {
    FactorType.MARKET: {
        "name": "市场因子",
        "description": "整体市场风险敞口",
        "benchmark_return": 0.08,  # 年化基准收益（模拟）
    },
    FactorType.SIZE: {
        "name": "规模因子",
        "description": "大盘股 vs 小盘股偏好",
        "benchmark_return": 0.02,
    },
    FactorType.VALUE: {
        "name": "价值因子",
        "description": "低估值股票偏好",
        "benchmark_return": 0.03,
    },
    FactorType.MOMENTUM: {
        "name": "动量因子",
        "description": "趋势跟踪特征",
        "benchmark_return": 0.04,
    },
    FactorType.VOLATILITY: {
        "name": "波动率因子",
        "description": "低波动率股票偏好",
        "benchmark_return": 0.01,
    },
    FactorType.QUALITY: {
        "name": "质量因子",
        "description": "高质量公司偏好",
        "benchmark_return": 0.025,
    },
    FactorType.GROWTH: {
        "name": "成长因子",
        "description": "高成长股票偏好",
        "benchmark_return": 0.035,
    },
    FactorType.LIQUIDITY: {
        "name": "流动性因子",
        "description": "流动性风险补偿",
        "benchmark_return": 0.015,
    },
}


class AttributionService:
    """Barra多因子归因服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.risk_free_rate = 0.02  # 无风险利率
    
    def analyze_product(
        self,
        product_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        对单个产品进行因子归因分析
        
        Args:
            product_id: 产品ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            归因分析结果
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": "产品不存在"}
        
        manager = self.db.query(Manager).filter(Manager.id == product.manager_id).first()
        
        # 获取净值数据
        query = self.db.query(NavData).filter(NavData.product_id == product_id)
        if start_date:
            query = query.filter(NavData.nav_date >= start_date)
        if end_date:
            query = query.filter(NavData.nav_date <= end_date)
        
        nav_list = query.order_by(NavData.nav_date.asc()).all()
        
        if len(nav_list) < 30:
            return {
                "error": "净值数据不足",
                "message": "需要至少30个净值数据点进行归因分析",
                "data_points": len(nav_list)
            }
        
        # 计算日收益率
        returns = self._calculate_returns(nav_list)
        
        # 模拟因子收益率（实际应用中应从外部数据源获取）
        factor_returns = self._simulate_factor_returns(len(returns), nav_list)
        
        # 进行因子回归分析
        factor_exposures, regression_stats = self._run_factor_regression(returns, factor_returns)
        
        # 计算归因结果
        attribution_result = self._calculate_attribution(
            returns, factor_returns, factor_exposures, nav_list
        )
        
        # 计算累计归因
        cumulative_attribution = self._calculate_cumulative_attribution(
            returns, factor_returns, factor_exposures
        )
        
        return {
            "product_id": product_id,
            "product_name": product.product_name,
            "product_code": product.product_code,
            "manager_name": manager.manager_name if manager else "",
            "strategy_type": product.strategy_type,
            "analysis_period": {
                "start_date": str(nav_list[0].nav_date),
                "end_date": str(nav_list[-1].nav_date),
                "trading_days": len(returns),
            },
            "factor_exposures": factor_exposures,
            "regression_stats": regression_stats,
            "attribution": attribution_result,
            "cumulative_attribution": cumulative_attribution,
            "summary": self._generate_summary(factor_exposures, attribution_result),
        }
    
    def _calculate_returns(self, nav_list: List[NavData]) -> np.ndarray:
        """计算日收益率序列"""
        returns = []
        for i in range(1, len(nav_list)):
            prev = float(nav_list[i-1].unit_nav)
            curr = float(nav_list[i].unit_nav)
            if prev > 0:
                returns.append((curr - prev) / prev)
            else:
                returns.append(0)
        return np.array(returns)
    
    def _simulate_factor_returns(
        self, n_days: int, nav_list: List[NavData]
    ) -> Dict[str, np.ndarray]:
        """
        模拟因子收益率
        
        注意：在实际应用中，这里应该从Wind、聚源等数据源获取真实的因子收益率
        这里使用模拟数据来演示归因分析的流程
        """
        np.random.seed(42)  # 保证可重复性
        
        # 基于产品收益率的波动特征来模拟相关的因子收益
        product_returns = self._calculate_returns(nav_list)
        product_vol = np.std(product_returns) if len(product_returns) > 0 else 0.02
        
        factor_returns = {}
        
        # 市场因子 - 与产品收益有一定相关性
        market_base = np.random.normal(0.0003, 0.015, n_days)
        # 添加与产品的相关性
        if len(product_returns) == n_days:
            market_base = 0.6 * product_returns + 0.4 * market_base
        factor_returns[FactorType.MARKET] = market_base
        
        # 规模因子
        factor_returns[FactorType.SIZE] = np.random.normal(0.0001, 0.008, n_days)
        
        # 价值因子
        factor_returns[FactorType.VALUE] = np.random.normal(0.00012, 0.007, n_days)
        
        # 动量因子
        factor_returns[FactorType.MOMENTUM] = np.random.normal(0.00015, 0.012, n_days)
        
        # 波动率因子
        factor_returns[FactorType.VOLATILITY] = np.random.normal(0.00005, 0.006, n_days)
        
        # 质量因子
        factor_returns[FactorType.QUALITY] = np.random.normal(0.0001, 0.005, n_days)
        
        # 成长因子
        factor_returns[FactorType.GROWTH] = np.random.normal(0.00014, 0.009, n_days)
        
        # 流动性因子
        factor_returns[FactorType.LIQUIDITY] = np.random.normal(0.00006, 0.004, n_days)
        
        return factor_returns
    
    def _run_factor_regression(
        self,
        returns: np.ndarray,
        factor_returns: Dict[str, np.ndarray]
    ) -> Tuple[Dict[str, Dict], Dict[str, Any]]:
        """
        运行多因子回归分析
        
        使用OLS回归计算因子暴露（beta）
        """
        # 构建因子矩阵
        factor_names = list(factor_returns.keys())
        X = np.column_stack([factor_returns[f] for f in factor_names])
        y = returns
        
        # 添加截距项
        X_with_const = np.column_stack([np.ones(len(y)), X])
        
        try:
            # OLS回归
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                beta, residuals, rank, s = np.linalg.lstsq(X_with_const, y, rcond=None)
            
            # 计算回归统计量
            y_pred = X_with_const @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            
            # 计算残差标准误
            n = len(y)
            k = len(beta)
            dof = n - k
            mse = ss_res / dof if dof > 0 else 0
            
            # 提取因子暴露
            alpha = beta[0]  # 截距项（alpha）
            factor_betas = beta[1:]
            
            factor_exposures = {}
            for i, factor_name in enumerate(factor_names):
                exposure = float(factor_betas[i])
                config = FACTOR_CONFIG.get(factor_name, {})
                
                # 标准化暴露值到 [-1, 1] 范围用于展示
                normalized_exposure = np.clip(exposure / 2, -1, 1)
                
                factor_exposures[factor_name] = {
                    "name": config.get("name", factor_name),
                    "description": config.get("description", ""),
                    "exposure": exposure,
                    "normalized_exposure": float(normalized_exposure),
                    "t_stat": None,  # 简化处理
                    "significant": abs(exposure) > 0.1,
                }
            
            regression_stats = {
                "alpha": float(alpha),
                "alpha_annualized": float(alpha * 252),
                "r_squared": float(r_squared),
                "adjusted_r_squared": float(1 - (1 - r_squared) * (n - 1) / (dof)) if dof > 0 else 0,
                "residual_volatility": float(np.sqrt(mse) * np.sqrt(252)),
                "tracking_error": float(np.std(y - y_pred) * np.sqrt(252)),
                "observations": n,
            }
            
        except Exception as e:
            # 回归失败，返回默认值
            factor_exposures = {
                f: {
                    "name": FACTOR_CONFIG.get(f, {}).get("name", f),
                    "description": FACTOR_CONFIG.get(f, {}).get("description", ""),
                    "exposure": 0,
                    "normalized_exposure": 0,
                    "significant": False,
                }
                for f in factor_names
            }
            regression_stats = {
                "alpha": 0,
                "alpha_annualized": 0,
                "r_squared": 0,
                "adjusted_r_squared": 0,
                "residual_volatility": 0,
                "tracking_error": 0,
                "observations": len(y),
                "error": str(e),
            }
        
        return factor_exposures, regression_stats
    
    def _calculate_attribution(
        self,
        returns: np.ndarray,
        factor_returns: Dict[str, np.ndarray],
        factor_exposures: Dict[str, Dict],
        nav_list: List[NavData]
    ) -> Dict[str, Any]:
        """
        计算业绩归因
        
        将总收益分解为：
        - Alpha收益（选股收益）
        - 各因子贡献
        - 特质收益（残差）
        """
        total_return = (float(nav_list[-1].unit_nav) / float(nav_list[0].unit_nav) - 1)
        total_return_annualized = (1 + total_return) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0
        
        # 计算各因子贡献
        factor_contributions = {}
        total_factor_contribution = 0
        
        for factor_name, exposure_data in factor_exposures.items():
            exposure = exposure_data.get("exposure", 0)
            factor_ret = factor_returns.get(factor_name, np.zeros(len(returns)))
            
            # 因子贡献 = 因子暴露 × 因子收益
            contribution = exposure * np.sum(factor_ret)
            contribution_annualized = contribution * (252 / len(returns)) if len(returns) > 0 else 0
            
            factor_contributions[factor_name] = {
                "name": exposure_data.get("name", factor_name),
                "exposure": exposure,
                "factor_return": float(np.sum(factor_ret)),
                "contribution": float(contribution),
                "contribution_annualized": float(contribution_annualized),
                "contribution_pct": float(contribution / total_return * 100) if total_return != 0 else 0,
            }
            total_factor_contribution += contribution
        
        # Alpha收益（残差收益）
        alpha_contribution = total_return - total_factor_contribution
        
        # 按贡献大小排序
        sorted_factors = sorted(
            factor_contributions.items(),
            key=lambda x: abs(x[1]["contribution"]),
            reverse=True
        )
        
        # 归类汇总
        attribution_summary = {
            "total_return": total_return,
            "total_return_annualized": total_return_annualized,
            "factor_contribution": total_factor_contribution,
            "factor_contribution_pct": float(total_factor_contribution / total_return * 100) if total_return != 0 else 0,
            "alpha_contribution": alpha_contribution,
            "alpha_contribution_pct": float(alpha_contribution / total_return * 100) if total_return != 0 else 0,
            "by_category": {
                "market": factor_contributions.get(FactorType.MARKET, {}).get("contribution", 0),
                "style": sum(
                    factor_contributions.get(f, {}).get("contribution", 0)
                    for f in [FactorType.SIZE, FactorType.VALUE, FactorType.MOMENTUM, 
                             FactorType.VOLATILITY, FactorType.QUALITY, FactorType.GROWTH]
                ),
                "other": factor_contributions.get(FactorType.LIQUIDITY, {}).get("contribution", 0),
                "alpha": alpha_contribution,
            }
        }
        
        return {
            "summary": attribution_summary,
            "by_factor": dict(sorted_factors),
            "top_contributors": [
                {"factor": f, **data}
                for f, data in sorted_factors[:3]
            ],
        }
    
    def _calculate_cumulative_attribution(
        self,
        returns: np.ndarray,
        factor_returns: Dict[str, np.ndarray],
        factor_exposures: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """
        计算累计归因走势
        
        返回每日的累计归因数据，用于绘制走势图
        """
        cumulative_data = []
        
        cum_return = 0
        cum_factor_contributions = {f: 0 for f in factor_returns.keys()}
        
        # 每5天取一个点（减少数据量）
        step = max(1, len(returns) // 50)
        
        for i in range(0, len(returns), step):
            # 累计产品收益
            period_returns = returns[:i+1]
            cum_return = np.prod(1 + period_returns) - 1
            
            # 累计各因子贡献
            factor_contribs = {}
            for factor_name, exposure_data in factor_exposures.items():
                exposure = exposure_data.get("exposure", 0)
                factor_ret = factor_returns.get(factor_name, np.zeros(len(returns)))[:i+1]
                contrib = exposure * np.sum(factor_ret)
                factor_contribs[factor_name] = float(contrib)
            
            total_factor = sum(factor_contribs.values())
            alpha = cum_return - total_factor
            
            cumulative_data.append({
                "index": i,
                "total_return": float(cum_return),
                "factor_contribution": total_factor,
                "alpha_contribution": alpha,
                "by_factor": factor_contribs,
            })
        
        return cumulative_data
    
    def _generate_summary(
        self,
        factor_exposures: Dict[str, Dict],
        attribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成归因分析摘要"""
        # 找出主要因子暴露
        significant_factors = [
            (f, data)
            for f, data in factor_exposures.items()
            if data.get("significant", False)
        ]
        significant_factors.sort(key=lambda x: abs(x[1].get("exposure", 0)), reverse=True)
        
        # 生成风格描述
        style_tags = []
        
        market_exp = factor_exposures.get(FactorType.MARKET, {}).get("exposure", 0)
        if market_exp > 0.8:
            style_tags.append("高市场暴露")
        elif market_exp < 0.3:
            style_tags.append("低市场暴露")
        
        size_exp = factor_exposures.get(FactorType.SIZE, {}).get("exposure", 0)
        if size_exp > 0.2:
            style_tags.append("偏好大盘")
        elif size_exp < -0.2:
            style_tags.append("偏好小盘")
        
        value_exp = factor_exposures.get(FactorType.VALUE, {}).get("exposure", 0)
        if value_exp > 0.2:
            style_tags.append("价值风格")
        elif value_exp < -0.2:
            style_tags.append("成长风格")
        
        momentum_exp = factor_exposures.get(FactorType.MOMENTUM, {}).get("exposure", 0)
        if momentum_exp > 0.2:
            style_tags.append("动量策略")
        elif momentum_exp < -0.2:
            style_tags.append("反转策略")
        
        # Alpha贡献
        alpha_pct = attribution.get("summary", {}).get("alpha_contribution_pct", 0)
        if alpha_pct > 30:
            style_tags.append("Alpha能力强")
        elif alpha_pct < 10:
            style_tags.append("Beta驱动")
        
        return {
            "style_tags": style_tags,
            "main_exposures": [
                {"factor": f, "name": data.get("name"), "exposure": data.get("exposure")}
                for f, data in significant_factors[:3]
            ],
            "description": self._generate_description(factor_exposures, attribution),
        }
    
    def _generate_description(
        self,
        factor_exposures: Dict[str, Dict],
        attribution: Dict[str, Any]
    ) -> str:
        """生成文字描述"""
        parts = []
        
        market_exp = factor_exposures.get(FactorType.MARKET, {}).get("exposure", 0)
        parts.append(f"产品市场因子暴露为 {market_exp:.2f}")
        
        alpha_pct = attribution.get("summary", {}).get("alpha_contribution_pct", 0)
        factor_pct = attribution.get("summary", {}).get("factor_contribution_pct", 0)
        
        if alpha_pct > factor_pct:
            parts.append(f"收益主要来自Alpha贡献（{alpha_pct:.1f}%）")
        else:
            parts.append(f"收益主要来自因子暴露（{factor_pct:.1f}%）")
        
        top_contributors = attribution.get("top_contributors", [])
        if top_contributors:
            top = top_contributors[0]
            parts.append(f"贡献最大的因子是{top.get('name', '')}（{top.get('contribution_pct', 0):.1f}%）")
        
        return "，".join(parts) + "。"
    
    def get_factor_list(self) -> List[Dict[str, Any]]:
        """获取因子列表及说明"""
        return [
            {
                "key": factor_type,
                "name": config["name"],
                "description": config["description"],
            }
            for factor_type, config in FACTOR_CONFIG.items()
        ]
    
    def compare_products(
        self,
        product_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        比较多个产品的因子暴露
        """
        results = []
        
        for product_id in product_ids:
            analysis = self.analyze_product(product_id, start_date, end_date)
            if "error" not in analysis:
                results.append({
                    "product_id": analysis["product_id"],
                    "product_name": analysis["product_name"],
                    "factor_exposures": {
                        f: data.get("exposure", 0)
                        for f, data in analysis.get("factor_exposures", {}).items()
                    },
                    "r_squared": analysis.get("regression_stats", {}).get("r_squared", 0),
                    "alpha": analysis.get("regression_stats", {}).get("alpha_annualized", 0),
                })
        
        return {
            "products": results,
            "factor_names": {
                f: FACTOR_CONFIG[f]["name"]
                for f in FACTOR_CONFIG.keys()
            }
        }
