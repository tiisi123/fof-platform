"""
AI智能报告生成服务 - 自动生成产品/管理人/组合分析报告
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np

from app.models.nav import NavData
from app.models.product import Product
from app.models.manager import Manager
from app.models.portfolio import Portfolio, PortfolioComponent
from app.services import performance_service
from app.services.alert_service import AlertService, AlertLevel
from app.services.llm_service import llm_service
from app.core.logger import logger


class ReportType:
    """报告类型"""
    PRODUCT = "product"           # 产品分析报告
    MANAGER = "manager"           # 管理人分析报告
    PORTFOLIO = "portfolio"       # 组合分析报告
    MARKET = "market"             # 市场概览报告


class AIReportService:
    """AI智能报告生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.alert_service = AlertService(db)
        
        # 策略名称映射
        self.strategy_map = {
            "equity_long": "股票多头", "quant_neutral": "量化中性", "cta": "CTA",
            "arbitrage": "套利", "multi_strategy": "多策略", "bond": "债券", "other": "其他"
        }
        
        # 跟踪池映射
        self.pool_map = {
            "invested": "在投池", "key_tracking": "重点跟踪池", "observation": "观察池",
            "eliminated": "淘汰池", "contacted": "已看过"
        }
    
    def generate_product_report(self, product_id: int) -> Dict[str, Any]:
        """
        生成产品分析报告
        
        Args:
            product_id: 产品ID
        
        Returns:
            报告内容字典
        """
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"error": "产品不存在"}
            
            manager = self.db.query(Manager).filter(Manager.id == product.manager_id).first()
            
            # 获取业绩数据
            metrics = self._get_multi_period_metrics(product_id)
            
            # 获取净值数据
            nav_data = self._get_nav_summary(product_id)
            
            # 获取预警信息
            try:
                alerts = self.alert_service.check_product(product_id)
            except Exception:
                alerts = []
            
            # 生成分析文本
            analysis = self._generate_product_analysis(product, manager, metrics, nav_data, alerts)
            
            # 构建报告
            report = {
                "type": ReportType.PRODUCT,
                "generated_at": datetime.now().isoformat(),
                "title": f"{product.product_name} 分析报告",
                "summary": self._generate_product_summary(product, metrics, alerts),
                "basic_info": {
                    "product_name": product.product_name,
                    "product_code": product.product_code,
                    "manager_name": manager.manager_name if manager else "",
                    "strategy_type": self.strategy_map.get(product.strategy_type, product.strategy_type or ""),
                    "inception_date": str(product.established_date) if product.established_date else None,
                },
                "nav_summary": nav_data,
                "performance": metrics,
                "alerts": {
                    "total": len(alerts),
                    "critical": sum(1 for a in alerts if a.get("level") == AlertLevel.CRITICAL),
                    "warning": sum(1 for a in alerts if a.get("level") == AlertLevel.WARNING),
                    "items": alerts[:5],  # 最多展示5条
                },
                "analysis": analysis,
                "recommendations": self._generate_product_recommendations(product, metrics, alerts),
            }
            
            return report
        except Exception as e:
            logger.error(f"生成产品报告失败: {e}")
            return {"error": f"生成报告失败: {str(e)}"}
    
    def generate_manager_report(self, manager_id: int) -> Dict[str, Any]:
        """
        生成管理人分析报告
        
        Args:
            manager_id: 管理人ID
        
        Returns:
            报告内容字典
        """
        try:
            manager = self.db.query(Manager).filter(Manager.id == manager_id).first()
            if not manager:
                return {"error": "管理人不存在"}
            
            # 获取旗下产品
            products = self.db.query(Product).filter(Product.manager_id == manager_id).all()
            
            # 选取代表产品：取净值数据最多的产品作为代表
            representative = None
            if products:
                from app.models.nav import NavData
                best_count = 0
                for prod in products:
                    cnt = self.db.query(func.count(NavData.id)).filter(NavData.product_id == prod.id).scalar() or 0
                    if cnt > best_count:
                        best_count = cnt
                        representative = prod
            
            # 产品业绩汇总
            products_summary = []
            for prod in products:
                metrics = self._get_multi_period_metrics(prod.id)
                products_summary.append({
                    "product_name": prod.product_name,
                    "product_code": prod.product_code,
                    "is_representative": (prod.id == representative.id) if representative else False,
                    "metrics": metrics.get("1y", {}),
                })
            
            # 代表产品详细分析
            rep_metrics = {}
            rep_alerts = []
            if representative:
                rep_metrics = self._get_multi_period_metrics(representative.id)
                try:
                    rep_alerts = self.alert_service.check_product(representative.id)
                except Exception:
                    rep_alerts = []
            
            # 生成分析
            analysis = self._generate_manager_analysis(manager, products, representative, rep_metrics)
            
            report = {
                "type": ReportType.MANAGER,
                "generated_at": datetime.now().isoformat(),
                "title": f"{manager.manager_name} 管理人分析报告",
                "summary": self._generate_manager_summary(manager, products, rep_metrics),
                "basic_info": {
                    "manager_name": manager.manager_name,
                    "short_name": manager.short_name,
                    "manager_code": manager.manager_code,
                    "primary_strategy": self.strategy_map.get(manager.primary_strategy, manager.primary_strategy or ""),
                    "pool_category": self.pool_map.get(manager.pool_category, manager.pool_category or ""),
                    "aum_range": manager.aum_range,
                    "registration_no": manager.registration_no,
                    "established_date": str(manager.established_date) if manager.established_date else None,
                    "product_count": len(products),
                },
                "products": products_summary,
                "representative_product": {
                    "product_name": representative.product_name if representative else None,
                    "metrics": rep_metrics,
                    "alerts_count": len(rep_alerts),
                } if representative else None,
                "analysis": analysis,
                "recommendations": self._generate_manager_recommendations(manager, products, rep_metrics, rep_alerts),
            }
            
            return report
        except Exception as e:
            logger.error(f"生成管理人报告失败: {e}")
            return {"error": f"生成报告失败: {str(e)}"}
    
    def generate_portfolio_report(self, portfolio_id: int) -> Dict[str, Any]:
        """
        生成组合分析报告
        
        Args:
            portfolio_id: 组合ID
        
        Returns:
            报告内容字典
        """
        try:
            portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not portfolio:
                return {"error": "组合不存在"}
            
            # 获取成分
            components = self.db.query(PortfolioComponent).filter(
                PortfolioComponent.portfolio_id == portfolio_id
            ).all()
            
            # 成分详情
            components_detail = []
            total_alerts = 0
            
            for comp in components:
                product = self.db.query(Product).filter(Product.id == comp.product_id).first()
                if product:
                    manager = self.db.query(Manager).filter(Manager.id == product.manager_id).first()
                    metrics = self._get_multi_period_metrics(product.id)
                    try:
                        alerts = self.alert_service.check_product(product.id)
                    except Exception:
                        alerts = []
                    total_alerts += len(alerts)
                    
                    components_detail.append({
                        "product_id": product.id,
                        "product_name": product.product_name,
                        "manager_name": manager.manager_name if manager else "",
                        "strategy_type": self.strategy_map.get(product.strategy_type, ""),
                        "weight": float(comp.weight),
                        "metrics": metrics.get("1y", {}),
                        "alerts_count": len(alerts),
                    })
            
            # 计算加权收益
            weighted_return = sum(
                (c["metrics"].get("total_return", 0) or 0) * c["weight"]
                for c in components_detail
            )
            
            # 策略分布
            strategy_dist = {}
            for comp in components_detail:
                st = comp.get("strategy_type", "其他")
                if st not in strategy_dist:
                    strategy_dist[st] = 0
                strategy_dist[st] += comp["weight"]
            
            analysis = self._generate_portfolio_analysis(portfolio, components_detail, weighted_return)
            
            report = {
                "type": ReportType.PORTFOLIO,
                "generated_at": datetime.now().isoformat(),
                "title": f"{portfolio.name} 组合分析报告",
                "summary": f"组合包含 {len(components)} 个产品，加权年化收益 {weighted_return*100:.2f}%",
                "basic_info": {
                    "name": portfolio.name,
                    "description": portfolio.description,
                    "component_count": len(components),
                    "created_at": str(portfolio.created_at.date()) if portfolio.created_at else None,
                },
                "components": components_detail,
                "strategy_distribution": strategy_dist,
                "performance": {
                    "weighted_return_1y": weighted_return,
                },
                "alerts": {
                    "total": total_alerts,
                },
                "analysis": analysis,
                "recommendations": self._generate_portfolio_recommendations(portfolio, components_detail),
            }
            
            return report
        except Exception as e:
            logger.error(f"生成组合报告失败: {e}")
            return {"error": f"生成报告失败: {str(e)}"}
    
    def generate_market_overview(self) -> Dict[str, Any]:
        """
        生成市场概览报告
        
        Returns:
            报告内容字典
        """
        try:
            # 统计各策略产品数量和平均业绩
            strategy_stats = {}
            
            for strategy_code, strategy_name in self.strategy_map.items():
                products = self.db.query(Product).filter(
                    Product.strategy_type == strategy_code
                ).all()
                
                if not products:
                    continue
                
                returns = []
                for prod in products:
                    metrics = self._get_multi_period_metrics(prod.id)
                    ret = metrics.get("1y", {}).get("total_return")
                    if ret is not None:
                        returns.append(ret)
                
                if returns:
                    strategy_stats[strategy_name] = {
                        "count": len(products),
                        "avg_return": float(np.mean(returns)),
                        "median_return": float(np.median(returns)),
                        "best_return": float(max(returns)),
                        "worst_return": float(min(returns)),
                    }
            
            # 跟踪池分布
            pool_stats = {}
            for pool_code, pool_name in self.pool_map.items():
                count = self.db.query(func.count(Manager.id)).filter(
                    Manager.pool_category == pool_code,
                    Manager.is_deleted == False
                ).scalar()
                pool_stats[pool_name] = count
            
            # 预警统计
            try:
                alerts_summary = self.alert_service.get_alerts_summary()
            except Exception:
                alerts_summary = {"total": 0, "by_level": {}, "alerts": []}
            
            analysis = self._generate_market_analysis(strategy_stats, pool_stats, alerts_summary)
            
            report = {
                "type": ReportType.MARKET,
                "generated_at": datetime.now().isoformat(),
                "title": "市场概览分析报告",
                "summary": self._generate_market_summary(strategy_stats, alerts_summary),
                "strategy_stats": strategy_stats,
                "pool_distribution": pool_stats,
                "alerts_summary": {
                    "total": alerts_summary.get("total", 0),
                    "critical": alerts_summary.get("by_level", {}).get(AlertLevel.CRITICAL, 0),
                    "warning": alerts_summary.get("by_level", {}).get(AlertLevel.WARNING, 0),
                },
                "analysis": analysis,
                "recommendations": self._generate_market_recommendations(strategy_stats, alerts_summary),
            }
            
            return report
        except Exception as e:
            logger.error(f"生成市场报告失败: {e}")
            return {"error": f"生成报告失败: {str(e)}"}
    
    # ========== 辅助方法 ==========
    
    def _get_multi_period_metrics(self, product_id: int) -> Dict[str, Dict]:
        """获取多周期业绩指标"""
        result = {}
        periods = ["1m", "3m", "6m", "1y", "ytd"]
        
        for period in periods:
            try:
                end_date = date.today()
                start_date = performance_service.get_period_start_date(end_date, period)
                nav_series = performance_service.get_nav_series(self.db, product_id, start_date, end_date)
                
                if len(nav_series) < 2:
                    continue
                
                daily_returns = performance_service.calculate_daily_returns(nav_series)
                return_data = performance_service.calculate_return(nav_series)
                vol_data = performance_service.calculate_volatility(daily_returns)
                dd_data = performance_service.calculate_max_drawdown(nav_series)
                
                metrics = {
                    "total_return": return_data.get("total_return"),
                    "annualized_return": return_data.get("annualized_return"),
                    "annualized_volatility": vol_data.get("annualized_volatility"),
                    "max_drawdown": dd_data.get("max_drawdown"),
                }
                
                # 夏普比率
                if metrics["annualized_return"] and metrics["annualized_volatility"] and metrics["annualized_volatility"] > 0:
                    metrics["sharpe_ratio"] = (metrics["annualized_return"] - 0.02) / metrics["annualized_volatility"]
                
                # 卡玛比率
                if metrics["annualized_return"] and metrics["max_drawdown"] and metrics["max_drawdown"] > 0:
                    metrics["calmar_ratio"] = metrics["annualized_return"] / metrics["max_drawdown"]
                
                result[period] = metrics
            except:
                pass
        
        return result
    
    def _get_nav_summary(self, product_id: int) -> Dict:
        """获取净值摘要"""
        latest = self.db.query(NavData).filter(
            NavData.product_id == product_id
        ).order_by(NavData.nav_date.desc()).first()
        
        earliest = self.db.query(NavData).filter(
            NavData.product_id == product_id
        ).order_by(NavData.nav_date.asc()).first()
        
        nav_count = self.db.query(func.count(NavData.id)).filter(
            NavData.product_id == product_id
        ).scalar()
        
        return {
            "latest_date": str(latest.nav_date) if latest else None,
            "latest_nav": float(latest.unit_nav) if latest else None,
            "earliest_date": str(earliest.nav_date) if earliest else None,
            "earliest_nav": float(earliest.unit_nav) if earliest else None,
            "data_points": nav_count,
        }
    
    def _generate_product_summary(self, product: Product, metrics: Dict, alerts: List) -> str:
        """生成产品摘要"""
        parts = []
        
        m_1y = metrics.get("1y", {})
        ret = m_1y.get("total_return")
        if ret is not None:
            parts.append(f"近1年收益 {ret*100:.2f}%")
        
        dd = m_1y.get("max_drawdown")
        if dd is not None:
            parts.append(f"最大回撤 {dd*100:.2f}%")
        
        sharpe = m_1y.get("sharpe_ratio")
        if sharpe is not None:
            parts.append(f"夏普比率 {sharpe:.2f}")
        
        critical = sum(1 for a in alerts if a.get("level") == AlertLevel.CRITICAL)
        if critical > 0:
            parts.append(f"⚠️ {critical} 条严重预警")
        
        return "，".join(parts) if parts else "暂无足够数据"
    
    def _try_llm_analysis(self, data_context: str, analysis_type: str) -> Optional[List[Dict]]:
        """尝试使用LLM生成分析，失败返回None"""
        system_prompt = """你是一位专业的FOF投资分析师。请根据提供的数据生成专业、简洁的分析。
输出要求：
- 返回JSON数组格式: [{"title": "段落标题", "content": "分析内容"}]
- 包含3-5个段落
- 语言专业但易懂
- 数据引用准确
- 包含明确的判断和建议
- 只返回JSON数组，不要添加其他文字"""

        prompt = f"请为以下{analysis_type}数据生成专业分析:\n\n{data_context}"

        try:
            content = llm_service.generate_text(prompt, system_prompt=system_prompt, temperature=0.5)
            if not content:
                return None
            
            # 尝试解析JSON
            import json
            # 处理可能的markdown代码块包裹
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            
            sections = json.loads(cleaned)
            if isinstance(sections, list) and all(isinstance(s, dict) and "title" in s and "content" in s for s in sections):
                return sections
            return None
        except Exception as e:
            logger.warning(f"LLM分析解析失败: {e}")
            return None

    def _build_product_data_context(self, product, manager, metrics, nav_data, alerts) -> str:
        """构建产品分析的数据上下文"""
        lines = []
        lines.append(f"产品名称: {product.product_name}")
        if manager:
            lines.append(f"管理人: {manager.manager_name}")
        if product.strategy_type:
            lines.append(f"策略: {self.strategy_map.get(product.strategy_type, product.strategy_type)}")
        if product.established_date:
            lines.append(f"成立日期: {product.established_date}, 运作{(date.today()-product.established_date).days}天")
        if nav_data.get("latest_nav"):
            lines.append(f"最新净值: {nav_data['latest_nav']} ({nav_data.get('latest_date','')})")
            lines.append(f"数据点数: {nav_data.get('data_points', 0)}")
        for period in ["1m", "3m", "6m", "1y", "ytd"]:
            m = metrics.get(period, {})
            if m:
                parts = [f"近{period}指标:"]
                if m.get("total_return") is not None: parts.append(f"收益{m['total_return']*100:.2f}%")
                if m.get("max_drawdown") is not None: parts.append(f"最大回撤{m['max_drawdown']*100:.2f}%")
                if m.get("sharpe_ratio") is not None: parts.append(f"夏普{m['sharpe_ratio']:.2f}")
                if m.get("annualized_volatility") is not None: parts.append(f"波动率{m['annualized_volatility']*100:.2f}%")
                lines.append(" ".join(parts))
        if alerts:
            critical = [a for a in alerts if a.get("level") == AlertLevel.CRITICAL]
            warning = [a for a in alerts if a.get("level") == AlertLevel.WARNING]
            lines.append(f"预警: 严重{len(critical)}条, 警告{len(warning)}条")
            for a in alerts[:3]:
                lines.append(f"  - [{a.get('level','')}] {a.get('title','')}")
        return "\n".join(lines)

    def _generate_product_analysis(self, product, manager, metrics, nav_data, alerts) -> List[Dict]:
        """生成产品分析段落 - 优先使用LLM，失败回退规则引擎"""
        # 尝试LLM
        data_ctx = self._build_product_data_context(product, manager, metrics, nav_data, alerts)
        llm_result = self._try_llm_analysis(data_ctx, "产品分析")
        if llm_result:
            return llm_result

        # 规则引擎降级
        sections = []
        
        basic_text = f"{product.product_name}"
        if manager:
            basic_text += f"由{manager.manager_name}管理"
        if product.strategy_type:
            basic_text += f"，采用{self.strategy_map.get(product.strategy_type, product.strategy_type)}策略"
        if product.established_date:
            days = (date.today() - product.established_date).days
            basic_text += f"，成立已{days}天"
        sections.append({"title": "基本情况", "content": basic_text})
        
        m_1y = metrics.get("1y", {})
        perf_parts = []
        ret_1y = m_1y.get("total_return")
        if ret_1y is not None:
            label = "表现优异" if ret_1y > 0.15 else "表现良好" if ret_1y > 0.05 else "表现平稳" if ret_1y > 0 else "业绩承压"
            perf_parts.append(f"近1年收益率 {ret_1y*100:.2f}%，{label}")
        dd = m_1y.get("max_drawdown")
        if dd is not None:
            label = "风险控制出色" if dd < 0.05 else "风险可控" if dd < 0.15 else "需关注下行风险"
            perf_parts.append(f"最大回撤 {dd*100:.2f}%，{label}")
        sharpe = m_1y.get("sharpe_ratio")
        if sharpe is not None:
            label = "风险调整后收益优秀" if sharpe > 1.5 else "风险收益比良好" if sharpe > 0.5 else "风险收益比一般"
            perf_parts.append(f"夏普比率 {sharpe:.2f}，{label}")
        if perf_parts:
            sections.append({"title": "业绩分析", "content": "。".join(perf_parts) + "。"})
        
        if alerts:
            critical_alerts = [a for a in alerts if a.get("level") == AlertLevel.CRITICAL]
            warning_alerts = [a for a in alerts if a.get("level") == AlertLevel.WARNING]
            risk_parts = []
            if critical_alerts:
                risk_parts.append(f"存在 {len(critical_alerts)} 条严重预警，包括：" + "、".join(a["title"] for a in critical_alerts[:3]))
            if warning_alerts:
                risk_parts.append(f"存在 {len(warning_alerts)} 条一般预警")
            if risk_parts:
                sections.append({"title": "风险提示", "content": "。".join(risk_parts) + "。"})
        
        return sections
    
    def _generate_product_recommendations(self, product, metrics, alerts) -> List[str]:
        """生成产品建议"""
        recommendations = []
        
        m_1y = metrics.get("1y", {})
        
        # 基于业绩
        ret = m_1y.get("total_return")
        dd = m_1y.get("max_drawdown")
        sharpe = m_1y.get("sharpe_ratio")
        
        if ret is not None and ret < 0:
            recommendations.append("产品近1年收益为负，建议密切关注后续表现，评估是否调整配置")
        
        if dd is not None and dd > 0.2:
            recommendations.append("最大回撤超过20%，建议关注产品风控措施和回撤修复能力")
        
        if sharpe is not None and sharpe < 0.5:
            recommendations.append("夏普比率较低，风险调整后收益一般，建议与同策略产品对比分析")
        
        # 基于预警
        critical = sum(1 for a in alerts if a.get("level") == AlertLevel.CRITICAL)
        if critical > 0:
            recommendations.append(f"存在{critical}条严重预警，建议及时与管理人沟通了解情况")
        
        no_update = [a for a in alerts if a.get("type") == "no_update"]
        if no_update:
            recommendations.append("产品净值长期未更新，建议跟进净值披露情况")
        
        if not recommendations:
            recommendations.append("产品整体表现正常，建议保持定期跟踪")
        
        return recommendations
    
    def _generate_manager_summary(self, manager, products, rep_metrics) -> str:
        """生成管理人摘要"""
        parts = [f"旗下 {len(products)} 只产品"]
        
        if rep_metrics:
            m_1y = rep_metrics.get("1y", {})
            ret = m_1y.get("total_return")
            if ret is not None:
                parts.append(f"代表产品近1年收益 {ret*100:.2f}%")
        
        if manager.pool_category:
            parts.append(f"分类：{self.pool_map.get(manager.pool_category, manager.pool_category)}")
        
        return "，".join(parts)
    
    def _generate_manager_analysis(self, manager, products, representative, rep_metrics) -> List[Dict]:
        """生成管理人分析 - 优先LLM，降级规则引擎"""
        # 构建数据上下文
        lines = [
            f"管理人: {manager.manager_name}",
            f"策略: {self.strategy_map.get(manager.primary_strategy, manager.primary_strategy or '')}",
            f"规模: {manager.aum_range or '未知'}",
            f"分类: {self.pool_map.get(manager.pool_category, manager.pool_category or '')}",
            f"产品数: {len(products)}",
        ]
        if representative and rep_metrics:
            m_1y = rep_metrics.get("1y", {})
            lines.append(f"代表产品: {representative.product_name}")
            if m_1y.get("total_return") is not None:
                lines.append(f"代表产品近1年收益: {m_1y['total_return']*100:.2f}%")
            if m_1y.get("sharpe_ratio") is not None:
                lines.append(f"代表产品夏普: {m_1y['sharpe_ratio']:.2f}")
        
        llm_result = self._try_llm_analysis("\n".join(lines), "管理人分析")
        if llm_result:
            return llm_result

        # 规则引擎降级
        sections = []
        basic_text = f"{manager.manager_name}"
        if manager.primary_strategy:
            basic_text += f"，主策略为{self.strategy_map.get(manager.primary_strategy, manager.primary_strategy)}"
        if manager.aum_range:
            basic_text += f"，管理规模{manager.aum_range}"
        basic_text += f"，旗下共有 {len(products)} 只产品"
        sections.append({"title": "管理人概况", "content": basic_text})
        
        if representative and rep_metrics:
            m_1y = rep_metrics.get("1y", {})
            rep_text = f"代表产品{representative.product_name}"
            ret = m_1y.get("total_return")
            if ret is not None: rep_text += f"，近1年收益 {ret*100:.2f}%"
            sharpe = m_1y.get("sharpe_ratio")
            if sharpe is not None: rep_text += f"，夏普比率 {sharpe:.2f}"
            sections.append({"title": "代表产品", "content": rep_text})
        
        return sections
    
    def _generate_manager_recommendations(self, manager, products, rep_metrics, rep_alerts) -> List[str]:
        """生成管理人建议"""
        recommendations = []
        
        if manager.pool_category == "invested":
            recommendations.append("已在投管理人，建议保持定期沟通和业绩跟踪")
        elif manager.pool_category == "key_tracking":
            recommendations.append("重点跟踪管理人，建议持续关注并适时推进合作")
        elif manager.pool_category == "observation":
            recommendations.append("观察池管理人，建议继续收集信息评估投资价值")
        
        if rep_metrics:
            m_1y = rep_metrics.get("1y", {})
            ret = m_1y.get("total_return")
            if ret is not None and ret > 0.15:
                recommendations.append("代表产品业绩优异，可考虑加大配置或新增产品")
        
        critical = sum(1 for a in rep_alerts if a.get("level") == AlertLevel.CRITICAL)
        if critical > 0:
            recommendations.append("代表产品存在严重预警，建议及时了解原因")
        
        if not recommendations:
            recommendations.append("建议保持常规跟踪频率")
        
        return recommendations
    
    def _generate_portfolio_analysis(self, portfolio, components, weighted_return) -> List[Dict]:
        """生成组合分析 - 优先LLM，降级规则引擎"""
        # 构建数据上下文
        lines = [f"组合名称: {portfolio.name}", f"成分数: {len(components)}", f"加权收益: {weighted_return*100:.2f}%"]
        for c in components:
            m = c.get("metrics", {})
            ret = m.get("total_return")
            lines.append(f"  - {c['product_name']}({c.get('strategy_type','')}): 权重{c['weight']*100:.1f}%, 收益{ret*100:.2f}%" if ret is not None else f"  - {c['product_name']}: 权重{c['weight']*100:.1f}%")
        
        llm_result = self._try_llm_analysis("\n".join(lines), "组合分析")
        if llm_result:
            return llm_result

        # 规则引擎降级
        sections = []
        sections.append({"title": "组合概况", "content": f"{portfolio.name}组合包含 {len(components)} 个成分产品，加权收益率 {weighted_return*100:.2f}%"})
        weights = [c["weight"] for c in components]
        max_weight = max(weights) if weights else 0
        top3_weight = sum(sorted(weights, reverse=True)[:3])
        conc_label = "集中度较高" if max_weight > 0.3 else "配置较为分散"
        sections.append({"title": "集中度分析", "content": f"最大成分权重 {max_weight*100:.1f}%，前三大成分合计 {top3_weight*100:.1f}%，{conc_label}"})
        return sections
    
    def _generate_portfolio_recommendations(self, portfolio, components) -> List[str]:
        """生成组合建议"""
        recommendations = []
        
        # 预警检查
        alerts_products = [c for c in components if c.get("alerts_count", 0) > 0]
        if alerts_products:
            recommendations.append(f"组合中 {len(alerts_products)} 个产品存在预警，建议逐一检查")
        
        # 集中度检查
        weights = [c["weight"] for c in components]
        if weights and max(weights) > 0.4:
            recommendations.append("单一产品权重超过40%，建议考虑分散配置")
        
        # 策略多样性
        strategies = set(c.get("strategy_type") for c in components)
        if len(strategies) < 2:
            recommendations.append("组合策略单一，可考虑增加不同策略产品提升分散度")
        
        if not recommendations:
            recommendations.append("组合配置合理，建议定期审视和再平衡")
        
        return recommendations
    
    def _generate_market_summary(self, strategy_stats, alerts_summary) -> str:
        """生成市场摘要"""
        parts = []
        
        total_products = sum(s.get("count", 0) for s in strategy_stats.values())
        parts.append(f"共跟踪 {total_products} 只产品")
        
        # 找出表现最好的策略
        best_strategy = None
        best_return = -float('inf')
        for name, stats in strategy_stats.items():
            avg = stats.get("avg_return", 0)
            if avg > best_return:
                best_return = avg
                best_strategy = name
        
        if best_strategy and best_return > 0:
            parts.append(f"{best_strategy}策略平均收益最高（{best_return*100:.2f}%）")
        
        alert_total = alerts_summary.get("total", 0)
        if alert_total > 0:
            parts.append(f"当前 {alert_total} 条预警")
        
        return "，".join(parts)
    
    def _generate_market_analysis(self, strategy_stats, pool_stats, alerts_summary) -> List[Dict]:
        """生成市场分析 - 优先LLM，降级规则引擎"""
        lines = ["市场概览数据:"]
        for name, stats in strategy_stats.items():
            lines.append(f"  {name}: {stats['count']}只, 平均收益{stats.get('avg_return',0)*100:.2f}%, 中位数{stats.get('median_return',0)*100:.2f}%")
        lines.append("跟踪池:")
        for name, count in pool_stats.items():
            if count > 0: lines.append(f"  {name}: {count}家")
        alert_total = alerts_summary.get("total", 0)
        if alert_total:
            lines.append(f"预警总数: {alert_total}")
        
        llm_result = self._try_llm_analysis("\n".join(lines), "市场概览分析")
        if llm_result:
            return llm_result

        # 规则引擎降级
        sections = []
        if strategy_stats:
            strategy_lines = []
            for name, stats in sorted(strategy_stats.items(), key=lambda x: x[1].get("avg_return", 0), reverse=True):
                avg = stats.get("avg_return", 0)
                strategy_lines.append(f"{name}（{stats['count']}只）：平均收益 {avg*100:.2f}%")
            sections.append({"title": "策略表现对比", "content": "；".join(strategy_lines)})
        pool_lines = [f"{name} {count}家" for name, count in pool_stats.items() if count > 0]
        if pool_lines:
            sections.append({"title": "跟踪池分布", "content": "、".join(pool_lines)})
        return sections
    
    def _generate_market_recommendations(self, strategy_stats, alerts_summary) -> List[str]:
        """生成市场建议"""
        recommendations = []
        
        # 基于预警
        critical = alerts_summary.get("by_level", {}).get(AlertLevel.CRITICAL, 0)
        if critical > 0:
            recommendations.append(f"当前有 {critical} 条严重预警，建议优先处理")
        
        # 基于策略表现
        for name, stats in strategy_stats.items():
            avg = stats.get("avg_return", 0)
            if avg < -0.05:
                recommendations.append(f"{name}策略整体表现较弱，建议关注持仓产品风险")
        
        if not recommendations:
            recommendations.append("市场整体平稳，建议保持正常监控频率")
        
        return recommendations
