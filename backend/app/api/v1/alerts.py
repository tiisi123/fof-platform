"""
异常预警 API
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.alert_service import AlertService, AlertType, AlertLevel
from app.services.dingtalk_service import dingtalk_service

router = APIRouter(prefix="/alerts", tags=["异常预警"])


@router.get("", summary="获取预警汇总")
async def get_alerts_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有产品的预警汇总
    
    包含：
    - 预警总数
    - 按级别统计（严重/警告/提示）
    - 按类型统计（净值下跌/回撤/未更新/异常波动）
    - 最新50条预警详情
    """
    service = AlertService(db)
    return service.get_alerts_summary()


@router.get("/product/{product_id}", summary="获取产品预警")
async def get_product_alerts(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个产品的预警信息
    """
    service = AlertService(db)
    return service.get_product_alerts(product_id)


@router.get("/types", summary="获取预警类型")
async def get_alert_types():
    """获取预警类型列表"""
    return [
        {"key": AlertType.NAV_DROP, "name": "净值下跌", "description": "单日净值大幅下跌"},
        {"key": AlertType.NAV_ANOMALY, "name": "异常波动", "description": "净值偏离历史均值"},
        {"key": AlertType.DRAWDOWN, "name": "回撤预警", "description": "累计回撤超过阈值"},
        {"key": AlertType.NO_UPDATE, "name": "未更新", "description": "长期未更新净值"},
        {"key": AlertType.VOLATILITY, "name": "波动率异常", "description": "波动率超过历史水平"},
    ]


@router.get("/levels", summary="获取预警级别")
async def get_alert_levels():
    """获取预警级别列表"""
    return [
        {"key": AlertLevel.CRITICAL, "name": "严重", "color": "#f56c6c"},
        {"key": AlertLevel.WARNING, "name": "警告", "color": "#e6a23c"},
        {"key": AlertLevel.INFO, "name": "提示", "color": "#909399"},
    ]


# ========== 钉钉推送相关 ==========

@router.post("/dingtalk/push", summary="推送预警到钉钉")
async def push_alerts_to_dingtalk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发推送当前预警汇总到钉钉群"""
    service = AlertService(db)
    alerts = service.check_all_products()
    
    if not alerts:
        return {"message": "当前无预警", "pushed": False}
    
    success = dingtalk_service.send_alerts_summary(alerts)
    return {
        "message": "推送成功" if success else "推送失败",
        "pushed": success,
        "alert_count": len(alerts),
    }


@router.post("/dingtalk/test", summary="测试钉钉推送")
async def test_dingtalk_push(
    current_user: User = Depends(get_current_user),
):
    """发送测试消息到钉钉群，验证配置是否正确"""
    success = dingtalk_service.send_text("✅ FOF管理平台钉钉推送测试成功！")
    return {
        "message": "测试成功" if success else "测试失败，请检查配置",
        "success": success,
        "config": {
            "enabled": settings.DINGTALK_ENABLED,
            "webhook_configured": bool(settings.DINGTALK_WEBHOOK_URL),
            "secret_configured": bool(settings.DINGTALK_SECRET),
        },
    }


# ========== 预警规则配置 ==========

# 全局规则存储（生产环境建议存数据库）
_alert_rules_store: dict = {}


@router.get("/rules", summary="获取预警规则配置")
async def get_alert_rules(
    current_user: User = Depends(get_current_user),
):
    """获取当前预警阈值规则配置"""
    service = AlertService(None)
    rules = {**service.thresholds}
    # 覆盖自定义配置
    rules.update(_alert_rules_store)
    return {
        "rules": rules,
        "rule_descriptions": {
            "nav_drop_warning": {"name": "净值下跌-警告阈值", "unit": "%", "multiplier": 100, "description": "单日跌幅超过此值触发警告"},
            "nav_drop_critical": {"name": "净值下跌-严重阈值", "unit": "%", "multiplier": 100, "description": "单日跌幅超过此值触发严重预警"},
            "drawdown_warning": {"name": "回撤-警告阈值", "unit": "%", "multiplier": 100, "description": "累计回撤超过此值触发警告"},
            "drawdown_critical": {"name": "回撤-严重阈值", "unit": "%", "multiplier": 100, "description": "累计回撤超过此值触发严重预警"},
            "no_update_days": {"name": "未更新天数", "unit": "天", "multiplier": 1, "description": "超过此天数未更新净值触发预警"},
            "volatility_threshold": {"name": "波动率异常倍数", "unit": "倍", "multiplier": 1, "description": "波动率超过历史水平的倍数"},
            "anomaly_std_multiple": {"name": "异常波动标准差倍数", "unit": "倍", "multiplier": 1, "description": "日收益率偏离均值超过此倍标准差"},
        }
    }


@router.put("/rules", summary="更新预警规则配置")
async def update_alert_rules(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """更新预警阈值规则配置"""
    body = await request.json()
    rules = body.get("rules", {})
    
    # 验证字段
    valid_keys = {
        "nav_drop_warning", "nav_drop_critical",
        "drawdown_warning", "drawdown_critical",
        "no_update_days", "volatility_threshold", "anomaly_std_multiple"
    }
    
    updated = {}
    for key, value in rules.items():
        if key in valid_keys:
            try:
                updated[key] = float(value) if key != "no_update_days" else int(value)
            except (ValueError, TypeError):
                pass
    
    _alert_rules_store.update(updated)
    
    return {"message": "预警规则更新成功", "rules": {**AlertService(None).thresholds, **_alert_rules_store}}


@router.get("/dingtalk/config", summary="获取钉钉推送配置状态")
async def get_dingtalk_config(
    current_user: User = Depends(get_current_user),
):
    """获取钉钉推送的配置状态"""
    return {
        "enabled": settings.DINGTALK_ENABLED,
        "webhook_configured": bool(settings.DINGTALK_WEBHOOK_URL),
        "secret_configured": bool(settings.DINGTALK_SECRET),
    }
