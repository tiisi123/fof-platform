"""
Quant engine facade for portfolio optimization and performance analytics.

Optional third-party engines:
- PyPortfolioOpt
- Riskfolio-Lib
- quantstats
- AKShare
- native fallback
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sqlalchemy.orm import Session

from app.models.nav import NavData
from app.models.portfolio import Portfolio, PortfolioComponent
from app.models.product import Product
from app.schemas.quant import (
    BenchmarkCompareRequest,
    OptimizationRequest,
    PerformanceSummaryRequest,
)
from app.services.open_source_integration_service import OpenSourceIntegrationService


class QuantEngineService:
    """Unified quant facade with optional dependencies and native fallback."""

    def __init__(self, db: Session):
        self.db = db
        self.integration_service = OpenSourceIntegrationService()

    def get_provider_statuses(self) -> List[Dict[str, Any]]:
        return self.integration_service.get_provider_statuses()

    def get_openbb_status(self) -> Dict[str, Any]:
        return self.integration_service.get_openbb_status()

    def optimize_portfolio(self, portfolio_id: int, req: OptimizationRequest) -> Dict[str, Any]:
        (
            portfolio,
            component_meta,
            returns_df,
            base_weights,
            warnings,
        ) = self._load_portfolio_context(
            portfolio_id=portfolio_id,
            start_date=req.start_date,
            end_date=req.end_date,
        )

        engine_requested = req.engine
        engine_used = self._select_optimization_engine(engine_requested, req.objective)

        optimized_weights: pd.Series
        if engine_used == "pypfopt":
            optimized_weights, extra_warnings = self._optimize_with_pypfopt(
                returns_df=returns_df,
                objective=req.objective,
                risk_free_rate=req.risk_free_rate,
                allow_short=req.allow_short,
                target_return=req.target_return,
            )
            warnings.extend(extra_warnings)
            if optimized_weights is None or optimized_weights.empty:
                optimized_weights, native_warnings = self._optimize_native(
                    returns_df=returns_df,
                    objective=req.objective,
                    risk_free_rate=req.risk_free_rate,
                    allow_short=req.allow_short,
                    target_return=req.target_return,
                )
                warnings.extend(native_warnings)
                engine_used = "native"
        elif engine_used == "riskfolio":
            optimized_weights, extra_warnings = self._optimize_with_riskfolio(
                returns_df=returns_df,
                objective=req.objective,
                risk_free_rate=req.risk_free_rate,
                allow_short=req.allow_short,
            )
            warnings.extend(extra_warnings)
            if optimized_weights is None or optimized_weights.empty:
                optimized_weights, native_warnings = self._optimize_native(
                    returns_df=returns_df,
                    objective=req.objective,
                    risk_free_rate=req.risk_free_rate,
                    allow_short=req.allow_short,
                    target_return=req.target_return,
                )
                warnings.extend(native_warnings)
                engine_used = "native"
        else:
            optimized_weights, extra_warnings = self._optimize_native(
                returns_df=returns_df,
                objective=req.objective,
                risk_free_rate=req.risk_free_rate,
                allow_short=req.allow_short,
                target_return=req.target_return,
            )
            warnings.extend(extra_warnings)

        optimized_weights = self._normalize_series_weights(optimized_weights)
        portfolio_returns = returns_df.mul(optimized_weights, axis=1).sum(axis=1)
        metrics = self._compute_native_metrics(portfolio_returns, req.risk_free_rate)

        rows: List[Dict[str, Any]] = []
        for product_id, weight in optimized_weights.sort_values(ascending=False).items():
            meta = component_meta.get(int(product_id), {})
            rows.append(
                {
                    "product_id": int(product_id),
                    "product_code": meta.get("product_code"),
                    "product_name": meta.get("product_name", str(product_id)),
                    "weight": round(float(weight), 6),
                }
            )

        return {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "engine_requested": engine_requested,
            "engine_used": engine_used,
            "objective": req.objective,
            "data_points": int(len(portfolio_returns)),
            "weights": rows,
            "expected_annual_return": metrics.get("annualized_return"),
            "expected_annual_volatility": metrics.get("annualized_volatility"),
            "sharpe_ratio": metrics.get("sharpe_ratio"),
            "cvar_95": metrics.get("cvar_95"),
            "warnings": warnings,
        }

    def summarize_performance(self, portfolio_id: int, req: PerformanceSummaryRequest) -> Dict[str, Any]:
        (
            portfolio,
            _component_meta,
            returns_df,
            base_weights,
            warnings,
        ) = self._load_portfolio_context(
            portfolio_id=portfolio_id,
            start_date=req.start_date,
            end_date=req.end_date,
        )

        engine_requested = req.engine
        engine_used = engine_requested
        if engine_used == "auto":
            engine_used = "quantstats" if self._provider_available("quantstats") else "native"
        elif engine_used == "quantstats" and not self._provider_available("quantstats"):
            warnings.append("quantstats is unavailable, switched to native engine.")
            engine_used = "native"

        portfolio_returns = returns_df.mul(base_weights, axis=1).sum(axis=1)
        metrics = self._compute_native_metrics(portfolio_returns, req.risk_free_rate)

        if engine_used == "quantstats":
            quant_metrics, quant_warnings = self._compute_quantstats_metrics(
                portfolio_returns=portfolio_returns,
                risk_free_rate=req.risk_free_rate,
            )
            metrics.update(quant_metrics)
            warnings.extend(quant_warnings)

        if req.benchmark_code:
            benchmark_returns, source, bench_warnings = self._load_benchmark_returns(
                benchmark_code=req.benchmark_code,
                start_date=req.start_date,
                end_date=req.end_date,
                requested_engine=req.benchmark_engine,
            )
            warnings.extend(bench_warnings)
            aligned_portfolio, aligned_benchmark = self._align_returns(portfolio_returns, benchmark_returns)
            if len(aligned_portfolio) >= 2:
                capm_metrics = self._compute_capm_metrics(
                    portfolio_returns=aligned_portfolio,
                    benchmark_returns=aligned_benchmark,
                    risk_free_rate=req.risk_free_rate,
                )
                metrics.update(capm_metrics)
                metrics["benchmark_source"] = source
            else:
                warnings.append("Benchmark overlap is too short to compute CAPM metrics.")

        return {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "engine_requested": engine_requested,
            "engine_used": engine_used,
            "data_points": int(len(portfolio_returns)),
            "metrics": metrics,
            "warnings": warnings,
        }

    def compare_benchmark(self, portfolio_id: int, req: BenchmarkCompareRequest) -> Dict[str, Any]:
        (
            portfolio,
            _component_meta,
            returns_df,
            base_weights,
            warnings,
        ) = self._load_portfolio_context(
            portfolio_id=portfolio_id,
            start_date=req.start_date,
            end_date=req.end_date,
        )

        portfolio_returns = returns_df.mul(base_weights, axis=1).sum(axis=1)
        benchmark_returns, source, bench_warnings = self._load_benchmark_returns(
            benchmark_code=req.benchmark_code,
            start_date=req.start_date,
            end_date=req.end_date,
            requested_engine=req.engine,
        )
        warnings.extend(bench_warnings)

        aligned_portfolio, aligned_benchmark = self._align_returns(portfolio_returns, benchmark_returns)
        if len(aligned_portfolio) < 2:
            raise ValueError("Insufficient overlapping points between portfolio and benchmark.")

        capm_metrics = self._compute_capm_metrics(
            portfolio_returns=aligned_portfolio,
            benchmark_returns=aligned_benchmark,
            risk_free_rate=req.risk_free_rate,
        )

        return {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "benchmark_code": req.benchmark_code,
            "engine_requested": req.engine,
            "engine_used": source if source in ("akshare", "openbb") else "native",
            "source": source,
            "data_points": int(len(aligned_portfolio)),
            "metrics": capm_metrics,
            "warnings": warnings,
        }

    def _load_portfolio_context(
        self,
        portfolio_id: int,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Tuple[Portfolio, Dict[int, Dict[str, Optional[str]]], pd.DataFrame, pd.Series, List[str]]:
        warnings: List[str] = []

        portfolio = (
            self.db.query(Portfolio)
            .filter(Portfolio.id == portfolio_id, Portfolio.is_deleted == False)  # noqa: E712
            .first()
        )
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        components = (
            self.db.query(PortfolioComponent)
            .filter(
                PortfolioComponent.portfolio_id == portfolio_id,
                PortfolioComponent.is_active == True,  # noqa: E712
            )
            .all()
        )
        if not components:
            raise ValueError("Portfolio has no active components.")

        component_meta: Dict[int, Dict[str, Optional[str]]] = {}
        raw_weights: Dict[int, float] = {}
        product_ids: List[int] = []
        for comp in components:
            product_id = int(comp.product_id)
            product = comp.product
            product_ids.append(product_id)
            raw_weights[product_id] = float(comp.weight or 0.0)
            component_meta[product_id] = {
                "product_code": product.product_code if product else None,
                "product_name": product.product_name if product else str(product_id),
            }

        nav_query = self.db.query(NavData).filter(NavData.product_id.in_(product_ids))
        if start_date:
            nav_query = nav_query.filter(NavData.nav_date >= start_date)
        if end_date:
            nav_query = nav_query.filter(NavData.nav_date <= end_date)
        nav_rows = nav_query.order_by(NavData.nav_date.asc()).all()
        if not nav_rows:
            raise ValueError("No NAV data found in selected date range.")

        records: List[Dict[str, Any]] = []
        for row in nav_rows:
            if row.unit_nav is None:
                continue
            records.append(
                {
                    "product_id": int(row.product_id),
                    "nav_date": row.nav_date,
                    "unit_nav": float(row.unit_nav),
                }
            )
        if not records:
            raise ValueError("NAV data exists but unit_nav values are empty.")

        price_df = (
            pd.DataFrame(records)
            .pivot_table(index="nav_date", columns="product_id", values="unit_nav", aggfunc="last")
            .sort_index()
            .ffill()
        )

        valid_cols = [col for col in price_df.columns if price_df[col].count() >= 3]
        dropped = sorted(set(price_df.columns.tolist()) - set(valid_cols))
        if dropped:
            warnings.append(
                "Dropped components with insufficient NAV history: "
                + ", ".join(str(int(x)) for x in dropped)
            )
        price_df = price_df[valid_cols]

        if price_df.shape[1] < 1:
            raise ValueError("No component has sufficient NAV history.")

        returns_df = price_df.pct_change().replace([np.inf, -np.inf], np.nan).dropna(how="all")
        returns_df = returns_df.fillna(0.0)
        returns_df.index = pd.to_datetime(returns_df.index)
        if returns_df.empty:
            raise ValueError("Failed to build return matrix from NAV data.")

        base_weights = pd.Series(
            {int(col): float(raw_weights.get(int(col), 0.0)) for col in returns_df.columns},
            dtype=float,
        )
        base_weights = self._normalize_series_weights(base_weights)

        return portfolio, component_meta, returns_df, base_weights, warnings

    def _select_optimization_engine(self, requested: str, objective: str) -> str:
        if requested != "auto":
            if requested in ("pypfopt", "riskfolio") and not self._provider_available(requested):
                return "native"
            return requested

        if objective in ("risk_budget", "cvar_min"):
            if self._provider_available("riskfolio"):
                return "riskfolio"
            if self._provider_available("pypfopt"):
                return "pypfopt"
            return "native"

        if self._provider_available("pypfopt"):
            return "pypfopt"
        return "native"

    def _optimize_with_pypfopt(
        self,
        returns_df: pd.DataFrame,
        objective: str,
        risk_free_rate: float,
        allow_short: bool,
        target_return: Optional[float],
    ) -> Tuple[Optional[pd.Series], List[str]]:
        warnings: List[str] = []
        if not self._provider_available("pypfopt"):
            warnings.append("PyPortfolioOpt is unavailable.")
            return None, warnings

        try:
            from pypfopt import EfficientFrontier, expected_returns, risk_models
        except Exception as exc:  # pragma: no cover
            warnings.append(f"Failed to import PyPortfolioOpt: {exc}")
            return None, warnings

        bounds = (-1.0, 1.0) if allow_short else (0.0, 1.0)
        mu = expected_returns.mean_historical_return(
            returns_df,
            returns_data=True,
            frequency=252,
        )
        sigma = risk_models.sample_cov(
            returns_df,
            returns_data=True,
            frequency=252,
        )
        ef = EfficientFrontier(mu, sigma, weight_bounds=bounds)

        try:
            if objective == "min_volatility":
                ef.min_volatility()
            elif objective == "max_sharpe":
                ef.max_sharpe(risk_free_rate=risk_free_rate)
            elif objective == "target_return":
                if target_return is None:
                    warnings.append("target_return is missing, switched to max_sharpe.")
                    ef.max_sharpe(risk_free_rate=risk_free_rate)
                else:
                    ef.efficient_return(target_return=target_return)
            elif objective in ("cvar_min", "risk_budget"):
                warnings.append(f"PyPortfolioOpt has no direct {objective} objective here. Switched to min_volatility.")
                ef.min_volatility()
            else:
                ef.max_sharpe(risk_free_rate=risk_free_rate)

            raw_weights = ef.clean_weights()
            result = pd.Series(
                [float(raw_weights.get(col, raw_weights.get(str(col), 0.0))) for col in returns_df.columns],
                index=returns_df.columns,
                dtype=float,
            )
            return result, warnings
        except Exception as exc:  # pragma: no cover
            warnings.append(f"PyPortfolioOpt optimization failed: {exc}")
            return None, warnings

    def _optimize_with_riskfolio(
        self,
        returns_df: pd.DataFrame,
        objective: str,
        risk_free_rate: float,
        allow_short: bool,
    ) -> Tuple[Optional[pd.Series], List[str]]:
        warnings: List[str] = []
        if not self._provider_available("riskfolio"):
            warnings.append("Riskfolio-Lib is unavailable.")
            return None, warnings
        if allow_short:
            warnings.append("Riskfolio path currently assumes long-only constraints.")

        try:
            import riskfolio as rp
        except Exception as exc:  # pragma: no cover
            warnings.append(f"Failed to import riskfolio: {exc}")
            return None, warnings

        port = rp.Portfolio(returns=returns_df)
        try:
            port.assets_stats(method_mu="hist", method_cov="hist")
        except Exception as exc:  # pragma: no cover
            warnings.append(f"Riskfolio assets_stats failed: {exc}")
            return None, warnings

        w = None
        try:
            if objective == "risk_budget":
                w = port.rp_optimization(model="Classic", rm="CVaR", rf=risk_free_rate, hist=True)
            elif objective == "cvar_min":
                w = port.optimization(
                    model="Classic",
                    rm="CVaR",
                    obj="MinRisk",
                    rf=risk_free_rate,
                    l=0,
                    hist=True,
                )
            elif objective == "min_volatility":
                w = port.optimization(
                    model="Classic",
                    rm="MV",
                    obj="MinRisk",
                    rf=risk_free_rate,
                    l=0,
                    hist=True,
                )
            elif objective == "target_return":
                warnings.append("Riskfolio target_return objective is not implemented, switched to Sharpe.")
                w = port.optimization(
                    model="Classic",
                    rm="MV",
                    obj="Sharpe",
                    rf=risk_free_rate,
                    l=0,
                    hist=True,
                )
            else:
                w = port.optimization(
                    model="Classic",
                    rm="MV",
                    obj="Sharpe",
                    rf=risk_free_rate,
                    l=0,
                    hist=True,
                )
        except Exception as exc:  # pragma: no cover
            warnings.append(f"Riskfolio optimization failed: {exc}")
            return None, warnings

        if w is None or w.empty:
            warnings.append("Riskfolio returned empty weights.")
            return None, warnings

        if isinstance(w, pd.DataFrame):
            series = w.iloc[:, 0]
        else:
            series = pd.Series(w)

        result = pd.Series(
            [float(series.get(col, series.get(str(col), 0.0))) for col in returns_df.columns],
            index=returns_df.columns,
            dtype=float,
        )
        return result, warnings

    def _optimize_native(
        self,
        returns_df: pd.DataFrame,
        objective: str,
        risk_free_rate: float,
        allow_short: bool,
        target_return: Optional[float],
    ) -> Tuple[pd.Series, List[str]]:
        warnings: List[str] = []
        cols = returns_df.columns.tolist()
        n = len(cols)
        if n == 0:
            raise ValueError("Empty return matrix.")

        mu = returns_df.mean().to_numpy() * 252.0
        cov = returns_df.cov().to_numpy() * 252.0

        x0 = np.full(n, 1.0 / n)
        bounds = [(-1.0, 1.0)] * n if allow_short else [(0.0, 1.0)] * n
        constraints = [{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}]

        def annual_ret(w: np.ndarray) -> float:
            return float(np.dot(w, mu))

        def annual_vol(w: np.ndarray) -> float:
            var = float(np.dot(w, np.dot(cov, w)))
            return float(np.sqrt(max(var, 0.0)))

        def daily_cvar_95(w: np.ndarray) -> float:
            series = returns_df.to_numpy() @ w
            if series.size == 0:
                return 0.0
            q = float(np.quantile(series, 0.05))
            tail = series[series <= q]
            if tail.size == 0:
                return 0.0
            return float(-np.mean(tail))

        def sharpe_loss(w: np.ndarray) -> float:
            vol = annual_vol(w)
            if vol <= 1e-12:
                return 1e6
            return -((annual_ret(w) - risk_free_rate) / vol)

        def risk_budget_loss(w: np.ndarray) -> float:
            sigma = annual_vol(w)
            if sigma <= 1e-12:
                return 1e6
            marginal = np.dot(cov, w) / sigma
            contribution = w * marginal
            target = np.full(n, sigma / n)
            return float(np.sum((contribution - target) ** 2))

        if objective == "min_volatility":
            objective_fn = annual_vol
        elif objective == "cvar_min":
            objective_fn = daily_cvar_95
        elif objective == "risk_budget":
            objective_fn = risk_budget_loss
        elif objective == "target_return":
            if target_return is None:
                warnings.append("target_return is missing, switched to max_sharpe.")
                objective_fn = sharpe_loss
            else:
                constraints.append(
                    {
                        "type": "ineq",
                        "fun": lambda w, target=target_return: float(annual_ret(w) - target),
                    }
                )
                objective_fn = annual_vol
        else:
            objective_fn = sharpe_loss

        result = minimize(
            objective_fn,
            x0=x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500, "ftol": 1e-10},
        )

        if not result.success:
            warnings.append(f"Native optimizer fallback used equal weights: {result.message}")
            weights = x0
        else:
            weights = result.x

        series = pd.Series(weights, index=cols, dtype=float)
        series = self._normalize_series_weights(series)
        return series, warnings

    def _compute_quantstats_metrics(
        self,
        portfolio_returns: pd.Series,
        risk_free_rate: float,
    ) -> Tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []
        if not self._provider_available("quantstats"):
            warnings.append("quantstats is unavailable.")
            return {}, warnings

        try:
            import quantstats as qs
        except Exception as exc:  # pragma: no cover
            warnings.append(f"Failed to import quantstats: {exc}")
            return {}, warnings

        s = portfolio_returns.dropna()
        s.index = pd.to_datetime(s.index)
        if len(s) < 2:
            return {}, warnings

        metrics: Dict[str, Any] = {}
        metrics["quantstats_cagr"] = self._safe_float(qs.stats.cagr(s))
        metrics["quantstats_volatility"] = self._safe_float(qs.stats.volatility(s))
        metrics["quantstats_sharpe"] = self._safe_float(qs.stats.sharpe(s, rf=risk_free_rate))
        metrics["quantstats_sortino"] = self._safe_float(qs.stats.sortino(s, rf=risk_free_rate))
        metrics["quantstats_max_drawdown"] = abs(self._safe_float(qs.stats.max_drawdown(s)) or 0.0)
        metrics["quantstats_calmar"] = self._safe_float(qs.stats.calmar(s))
        try:
            metrics["quantstats_win_rate"] = self._safe_float(qs.stats.win_rate(s))
        except Exception:
            pass
        return metrics, warnings

    def _load_benchmark_returns(
        self,
        benchmark_code: str,
        start_date: Optional[date],
        end_date: Optional[date],
        requested_engine: str,
    ) -> Tuple[pd.Series, str, List[str]]:
        warnings: List[str] = []
        akshare_available = self._provider_available("akshare")
        openbb_available = self._provider_available("openbb")

        candidate_engines: List[str] = []
        if requested_engine == "auto":
            if akshare_available:
                candidate_engines.append("akshare")
            if openbb_available:
                candidate_engines.append("openbb")
            candidate_engines.append("native")
        elif requested_engine == "akshare":
            if akshare_available:
                candidate_engines.append("akshare")
            else:
                warnings.append("AKShare is unavailable, switched to fallback sources.")
            if openbb_available:
                candidate_engines.append("openbb")
            candidate_engines.append("native")
        elif requested_engine == "openbb":
            if openbb_available:
                candidate_engines.append("openbb")
            else:
                warnings.append("OpenBB is unavailable, switched to fallback sources.")
            if akshare_available:
                candidate_engines.append("akshare")
            candidate_engines.append("native")
        else:
            candidate_engines.append("native")

        for engine in candidate_engines:
            if engine == "akshare":
                try:
                    bench = self._load_akshare_benchmark_returns(benchmark_code, start_date, end_date)
                    if len(bench) >= 2:
                        return bench, "akshare", warnings
                    warnings.append("AKShare returned too few points, trying next source.")
                except Exception as exc:
                    warnings.append(f"AKShare benchmark fetch failed: {exc}")
                continue

            if engine == "openbb":
                try:
                    bench = self._load_openbb_benchmark_returns(benchmark_code, start_date, end_date)
                    if len(bench) >= 2:
                        return bench, "openbb", warnings
                    warnings.append("OpenBB returned too few points, trying next source.")
                except Exception as exc:
                    warnings.append(f"OpenBB benchmark fetch failed: {exc}")
                continue

            bench_native = self._load_internal_benchmark_returns(benchmark_code, start_date, end_date)
            if bench_native is not None and len(bench_native) >= 2:
                return bench_native, "native_internal_product", warnings

        raise ValueError(
            f"Failed to load benchmark '{benchmark_code}'. "
            "Provide a valid index code for AKShare/OpenBB, or maintain internal NAV data with matching product_code."
        )

    def _load_internal_benchmark_returns(
        self,
        benchmark_code: str,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Optional[pd.Series]:
        product = self.db.query(Product).filter(Product.product_code == benchmark_code).first()
        if not product:
            return None

        query = self.db.query(NavData).filter(NavData.product_id == product.id)
        if start_date:
            query = query.filter(NavData.nav_date >= start_date)
        if end_date:
            query = query.filter(NavData.nav_date <= end_date)
        rows = query.order_by(NavData.nav_date.asc()).all()
        if len(rows) < 3:
            return None

        frame = pd.DataFrame(
            [{"nav_date": r.nav_date, "unit_nav": float(r.unit_nav)} for r in rows if r.unit_nav is not None]
        )
        if frame.empty:
            return None

        frame["nav_date"] = pd.to_datetime(frame["nav_date"])
        frame = frame.sort_values("nav_date")
        series = frame.set_index("nav_date")["unit_nav"].pct_change().dropna()
        series.name = f"benchmark_{benchmark_code}"
        return series

    def _load_akshare_benchmark_returns(
        self,
        benchmark_code: str,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> pd.Series:
        import akshare as ak  # pragma: no cover

        start = (start_date or (date.today() - timedelta(days=3 * 365))).strftime("%Y%m%d")
        end = (end_date or date.today()).strftime("%Y%m%d")

        errors: List[str] = []
        df: Optional[pd.DataFrame] = None

        try:
            df = ak.index_zh_a_hist(
                symbol=benchmark_code,
                period="daily",
                start_date=start,
                end_date=end,
            )
        except Exception as exc:  # pragma: no cover
            errors.append(str(exc))

        if df is None or df.empty:
            try:
                df = ak.stock_zh_index_daily(symbol=benchmark_code)
            except Exception as exc:  # pragma: no cover
                errors.append(str(exc))

        if df is None or df.empty:
            raise ValueError("; ".join(errors) if errors else "No AKShare data returned.")

        date_col = self._pick_column(df, ["\u65e5\u671f", "date", "Date"])
        close_col = self._pick_column(df, ["\u6536\u76d8", "close", "Close", "\u6536\u76d8\u4ef7"])
        if not date_col or not close_col:
            raise ValueError(f"Unexpected AKShare columns: {list(df.columns)}")

        frame = df[[date_col, close_col]].copy()
        frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
        frame = frame.dropna(subset=[date_col, close_col]).sort_values(date_col)
        frame[close_col] = pd.to_numeric(frame[close_col], errors="coerce")
        frame = frame.dropna(subset=[close_col])

        if start_date:
            frame = frame[frame[date_col] >= pd.Timestamp(start_date)]
        if end_date:
            frame = frame[frame[date_col] <= pd.Timestamp(end_date)]

        returns = frame.set_index(date_col)[close_col].pct_change().dropna()
        returns.name = f"benchmark_{benchmark_code}"
        return returns

    def _load_openbb_benchmark_returns(
        self,
        benchmark_code: str,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> pd.Series:
        try:
            from openbb import obb  # pragma: no cover
        except Exception as exc:  # pragma: no cover
            raise ValueError(f"Failed to import openbb: {exc}")

        start = start_date or (date.today() - timedelta(days=3 * 365))
        end = end_date or date.today()
        query_payload = {
            "symbol": benchmark_code,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "interval": "1d",
            "provider": "yfinance",
            "adjustment": "splits_and_dividends",
        }

        errors: List[str] = []
        endpoints = ["equity.price.historical", "index.price.historical"]

        for endpoint_path in endpoints:
            endpoint = self._resolve_attr_path(obb, endpoint_path)
            if endpoint is None:
                errors.append(f"OpenBB endpoint unavailable: {endpoint_path}")
                continue

            result: Any = None
            endpoint_error: Optional[Exception] = None
            payload_attempts = [
                query_payload,
                {k: v for k, v in query_payload.items() if k != "adjustment"},
                {k: v for k, v in query_payload.items() if k not in ("provider", "adjustment")},
                {k: v for k, v in query_payload.items() if k not in ("provider", "adjustment", "interval")},
            ]

            for payload in payload_attempts:
                try:
                    result = endpoint(**payload)
                    endpoint_error = None
                    break
                except TypeError as exc:
                    endpoint_error = exc
                    continue
                except Exception as exc:  # pragma: no cover
                    endpoint_error = exc
                    break

            if result is None:
                if endpoint_error:
                    errors.append(f"{endpoint_path}: {endpoint_error}")
                continue

            frame = self._openbb_result_to_dataframe(result)
            if frame.empty:
                errors.append(f"{endpoint_path}: empty dataframe")
                continue

            if isinstance(frame.index, pd.MultiIndex):
                frame = frame.reset_index()
            elif frame.index.name and frame.index.name not in frame.columns:
                frame = frame.reset_index()

            symbol_col = self._pick_column(frame, ["symbol", "Symbol", "ticker", "Ticker"])
            if symbol_col and frame[symbol_col].nunique(dropna=True) > 1:
                frame = frame[frame[symbol_col].astype(str).str.upper() == benchmark_code.upper()]

            date_col = self._pick_column(frame, ["date", "Date", "datetime", "Datetime", "timestamp", "Timestamp"])
            close_col = self._pick_column(
                frame,
                [
                    "close",
                    "Close",
                    "adj_close",
                    "Adj Close",
                    "adjusted_close",
                    "adjustedClose",
                    "close_price",
                    "Close Price",
                    "last_price",
                    "Last Price",
                    "price",
                    "Price",
                ],
            )

            if date_col is None:
                errors.append(f"{endpoint_path}: date column not found ({list(frame.columns)})")
                continue

            if close_col is None:
                numeric_cols = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c])]
                if numeric_cols:
                    close_col = numeric_cols[-1]

            if close_col is None:
                errors.append(f"{endpoint_path}: close column not found ({list(frame.columns)})")
                continue

            working = frame[[date_col, close_col]].copy()
            working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
            working[close_col] = pd.to_numeric(working[close_col], errors="coerce")
            working = working.dropna(subset=[date_col, close_col]).sort_values(date_col)

            if start_date:
                working = working[working[date_col] >= pd.Timestamp(start_date)]
            if end_date:
                working = working[working[date_col] <= pd.Timestamp(end_date)]

            returns = working.set_index(date_col)[close_col].pct_change().dropna()
            returns.name = f"benchmark_{benchmark_code}"
            if len(returns) >= 2:
                return returns
            errors.append(f"{endpoint_path}: insufficient points after processing")

        if errors:
            raise ValueError("; ".join(errors))
        raise ValueError("OpenBB returned no usable benchmark data.")

    def _openbb_result_to_dataframe(self, result: Any) -> pd.DataFrame:
        if result is None:
            return pd.DataFrame()
        if isinstance(result, pd.DataFrame):
            return result.copy()

        for method_name in ("to_df", "to_dataframe", "to_pandas"):
            method = getattr(result, method_name, None)
            if callable(method):
                try:
                    frame = method()
                except Exception:
                    continue
                if isinstance(frame, pd.DataFrame):
                    return frame.copy()

        payload: Any = None
        if isinstance(result, dict):
            payload = result.get("results") or result.get("data")
        else:
            payload = getattr(result, "results", None)

        if isinstance(payload, pd.DataFrame):
            return payload.copy()
        if isinstance(payload, list):
            rows: List[Dict[str, Any]] = []
            for item in payload:
                if isinstance(item, dict):
                    rows.append(item)
                elif hasattr(item, "model_dump"):
                    try:
                        rows.append(item.model_dump())
                    except Exception:
                        continue
                elif hasattr(item, "dict"):
                    try:
                        rows.append(item.dict())
                    except Exception:
                        continue
            if rows:
                return pd.DataFrame(rows)

        if isinstance(result, list):
            rows: List[Dict[str, Any]] = []
            for item in result:
                if isinstance(item, dict):
                    rows.append(item)
                elif hasattr(item, "model_dump"):
                    try:
                        rows.append(item.model_dump())
                    except Exception:
                        continue
            if rows:
                return pd.DataFrame(rows)

        return pd.DataFrame()

    def _compute_native_metrics(self, returns: pd.Series, risk_free_rate: float) -> Dict[str, Optional[float]]:
        s = returns.dropna()
        if len(s) < 2:
            return {
                "total_return": None,
                "annualized_return": None,
                "annualized_volatility": None,
                "sharpe_ratio": None,
                "sortino_ratio": None,
                "max_drawdown": None,
                "calmar_ratio": None,
                "win_rate": None,
                "var_95": None,
                "cvar_95": None,
            }

        total_return = float((1.0 + s).prod() - 1.0)
        annualized_return = float((1.0 + total_return) ** (252.0 / len(s)) - 1.0)
        annualized_volatility = float(s.std(ddof=1) * np.sqrt(252.0))

        sharpe_ratio = None
        if annualized_volatility > 1e-12:
            sharpe_ratio = float((annualized_return - risk_free_rate) / annualized_volatility)

        downside = s[s < 0]
        if len(downside) > 1:
            downside_vol = float(downside.std(ddof=1) * np.sqrt(252.0))
        else:
            downside_vol = 0.0

        sortino_ratio = None
        if downside_vol > 1e-12:
            sortino_ratio = float((annualized_return - risk_free_rate) / downside_vol)

        wealth = (1.0 + s).cumprod()
        drawdown = wealth / wealth.cummax() - 1.0
        max_drawdown_signed = float(drawdown.min())
        max_drawdown = abs(max_drawdown_signed)

        calmar_ratio = None
        if max_drawdown > 1e-12:
            calmar_ratio = float(annualized_return / max_drawdown)

        var_95 = float(-np.quantile(s, 0.05))
        tail = s[s <= np.quantile(s, 0.05)]
        cvar_95 = float(-tail.mean()) if len(tail) > 0 else 0.0

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "annualized_volatility": annualized_volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "calmar_ratio": calmar_ratio,
            "win_rate": float((s > 0).mean()),
            "var_95": var_95,
            "cvar_95": cvar_95,
        }

    def _compute_capm_metrics(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_rate: float,
    ) -> Dict[str, Optional[float]]:
        p, b = self._align_returns(portfolio_returns, benchmark_returns)
        if len(p) < 2:
            return {
                "portfolio_total_return": None,
                "benchmark_total_return": None,
                "portfolio_annualized_return": None,
                "benchmark_annualized_return": None,
                "alpha": None,
                "beta": None,
                "correlation": None,
                "tracking_error": None,
                "information_ratio": None,
            }

        cov = np.cov(p, b, ddof=1)[0, 1]
        var_b = np.var(b, ddof=1)
        beta = float(cov / var_b) if var_b > 1e-12 else None
        corr = float(np.corrcoef(p, b)[0, 1]) if len(p) > 2 else None

        p_total = float((1.0 + p).prod() - 1.0)
        b_total = float((1.0 + b).prod() - 1.0)
        p_ann = float((1.0 + p_total) ** (252.0 / len(p)) - 1.0)
        b_ann = float((1.0 + b_total) ** (252.0 / len(b)) - 1.0)

        alpha = None
        if beta is not None:
            alpha = float(p_ann - (risk_free_rate + beta * (b_ann - risk_free_rate)))

        excess = p - b
        tracking_error = float(excess.std(ddof=1) * np.sqrt(252.0))
        information_ratio = None
        if tracking_error > 1e-12:
            information_ratio = float((excess.mean() * 252.0) / tracking_error)

        return {
            "portfolio_total_return": p_total,
            "benchmark_total_return": b_total,
            "portfolio_annualized_return": p_ann,
            "benchmark_annualized_return": b_ann,
            "alpha": alpha,
            "beta": beta,
            "correlation": corr,
            "tracking_error": tracking_error,
            "information_ratio": information_ratio,
        }

    def _align_returns(self, a: pd.Series, b: pd.Series) -> Tuple[pd.Series, pd.Series]:
        merged = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
        return merged["a"], merged["b"]

    def _normalize_series_weights(self, weights: pd.Series) -> pd.Series:
        if weights is None or weights.empty:
            return weights
        total = float(weights.sum())
        if abs(total) <= 1e-12:
            return pd.Series(
                np.full(len(weights), 1.0 / len(weights)),
                index=weights.index,
                dtype=float,
            )
        return weights.astype(float) / total

    def _provider_available(self, provider: str) -> bool:
        return self.integration_service.provider_available(provider)

    def _provider_version(self, provider: str) -> Optional[str]:
        return self.integration_service.provider_version(provider)

    def _pick_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        for col in candidates:
            if col in df.columns:
                return col
        lowered = {str(c).lower(): c for c in df.columns}
        for col in candidates:
            key = str(col).lower()
            if key in lowered:
                return lowered[key]
        return None

    def _resolve_attr_path(self, root: Any, attr_path: str) -> Any:
        current = root
        for attr in attr_path.split("."):
            current = getattr(current, attr, None)
            if current is None:
                return None
        return current

    def _safe_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            v = float(value)
        except Exception:
            return None
        if np.isnan(v) or np.isinf(v):
            return None
        return v
