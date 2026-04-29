"""
Quant engine API endpoints.
"""
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.quant import (
    BenchmarkCompareRequest,
    BenchmarkCompareResponse,
    OpenBBStatusResponse,
    OptimizationRequest,
    OptimizationResponse,
    PerformanceSummaryRequest,
    PerformanceSummaryResponse,
    ProviderStatusResponse,
)
from app.services.quant_engine_service import QuantEngineService

router = APIRouter()


@router.get("/providers", response_model=ProviderStatusResponse, summary="Quant provider status")
def get_provider_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuantEngineService(db)
    return {"items": service.get_provider_statuses()}


@router.get("/openbb/status", response_model=OpenBBStatusResponse, summary="OpenBB integration status")
def get_openbb_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuantEngineService(db)
    return service.get_openbb_status()


@router.post(
    "/portfolios/{portfolio_id}/optimize",
    response_model=OptimizationResponse,
    summary="Optimize portfolio weights",
)
def optimize_portfolio(
    portfolio_id: int,
    payload: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuantEngineService(db)
    try:
        return service.optimize_portfolio(portfolio_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/portfolios/{portfolio_id}/performance",
    response_model=PerformanceSummaryResponse,
    summary="Portfolio performance summary",
)
def get_performance_summary(
    portfolio_id: int,
    engine: Literal["auto", "quantstats", "native"] = Query("auto", description="auto/quantstats/native"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    benchmark_code: Optional[str] = Query(None),
    benchmark_engine: Literal["auto", "akshare", "openbb", "native"] = Query(
        "auto", description="auto/akshare/openbb/native"
    ),
    risk_free_rate: float = Query(0.02),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuantEngineService(db)
    payload = PerformanceSummaryRequest(
        engine=engine,
        start_date=start_date,
        end_date=end_date,
        benchmark_code=benchmark_code,
        benchmark_engine=benchmark_engine,
        risk_free_rate=risk_free_rate,
    )
    try:
        return service.summarize_performance(portfolio_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/portfolios/{portfolio_id}/benchmark",
    response_model=BenchmarkCompareResponse,
    summary="Benchmark and CAPM comparison",
)
def compare_benchmark(
    portfolio_id: int,
    benchmark_code: str = Query(..., description="Index code or internal product_code"),
    engine: Literal["auto", "akshare", "openbb", "native"] = Query(
        "auto", description="auto/akshare/openbb/native"
    ),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    risk_free_rate: float = Query(0.02),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuantEngineService(db)
    payload = BenchmarkCompareRequest(
        benchmark_code=benchmark_code,
        engine=engine,
        start_date=start_date,
        end_date=end_date,
        risk_free_rate=risk_free_rate,
    )
    try:
        return service.compare_benchmark(portfolio_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
