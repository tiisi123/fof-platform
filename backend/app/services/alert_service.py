"""
异常预警服务 - 净值异常检测、业绩预警
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np

from app.models.nav import NavData
from app.models.product import Product
from app.models.manager import Manager


class AlertType:
    """预警类型"""
    NAV_DROP = "nav_drop"              # 净值大幅下跌
    NAV_ANOMALY = "nav_anomaly"        # 净值异常波动
    DRAWDOWN = "drawdown"              # 回撤预警
    NO_UPDATE = "no_update"            # 长期未更新
    VOLATILITY = "volatility"          # 波动率异常


class AlertLevel:
    """预警级别"""
    INFO = "info"           # 提示
    WARNING = "warning"     # 警告
    CRITICAL = "critical"   # 严重


class AlertService:
    """异常预警服务"""
    
    # 默认阈值
    DEFAULT_THRESHOLDS = {
        "nav_drop_warning": -0.03,      # 单日跌幅超3%警告
        "nav_drop_critical": -0.05,     # 单日跌幅超5%严重
        "drawdown_warning": -0.10,      # 回撤超10%警告
        "drawdown_critical": -0.20,     # 回撤超20%严重
        "no_update_days": 14,           # 超过14天未更新
        "volatility_threshold": 2.0,    # 波动率超过历史2倍
        "anomaly_std_multiple": 3.0,    # 异常检测：超过3倍标准差
    }

    def __init__(self, db: Session):
        self.db = db
        
        # 预警阈值配置（从默认值复制）
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        # 合并运行时自定义配置
        try:
            from app.api.v1.alerts import _alert_rules_store
            self.thresholds.update(_alert_rules_store)
        except ImportError:
            pass
    
    def check_all_products(self) -> List[Dict[str, Any]]:
        """
        检查所有产品的异常情况
        
        Returns:
            预警列表
        """
        alerts = []
        
        # 获取所有有净值数据的产品
        products = self.db.query(Product).all()
        
        for product in products:
            product_alerts = self.check_product(product.id)
            alerts.extend(product_alerts)
        
        # 按级别和时间排序
        level_order = {AlertLevel.CRITICAL: 0, AlertLevel.WARNING: 1, AlertLevel.INFO: 2}
        alerts.sort(key=lambda x: (level_order.get(x['level'], 3), x.get('date', '') or ''), reverse=True)
        
        return alerts
    
    def check_product(self, product_id: int) -> List[Dict[str, Any]]:
        """
        检查单个产品的异常情况
        
        Args:
            product_id: 产品ID
        
        Returns:
            预警列表
        """
        alerts = []
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return alerts
        
        # 获取管理人信息
        manager = self.db.query(Manager).filter(Manager.id == product.manager_id).first()
        manager_name = manager.manager_name if manager else ""
        
        # 获取最近的净值数据（最多180天）
        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        
        nav_list = self.db.query(NavData).filter(
            NavData.product_id == product_id,
            NavData.nav_date >= start_date
        ).order_by(NavData.nav_date.asc()).all()
        
        if not nav_list:
            return alerts
        
        base_info = {
            "product_id": product_id,
            "product_name": product.product_name,
            "product_code": product.product_code,
            "manager_name": manager_name,
        }
        
        # 1. 检查净值更新
        alerts.extend(self._check_no_update(nav_list, base_info))
        
        # 2. 检查单日大幅下跌
        alerts.extend(self._check_nav_drop(nav_list, base_info))
        
        # 3. 检查回撤
        alerts.extend(self._check_drawdown(nav_list, base_info))
        
        # 4. 检查异常波动
        alerts.extend(self._check_anomaly(nav_list, base_info))
        
        return alerts
    
    def _check_no_update(self, nav_list: List[NavData], base_info: dict) -> List[Dict]:
        """检查长期未更新"""
        alerts = []
        
        if not nav_list:
            return alerts
        
        latest_date = nav_list[-1].nav_date
        days_since_update = (date.today() - latest_date).days
        
        if days_since_update > self.thresholds["no_update_days"]:
            alerts.append({
                **base_info,
                "type": AlertType.NO_UPDATE,
                "level": AlertLevel.WARNING,
                "title": "净值长期未更新",
                "message": f"最新净值日期为 {latest_date}，已超过 {days_since_update} 天未更新",
                "date": str(latest_date),
                "value": days_since_update,
                "threshold": self.thresholds["no_update_days"],
            })
        
        return alerts
    
    def _check_nav_drop(self, nav_list: List[NavData], base_info: dict) -> List[Dict]:
        """检查单日大幅下跌"""
        alerts = []
        
        if len(nav_list) < 2:
            return alerts
        
        # 只检查最近30天
        recent_nav = nav_list[-30:] if len(nav_list) > 30 else nav_list
        
        for i in range(1, len(recent_nav)):
            prev_nav = float(recent_nav[i-1].unit_nav)
            curr_nav = float(recent_nav[i].unit_nav)
            
            if prev_nav > 0:
                daily_return = (curr_nav - prev_nav) / prev_nav
                
                if daily_return <= self.thresholds["nav_drop_critical"]:
                    alerts.append({
                        **base_info,
                        "type": AlertType.NAV_DROP,
                        "level": AlertLevel.CRITICAL,
                        "title": "单日净值大幅下跌",
                        "message": f"{recent_nav[i].nav_date} 单日跌幅 {daily_return*100:.2f}%",
                        "date": str(recent_nav[i].nav_date),
                        "value": daily_return,
                        "threshold": self.thresholds["nav_drop_critical"],
                    })
                elif daily_return <= self.thresholds["nav_drop_warning"]:
                    alerts.append({
                        **base_info,
                        "type": AlertType.NAV_DROP,
                        "level": AlertLevel.WARNING,
                        "title": "单日净值下跌",
                        "message": f"{recent_nav[i].nav_date} 单日跌幅 {daily_return*100:.2f}%",
                        "date": str(recent_nav[i].nav_date),
                        "value": daily_return,
                        "threshold": self.thresholds["nav_drop_warning"],
                    })
        
        return alerts
    
    def _check_drawdown(self, nav_list: List[NavData], base_info: dict) -> List[Dict]:
        """检查回撤"""
        alerts = []
        
        if len(nav_list) < 2:
            return alerts
        
        # 计算当前回撤
        peak = float(nav_list[0].unit_nav)
        peak_date = nav_list[0].nav_date
        
        for nav in nav_list:
            nav_value = float(nav.unit_nav)
            if nav_value > peak:
                peak = nav_value
                peak_date = nav.nav_date
        
        # 最新净值
        latest_nav = float(nav_list[-1].unit_nav)
        current_drawdown = (latest_nav - peak) / peak if peak > 0 else 0
        
        if current_drawdown <= self.thresholds["drawdown_critical"]:
            alerts.append({
                **base_info,
                "type": AlertType.DRAWDOWN,
                "level": AlertLevel.CRITICAL,
                "title": "严重回撤预警",
                "message": f"自 {peak_date} 高点以来回撤 {current_drawdown*100:.2f}%",
                "date": str(nav_list[-1].nav_date),
                "value": current_drawdown,
                "threshold": self.thresholds["drawdown_critical"],
                "peak_date": str(peak_date),
                "peak_value": peak,
            })
        elif current_drawdown <= self.thresholds["drawdown_warning"]:
            alerts.append({
                **base_info,
                "type": AlertType.DRAWDOWN,
                "level": AlertLevel.WARNING,
                "title": "回撤预警",
                "message": f"自 {peak_date} 高点以来回撤 {current_drawdown*100:.2f}%",
                "date": str(nav_list[-1].nav_date),
                "value": current_drawdown,
                "threshold": self.thresholds["drawdown_warning"],
                "peak_date": str(peak_date),
                "peak_value": peak,
            })
        
        return alerts
    
    def _check_anomaly(self, nav_list: List[NavData], base_info: dict) -> List[Dict]:
        """检查异常波动（基于历史标准差）"""
        alerts = []
        
        if len(nav_list) < 30:
            return alerts
        
        # 计算日收益率
        daily_returns = []
        for i in range(1, len(nav_list)):
            prev_nav = float(nav_list[i-1].unit_nav)
            curr_nav = float(nav_list[i].unit_nav)
            if prev_nav > 0:
                daily_returns.append((curr_nav - prev_nav) / prev_nav)
        
        if len(daily_returns) < 20:
            return alerts
        
        # 计算历史均值和标准差（排除最近5天）
        historical_returns = daily_returns[:-5]
        if len(historical_returns) < 15:
            return alerts
        
        mean_return = np.mean(historical_returns)
        std_return = np.std(historical_returns)
        
        if std_return == 0:
            return alerts
        
        # 检查最近5天是否有异常
        recent_returns = daily_returns[-5:]
        threshold = self.thresholds["anomaly_std_multiple"]
        
        for i, ret in enumerate(recent_returns):
            z_score = abs(ret - mean_return) / std_return
            if z_score > threshold:
                idx = len(nav_list) - 5 + i
                alerts.append({
                    **base_info,
                    "type": AlertType.NAV_ANOMALY,
                    "level": AlertLevel.WARNING,
                    "title": "净值异常波动",
                    "message": f"{nav_list[idx].nav_date} 日收益率 {ret*100:.2f}% 偏离历史均值 {z_score:.1f} 个标准差",
                    "date": str(nav_list[idx].nav_date),
                    "value": ret,
                    "z_score": z_score,
                    "threshold": threshold,
                })
        
        return alerts
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """
        获取预警汇总
        
        Returns:
            预警统计信息
        """
        alerts = self.check_all_products()
        
        # 统计
        summary = {
            "total": len(alerts),
            "by_level": {
                AlertLevel.CRITICAL: 0,
                AlertLevel.WARNING: 0,
                AlertLevel.INFO: 0,
            },
            "by_type": {
                AlertType.NAV_DROP: 0,
                AlertType.NAV_ANOMALY: 0,
                AlertType.DRAWDOWN: 0,
                AlertType.NO_UPDATE: 0,
                AlertType.VOLATILITY: 0,
            },
            "alerts": alerts[:50],  # 只返回前50条
        }
        
        for alert in alerts:
            level = alert.get("level")
            alert_type = alert.get("type")
            
            if level in summary["by_level"]:
                summary["by_level"][level] += 1
            if alert_type in summary["by_type"]:
                summary["by_type"][alert_type] += 1
        
        return summary
    
    def get_product_alerts(self, product_id: int) -> Dict[str, Any]:
        """获取单个产品的预警信息"""
        alerts = self.check_product(product_id)
        
        return {
            "product_id": product_id,
            "total": len(alerts),
            "critical_count": sum(1 for a in alerts if a.get("level") == AlertLevel.CRITICAL),
            "warning_count": sum(1 for a in alerts if a.get("level") == AlertLevel.WARNING),
            "alerts": alerts,
        }
