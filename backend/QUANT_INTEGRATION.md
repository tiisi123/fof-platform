# Quant Engine Integration

This backend now supports a pluggable quant engine layer with fallback behavior.

## Integrated providers

- `PyPortfolioOpt==1.5.6`: mean-variance style optimization
- `riskfolio-lib==7.0.1`: CVaR and risk-budget style optimization
- `quantstats==0.0.77`: performance metric enrichment
- `akshare==1.16.96`: benchmark index data retrieval
- `openbb==4.7.1`: optional multi-source benchmark data retrieval
- `native`: built-in fallback engine (always available)

## API endpoints

- `GET /api/v1/quant/providers`
  - Runtime provider availability and detected package versions.

- `GET /api/v1/quant/openbb/status`
  - Current OpenBB status (`integrated=true`, requires runtime package installation).

- `POST /api/v1/quant/portfolios/{portfolio_id}/optimize`
  - Portfolio weight optimization.
  - Engine: `auto|pypfopt|riskfolio|native`
  - Objective: `max_sharpe|min_volatility|risk_budget|cvar_min|target_return`
  - `target_return` is required when objective is `target_return`.

- `GET /api/v1/quant/portfolios/{portfolio_id}/performance`
  - Performance summary.
  - Engine: `auto|quantstats|native`
  - Benchmark engine (optional): `auto|akshare|openbb|native`
  - Optional benchmark comparison by `benchmark_code`.

- `GET /api/v1/quant/portfolios/{portfolio_id}/benchmark`
  - CAPM/benchmark comparison.
  - Engine: `auto|akshare|openbb|native`

## Fallback strategy

- If requested provider is unavailable, service automatically falls back to `native`.
- For benchmark data in `auto` mode, service tries `AKShare -> OpenBB -> native internal`.
- If AKShare benchmark fetch fails, service tries internal benchmark by matching `products.product_code`.
- If fallback cannot build enough data points, API returns a clear 400 error with reason.
