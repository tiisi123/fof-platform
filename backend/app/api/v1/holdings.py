"""
持仓明细 API - 四级估值表
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import pandas as pd
import io

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.holdings_detail import HoldingsDetail

router = APIRouter(prefix="/holdings", tags=["持仓明细"])


def _h_to_dict(h: HoldingsDetail) -> dict:
    return {
        "id": h.id,
        "product_id": h.product_id,
        "holding_date": str(h.holding_date) if h.holding_date else None,
        "security_type": h.security_type,
        "security_code": h.security_code,
        "security_name": h.security_name,
        "market": h.market,
        "quantity": float(h.quantity) if h.quantity else None,
        "cost_price": float(h.cost_price) if h.cost_price else None,
        "market_price": float(h.market_price) if h.market_price else None,
        "market_value": float(h.market_value) if h.market_value else None,
        "cost": float(h.cost) if h.cost else None,
        "weight": float(h.weight) if h.weight else None,
        "pnl": float(h.pnl) if h.pnl else None,
        "pnl_ratio": float(h.pnl_ratio) if h.pnl_ratio else None,
        "industry_l1": h.industry_l1,
        "industry_l2": h.industry_l2,
        "market_cap_type": h.market_cap_type,
        "level": h.level,
        "parent_id": h.parent_id,
    }


@router.get("", summary="获取持仓列表")
async def list_holdings(
    product_id: int = Query(...),
    holding_date: Optional[str] = Query(None),
    security_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(HoldingsDetail).filter(HoldingsDetail.product_id == product_id)
    if holding_date:
        query = query.filter(HoldingsDetail.holding_date == holding_date)
    if security_type:
        query = query.filter(HoldingsDetail.security_type == security_type)

    total = query.count()
    items = query.order_by(desc(HoldingsDetail.market_value)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 统计
    all_items = query.all() if not holding_date else items
    total_mv = sum(float(h.market_value or 0) for h in all_items)
    by_type = {}
    for h in all_items:
        t = h.security_type or "other"
        by_type[t] = by_type.get(t, 0) + float(h.market_value or 0)

    return {
        "total": total,
        "items": [_h_to_dict(h) for h in items],
        "summary": {
            "total_market_value": round(total_mv, 2),
            "by_security_type": {k: round(v, 2) for k, v in by_type.items()},
        },
    }


@router.post("", summary="添加持仓")
async def create_holding(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json()
    h = HoldingsDetail(**{k: body[k] for k in body if hasattr(HoldingsDetail, k) and k != "id"})
    db.add(h)
    db.commit()
    db.refresh(h)
    return {"id": h.id, "message": "持仓已添加"}


@router.post("/import", summary="导入持仓明细(Excel)")
async def import_holdings(
    product_id: int = Query(...),
    holding_date: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从Excel导入持仓明细(四级估值表)"""
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))

    col_map = {
        "证券类别": "security_type", "证券代码": "security_code", "证券名称": "security_name",
        "交易市场": "market", "数量": "quantity", "成本价": "cost_price",
        "市场价": "market_price", "市值": "market_value", "成本": "cost",
        "占比": "weight", "盈亏": "pnl", "盈亏比例": "pnl_ratio",
        "申万一级行业": "industry_l1", "申万二级行业": "industry_l2",
        "市值类型": "market_cap_type", "层级": "level",
    }

    count = 0
    for _, row in df.iterrows():
        data = {"product_id": product_id, "holding_date": holding_date}
        for cn, en in col_map.items():
            if cn in df.columns and pd.notna(row[cn]):
                data[en] = row[cn]
        if data.get("security_name"):
            db.add(HoldingsDetail(**data))
            count += 1

    db.commit()
    return {"message": f"导入{count}条持仓记录", "count": count}


@router.delete("/{holding_id}", summary="删除持仓")
async def delete_holding(holding_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(HoldingsDetail).filter(HoldingsDetail.id == holding_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="持仓不存在")
    db.delete(h)
    db.commit()
    return {"message": "已删除"}


@router.get("/analysis", summary="持仓穿透分析")
async def analyze_holdings(
    product_id: int = Query(...),
    holding_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """基于四级估值表的持仓穿透分析"""
    from app.services.holdings_service import HoldingsService
    from datetime import datetime
    
    # 转换日期
    date_obj = datetime.strptime(holding_date, '%Y-%m-%d').date() if holding_date else None
    
    # 使用服务进行分析
    result = HoldingsService.get_comprehensive_analysis(db, product_id, date_obj)
    
    return result


@router.get("/compare", summary="持仓对比分析")
async def compare_holdings(
    product_id: int = Query(...),
    date1: str = Query(..., description="对比日期1 (YYYY-MM-DD)"),
    date2: str = Query(..., description="对比日期2 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """对比两个日期的持仓变化"""
    from app.services.holdings_service import HoldingsService
    from datetime import datetime
    
    date1_obj = datetime.strptime(date1, '%Y-%m-%d').date()
    date2_obj = datetime.strptime(date2, '%Y-%m-%d').date()
    
    result = HoldingsService.compare_holdings(db, product_id, date1_obj, date2_obj)
    
    return result


@router.get("/turnover", summary="计算换手率")
async def calculate_turnover(
    product_id: int = Query(...),
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """计算指定期间的换手率"""
    from app.services.holdings_service import HoldingsService
    from datetime import datetime
    
    start_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    result = HoldingsService.calculate_turnover_rate(db, product_id, start_obj, end_obj)
    
    return result


@router.get("/dates", summary="获取可用报告日期")
async def get_available_dates(
    product_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dates = db.query(HoldingsDetail.holding_date).filter(
        HoldingsDetail.product_id == product_id
    ).distinct().order_by(desc(HoldingsDetail.holding_date)).all()
    return {"dates": [str(d[0]) for d in dates]}
