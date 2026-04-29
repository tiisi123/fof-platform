"""
Quant engine schemas.
"""
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


OptimizationEngine = Literal["auto", "pypfopt", "riskfolio", "native"]
PerformanceEngine = Literal["auto", "quantstats", "native"]
BenchmarkEngine = Literal["auto", "akshare", "openbb", "native"]
OptimizationObjective = Literal["max_sharpe", "min_volatility", "risk_budget", "cvar_min", "target_return"]


class ProviderStatus(BaseModel):
    provider: str
    package: str
    role: str
    available: bool
    version: Optional[str] = None
    note: Optional[str] = None


class ProviderStatusResponse(BaseModel):
    items: List[ProviderStatus]


class OpenBBStatusResponse(BaseModel):
    available: bool
    integrated: bool
    version: Optional[str] = None
    note: str


class OptimizationRequest(BaseModel):
    engine: OptimizationEngine = "auto"
    objective: OptimizationObjective = "max_sharpe"
    risk_free_rate: float = Field(0.02, ge=-0.2, le=0.5)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    allow_short: bool = False
    target_return: Optional[float] = Field(None, ge=-1.0, le=5.0)

    @model_validator(mode="after")
    def validate_target_return(self) -> "OptimizationRequest":
        if self.objective == "target_return" and self.target_return is None:
            raise ValueError("target_return is required when objective='target_return'.")
        return self


class OptimizationWeight(BaseModel):
    product_id: int
    product_code: Optional[str] = None
    product_name: str
    weight: float


class OptimizationResponse(BaseModel):
    portfolio_id: int
    portfolio_name: str
    engine_requested: str
    engine_used: str
    objective: str
    data_points: int
    weights: List[OptimizationWeight]
    expected_annual_return: Optional[float] = None
    expected_annual_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    cvar_95: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)


class PerformanceSummaryRequest(BaseModel):
    engine: PerformanceEngine = "auto"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    benchmark_code: Optional[str] = Field(None, min_length=2, max_length=30)
    benchmark_engine: BenchmarkEngine = "auto"
    risk_free_rate: float = Field(0.02, ge=-0.2, le=0.5)


class PerformanceSummaryResponse(BaseModel):
    portfolio_id: int
    portfolio_name: str
    engine_requested: str
    engine_used: str
    data_points: int
    metrics: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)


class BenchmarkCompareRequest(BaseModel):
    engine: BenchmarkEngine = "auto"
    benchmark_code: str = Field(..., min_length=2, max_length=30)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    risk_free_rate: float = Field(0.02, ge=-0.2, le=0.5)


class BenchmarkCompareResponse(BaseModel):
    portfolio_id: int
    portfolio_name: str
    benchmark_code: str
    engine_requested: str
    engine_used: str
    source: str
    data_points: int
    metrics: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
