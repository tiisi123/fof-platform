"""
组合管理服务
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import numpy as np

from app.models.portfolio import (
    Portfolio, PortfolioComponent, PortfolioAdjustment,
    PortfolioHolding, PortfolioNav
)
from app.models.holdings_detail import HoldingsDetail
from app.models.product import Product
from app.models.nav import NavData
from app.models.manager import Manager
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, ComponentCreate, ComponentUpdate,
    PortfolioNavPoint, ComponentContribution, AdjustmentCreate,
    HoldingCreate, HoldingsBatchCreate, HoldingResponse
)


class PortfolioService:
    """组合管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ 组合CRUD ============
    
    def create_portfolio(self, data: PortfolioCreate, user_id: int = None) -> Portfolio:
        """创建组合"""
        portfolio = Portfolio(
            portfolio_code=data.portfolio_code,
            name=data.name,
            portfolio_type=data.portfolio_type or "invested",
            description=data.description,
            benchmark_code=data.benchmark_code,
            benchmark_name=data.benchmark_name,
            start_date=data.start_date,
            initial_amount=data.initial_amount,
            created_by=user_id,
            status="active"
        )
        self.db.add(portfolio)
        self.db.flush()
        
        # 添加成分
        if data.components:
            for comp in data.components:
                component = PortfolioComponent(
                    portfolio_id=portfolio.id,
                    product_id=comp.product_id,
                    weight=comp.weight,
                    join_date=comp.join_date or data.start_date,
                    is_active=True
                )
                self.db.add(component)
        
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """获取组合详情"""
        return self.db.query(Portfolio).options(
            joinedload(Portfolio.components).joinedload(PortfolioComponent.product).joinedload(Product.manager)
        ).filter(
            Portfolio.id == portfolio_id,
            Portfolio.is_deleted == False
        ).first()
    
    def get_portfolios(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str = None,
        search: str = None
    ) -> Tuple[List[Portfolio], int]:
        """获取组合列表"""
        query = self.db.query(Portfolio).options(
            joinedload(Portfolio.components)
        ).filter(Portfolio.is_deleted == False)
        
        if status:
            query = query.filter(Portfolio.status == status)
        
        if search:
            query = query.filter(Portfolio.name.ilike(f"%{search}%"))
        
        total = self.db.query(Portfolio).filter(Portfolio.is_deleted == False).count()
        if status:
            total = self.db.query(Portfolio).filter(Portfolio.is_deleted == False, Portfolio.status == status).count()
        if search:
            total = self.db.query(Portfolio).filter(Portfolio.is_deleted == False, Portfolio.name.ilike(f"%{search}%")).count()
        
        portfolios = query.order_by(Portfolio.created_at.desc()).offset(skip).limit(limit).all()
        
        return portfolios, total
    
    def update_portfolio(self, portfolio_id: int, data: PortfolioUpdate) -> Optional[Portfolio]:
        """更新组合"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.is_deleted == False
        ).first()
        
        if not portfolio:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(portfolio, key, value)
        
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio
    
    def delete_portfolio(self, portfolio_id: int) -> bool:
        """删除组合（软删除）"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.is_deleted == False
        ).first()
        
        if not portfolio:
            return False
        
        portfolio.is_deleted = True
        self.db.commit()
        return True
    
    # ============ 成分管理 ============
    
    def add_component(self, portfolio_id: int, data: ComponentCreate) -> Optional[PortfolioComponent]:
        """添加成分"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        # 检查产品是否已存在
        existing = self.db.query(PortfolioComponent).filter(
            PortfolioComponent.portfolio_id == portfolio_id,
            PortfolioComponent.product_id == data.product_id,
            PortfolioComponent.is_active == True
        ).first()
        
        if existing:
            # 更新权重
            existing.weight = data.weight
            self.db.commit()
            return existing
        
        component = PortfolioComponent(
            portfolio_id=portfolio_id,
            product_id=data.product_id,
            weight=data.weight,
            join_date=data.join_date,
            is_active=True
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def update_component(self, component_id: int, data: ComponentUpdate) -> Optional[PortfolioComponent]:
        """更新成分"""
        component = self.db.query(PortfolioComponent).filter(
            PortfolioComponent.id == component_id
        ).first()
        
        if not component:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(component, key, value)
        
        self.db.commit()
        self.db.refresh(component)
        return component
    
    def remove_component(self, component_id: int, exit_date: date = None) -> bool:
        """移除成分"""
        component = self.db.query(PortfolioComponent).filter(
            PortfolioComponent.id == component_id
        ).first()
        
        if not component:
            return False
        
        component.is_active = False
        component.exit_date = exit_date or date.today()
        self.db.commit()
        return True
    
    def set_components(self, portfolio_id: int, components: List[ComponentCreate]) -> List[PortfolioComponent]:
        """设置组合成分（替换所有）"""
        # 将现有成分设为无效
        self.db.query(PortfolioComponent).filter(
            PortfolioComponent.portfolio_id == portfolio_id,
            PortfolioComponent.is_active == True
        ).update({"is_active": False, "exit_date": date.today()})
        
        # 添加新成分
        result = []
        for comp in components:
            component = PortfolioComponent(
                portfolio_id=portfolio_id,
                product_id=comp.product_id,
                weight=comp.weight,
                join_date=comp.join_date or date.today(),
                is_active=True
            )
            self.db.add(component)
            result.append(component)
        
        self.db.commit()
        return result

    
    # ============ 组合净值计算 ============
    
    def calculate_portfolio_nav(
        self,
        portfolio_id: int,
        start_date: date = None,
        end_date: date = None
    ) -> Dict:
        """Calculate portfolio NAV series."""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None

        components = [c for c in portfolio.components if c.product_id]
        if not components:
            return {"error": "No valid components in portfolio"}

        if not end_date:
            end_date = date.today()

        if not start_date:
            candidate_start_dates = [d for d in [portfolio.start_date] if d]
            candidate_start_dates.extend(c.join_date for c in components if c.join_date)
            if candidate_start_dates:
                start_date = min(candidate_start_dates)

        if not start_date:
            all_product_ids = list({c.product_id for c in components})
            start_date = self.db.query(func.min(NavData.nav_date)).filter(
                NavData.product_id.in_(all_product_ids)
            ).scalar()

        if not start_date:
            return {"error": "Unable to determine start date"}
        if start_date > end_date:
            return {"error": "start_date cannot be later than end_date"}

        component_windows = []
        product_ids = set()
        for comp in components:
            if not comp.is_active and not comp.exit_date:
                # Skip components with unknown historical effective window.
                continue

            component_start = comp.join_date or portfolio.start_date or start_date
            component_end = comp.exit_date or end_date

            window_start = max(component_start, start_date)
            window_end = min(component_end, end_date)
            weight = float(comp.weight or 0)

            if weight <= 0 or window_start > window_end:
                continue

            component_windows.append({
                "product_id": comp.product_id,
                "weight": weight,
                "start": window_start,
                "end": window_end
            })
            product_ids.add(comp.product_id)

        if not component_windows:
            return {"error": "No effective components in requested period"}

        nav_data = self.db.query(NavData).filter(
            NavData.product_id.in_(list(product_ids)),
            NavData.nav_date >= start_date,
            NavData.nav_date <= end_date
        ).order_by(NavData.nav_date.asc()).all()
        if not nav_data:
            return {"error": "No NAV data in requested period"}

        date_nav_map: Dict[date, Dict[int, float]] = {}
        for nav in nav_data:
            if nav.nav_date not in date_nav_map:
                date_nav_map[nav.nav_date] = {}
            date_nav_map[nav.nav_date][nav.product_id] = float(nav.unit_nav)

        latest_nav_by_product: Dict[int, Tuple[date, float]] = {}
        for pid in product_ids:
            prev_nav = self.db.query(NavData).filter(
                NavData.product_id == pid,
                NavData.nav_date < start_date
            ).order_by(NavData.nav_date.desc()).first()
            if prev_nav and prev_nav.unit_nav is not None:
                latest_nav_by_product[pid] = (prev_nav.nav_date, float(prev_nav.unit_nav))

        sorted_dates = sorted(date_nav_map.keys())
        max_carry_forward_days = 10
        nav_series = []
        prev_portfolio_nav = 1.0
        prev_component_nav: Dict[int, float] = {}
        included_pids_last_step = set()
        effective_dates = 0
        skipped_dates = 0
        partial_weight_dates = 0
        carry_forward_component_days = 0
        stale_component_days = 0
        missing_component_days = 0
        total_weight_coverage = 0.0
        carry_forward_dates = set()

        for nav_date in sorted_dates:
            day_navs = date_nav_map[nav_date]
            for pid, nav_value in day_navs.items():
                latest_nav_by_product[pid] = (nav_date, nav_value)

            effective_components = [
                c for c in component_windows
                if c["start"] <= nav_date <= c["end"]
            ]
            if not effective_components:
                included_pids_last_step = set()
                continue

            total_effective_weight = sum(c["weight"] for c in effective_components)
            if total_effective_weight <= 0:
                included_pids_last_step = set()
                continue

            effective_dates += 1
            day_weight_coverage = 0.0
            available_components = []
            for c in effective_components:
                pid = c["product_id"]
                latest_nav = latest_nav_by_product.get(pid)
                if not latest_nav:
                    missing_component_days += 1
                    continue
                latest_date, latest_value = latest_nav
                if latest_value <= 0:
                    missing_component_days += 1
                    continue
                gap_days = (nav_date - latest_date).days
                if gap_days > max_carry_forward_days:
                    stale_component_days += 1
                    continue
                if gap_days > 0:
                    carry_forward_component_days += 1
                    carry_forward_dates.add(nav_date)
                available_components.append((c, pid, latest_value))

            if not available_components:
                included_pids_last_step = set()
                skipped_dates += 1
                partial_weight_dates += 1
                total_weight_coverage += day_weight_coverage
                continue

            total_available_weight = sum(c["weight"] for c, _, _ in available_components)
            if total_available_weight <= 0:
                included_pids_last_step = set()
                skipped_dates += 1
                partial_weight_dates += 1
                total_weight_coverage += day_weight_coverage
                continue

            day_weight_coverage = total_available_weight / total_effective_weight
            total_weight_coverage += day_weight_coverage
            if day_weight_coverage < 0.9999:
                partial_weight_dates += 1

            if not nav_series:
                portfolio_daily_return = 0.0
                portfolio_nav = 1.0
            else:
                portfolio_daily_return = 0.0
                for c, pid, current_nav in available_components:
                    normalized_weight = c["weight"] / total_available_weight
                    prev_nav = prev_component_nav.get(pid)
                    if pid not in included_pids_last_step or not prev_nav or prev_nav <= 0:
                        component_return = 0.0
                    else:
                        component_return = current_nav / prev_nav - 1
                    portfolio_daily_return += normalized_weight * component_return
                portfolio_nav = prev_portfolio_nav * (1 + portfolio_daily_return)

            nav_series.append(PortfolioNavPoint(
                date=nav_date,
                nav=round(portfolio_nav, 4),
                daily_return=round(portfolio_daily_return, 6)
            ))

            prev_portfolio_nav = portfolio_nav
            included_pids_last_step = set()
            for _, pid, current_nav in available_components:
                prev_component_nav[pid] = current_nav
                included_pids_last_step.add(pid)

        if not nav_series:
            return {"error": "Unable to calculate portfolio NAV"}

        calculated_dates = len(nav_series)
        avg_weight_coverage = (total_weight_coverage / effective_dates) if effective_dates > 0 else 0.0

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name,
            "start_date": nav_series[0].date,
            "end_date": nav_series[-1].date,
            "nav_series": nav_series,
            "initial_nav": 1.0,
            "latest_nav": nav_series[-1].nav,
            "total_return": nav_series[-1].nav - 1.0,
            "nav_quality": {
                "effective_dates": effective_dates,
                "calculated_dates": calculated_dates,
                "skipped_dates": skipped_dates,
                "coverage_ratio": round(calculated_dates / effective_dates, 6) if effective_dates > 0 else 0.0,
                "avg_weight_coverage": round(avg_weight_coverage, 6),
                "partial_weight_dates": partial_weight_dates,
                "carry_forward_dates": len(carry_forward_dates),
                "carry_forward_component_days": carry_forward_component_days,
                "stale_component_days": stale_component_days,
                "missing_component_days": missing_component_days,
                "max_carry_forward_days": max_carry_forward_days
            }
        }

    # ============ 成分贡献分析 ============

    def calculate_contribution(
        self,
        portfolio_id: int,
        start_date: date = None,
        end_date: date = None
    ) -> Dict:
        """计算成分贡献"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components:
            return {"error": "组合没有有效成分"}
        
        # 确定日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)  # 默认近1个月
        
        contributions = []
        total_contribution = 0.0
        
        for comp in active_components:
            product = comp.product
            weight = float(comp.weight)
            
            # 获取期间收益率
            nav_start = self.db.query(NavData).filter(
                NavData.product_id == comp.product_id,
                NavData.nav_date >= start_date
            ).order_by(NavData.nav_date).first()
            
            nav_end = self.db.query(NavData).filter(
                NavData.product_id == comp.product_id,
                NavData.nav_date <= end_date
            ).order_by(NavData.nav_date.desc()).first()
            
            if nav_start and nav_end and float(nav_start.unit_nav) > 0:
                period_return = float(nav_end.unit_nav) / float(nav_start.unit_nav) - 1
            else:
                period_return = 0.0
            
            contribution = weight * period_return
            total_contribution += contribution
            
            contributions.append(ComponentContribution(
                product_id=comp.product_id,
                product_code=product.product_code if product else "",
                product_name=product.product_name if product else "",
                weight=weight,
                period_return=period_return,
                contribution=contribution,
                contribution_pct=0.0  # 稍后计算
            ))
        
        # 计算贡献占比
        if total_contribution != 0:
            for c in contributions:
                c.contribution_pct = c.contribution / total_contribution * 100
        
        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name,
            "start_date": start_date,
            "end_date": end_date,
            "portfolio_return": total_contribution,
            "contributions": contributions
        }
    
    # ============ 组合业绩指标 ============
    
    def calculate_performance(
        self,
        portfolio_id: int,
        period: str = "1m"
    ) -> Dict:
        """计算组合业绩指标"""
        # 确定日期范围
        end_date = date.today()
        period_days = {
            "1w": 7, "1m": 30, "3m": 90, "6m": 180,
            "1y": 365, "ytd": (end_date - date(end_date.year, 1, 1)).days,
            "inception": 3650
        }
        days = period_days.get(period, 30)
        start_date = end_date - timedelta(days=days)
        
        # 向前多取30天缓冲，防止周频/月频数据点不足
        buffer_start = start_date - timedelta(days=30)
        
        # 获取组合净值序列（使用扩展的开始日期）
        nav_result = self.calculate_portfolio_nav(portfolio_id, buffer_start, end_date)
        if not nav_result or "error" in nav_result:
            return nav_result
        
        nav_series = nav_result["nav_series"]
        if len(nav_series) < 2:
            return {"error": "净值数据不足"}
        
        # 在缓冲数据中找到最接近 start_date 的起始点
        trimmed_series = [p for p in nav_series if p.date >= start_date]
        if len(trimmed_series) < 2:
            # 如果严格区间内不够，取最近的前一个点作为基准
            before_points = [p for p in nav_series if p.date < start_date]
            if before_points:
                trimmed_series = [before_points[-1]] + trimmed_series
        if len(trimmed_series) < 2:
            # 仍不够则使用全部缓冲数据
            trimmed_series = nav_series
        nav_series = trimmed_series
        
        # 计算收益率
        returns = []
        for i in range(1, len(nav_series)):
            if nav_series[i-1].nav > 0:
                r = float(nav_series[i].nav) / float(nav_series[i-1].nav) - 1
                returns.append(r)
        
        if not returns:
            return {"error": "无法计算收益率"}
        
        returns_arr = np.array(returns)
        
        # 总收益率
        total_return = float(nav_series[-1].nav) / float(nav_series[0].nav) - 1
        
        # 年化收益率
        actual_days = (nav_series[-1].date - nav_series[0].date).days
        if actual_days > 0:
            annualized_return = (1 + total_return) ** (365 / actual_days) - 1
        else:
            annualized_return = 0
        
        # 波动率
        volatility = float(np.std(returns_arr)) * np.sqrt(252) if len(returns_arr) > 1 else 0
        
        # 最大回撤
        nav_values = [float(n.nav) for n in nav_series]
        peak = nav_values[0]
        max_drawdown = 0
        for nav in nav_values:
            if nav > peak:
                peak = nav
            drawdown = (peak - nav) / peak if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 夏普比率
        risk_free_rate = 0.03
        excess_return = annualized_return - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # 卡玛比率
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        portfolio = self.get_portfolio(portfolio_id)
        
        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name if portfolio else "",
            "period": period,
            "total_return": round(total_return, 4),
            "annualized_return": round(annualized_return, 4),
            "volatility": round(volatility, 4),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "calmar_ratio": round(calmar_ratio, 2)
        }
    
    # ============ 调整记录 ============
    
    def record_adjustment(
        self,
        portfolio_id: int,
        data: AdjustmentCreate,
        user_id: int = None
    ) -> PortfolioAdjustment:
        """记录组合调整"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        # 记录调整前权重
        before_weights = {
            c.product_id: float(c.weight)
            for c in portfolio.components if c.is_active
        }
        
        # 执行调整
        self.set_components(portfolio_id, data.components)
        
        # 记录调整后权重
        after_weights = {
            c.product_id: float(c.weight)
            for c in data.components
        }
        
        # 创建调整记录
        adjustment = PortfolioAdjustment(
            portfolio_id=portfolio_id,
            adjust_date=data.adjust_date,
            adjust_type=data.adjust_type,
            description=data.description,
            before_weights=json.dumps(before_weights),
            after_weights=json.dumps(after_weights),
            created_by=user_id
        )
        self.db.add(adjustment)
        self.db.commit()
        self.db.refresh(adjustment)
        return adjustment
    
    def get_adjustments(self, portfolio_id: int) -> List[PortfolioAdjustment]:
        """获取调整记录"""
        return self.db.query(PortfolioAdjustment).filter(
            PortfolioAdjustment.portfolio_id == portfolio_id
        ).order_by(PortfolioAdjustment.adjust_date.desc()).all()
    
    # ============ 相关性分析 ============
    
    def calculate_correlation_matrix(
        self,
        portfolio_id: int,
        start_date: date = None,
        end_date: date = None
    ) -> Dict:
        """计算组合成分相关性矩阵"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        active_components = [c for c in portfolio.components if c.is_active]
        if len(active_components) < 2:
            return {"error": "组合成分数量不足，无法计算相关性"}
        
        # 确定日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)  # 默认近1年
        
        # 获取所有成分的净值数据
        product_ids = [c.product_id for c in active_components]
        nav_data = self.db.query(NavData).filter(
            NavData.product_id.in_(product_ids),
            NavData.nav_date >= start_date,
            NavData.nav_date <= end_date
        ).order_by(NavData.nav_date).all()
        
        if not nav_data:
            return {"error": "没有净值数据"}
        
        # 按产品组织数据
        product_navs = {pid: {} for pid in product_ids}
        for nav in nav_data:
            product_navs[nav.product_id][nav.nav_date] = float(nav.unit_nav)
        
        # 找到所有产品都有数据的日期
        common_dates = None
        for pid in product_ids:
            dates = set(product_navs[pid].keys())
            if common_dates is None:
                common_dates = dates
            else:
                common_dates = common_dates.intersection(dates)
        
        if not common_dates or len(common_dates) < 20:
            return {"error": "共同有效数据点不足"}
        
        sorted_dates = sorted(common_dates)
        
        # 计算每个产品的日收益率序列
        returns_dict = {}
        product_info = {}
        
        for c in active_components:
            product = c.product
            product_info[c.product_id] = {
                'code': product.product_code if product else str(c.product_id),
                'name': product.product_name if product else str(c.product_id)
            }
            
            navs = [product_navs[c.product_id][d] for d in sorted_dates]
            returns = []
            for i in range(1, len(navs)):
                if navs[i-1] > 0:
                    returns.append(navs[i] / navs[i-1] - 1)
                else:
                    returns.append(0)
            returns_dict[c.product_id] = returns
        
        # 计算相关性矩阵
        n = len(product_ids)
        correlation_matrix = [[0.0] * n for _ in range(n)]
        
        for i, pid_i in enumerate(product_ids):
            for j, pid_j in enumerate(product_ids):
                if i == j:
                    correlation_matrix[i][j] = 1.0
                else:
                    returns_i = np.array(returns_dict[pid_i])
                    returns_j = np.array(returns_dict[pid_j])
                    if len(returns_i) > 1 and len(returns_j) > 1:
                        corr = np.corrcoef(returns_i, returns_j)[0, 1]
                        correlation_matrix[i][j] = round(corr, 4) if not np.isnan(corr) else 0
                    else:
                        correlation_matrix[i][j] = 0
        
        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name,
            "start_date": start_date,
            "end_date": end_date,
            "data_points": len(sorted_dates) - 1,
            "products": [
                {
                    "product_id": pid,
                    "product_code": product_info[pid]['code'],
                    "product_name": product_info[pid]['name']
                }
                for pid in product_ids
            ],
            "matrix": correlation_matrix
        }
    
    # ============ 组合对比 ============
    
    def compare_portfolios(
        self,
        portfolio_ids: List[int],
        period: str = "3m"
    ) -> Dict:
        """对比多个组合的业绩表现"""
        results = []
        nav_data_map = {}  # 存储各组合的净值序列以便计算相关性
        
        for pid in portfolio_ids:
            # 获取业绩指标
            perf = self.calculate_performance(pid, period)
            if not perf or "error" in perf:
                continue
            
            # 获取组合信息
            portfolio = self.get_portfolio(pid)
            if not portfolio:
                continue
            
            # 获取成分数量
            active_components = [c for c in portfolio.components if c.is_active]
            
            results.append({
                "portfolio_id": pid,
                "portfolio_name": perf["portfolio_name"],
                "component_count": len(active_components),
                "status": portfolio.status,
                "total_return": float(perf["total_return"]),
                "annualized_return": float(perf["annualized_return"]),
                "volatility": float(perf["volatility"]),
                "max_drawdown": float(perf["max_drawdown"]),
                "sharpe_ratio": float(perf["sharpe_ratio"]),
                "calmar_ratio": float(perf["calmar_ratio"])
            })
            
            # 获取净值序列用于相关性计算
            nav_result = self.calculate_portfolio_nav(pid)
            if nav_result and "nav_series" in nav_result:
                nav_data_map[pid] = {
                    point.date: float(point.nav)
                    for point in nav_result["nav_series"]
                }
        
        if len(results) < 2:
            return {"error": "有效组合数量不足"}
        
        # 计算组合之间的相关性矩阵
        correlation_matrix = self._calculate_cross_correlation(nav_data_map, portfolio_ids)
        
        # 按年化收益排序
        results.sort(key=lambda x: x["annualized_return"], reverse=True)
        
        return {
            "period": period,
            "portfolios": results,
            "correlation_matrix": correlation_matrix
        }
    
    # ============ 持仓快照管理 ============
    
    def save_holdings_snapshot(
        self,
        portfolio_id: int,
        holding_date: date,
        holdings: List[HoldingCreate]
    ) -> List[PortfolioHolding]:
        """保存某日的持仓快照"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return []
        
        # 删除该日已有的快照
        self.db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.holding_date == holding_date
        ).delete()
        
        # 计算总市值
        total_mv = sum(float(h.market_value) for h in holdings) or 1
        
        result = []
        for h in holdings:
            mv = float(h.market_value)
            cost_val = float(h.cost)
            pnl_val = mv - cost_val
            pnl_ratio_val = pnl_val / cost_val if cost_val > 0 else 0
            weight_val = mv / total_mv if total_mv > 0 else 0
            
            holding = PortfolioHolding(
                portfolio_id=portfolio_id,
                product_id=h.product_id,
                holding_date=holding_date,
                shares=h.shares,
                market_value=h.market_value,
                weight=round(weight_val, 6),
                cost=h.cost,
                pnl=round(pnl_val, 2),
                pnl_ratio=round(pnl_ratio_val, 6)
            )
            self.db.add(holding)
            result.append(holding)
        
        self.db.commit()
        return result
    
    def get_holdings_by_date(
        self,
        portfolio_id: int,
        holding_date: date = None
    ) -> List[PortfolioHolding]:
        """获取某日的持仓快照，默认最新"""
        if not holding_date:
            # 获取最新持仓日期
            latest = self.db.query(func.max(PortfolioHolding.holding_date)).filter(
                PortfolioHolding.portfolio_id == portfolio_id
            ).scalar()
            if not latest:
                return []
            holding_date = latest
        
        return self.db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.holding_date == holding_date
        ).all()
    
    def get_holdings_dates(self, portfolio_id: int) -> List[date]:
        """获取所有持仓快照日期"""
        dates = self.db.query(PortfolioHolding.holding_date).filter(
            PortfolioHolding.portfolio_id == portfolio_id
        ).distinct().order_by(PortfolioHolding.holding_date.desc()).all()
        return [d[0] for d in dates]
    
    # ============ 组合净值持久化 ============
    
    def persist_portfolio_nav(self, portfolio_id: int) -> Dict:
        """计算并持久化组合净值序列到PortfolioNav表"""
        nav_result = self.calculate_portfolio_nav(portfolio_id)
        if not nav_result or "error" in nav_result:
            return nav_result or {"error": "组合不存在"}
        
        nav_series = nav_result.get("nav_series", [])
        if not nav_series:
            return {"error": "无净值数据"}
        
        count = 0
        for point in nav_series:
            # upsert逻辑
            existing = self.db.query(PortfolioNav).filter(
                PortfolioNav.portfolio_id == portfolio_id,
                PortfolioNav.nav_date == point.date
            ).first()
            
            if existing:
                existing.unit_nav = point.nav
                existing.daily_return = point.daily_return
                existing.cumulative_return = point.nav - 1.0
            else:
                nav_record = PortfolioNav(
                    portfolio_id=portfolio_id,
                    nav_date=point.date,
                    unit_nav=point.nav,
                    daily_return=point.daily_return,
                    cumulative_return=point.nav - 1.0
                )
                self.db.add(nav_record)
            count += 1
        
        self.db.commit()
        return {"message": f"已持久化 {count} 条净值记录", "count": count}
    
    def get_persisted_nav(
        self,
        portfolio_id: int,
        start_date: date = None,
        end_date: date = None
    ) -> List[PortfolioNav]:
        """获取持久化的组合净值序列"""
        query = self.db.query(PortfolioNav).filter(
            PortfolioNav.portfolio_id == portfolio_id
        )
        if start_date:
            query = query.filter(PortfolioNav.nav_date >= start_date)
        if end_date:
            query = query.filter(PortfolioNav.nav_date <= end_date)
        return query.order_by(PortfolioNav.nav_date).all()
    
    def get_latest_nav(self, portfolio_id: int) -> Optional[PortfolioNav]:
        """获取最新净值记录"""
        return self.db.query(PortfolioNav).filter(
            PortfolioNav.portfolio_id == portfolio_id
        ).order_by(PortfolioNav.nav_date.desc()).first()
    
    # ============ Brinson BHB 归因 ============
    
    def brinson_attribution(
        self,
        portfolio_id: int,
        start_date: date = None,
        end_date: date = None
    ) -> Dict:
        """Brinson BHB 模型归因: 配置效应(AA)、选择效应(SS)、交互效应(IR) 按策略分解"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None

        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components:
            return {"error": "组合没有有效成分"}

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # 按策略分组
        strategy_groups: Dict[str, list] = {}
        for c in active_components:
            product = c.product
            strategy = (product.strategy_type if product and product.strategy_type else '其他')
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(c)

        # 基准权重: 各策略等权
        n_strategies = len(strategy_groups)
        benchmark_strategy_weight = 1.0 / n_strategies if n_strategies > 0 else 0

        # 计算各成分期间收益
        component_returns = {}
        for c in active_components:
            nav_start = self.db.query(NavData).filter(
                NavData.product_id == c.product_id,
                NavData.nav_date >= start_date
            ).order_by(NavData.nav_date).first()
            nav_end = self.db.query(NavData).filter(
                NavData.product_id == c.product_id,
                NavData.nav_date <= end_date
            ).order_by(NavData.nav_date.desc()).first()
            if nav_start and nav_end and float(nav_start.unit_nav) > 0:
                component_returns[c.product_id] = float(nav_end.unit_nav) / float(nav_start.unit_nav) - 1
            else:
                component_returns[c.product_id] = 0.0

        all_returns = list(component_returns.values())
        benchmark_total_return = sum(all_returns) / len(all_returns) if all_returns else 0.0

        attributions = []
        total_aa = total_ss = total_ir = 0.0

        for strategy, comps in strategy_groups.items():
            wp = sum(float(c.weight) for c in comps)
            rp = sum(float(c.weight) * component_returns.get(c.product_id, 0) for c in comps) / wp if wp > 0 else 0.0
            wb = benchmark_strategy_weight
            strategy_rets = [component_returns.get(c.product_id, 0) for c in comps]
            rb = sum(strategy_rets) / len(strategy_rets) if strategy_rets else 0.0

            aa = (wp - wb) * (rb - benchmark_total_return)
            ss = wb * (rp - rb)
            ir = (wp - wb) * (rp - rb)
            total_aa += aa; total_ss += ss; total_ir += ir

            attributions.append({
                "strategy": strategy,
                "portfolio_weight": round(wp, 4),
                "benchmark_weight": round(wb, 4),
                "portfolio_return": round(rp, 6),
                "benchmark_return": round(rb, 6),
                "allocation_effect": round(aa, 6),
                "selection_effect": round(ss, 6),
                "interaction_effect": round(ir, 6),
                "total_effect": round(aa + ss + ir, 6)
            })

        portfolio_return = sum(float(c.weight) * component_returns.get(c.product_id, 0) for c in active_components)

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name,
            "start_date": start_date, "end_date": end_date,
            "portfolio_return": round(portfolio_return, 6),
            "benchmark_return": round(benchmark_total_return, 6),
            "excess_return": round(portfolio_return - benchmark_total_return, 6),
            "total_allocation_effect": round(total_aa, 6),
            "total_selection_effect": round(total_ss, 6),
            "total_interaction_effect": round(total_ir, 6),
            "attributions": attributions
        }

    # ============ 风险贡献归因 ============

    def risk_contribution(
        self, portfolio_id: int, start_date: date = None, end_date: date = None
    ) -> Dict:
        """风险贡献归因: MCTR/CCTR 基于协方差矩阵"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        active_components = [c for c in portfolio.components if c.is_active]
        if len(active_components) < 2:
            return {"error": "组合成分不足，至少需要2个"}
        if not end_date: end_date = date.today()
        if not start_date: start_date = end_date - timedelta(days=365)

        product_ids = [c.product_id for c in active_components]
        weights = np.array([float(c.weight) for c in active_components])

        nav_data_list = self.db.query(NavData).filter(
            NavData.product_id.in_(product_ids),
            NavData.nav_date >= start_date, NavData.nav_date <= end_date
        ).order_by(NavData.nav_date).all()
        if not nav_data_list:
            return {"error": "没有净值数据"}

        product_navs = {pid: {} for pid in product_ids}
        for nav in nav_data_list:
            product_navs[nav.product_id][nav.nav_date] = float(nav.unit_nav)

        common_dates = None
        for pid in product_ids:
            dates = set(product_navs[pid].keys())
            common_dates = dates if common_dates is None else common_dates.intersection(dates)
        if not common_dates or len(common_dates) < 30:
            return {"error": "共同有效数据点不足(需>=30)"}

        sorted_dates = sorted(common_dates)
        n_assets = len(product_ids)
        n_obs = len(sorted_dates) - 1
        returns_matrix = np.zeros((n_obs, n_assets))
        for j, pid in enumerate(product_ids):
            navs = [product_navs[pid][d] for d in sorted_dates]
            for i in range(n_obs):
                returns_matrix[i, j] = (navs[i+1] / navs[i] - 1) if navs[i] > 0 else 0

        cov_matrix = np.cov(returns_matrix, rowvar=False) * 252
        portfolio_var = float(weights @ cov_matrix @ weights)
        portfolio_vol = float(np.sqrt(portfolio_var)) if portfolio_var > 0 else 0.0001
        mctr = (cov_matrix @ weights) / portfolio_vol
        cctr = weights * mctr
        cctr_pct = cctr / portfolio_vol if portfolio_vol > 0 else cctr

        contributions = []
        for idx, c in enumerate(active_components):
            product = c.product
            contributions.append({
                "product_id": c.product_id,
                "product_code": product.product_code if product else "",
                "product_name": product.product_name if product else "",
                "weight": round(float(weights[idx]), 4),
                "mctr": round(float(mctr[idx]), 6),
                "cctr": round(float(cctr[idx]), 6),
                "risk_contribution_pct": round(float(cctr_pct[idx]) * 100, 2)
            })

        return {
            "portfolio_id": portfolio_id, "portfolio_name": portfolio.name,
            "start_date": start_date, "end_date": end_date,
            "portfolio_volatility": round(portfolio_vol, 6),
            "data_points": n_obs, "contributions": contributions
        }

    # ============ 调仓模拟 ============

    def simulate_rebalance(
        self, portfolio_id: int, new_weights: Dict[int, float],
        start_date: date = None, end_date: date = None
    ) -> Dict:
        """调仓模拟: 用新权重回测 vs 原组合"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio: return None
        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components: return {"error": "组合没有有效成分"}
        if not end_date: end_date = date.today()
        if not start_date: start_date = end_date - timedelta(days=180)

        product_ids = [c.product_id for c in active_components]
        original_weights = {c.product_id: float(c.weight) for c in active_components}

        nav_data_list = self.db.query(NavData).filter(
            NavData.product_id.in_(product_ids),
            NavData.nav_date >= start_date, NavData.nav_date <= end_date
        ).order_by(NavData.nav_date).all()
        if not nav_data_list: return {"error": "没有净值数据"}

        date_nav_map: Dict[date, Dict[int, float]] = {}
        for nav in nav_data_list:
            if nav.nav_date not in date_nav_map: date_nav_map[nav.nav_date] = {}
            date_nav_map[nav.nav_date][nav.product_id] = float(nav.unit_nav)

        sorted_dates = sorted(date_nav_map.keys())
        if len(sorted_dates) < 2: return {"error": "数据不足"}

        base_navs = {}
        for pid in product_ids:
            for d in sorted_dates:
                if pid in date_nav_map[d]:
                    base_navs[pid] = date_nav_map[d][pid]; break

        def calc_series(w_map):
            series = []; prev = 1.0
            for nd in sorted_dates:
                dn = date_nav_map[nd]
                if len(dn) < len(product_ids): continue
                pr = sum(w_map.get(pid, 0) * (dn[pid] / base_navs[pid] - 1) for pid in product_ids if pid in dn and pid in base_navs and base_navs[pid] > 0)
                nv = 1.0 + pr; dr = (nv / prev - 1) if prev > 0 else 0
                series.append({"date": nd.isoformat(), "nav": round(nv, 4), "daily_return": round(dr, 6)})
                prev = nv
            return series

        def calc_metrics(s):
            if len(s) < 2: return {}
            navs = [p["nav"] for p in s]
            rets = [(navs[i]/navs[i-1]-1) for i in range(1, len(navs)) if navs[i-1] > 0]
            if not rets: return {}
            ra = np.array(rets); tr = navs[-1]/navs[0]-1
            vol = float(np.std(ra))*np.sqrt(252)
            pk = navs[0]; md = 0
            for n in navs:
                if n > pk: pk = n
                dd = (pk-n)/pk if pk > 0 else 0
                if dd > md: md = dd
            return {"total_return": round(tr, 4), "volatility": round(vol, 4), "max_drawdown": round(md, 4), "sharpe_ratio": round((tr-0.03)/vol if vol > 0 else 0, 2)}

        return {
            "portfolio_id": portfolio_id, "portfolio_name": portfolio.name,
            "start_date": start_date, "end_date": end_date,
            "original_weights": {str(k): v for k, v in original_weights.items()},
            "simulated_weights": {str(k): v for k, v in new_weights.items()},
            "original_nav": calc_series(original_weights),
            "simulated_nav": calc_series(new_weights),
            "original_metrics": calc_metrics(calc_series(original_weights)),
            "simulated_metrics": calc_metrics(calc_series(new_weights))
        }

    # ============ 穿透分析 ============

    def lookthrough_analysis(self, portfolio_id: int) -> Dict:
        """穿透分析: 按策略类型和管理人两维度聚合"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio: return None
        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components: return {"error": "组合没有有效成分"}

        by_strategy: Dict[str, dict] = {}
        by_manager: Dict[str, dict] = {}

        for c in active_components:
            product = c.product
            w = float(c.weight)
            strategy = (product.strategy_type if product and product.strategy_type else '其他')
            mgr = (product.manager.manager_name if product and product.manager else '未知')

            if strategy not in by_strategy:
                by_strategy[strategy] = {"weight": 0.0, "count": 0, "products": []}
            by_strategy[strategy]["weight"] += w
            by_strategy[strategy]["count"] += 1
            by_strategy[strategy]["products"].append({"product_id": c.product_id, "product_name": product.product_name if product else "", "weight": round(w, 4)})

            if mgr not in by_manager:
                by_manager[mgr] = {"weight": 0.0, "count": 0, "products": []}
            by_manager[mgr]["weight"] += w
            by_manager[mgr]["count"] += 1
            by_manager[mgr]["products"].append({"product_id": c.product_id, "product_name": product.product_name if product else "", "weight": round(w, 4)})

        return {
            "portfolio_id": portfolio_id, "portfolio_name": portfolio.name,
            "total_components": len(active_components),
            "by_strategy": [{"name": k, "weight": round(v["weight"], 4), "count": v["count"], "products": v["products"]} for k, v in sorted(by_strategy.items(), key=lambda x: -x[1]["weight"])],
            "by_manager": [{"name": k, "weight": round(v["weight"], 4), "count": v["count"], "products": v["products"]} for k, v in sorted(by_manager.items(), key=lambda x: -x[1]["weight"])]
        }

    # ============ 风险预算 ============

    def update_risk_budget(self, portfolio_id: int, config: Dict) -> Optional[Portfolio]:
        """更新风险预算配置"""
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.is_deleted == False).first()
        if not portfolio: return None
        portfolio.risk_budget = json.dumps(config)
        self.db.commit(); self.db.refresh(portfolio)
        return portfolio

    def get_risk_budget(self, portfolio_id: int) -> Dict:
        """获取风险预算配置"""
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.is_deleted == False).first()
        if not portfolio: return None
        config = json.loads(portfolio.risk_budget) if portfolio.risk_budget else {}
        return {"portfolio_id": portfolio_id, "config": config}

    def check_risk_budget(self, portfolio_id: int, period: str = "3m") -> Dict:
        """检查风险预算超限告警"""
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.is_deleted == False).first()
        if not portfolio: return None
        config = json.loads(portfolio.risk_budget) if portfolio.risk_budget else {}
        if not config:
            return {"portfolio_id": portfolio_id, "alerts": [], "config": {}, "metrics": {}, "has_breach": False}

        perf = self.calculate_performance(portfolio_id, period)
        if not perf or "error" in perf:
            return {"portfolio_id": portfolio_id, "alerts": [], "config": config, "metrics": {}, "has_breach": False}

        metrics = {
            "max_drawdown": abs(float(perf.get("max_drawdown", 0))),
            "volatility": float(perf.get("volatility", 0)),
            "sharpe_ratio": float(perf.get("sharpe_ratio", 0)),
        }
        alerts = []
        if "max_drawdown" in config and metrics["max_drawdown"] > config["max_drawdown"]:
            alerts.append({"metric": "max_drawdown", "label": "最大回撤", "threshold": config["max_drawdown"], "current": metrics["max_drawdown"], "severity": "danger"})
        if "volatility" in config and metrics["volatility"] > config["volatility"]:
            alerts.append({"metric": "volatility", "label": "波动率", "threshold": config["volatility"], "current": metrics["volatility"], "severity": "danger"})
        if "sharpe_min" in config and metrics["sharpe_ratio"] < config["sharpe_min"]:
            alerts.append({"metric": "sharpe_ratio", "label": "夏普比率", "threshold": config["sharpe_min"], "current": metrics["sharpe_ratio"], "severity": "warning"})
        if "max_single_weight" in config:
            p = self.get_portfolio(portfolio_id)
            if p:
                for c in p.components:
                    if c.is_active and float(c.weight) > config["max_single_weight"]:
                        prd = c.product
                        alerts.append({"metric": "concentration", "label": f"集中度-{prd.product_name if prd else c.product_id}", "threshold": config["max_single_weight"], "current": float(c.weight), "severity": "warning"})

        return {"portfolio_id": portfolio_id, "period": period, "config": config, "metrics": metrics, "alerts": alerts, "has_breach": len(alerts) > 0}

    # ============ Brinson 第3层 管理人选择归因 ============

    def brinson_manager_attribution(
        self, portfolio_id: int, start_date: date = None, end_date: date = None
    ) -> Dict:
        """Brinson 第3层: 管理人选择效应 = Σ Wp,k × (Rp,k - Rb,k)"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components:
            return {"error": "组合没有有效成分"}
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # 按管理人分组
        manager_groups: Dict[str, list] = {}
        for c in active_components:
            product = c.product
            mgr = product.manager.manager_name if product and product.manager else '未知'
            strategy = product.strategy_type if product and product.strategy_type else '其他'
            if mgr not in manager_groups:
                manager_groups[mgr] = {'components': [], 'strategy': strategy}
            manager_groups[mgr]['components'].append(c)

        # 计算各成分期间收益
        comp_returns = self._get_component_returns(active_components, start_date, end_date)

        # 按策略计算基准收益
        strategy_benchmark = {}
        for mgr_info in manager_groups.values():
            strategy = mgr_info['strategy']
            if strategy not in strategy_benchmark:
                strategy_benchmark[strategy] = []
            for c in mgr_info['components']:
                strategy_benchmark[strategy].append(comp_returns.get(c.product_id, 0.0))
        for s in strategy_benchmark:
            rets = strategy_benchmark[s]
            strategy_benchmark[s] = sum(rets) / len(rets) if rets else 0.0

        n_managers = len(manager_groups)
        benchmark_weight = 1.0 / n_managers if n_managers > 0 else 0
        attributions = []
        total_se = 0.0

        for mgr, info in manager_groups.items():
            comps = info['components']
            strategy = info['strategy']
            wp = sum(float(c.weight) for c in comps)
            rp = sum(float(c.weight) * comp_returns.get(c.product_id, 0) for c in comps) / wp if wp > 0 else 0.0
            rb = strategy_benchmark.get(strategy, 0.0)
            se = wp * (rp - rb)
            total_se += se
            attributions.append({
                "manager_name": mgr,
                "strategy": strategy,
                "portfolio_weight": round(wp, 4),
                "benchmark_weight": round(benchmark_weight, 4),
                "portfolio_return": round(rp, 6),
                "benchmark_return": round(rb, 6),
                "selection_effect": round(se, 6)
            })

        attributions.sort(key=lambda x: abs(x["selection_effect"]), reverse=True)
        return {
            "portfolio_id": portfolio_id, "portfolio_name": portfolio.name,
            "start_date": start_date, "end_date": end_date,
            "total_selection_effect": round(total_se, 6),
            "attributions": attributions
        }

    # ============ Brinson 第4层 个券选择归因 ============

    def brinson_security_attribution(
        self, portfolio_id: int, holding_date: date = None
    ) -> Dict:
        """Brinson 第4层: 基于四级估值表的个券选股/行业配置效应"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components:
            return {"error": "组合没有有效成分"}

        product_ids = [c.product_id for c in active_components]

        # 获取最新持仓日期
        if not holding_date:
            latest = self.db.query(func.max(HoldingsDetail.holding_date)).filter(
                HoldingsDetail.product_id.in_(product_ids)
            ).scalar()
            if not latest:
                return {"error": "没有底层持仓明细数据，请先导入四级估值表"}
            holding_date = latest

        # 获取所有底层持仓
        details = self.db.query(HoldingsDetail).filter(
            HoldingsDetail.product_id.in_(product_ids),
            HoldingsDetail.holding_date == holding_date
        ).all()
        if not details:
            return {"error": "该日期没有底层持仓数据"}

        # 产品名映射
        product_map = {}
        for c in active_components:
            if c.product:
                product_map[c.product_id] = c.product.product_name or str(c.product_id)

        # 按行业计算基准收益
        industry_weights: Dict[str, float] = {}
        industry_returns: Dict[str, list] = {}
        all_securities = []

        for d in details:
            w = float(d.weight) if d.weight else 0
            # 简化：用 (market_value - cost) / cost 作为收益代理
            mv = float(d.market_value) if d.market_value else 0
            cost = float(d.cost) if d.cost else 0
            ret = (mv / cost - 1) if cost > 0 else 0
            sector = d.industry_l1 or '未分类'

            if sector not in industry_weights:
                industry_weights[sector] = 0.0
                industry_returns[sector] = []
            industry_weights[sector] += w
            industry_returns[sector].append((w, ret))
            all_securities.append({
                'security_code': d.security_code,
                'security_name': d.security_name or '',
                'product_name': product_map.get(d.product_id, ''),
                'weight': w,
                'return': ret,
                'sector': sector
            })

        # 各行业加权基准收益
        sector_avg_returns = {}
        for sector, items in industry_returns.items():
            total_w = sum(x[0] for x in items)
            sector_avg_returns[sector] = sum(x[0] * x[1] for x in items) / total_w if total_w > 0 else 0

        # 全组合平均收益
        total_w = sum(s['weight'] for s in all_securities)
        portfolio_avg = sum(s['weight'] * s['return'] for s in all_securities) / total_w if total_w > 0 else 0

        # 逐券归因
        total_stock_sel = 0.0
        total_sector_alloc = 0.0
        attributions = []

        for s in all_securities:
            sector_ret = sector_avg_returns.get(s['sector'], 0)
            stock_sel = s['weight'] * (s['return'] - sector_ret)  # 选股效应
            sector_alloc = s['weight'] * (sector_ret - portfolio_avg)  # 行业配置效应
            total_stock_sel += stock_sel
            total_sector_alloc += sector_alloc
            attributions.append({
                "security_code": s['security_code'],
                "security_name": s['security_name'],
                "product_name": s['product_name'],
                "weight": round(s['weight'], 6),
                "return_rate": round(s['return'], 6),
                "sector_return": round(sector_ret, 6),
                "stock_selection_effect": round(stock_sel, 6),
                "sector_allocation_effect": round(sector_alloc, 6)
            })

        # 按选股效应绝对值排序,取前50
        attributions.sort(key=lambda x: abs(x["stock_selection_effect"]), reverse=True)
        return {
            "portfolio_id": portfolio_id, "portfolio_name": portfolio.name,
            "start_date": holding_date, "end_date": holding_date,
            "total_stock_selection": round(total_stock_sel, 6),
            "total_sector_allocation": round(total_sector_alloc, 6),
            "attributions": attributions[:50]
        }

    # ============ 多因子模型 (Barra) ============

    def multi_factor_analysis(
        self, portfolio_id: int, start_date: date = None, end_date: date = None
    ) -> Dict:
        """Barra多因子: R = α + Σ(βi×Fi) + ε, 8个风格因子"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components:
            return {"error": "组合没有有效成分"}
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=540)  # 默认18个月，确保周频数据>=60

        product_ids = [c.product_id for c in active_components]
        weights = {c.product_id: float(c.weight) for c in active_components}

        # 获取收益率序列
        nav_data_list = self.db.query(NavData).filter(
            NavData.product_id.in_(product_ids),
            NavData.nav_date >= start_date, NavData.nav_date <= end_date
        ).order_by(NavData.nav_date).all()
        if not nav_data_list:
            return {"error": "没有净值数据"}

        product_navs = {pid: {} for pid in product_ids}
        for nav in nav_data_list:
            product_navs[nav.product_id][nav.nav_date] = float(nav.unit_nav)

        common_dates = None
        for pid in product_ids:
            dates = set(product_navs[pid].keys())
            common_dates = dates if common_dates is None else common_dates.intersection(dates)
        if not common_dates or len(common_dates) < 60:
            return {"error": "共同有效数据点不足(需>=60)"}

        sorted_dates = sorted(common_dates)
        n_obs = len(sorted_dates) - 1

        # 构建收益率矩阵
        returns_map = {}
        for pid in product_ids:
            navs = [product_navs[pid][d] for d in sorted_dates]
            returns_map[pid] = [(navs[i+1] / navs[i] - 1) if navs[i] > 0 else 0 for i in range(n_obs)]

        # 模拟8个Barra风格因子 (用组合内统计特征代理)
        # 实际生产环境应接入Wind/Bloomberg因子数据
        FACTORS = [
            ('market', '市值因子'), ('beta', 'Beta因子'), ('momentum', '动量因子'),
            ('volatility', '波动因子'), ('value', '价值因子'), ('growth', '成长因子'),
            ('liquidity', '流动性因子'), ('leverage', '杠杆因子')
        ]

        # 用成分收益率的统计特征构造因子代理
        all_returns = np.array([returns_map[pid] for pid in product_ids])  # (n_assets, n_obs)
        market_factor = np.mean(all_returns, axis=0)  # 等权市场因子

        # 构造因子矩阵 (n_obs, 8)
        factor_matrix = np.zeros((n_obs, 8))
        factor_matrix[:, 0] = market_factor  # 市值因子 = 市场平均
        for i in range(1, 8):
            # 用滞后/滚动统计构造差异化因子
            np.random.seed(42 + i)
            noise = np.random.normal(0, 0.001, n_obs)
            if i == 1:  # beta: 市场因子 + 噪声
                factor_matrix[:, i] = market_factor * 1.1 + noise
            elif i == 2:  # momentum: 12期滞后均值
                for t in range(n_obs):
                    lookback = min(t, 12)
                    factor_matrix[t, i] = np.mean(market_factor[max(0, t-lookback):t+1]) + noise[t]
            elif i == 3:  # volatility: 滚动波动率变化(使用一阶差分，使其为收益型序列)
                rolling_vol = np.zeros(n_obs)
                for t in range(n_obs):
                    lookback = min(t, 20)
                    rolling_vol[t] = np.std(market_factor[max(0, t-lookback):t+1])
                # 用波动率一阶差分(变化量)作为因子，确保零均值、收益型序列
                factor_matrix[0, i] = noise[0]
                factor_matrix[1:, i] = np.diff(rolling_vol) + noise[1:]
            else:
                # 其他因子: 用不同lag的市场因子
                shift = i * 3
                shifted = np.roll(market_factor, shift)
                shifted[:shift] = market_factor[:shift]
                factor_matrix[:, i] = shifted + noise

        # 对每只产品做多因子回归
        product_details = []
        portfolio_exposures_accum = np.zeros(8)

        for c in active_components:
            pid = c.product_id
            y = np.array(returns_map[pid])
            X = np.column_stack([np.ones(n_obs), factor_matrix])  # 含截距

            try:
                # OLS回归: y = α + β1*F1 + ... + β8*F8 + ε
                betas, residuals, _, _ = np.linalg.lstsq(X, y, rcond=None)
                alpha = betas[0]
                factor_betas = betas[1:]
                y_hat = X @ betas
                ss_res = np.sum((y - y_hat) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                residual_std = np.std(y - y_hat)
            except Exception:
                alpha = 0.0
                factor_betas = np.zeros(8)
                r_squared = 0.0
                residual_std = 0.0

            w = weights.get(pid, 0)
            portfolio_exposures_accum += factor_betas * w

            exposures = []
            for j, (fname, flabel) in enumerate(FACTORS):
                factor_ret = float(np.mean(factor_matrix[:, j]) * 252)  # 年化因子收益
                exposures.append({
                    "factor_name": fname,
                    "factor_label": flabel,
                    "exposure": round(float(factor_betas[j]), 4),
                    "factor_return": round(factor_ret, 4),
                    "contribution": round(float(factor_betas[j]) * factor_ret, 6)
                })

            product_details.append({
                "product_id": pid,
                "product_name": c.product.product_name if c.product else str(pid),
                "alpha": round(float(alpha) * 252, 4),  # 年化alpha
                "residual": round(float(residual_std) * np.sqrt(252), 4),
                "r_squared": round(float(r_squared), 4),
                "exposures": exposures
            })

        # 组合层面加权因子暴露
        portfolio_exposures = []
        for j, (fname, flabel) in enumerate(FACTORS):
            factor_ret = float(np.mean(factor_matrix[:, j]) * 252)
            exp = float(portfolio_exposures_accum[j])
            portfolio_exposures.append({
                "factor_name": fname,
                "factor_label": flabel,
                "exposure": round(exp, 4),
                "factor_return": round(factor_ret, 4),
                "contribution": round(exp * factor_ret, 6)
            })

        return {
            "portfolio_id": portfolio_id, "portfolio_name": portfolio.name,
            "start_date": start_date, "end_date": end_date,
            "portfolio_exposures": portfolio_exposures,
            "product_details": product_details
        }

    # ============ 四级估值表分析 ============

    def holdings_detail_analysis(self, portfolio_id: int, holding_date: date = None) -> Dict:
        """四级估值表分析: 行业分布、集中度(HHI)、市值分布"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        active_components = [c for c in portfolio.components if c.is_active]
        if not active_components:
            return {"error": "组合没有有效成分"}

        product_ids = [c.product_id for c in active_components]
        product_weights = {c.product_id: float(c.weight) for c in active_components}

        if not holding_date:
            latest = self.db.query(func.max(HoldingsDetail.holding_date)).filter(
                HoldingsDetail.product_id.in_(product_ids)
            ).scalar()
            if not latest:
                return {"error": "没有底层持仓明细数据"}
            holding_date = latest

        details = self.db.query(HoldingsDetail).filter(
            HoldingsDetail.product_id.in_(product_ids),
            HoldingsDetail.holding_date == holding_date
        ).all()
        if not details:
            return {"error": "该日期没有底层持仓数据"}

        # 加权到组合层面: 个券组合层面权重 = 个券在子基金中的权重 × 子基金在组合中的权重
        securities = []
        for d in details:
            pw = product_weights.get(d.product_id, 0)
            w = float(d.weight or 0) * pw  # 穿透权重
            securities.append({
                'code': d.security_code,
                'name': d.security_name or '',
                'type': d.security_type or 'other',
                'weight': w,
                'market_value': float(d.market_value or 0) * pw,
                'industry_l1': d.industry_l1 or '未分类',
                'industry_l2': d.industry_l2 or '未分类',
                'cap_type': d.market_cap_type or 'unknown'
            })

        total_w = sum(s['weight'] for s in securities) or 1
        # 归一化
        for s in securities:
            s['norm_weight'] = s['weight'] / total_w

        # 1. 行业分布
        def calc_industry_dist(field):
            groups: Dict[str, dict] = {}
            for s in securities:
                ind = s[field]
                if ind not in groups:
                    groups[ind] = {'weight': 0, 'count': 0, 'mv': 0}
                groups[ind]['weight'] += s['norm_weight']
                groups[ind]['count'] += 1
                groups[ind]['mv'] += s['market_value']
            return sorted([
                {'industry': k, 'weight': round(v['weight'], 6), 'count': v['count'], 'market_value': round(v['mv'], 2)}
                for k, v in groups.items()
            ], key=lambda x: -x['weight'])

        industry_l1 = calc_industry_dist('industry_l1')
        industry_l2 = calc_industry_dist('industry_l2')

        # 2. 集中度
        sorted_by_weight = sorted(securities, key=lambda x: -x['norm_weight'])
        weights_list = [s['norm_weight'] for s in sorted_by_weight]
        top5 = sum(weights_list[:5])
        top10 = sum(weights_list[:10])
        top20 = sum(weights_list[:20])
        hhi = sum(w ** 2 for w in weights_list)

        # 3. 市值分布
        cap_labels = {'large': '大盘', 'mid': '中盘', 'small': '小盘', 'unknown': '未知'}
        cap_groups: Dict[str, dict] = {}
        for s in securities:
            ct = s['cap_type']
            if ct not in cap_groups:
                cap_groups[ct] = {'weight': 0, 'count': 0}
            cap_groups[ct]['weight'] += s['norm_weight']
            cap_groups[ct]['count'] += 1
        market_cap_dist = sorted([
            {'cap_type': k, 'cap_label': cap_labels.get(k, k), 'weight': round(v['weight'], 6), 'count': v['count']}
            for k, v in cap_groups.items()
        ], key=lambda x: -x['weight'])

        # 4. 证券类型分布
        type_labels = {'stock': '股票', 'bond': '债券', 'fund': '基金', 'other': '其他'}
        type_groups: Dict[str, dict] = {}
        for s in securities:
            st = s['type']
            if st not in type_groups:
                type_groups[st] = {'weight': 0, 'count': 0}
            type_groups[st]['weight'] += s['norm_weight']
            type_groups[st]['count'] += 1
        security_type_dist = sorted([
            {'type': k, 'label': type_labels.get(k, k), 'weight': round(v['weight'], 6), 'count': v['count']}
            for k, v in type_groups.items()
        ], key=lambda x: -x['weight'])

        return {
            "portfolio_id": portfolio_id, "portfolio_name": portfolio.name,
            "holding_date": holding_date,
            "total_securities": len(securities),
            "industry_l1": industry_l1,
            "industry_l2": industry_l2,
            "concentration": {
                "top5_weight": round(top5, 4),
                "top10_weight": round(top10, 4),
                "top20_weight": round(top20, 4),
                "hhi": round(hhi, 6)
            },
            "market_cap_dist": market_cap_dist,
            "security_type_dist": security_type_dist
        }

    # ============ 底层持仓明细CRUD ============

    def save_holdings_detail(
        self, items: list
    ) -> int:
        """批量导入底层持仓明细"""
        count = 0
        for item in items:
            existing = self.db.query(HoldingsDetail).filter(
                HoldingsDetail.product_id == item.product_id,
                HoldingsDetail.holding_date == item.holding_date,
                HoldingsDetail.security_code == item.security_code
            ).first()
            if existing:
                for attr in ['security_name', 'security_type', 'quantity', 'market_value',
                             'cost', 'weight', 'industry_l1', 'industry_l2', 'market_cap_type']:
                    val = getattr(item, attr, None)
                    if val is not None:
                        setattr(existing, attr, val)
            else:
                record = HoldingsDetail(
                    product_id=item.product_id,
                    holding_date=item.holding_date,
                    security_code=item.security_code,
                    security_name=item.security_name,
                    security_type=item.security_type,
                    quantity=item.quantity,
                    market_value=item.market_value,
                    cost=item.cost,
                    weight=item.weight,
                    industry_l1=item.industry_l1,
                    industry_l2=item.industry_l2,
                    market_cap_type=item.market_cap_type
                )
                self.db.add(record)
            count += 1
        self.db.commit()
        return count

    def get_holdings_detail(
        self, portfolio_id: int, holding_date: date = None
    ) -> list:
        """获取组合底层持仓明细"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return []
        product_ids = [c.product_id for c in portfolio.components if c.is_active]
        if not product_ids:
            return []

        if not holding_date:
            latest = self.db.query(func.max(HoldingsDetail.holding_date)).filter(
                HoldingsDetail.product_id.in_(product_ids)
            ).scalar()
            if not latest:
                return []
            holding_date = latest

        return self.db.query(HoldingsDetail).filter(
            HoldingsDetail.product_id.in_(product_ids),
            HoldingsDetail.holding_date == holding_date
        ).order_by(HoldingsDetail.market_value.desc()).all()

    # ============ 辅助: 获取成分期间收益 ============

    def _get_component_returns(
        self, components: list, start_date: date, end_date: date
    ) -> Dict[int, float]:
        """获取各成分期间收益率"""
        result = {}
        for c in components:
            nav_start = self.db.query(NavData).filter(
                NavData.product_id == c.product_id,
                NavData.nav_date >= start_date
            ).order_by(NavData.nav_date).first()
            nav_end = self.db.query(NavData).filter(
                NavData.product_id == c.product_id,
                NavData.nav_date <= end_date
            ).order_by(NavData.nav_date.desc()).first()
            if nav_start and nav_end and float(nav_start.unit_nav) > 0:
                result[c.product_id] = float(nav_end.unit_nav) / float(nav_start.unit_nav) - 1
            else:
                result[c.product_id] = 0.0
        return result

    def _calculate_cross_correlation(
        self,
        nav_data_map: Dict[int, Dict],
        portfolio_ids: List[int]
    ) -> List[List[float]]:
        """计算组合之间的相关性矩阵"""
        # 找到所有组合都有数据的共同日期
        common_dates = None
        for pid in portfolio_ids:
            if pid not in nav_data_map:
                continue
            dates = set(nav_data_map[pid].keys())
            if common_dates is None:
                common_dates = dates
            else:
                common_dates = common_dates.intersection(dates)
        
        if not common_dates or len(common_dates) < 20:
            # 数据不足，返回空矩阵
            n = len(portfolio_ids)
            return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        
        sorted_dates = sorted(common_dates)
        
        # 计算每个组合的日收益率
        returns_dict = {}
        for pid in portfolio_ids:
            if pid not in nav_data_map:
                returns_dict[pid] = [0] * (len(sorted_dates) - 1)
                continue
            
            navs = [nav_data_map[pid][d] for d in sorted_dates]
            returns = []
            for i in range(1, len(navs)):
                if navs[i-1] > 0:
                    returns.append(navs[i] / navs[i-1] - 1)
                else:
                    returns.append(0)
            returns_dict[pid] = returns
        
        # 计算相关性矩阵
        n = len(portfolio_ids)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i, pid_i in enumerate(portfolio_ids):
            for j, pid_j in enumerate(portfolio_ids):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    returns_i = np.array(returns_dict[pid_i])
                    returns_j = np.array(returns_dict[pid_j])
                    if len(returns_i) > 1 and len(returns_j) > 1:
                        corr = np.corrcoef(returns_i, returns_j)[0, 1]
                        matrix[i][j] = round(corr, 4) if not np.isnan(corr) else 0
                    else:
                        matrix[i][j] = 0
        
        return matrix
