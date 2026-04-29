"""
项目IRR/MOIC计算服务
"""
from typing import Dict, Any, List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.logger import logger
from app.models.project import Project
from app.models.project_cashflow import ProjectCashflow, CashflowType


def _xnpv(rate: float, cashflows: List[tuple]) -> float:
    """
    XNPV: 不规则现金流净现值
    cashflows: [(date, amount), ...]
    """
    if not cashflows:
        return 0.0
    d0 = cashflows[0][0]
    return sum(cf / (1 + rate) ** ((d - d0).days / 365.25) for d, cf in cashflows)


def _xirr(cashflows: List[tuple], guess: float = 0.1, tol: float = 1e-6, max_iter: int = 200) -> Optional[float]:
    """
    XIRR: 不规则现金流内部收益率 (Newton-Raphson)
    cashflows: [(date, amount), ...]
    """
    if not cashflows or len(cashflows) < 2:
        return None

    # 检查是否有正负现金流
    has_positive = any(cf > 0 for _, cf in cashflows)
    has_negative = any(cf < 0 for _, cf in cashflows)
    if not (has_positive and has_negative):
        return None

    rate = guess
    d0 = cashflows[0][0]

    for _ in range(max_iter):
        npv = sum(cf / (1 + rate) ** ((d - d0).days / 365.25) for d, cf in cashflows)
        dnpv = sum(
            -cf * ((d - d0).days / 365.25) / (1 + rate) ** ((d - d0).days / 365.25 + 1)
            for d, cf in cashflows
        )
        if abs(dnpv) < 1e-12:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < tol:
            return new_rate
        rate = new_rate

    return rate if abs(_xnpv(rate, cashflows)) < 1.0 else None


def calculate_irr_moic(project_id: int, db: Session) -> Dict[str, Any]:
    """
    计算项目的IRR和MOIC

    Returns:
        {
            "irr": float or None,
            "moic": float or None,
            "total_invested": float,
            "total_distributed": float,
            "cashflow_count": int,
        }
    """
    cashflows = db.query(ProjectCashflow).filter(
        ProjectCashflow.project_id == project_id
    ).order_by(asc(ProjectCashflow.cashflow_date)).all()

    if not cashflows:
        return {"irr": None, "moic": None, "total_invested": 0, "total_distributed": 0, "cashflow_count": 0}

    total_invested = sum(float(abs(cf.amount)) for cf in cashflows if cf.cashflow_type == CashflowType.INVESTMENT)
    total_distributed = sum(float(cf.amount) for cf in cashflows if cf.cashflow_type == CashflowType.DISTRIBUTION)

    # MOIC = total_distributed / total_invested
    moic = round(total_distributed / total_invested, 4) if total_invested > 0 else None

    # IRR (XIRR)
    cf_pairs = []
    for cf in cashflows:
        amount = float(cf.amount)
        if cf.cashflow_type == CashflowType.INVESTMENT:
            amount = -abs(amount)  # 投入为负
        elif cf.cashflow_type == CashflowType.DISTRIBUTION:
            amount = abs(amount)   # 回收为正
        cf_pairs.append((cf.cashflow_date, amount))

    irr = _xirr(cf_pairs)
    if irr is not None:
        irr = round(irr, 6)

    # 更新项目的IRR/MOIC字段
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.irr = Decimal(str(irr)) if irr is not None else None
        project.moic = Decimal(str(moic)) if moic is not None else None
        db.commit()
        logger.info(f"项目{project_id} IRR={irr}, MOIC={moic}")

    return {
        "irr": irr,
        "moic": moic,
        "total_invested": round(total_invested, 2),
        "total_distributed": round(total_distributed, 2),
        "cashflow_count": len(cashflows),
    }
