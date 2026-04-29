"""
报表中心 API
"""
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["报表中心"])


@router.get("/manager", summary="导出管理人汇总报表")
async def export_manager_report(
    pool_category: Optional[str] = Query(None, description="跟踪池分类"),
    primary_strategy: Optional[str] = Query(None, description="一级策略"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出管理人汇总报表
    
    包含：管理人基本信息、旗下产品数量、代表产品业绩指标
    """
    service = ReportService(db)
    output = service.generate_manager_report(
        pool_category=pool_category,
        primary_strategy=primary_strategy
    )
    
    filename = f"管理人汇总报表_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


@router.get("/pool", summary="导出跟踪池报表")
async def export_pool_report(
    pool_category: Optional[str] = Query(None, description="跟踪池分类，不传则导出全部"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出跟踪池报表
    
    包含：各分类管理人及其代表产品的多周期业绩
    - 不传 pool_category 则导出所有分类（每个分类一个工作表）
    """
    service = ReportService(db)
    output = service.generate_pool_report(pool_category=pool_category)
    
    filename = f"跟踪池报表_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


@router.get("/product", summary="导出产品业绩报表")
async def export_product_report(
    strategy_type: Optional[str] = Query(None, description="策略类型"),
    period: str = Query("1y", description="业绩周期: 1m/3m/6m/1y/ytd"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出产品业绩报表
    
    包含：产品基本信息、最新净值、多周期收益、风险指标
    """
    service = ReportService(db)
    output = service.generate_product_report(
        strategy_type=strategy_type,
        period=period
    )
    
    filename = f"产品业绩报表_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


@router.get("/portfolio", summary="导出组合报表")
async def export_portfolio_report(
    portfolio_id: Optional[int] = Query(None, description="组合ID，不传则导出全部"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出组合报表
    
    包含：组合概览、成分明细
    """
    service = ReportService(db)
    output = service.generate_portfolio_report(portfolio_id=portfolio_id)
    
    filename = f"组合报表_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


@router.get("/project", summary="导出一级项目报表")
async def export_project_report(
    stage: Optional[str] = Query(None, description="项目阶段"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出一级项目汇总报表
    """
    service = ReportService(db)
    output = service.generate_project_report(stage=stage)
    
    filename = f"一级项目报表_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


@router.get("/nav/{product_id}", summary="导出产品净值数据")
async def export_nav_data(
    product_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出指定产品的净值数据
    """
    service = ReportService(db)
    
    try:
        output = service.export_nav_data(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    filename = f"净值数据_{product_id}_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


# ========== 报表预览 ==========

@router.get("/preview/{report_key}", summary="报表数据预览")
async def preview_report(
    report_key: str,
    pool_category: Optional[str] = Query(None),
    primary_strategy: Optional[str] = Query(None),
    strategy_type: Optional[str] = Query(None),
    period: str = Query("1y"),
    portfolio_id: Optional[int] = Query(None),
    stage: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回JSON格式的报表预览数据（前20条）"""
    service = ReportService(db)
    try:
        data = service.get_preview_data(
            report_key,
            pool_category=pool_category,
            primary_strategy=primary_strategy,
            strategy_type=strategy_type,
            period=period,
            portfolio_id=portfolio_id,
            stage=stage,
        )
        return data
    except Exception as e:
        return {"columns": [], "rows": [], "total": 0, "error": str(e)}


# 报表类型列表（供前端使用）
@router.get("/types", summary="获取可用报表类型")
async def get_report_types(
    current_user: User = Depends(get_current_user)
):
    """获取可用的报表类型列表"""
    return [
        {
            "key": "manager",
            "name": "管理人汇总报表",
            "description": "管理人基本信息、产品数量、代表产品业绩",
            "filters": ["pool_category", "primary_strategy"]
        },
        {
            "key": "pool",
            "name": "跟踪池报表",
            "description": "各分类管理人及代表产品多周期业绩",
            "filters": ["pool_category"]
        },
        {
            "key": "product",
            "name": "产品业绩报表",
            "description": "产品信息、最新净值、多周期收益、风险指标",
            "filters": ["strategy_type", "period"]
        },
        {
            "key": "portfolio",
            "name": "组合报表",
            "description": "组合概览、成分明细",
            "filters": ["portfolio_id"]
        },
        {
            "key": "project",
            "name": "一级项目报表",
            "description": "项目基本信息、阶段、投资金额等",
            "filters": ["stage"]
        }
    ]
