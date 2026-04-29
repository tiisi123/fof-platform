"""
持仓明细服务 - 四级估值表分析
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
import pandas as pd

from app.models.holdings_detail import HoldingsDetail
from app.models.product import Product


class HoldingsService:
    """持仓明细服务"""
    
    @staticmethod
    def get_latest_holding_date(db: Session, product_id: int) -> Optional[date]:
        """获取最新持仓日期"""
        result = db.query(func.max(HoldingsDetail.holding_date)).filter(
            HoldingsDetail.product_id == product_id
        ).scalar()
        return result
    
    @staticmethod
    def get_holdings_by_date(
        db: Session, 
        product_id: int, 
        holding_date: date,
        level: Optional[int] = None
    ) -> List[HoldingsDetail]:
        """获取指定日期的持仓"""
        query = db.query(HoldingsDetail).filter(
            HoldingsDetail.product_id == product_id,
            HoldingsDetail.holding_date == holding_date
        )
        if level is not None:
            query = query.filter(HoldingsDetail.level == level)
        return query.all()
    
    @staticmethod
    def calculate_portfolio_metrics(holdings: List[HoldingsDetail]) -> Dict:
        """计算组合指标"""
        if not holdings:
            return {
                "total_market_value": 0,
                "total_cost": 0,
                "total_pnl": 0,
                "total_pnl_ratio": 0,
                "holdings_count": 0,
            }
        
        total_mv = sum(float(h.market_value or 0) for h in holdings)
        total_cost = sum(float(h.cost or 0) for h in holdings)
        total_pnl = sum(float(h.pnl or 0) for h in holdings)
        
        return {
            "total_market_value": round(total_mv, 2),
            "total_cost": round(total_cost, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_ratio": round(total_pnl / total_cost * 100, 2) if total_cost > 0 else 0,
            "holdings_count": len(holdings),
        }
    
    @staticmethod
    def analyze_by_security_type(holdings: List[HoldingsDetail]) -> Dict[str, Dict]:
        """按证券类别分析"""
        total_mv = sum(float(h.market_value or 0) for h in holdings)
        
        by_type = {}
        for h in holdings:
            sec_type = h.security_type or 'unknown'
            if sec_type not in by_type:
                by_type[sec_type] = {
                    "market_value": 0,
                    "cost": 0,
                    "pnl": 0,
                    "count": 0,
                    "weight": 0,
                }
            
            by_type[sec_type]["market_value"] += float(h.market_value or 0)
            by_type[sec_type]["cost"] += float(h.cost or 0)
            by_type[sec_type]["pnl"] += float(h.pnl or 0)
            by_type[sec_type]["count"] += 1
        
        # 计算占比
        for data in by_type.values():
            data["weight"] = round(data["market_value"] / total_mv * 100, 2) if total_mv > 0 else 0
            data["market_value"] = round(data["market_value"], 2)
            data["cost"] = round(data["cost"], 2)
            data["pnl"] = round(data["pnl"], 2)
            data["pnl_ratio"] = round(data["pnl"] / data["cost"] * 100, 2) if data["cost"] > 0 else 0
        
        return by_type
    
    @staticmethod
    def analyze_by_industry(holdings: List[HoldingsDetail], level: int = 1) -> Dict[str, Dict]:
        """按行业分析"""
        total_mv = sum(float(h.market_value or 0) for h in holdings)
        
        by_industry = {}
        for h in holdings:
            industry = h.industry_l1 if level == 1 else h.industry_l2
            if not industry:
                industry = '未分类'
            
            if industry not in by_industry:
                by_industry[industry] = {
                    "market_value": 0,
                    "cost": 0,
                    "pnl": 0,
                    "count": 0,
                    "weight": 0,
                }
            
            by_industry[industry]["market_value"] += float(h.market_value or 0)
            by_industry[industry]["cost"] += float(h.cost or 0)
            by_industry[industry]["pnl"] += float(h.pnl or 0)
            by_industry[industry]["count"] += 1
        
        # 计算占比并排序
        for data in by_industry.values():
            data["weight"] = round(data["market_value"] / total_mv * 100, 2) if total_mv > 0 else 0
            data["market_value"] = round(data["market_value"], 2)
            data["cost"] = round(data["cost"], 2)
            data["pnl"] = round(data["pnl"], 2)
            data["pnl_ratio"] = round(data["pnl"] / data["cost"] * 100, 2) if data["cost"] > 0 else 0
        
        return dict(sorted(by_industry.items(), key=lambda x: x[1]["market_value"], reverse=True))
    
    @staticmethod
    def analyze_by_market_cap(holdings: List[HoldingsDetail]) -> Dict[str, Dict]:
        """按市值类型分析"""
        total_mv = sum(float(h.market_value or 0) for h in holdings)
        
        by_cap = {}
        for h in holdings:
            cap_type = h.market_cap_type or 'unknown'
            if cap_type not in by_cap:
                by_cap[cap_type] = {
                    "market_value": 0,
                    "count": 0,
                    "weight": 0,
                }
            
            by_cap[cap_type]["market_value"] += float(h.market_value or 0)
            by_cap[cap_type]["count"] += 1
        
        for data in by_cap.values():
            data["weight"] = round(data["market_value"] / total_mv * 100, 2) if total_mv > 0 else 0
            data["market_value"] = round(data["market_value"], 2)
        
        return by_cap
    
    @staticmethod
    def calculate_concentration(holdings: List[HoldingsDetail]) -> Dict:
        """计算持仓集中度"""
        if not holdings:
            return {
                "top5_weight": 0,
                "top10_weight": 0,
                "top20_weight": 0,
                "hhi_index": 0,
            }
        
        total_mv = sum(float(h.market_value or 0) for h in holdings)
        if total_mv == 0:
            return {
                "top5_weight": 0,
                "top10_weight": 0,
                "top20_weight": 0,
                "hhi_index": 0,
            }
        
        # 按市值排序
        sorted_holdings = sorted(holdings, key=lambda x: float(x.market_value or 0), reverse=True)
        
        # 计算TopN占比
        top5_mv = sum(float(h.market_value or 0) for h in sorted_holdings[:5])
        top10_mv = sum(float(h.market_value or 0) for h in sorted_holdings[:10])
        top20_mv = sum(float(h.market_value or 0) for h in sorted_holdings[:20])
        
        # 计算HHI指数 (Herfindahl-Hirschman Index)
        hhi = sum((float(h.market_value or 0) / total_mv * 100) ** 2 for h in holdings)
        
        return {
            "top5_weight": round(top5_mv / total_mv * 100, 2),
            "top10_weight": round(top10_mv / total_mv * 100, 2),
            "top20_weight": round(top20_mv / total_mv * 100, 2),
            "hhi_index": round(hhi, 2),
        }
    
    @staticmethod
    def get_top_holdings(holdings: List[HoldingsDetail], top_n: int = 20) -> List[Dict]:
        """获取前N大持仓"""
        total_mv = sum(float(h.market_value or 0) for h in holdings)
        
        sorted_holdings = sorted(holdings, key=lambda x: float(x.market_value or 0), reverse=True)
        
        result = []
        for h in sorted_holdings[:top_n]:
            mv = float(h.market_value or 0)
            result.append({
                "security_code": h.security_code,
                "security_name": h.security_name,
                "security_type": h.security_type,
                "market_value": round(mv, 2),
                "cost": round(float(h.cost or 0), 2),
                "weight": round(mv / total_mv * 100, 2) if total_mv > 0 else 0,
                "pnl": round(float(h.pnl or 0), 2),
                "pnl_ratio": round(float(h.pnl_ratio or 0) * 100, 2) if h.pnl_ratio else None,
                "industry_l1": h.industry_l1,
                "industry_l2": h.industry_l2,
                "market_cap_type": h.market_cap_type,
            })
        
        return result
    
    @staticmethod
    def compare_holdings(
        db: Session,
        product_id: int,
        date1: date,
        date2: date
    ) -> Dict:
        """对比两个日期的持仓变化"""
        holdings1 = HoldingsService.get_holdings_by_date(db, product_id, date1)
        holdings2 = HoldingsService.get_holdings_by_date(db, product_id, date2)
        
        # 转换为字典便于查找
        h1_dict = {h.security_code: h for h in holdings1}
        h2_dict = {h.security_code: h for h in holdings2}
        
        # 找出新增、减少、持续持有的证券
        codes1 = set(h1_dict.keys())
        codes2 = set(h2_dict.keys())
        
        added = codes2 - codes1  # 新增
        removed = codes1 - codes2  # 减少
        continued = codes1 & codes2  # 持续持有
        
        # 计算变化
        changes = []
        for code in continued:
            h1 = h1_dict[code]
            h2 = h2_dict[code]
            qty_change = float(h2.quantity or 0) - float(h1.quantity or 0)
            mv_change = float(h2.market_value or 0) - float(h1.market_value or 0)
            
            if abs(qty_change) > 0.01:  # 有变化
                changes.append({
                    "security_code": code,
                    "security_name": h2.security_name,
                    "quantity_before": float(h1.quantity or 0),
                    "quantity_after": float(h2.quantity or 0),
                    "quantity_change": qty_change,
                    "market_value_before": float(h1.market_value or 0),
                    "market_value_after": float(h2.market_value or 0),
                    "market_value_change": mv_change,
                })
        
        return {
            "date1": str(date1),
            "date2": str(date2),
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changes),
            "continued_count": len(continued),
            "added_securities": [
                {
                    "security_code": code,
                    "security_name": h2_dict[code].security_name,
                    "quantity": float(h2_dict[code].quantity or 0),
                    "market_value": float(h2_dict[code].market_value or 0),
                }
                for code in added
            ],
            "removed_securities": [
                {
                    "security_code": code,
                    "security_name": h1_dict[code].security_name,
                    "quantity": float(h1_dict[code].quantity or 0),
                    "market_value": float(h1_dict[code].market_value or 0),
                }
                for code in removed
            ],
            "changed_securities": sorted(changes, key=lambda x: abs(x["market_value_change"]), reverse=True),
        }
    
    @staticmethod
    def calculate_turnover_rate(
        db: Session,
        product_id: int,
        start_date: date,
        end_date: date
    ) -> Dict:
        """计算换手率"""
        # 获取期初期末持仓
        holdings_start = HoldingsService.get_holdings_by_date(db, product_id, start_date)
        holdings_end = HoldingsService.get_holdings_by_date(db, product_id, end_date)
        
        if not holdings_start or not holdings_end:
            return {"turnover_rate": 0, "message": "数据不足"}
        
        # 计算平均市值
        mv_start = sum(float(h.market_value or 0) for h in holdings_start)
        mv_end = sum(float(h.market_value or 0) for h in holdings_end)
        avg_mv = (mv_start + mv_end) / 2
        
        if avg_mv == 0:
            return {"turnover_rate": 0, "message": "平均市值为0"}
        
        # 计算买入和卖出金额
        h_start_dict = {h.security_code: h for h in holdings_start}
        h_end_dict = {h.security_code: h for h in holdings_end}
        
        buy_amount = 0
        sell_amount = 0
        
        # 新增的算买入
        for code in set(h_end_dict.keys()) - set(h_start_dict.keys()):
            buy_amount += float(h_end_dict[code].market_value or 0)
        
        # 减少的算卖出
        for code in set(h_start_dict.keys()) - set(h_end_dict.keys()):
            sell_amount += float(h_start_dict[code].market_value or 0)
        
        # 持续持有但数量变化的
        for code in set(h_start_dict.keys()) & set(h_end_dict.keys()):
            qty_change = float(h_end_dict[code].quantity or 0) - float(h_start_dict[code].quantity or 0)
            if qty_change > 0:
                buy_amount += abs(qty_change) * float(h_end_dict[code].market_price or 0)
            elif qty_change < 0:
                sell_amount += abs(qty_change) * float(h_start_dict[code].market_price or 0)
        
        # 换手率 = min(买入, 卖出) / 平均市值
        turnover = min(buy_amount, sell_amount) / avg_mv * 100
        
        return {
            "start_date": str(start_date),
            "end_date": str(end_date),
            "turnover_rate": round(turnover, 2),
            "buy_amount": round(buy_amount, 2),
            "sell_amount": round(sell_amount, 2),
            "avg_market_value": round(avg_mv, 2),
        }
    
    @staticmethod
    def get_comprehensive_analysis(
        db: Session,
        product_id: int,
        holding_date: Optional[date] = None
    ) -> Dict:
        """综合分析"""
        # 如果未指定日期，使用最新日期
        if not holding_date:
            holding_date = HoldingsService.get_latest_holding_date(db, product_id)
            if not holding_date:
                return {"error": "无持仓数据"}
        
        # 获取持仓
        holdings = HoldingsService.get_holdings_by_date(db, product_id, holding_date)
        if not holdings:
            return {"error": "指定日期无持仓数据"}
        
        # 基础指标
        metrics = HoldingsService.calculate_portfolio_metrics(holdings)
        
        # 各维度分析
        by_type = HoldingsService.analyze_by_security_type(holdings)
        by_industry_l1 = HoldingsService.analyze_by_industry(holdings, level=1)
        by_industry_l2 = HoldingsService.analyze_by_industry(holdings, level=2)
        by_market_cap = HoldingsService.analyze_by_market_cap(holdings)
        
        # 集中度
        concentration = HoldingsService.calculate_concentration(holdings)
        
        # 前20大持仓
        top_holdings = HoldingsService.get_top_holdings(holdings, 20)
        
        # 获取可用日期列表
        available_dates = db.query(HoldingsDetail.holding_date).filter(
            HoldingsDetail.product_id == product_id
        ).distinct().order_by(desc(HoldingsDetail.holding_date)).all()
        
        return {
            "holding_date": str(holding_date),
            "metrics": metrics,
            "by_security_type": by_type,
            "by_industry_l1": by_industry_l1,
            "by_industry_l2": by_industry_l2,
            "by_market_cap": by_market_cap,
            "concentration": concentration,
            "top_holdings": top_holdings,
            "available_dates": [str(d[0]) for d in available_dates],
        }
