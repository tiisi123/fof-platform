"""
组合管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.portfolio_service import PortfolioService
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioListResponse,
    ComponentCreate, ComponentUpdate, ComponentResponse,
    PortfolioNavResponse, PortfolioContributionResponse, PortfolioPerformance,
    AdjustmentCreate, AdjustmentResponse,
    HoldingCreate, HoldingResponse, HoldingsBatchCreate, PortfolioNavRecord,
    SimulateRequest, RiskBudgetConfig,
    HoldingsDetailBatchCreate
)

router = APIRouter()


# ============ 组合CRUD ============

@router.get("", summary="获取组合列表")
async def get_portfolios(
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(20, ge=1, le=100, description="每页条数"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组合列表"""
    service = PortfolioService(db)
    portfolios, total = service.get_portfolios(
        skip=skip, limit=limit, status=status, search=search
    )
    
    # 构建响应
    items = []
    for p in portfolios:
        active_components = [c for c in p.components if c.is_active]
        # 获取最新净值
        latest_nav_record = service.get_latest_nav(p.id)
        items.append(PortfolioListResponse(
            id=p.id,
            portfolio_code=p.portfolio_code,
            name=p.name,
            portfolio_type=p.portfolio_type or "invested",
            description=p.description,
            status=p.status,
            start_date=p.start_date,
            component_count=len(active_components),
            total_weight=sum(c.weight for c in active_components),
            latest_nav=latest_nav_record.unit_nav if latest_nav_record else None,
            total_return=latest_nav_record.cumulative_return if latest_nav_record else None,
            created_at=p.created_at
        ))
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("", response_model=PortfolioResponse, summary="创建组合")
async def create_portfolio(
    data: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新组合"""
    service = PortfolioService(db)
    portfolio = service.create_portfolio(data, user_id=current_user.id)
    return _build_portfolio_response(portfolio)


@router.get("/{portfolio_id}", response_model=PortfolioResponse, summary="获取组合详情")
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组合详情"""
    service = PortfolioService(db)
    portfolio = service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")
    return _build_portfolio_response(portfolio)


@router.put("/{portfolio_id}", response_model=PortfolioResponse, summary="更新组合")
async def update_portfolio(
    portfolio_id: int,
    data: PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新组合信息"""
    service = PortfolioService(db)
    portfolio = service.update_portfolio(portfolio_id, data)
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")
    return _build_portfolio_response(portfolio)


@router.delete("/{portfolio_id}", summary="删除组合")
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除组合（软删除）"""
    service = PortfolioService(db)
    success = service.delete_portfolio(portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail="组合不存在")
    return {"message": "删除成功"}


# ============ 成分管理 ============

@router.post("/{portfolio_id}/components", response_model=ComponentResponse, summary="添加成分")
async def add_component(
    portfolio_id: int,
    data: ComponentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加组合成分"""
    service = PortfolioService(db)
    component = service.add_component(portfolio_id, data)
    if not component:
        raise HTTPException(status_code=404, detail="组合不存在")
    return _build_component_response(component)


@router.put("/components/{component_id}", response_model=ComponentResponse, summary="更新成分")
async def update_component(
    component_id: int,
    data: ComponentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新组合成分"""
    service = PortfolioService(db)
    component = service.update_component(component_id, data)
    if not component:
        raise HTTPException(status_code=404, detail="成分不存在")
    return _build_component_response(component)


@router.delete("/components/{component_id}", summary="移除成分")
async def remove_component(
    component_id: int,
    exit_date: Optional[date] = Query(None, description="退出日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除组合成分"""
    service = PortfolioService(db)
    success = service.remove_component(component_id, exit_date)
    if not success:
        raise HTTPException(status_code=404, detail="成分不存在")
    return {"message": "移除成功"}


@router.put("/{portfolio_id}/components/batch", summary="批量设置成分")
async def set_components(
    portfolio_id: int,
    components: list[ComponentCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量设置组合成分（替换所有）"""
    service = PortfolioService(db)
    result = service.set_components(portfolio_id, components)
    return {
        "message": "设置成功",
        "count": len(result)
    }


# ============ 组合分析 ============

@router.get("/{portfolio_id}/nav", summary="获取组合净值")
async def get_portfolio_nav(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组合净值序列"""
    service = PortfolioService(db)
    result = service.calculate_portfolio_nav(portfolio_id, start_date, end_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # 转换为可序列化格式
    return {
        "portfolio_id": result["portfolio_id"],
        "portfolio_name": result["portfolio_name"],
        "start_date": result["start_date"].isoformat() if result.get("start_date") else None,
        "end_date": result["end_date"].isoformat() if result.get("end_date") else None,
        "nav_series": [
            {
                "date": point.date.isoformat(),
                "nav": float(point.nav),
                "daily_return": float(point.daily_return) if point.daily_return else 0
            }
            for point in result.get("nav_series", [])
        ],
        "initial_nav": float(result.get("initial_nav", 1)),
        "latest_nav": float(result.get("latest_nav", 1)),
        "total_return": float(result.get("total_return", 0)),
        "nav_quality": result.get("nav_quality")
    }


@router.get("/{portfolio_id}/contribution", summary="获取成分贡献")
async def get_contribution(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取成分贡献分析"""
    service = PortfolioService(db)
    result = service.calculate_contribution(portfolio_id, start_date, end_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "portfolio_id": result["portfolio_id"],
        "portfolio_name": result["portfolio_name"],
        "start_date": result["start_date"].isoformat(),
        "end_date": result["end_date"].isoformat(),
        "portfolio_return": float(result["portfolio_return"]),
        "contributions": [
            {
                "product_id": c.product_id,
                "product_code": c.product_code,
                "product_name": c.product_name,
                "weight": float(c.weight),
                "period_return": float(c.period_return),
                "contribution": float(c.contribution),
                "contribution_pct": float(c.contribution_pct)
            }
            for c in result["contributions"]
        ]
    }


@router.get("/{portfolio_id}/performance", summary="获取组合业绩")
async def get_performance(
    portfolio_id: int,
    period: str = Query("1m", description="周期: 1w/1m/3m/6m/1y/ytd/inception"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组合业绩指标"""
    service = PortfolioService(db)
    result = service.calculate_performance(portfolio_id, period)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "portfolio_id": result["portfolio_id"],
        "portfolio_name": result["portfolio_name"],
        "period": result["period"],
        "total_return": float(result["total_return"]),
        "annualized_return": float(result["annualized_return"]),
        "volatility": float(result["volatility"]),
        "max_drawdown": float(result["max_drawdown"]),
        "sharpe_ratio": float(result["sharpe_ratio"]),
        "calmar_ratio": float(result["calmar_ratio"])
    }


# ============ 调整记录 ============

@router.post("/{portfolio_id}/adjustments", response_model=AdjustmentResponse, summary="记录调整")
async def record_adjustment(
    portfolio_id: int,
    data: AdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """记录组合调整"""
    service = PortfolioService(db)
    adjustment = service.record_adjustment(portfolio_id, data, user_id=current_user.id)
    if not adjustment:
        raise HTTPException(status_code=404, detail="组合不存在")
    return adjustment


@router.get("/{portfolio_id}/adjustments", summary="获取调整记录")
async def get_adjustments(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组合调整记录"""
    service = PortfolioService(db)
    adjustments = service.get_adjustments(portfolio_id)
    return {
        "items": adjustments,
        "total": len(adjustments)
    }


# ============ 持仓快照 ============

@router.get("/{portfolio_id}/holdings", summary="获取持仓快照")
async def get_holdings(
    portfolio_id: int,
    holding_date: Optional[date] = Query(None, description="持仓日期，默认最新"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组合持仓快照"""
    service = PortfolioService(db)
    holdings = service.get_holdings_by_date(portfolio_id, holding_date)
    
    items = []
    total_mv = sum(float(h.market_value) for h in holdings) or 0
    for h in holdings:
        product = h.product
        items.append({
            "id": h.id,
            "portfolio_id": h.portfolio_id,
            "product_id": h.product_id,
            "holding_date": h.holding_date.isoformat(),
            "shares": float(h.shares),
            "market_value": float(h.market_value),
            "weight": float(h.weight),
            "cost": float(h.cost),
            "pnl": float(h.pnl),
            "pnl_ratio": float(h.pnl_ratio),
            "product_code": product.product_code if product else None,
            "product_name": product.product_name if product else None,
            "manager_name": product.manager.manager_name if product and product.manager else None
        })
    
    # 获取可用日期列表
    available_dates = service.get_holdings_dates(portfolio_id)
    
    return {
        "items": items,
        "total": len(items),
        "holding_date": holding_date.isoformat() if holding_date else (holdings[0].holding_date.isoformat() if holdings else None),
        "total_market_value": total_mv,
        "total_pnl": sum(float(h.pnl) for h in holdings),
        "available_dates": [d.isoformat() for d in available_dates]
    }


@router.post("/{portfolio_id}/holdings", summary="录入持仓快照")
async def save_holdings(
    portfolio_id: int,
    data: HoldingsBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量录入某日持仓快照"""
    service = PortfolioService(db)
    result = service.save_holdings_snapshot(portfolio_id, data.holding_date, data.holdings)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    return {"message": "录入成功", "count": len(result)}


# ============ 净值持久化 ============

@router.get("/{portfolio_id}/nav/history", summary="获取持久化净值")
async def get_nav_history(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持久化的组合净值序列"""
    service = PortfolioService(db)
    nav_records = service.get_persisted_nav(portfolio_id, start_date, end_date)
    return {
        "portfolio_id": portfolio_id,
        "items": [
            {
                "nav_date": r.nav_date.isoformat(),
                "total_nav": float(r.total_nav) if r.total_nav else None,
                "unit_nav": float(r.unit_nav) if r.unit_nav else None,
                "daily_return": float(r.daily_return) if r.daily_return else 0,
                "cumulative_return": float(r.cumulative_return) if r.cumulative_return else 0
            }
            for r in nav_records
        ],
        "total": len(nav_records)
    }


@router.post("/{portfolio_id}/nav/calculate", summary="计算并持久化净值")
async def calculate_and_persist_nav(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """触发组合净值计算并持久化"""
    service = PortfolioService(db)
    result = service.persist_portfolio_nav(portfolio_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============ Brinson归因 & 风险归因 ============

@router.get("/{portfolio_id}/attribution/brinson", summary="Brinson归因分析")
async def get_brinson_attribution(
    portfolio_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.brinson_attribution(portfolio_id, start_date, end_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    result["start_date"] = result["start_date"].isoformat()
    result["end_date"] = result["end_date"].isoformat()
    return result


@router.get("/{portfolio_id}/attribution/risk", summary="风险贡献归因")
async def get_risk_contribution(
    portfolio_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.risk_contribution(portfolio_id, start_date, end_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    result["start_date"] = result["start_date"].isoformat()
    result["end_date"] = result["end_date"].isoformat()
    return result


# ============ 调仓模拟 ============

@router.post("/{portfolio_id}/simulate", summary="调仓模拟")
async def simulate_rebalance(
    portfolio_id: int,
    data: SimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    new_weights = {item.product_id: float(item.weight) for item in data.weights}
    result = service.simulate_rebalance(portfolio_id, new_weights, data.start_date, data.end_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    result["start_date"] = result["start_date"].isoformat()
    result["end_date"] = result["end_date"].isoformat()
    return result


# ============ 穿透分析 ============

@router.get("/{portfolio_id}/lookthrough", summary="穿透分析")
async def get_lookthrough(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.lookthrough_analysis(portfolio_id)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============ 风险预算 ============

@router.get("/{portfolio_id}/risk-budget", summary="获取风险预算配置")
async def get_risk_budget(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.get_risk_budget(portfolio_id)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    return result


@router.put("/{portfolio_id}/risk-budget", summary="更新风险预算配置")
async def update_risk_budget(
    portfolio_id: int,
    data: RiskBudgetConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    config = data.model_dump(exclude_none=True)
    result = service.update_risk_budget(portfolio_id, config)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    return {"message": "风险预算配置已更新", "config": config}


@router.get("/{portfolio_id}/risk-budget/check", summary="检查风险预算超限")
async def check_risk_budget(
    portfolio_id: int,
    period: str = Query("3m"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.check_risk_budget(portfolio_id, period)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    return result


# ============ Brinson 第3层 管理人归因 ============

@router.get("/{portfolio_id}/attribution/brinson-manager", summary="管理人选择归因")
async def get_brinson_manager_attribution(
    portfolio_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.brinson_manager_attribution(portfolio_id, start_date, end_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    result["start_date"] = result["start_date"].isoformat()
    result["end_date"] = result["end_date"].isoformat()
    return result


# ============ Brinson 第4层 个券归因 ============

@router.get("/{portfolio_id}/attribution/brinson-security", summary="个券选择归因")
async def get_brinson_security_attribution(
    portfolio_id: int,
    holding_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.brinson_security_attribution(portfolio_id, holding_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    result["start_date"] = result["start_date"].isoformat()
    result["end_date"] = result["end_date"].isoformat()
    return result


# ============ 多因子分析 ============

@router.get("/{portfolio_id}/factor-analysis", summary="多因子分析")
async def get_factor_analysis(
    portfolio_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.multi_factor_analysis(portfolio_id, start_date, end_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    result["start_date"] = result["start_date"].isoformat()
    result["end_date"] = result["end_date"].isoformat()
    return result


# ============ 底层持仓明细 ============

@router.get("/{portfolio_id}/holdings-detail", summary="获取底层持仓明细")
async def get_holdings_detail(
    portfolio_id: int,
    holding_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    details = service.get_holdings_detail(portfolio_id, holding_date)
    items = []
    for d in details:
        product = d.product
        items.append({
            "id": d.id,
            "product_id": d.product_id,
            "product_name": product.product_name if product else None,
            "holding_date": d.holding_date.isoformat(),
            "security_code": d.security_code,
            "security_name": d.security_name,
            "security_type": d.security_type,
            "quantity": float(d.quantity) if d.quantity else 0,
            "market_value": float(d.market_value) if d.market_value else 0,
            "cost": float(d.cost) if d.cost else 0,
            "weight": float(d.weight) if d.weight else 0,
            "industry_l1": d.industry_l1,
            "industry_l2": d.industry_l2,
            "market_cap_type": d.market_cap_type
        })
    return {"items": items, "total": len(items)}


@router.post("/{portfolio_id}/holdings-detail", summary="导入底层持仓明细")
async def import_holdings_detail(
    portfolio_id: int,
    data: HoldingsDetailBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    # 验证组合存在
    portfolio = service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")
    count = service.save_holdings_detail(data.items)
    return {"message": f"已导入 {count} 条底层持仓明细", "count": count}


# ============ 四级估值表分析 ============

@router.get("/{portfolio_id}/holdings-detail/analysis", summary="四级估值表分析")
async def get_holdings_detail_analysis(
    portfolio_id: int,
    holding_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    result = service.holdings_detail_analysis(portfolio_id, holding_date)
    if not result:
        raise HTTPException(status_code=404, detail="组合不存在")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    result["holding_date"] = result["holding_date"].isoformat()
    return result


# ============ VaR与风险归因 ============

from app.services.var_service import calculate_portfolio_var, calculate_risk_attribution


@router.get("/{portfolio_id}/var", summary="计算组合VaR")
async def get_portfolio_var(
    portfolio_id: int,
    method: str = Query("historical", description="方法: historical/parametric"),
    holding_period: int = Query(1, description="持有期(天)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """计算组合VaR (Value at Risk)"""
    result = calculate_portfolio_var(portfolio_id, db, method=method, holding_period=holding_period)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{portfolio_id}/risk-attribution", summary="组合风险归因")
async def get_risk_attribution(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """计算组合风险归因（各成分风险贡献）"""
    result = calculate_risk_attribution(portfolio_id, db)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============ 辅助函数 ============

def _build_portfolio_response(portfolio) -> PortfolioResponse:
    """构建组合响应"""
    components = []
    for c in portfolio.components:
        if c.is_active:
            components.append(_build_component_response(c))
    
    return PortfolioResponse(
        id=portfolio.id,
        portfolio_code=portfolio.portfolio_code,
        name=portfolio.name,
        portfolio_type=portfolio.portfolio_type or "invested",
        description=portfolio.description,
        benchmark_code=portfolio.benchmark_code,
        benchmark_name=portfolio.benchmark_name,
        start_date=portfolio.start_date,
        initial_amount=portfolio.initial_amount,
        status=portfolio.status,
        created_by=portfolio.created_by,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        components=components
    )


def _build_component_response(component) -> ComponentResponse:
    """构建成分响应"""
    product = component.product
    return ComponentResponse(
        id=component.id,
        portfolio_id=component.portfolio_id,
        product_id=component.product_id,
        weight=component.weight,
        join_date=component.join_date,
        exit_date=component.exit_date,
        is_active=component.is_active,
        product_code=product.product_code if product else None,
        product_name=product.product_name if product else None,
        manager_name=product.manager.manager_name if product and product.manager else None
    )

