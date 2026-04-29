"""
Open-source integration catalog and runtime status helpers.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.external_adapters import ExternalAdapters


class OpenSourceIntegrationService:
    """Single source of truth for quant-related integration metadata."""

    _CATALOG: List[Dict[str, Any]] = [
        {
            "provider": "pypfopt",
            "display_name": "PyPortfolioOpt",
            "module": "pypfopt",
            "package": "PyPortfolioOpt",
            "version_pinned": "1.5.6",
            "github": "https://github.com/robertmartin8/PyPortfolioOpt",
            "role": "portfolio_mean_variance_optimization",
            "integrated": True,
            "note": None,
        },
        {
            "provider": "riskfolio",
            "display_name": "Riskfolio-Lib",
            "module": "riskfolio",
            "package": "Riskfolio-Lib",
            "version_pinned": "7.0.1",
            "github": "https://github.com/dcajasn/Riskfolio-Lib",
            "role": "risk_budget_and_cvar_optimization",
            "integrated": True,
            "note": None,
        },
        {
            "provider": "quantstats",
            "display_name": "quantstats",
            "module": "quantstats",
            "package": "quantstats",
            "version_pinned": "0.0.77",
            "github": "https://github.com/ranaroussi/quantstats",
            "role": "performance_summary_and_report",
            "integrated": True,
            "note": None,
        },
        {
            "provider": "akshare",
            "display_name": "AKShare",
            "module": "akshare",
            "package": "akshare",
            "version_pinned": "1.16.96",
            "github": "https://github.com/akfamily/akshare",
            "role": "benchmark_market_data",
            "integrated": True,
            "note": None,
        },
        {
            "provider": "native",
            "display_name": "native",
            "module": None,
            "package": None,
            "version_pinned": None,
            "github": None,
            "role": "built_in_fallback_engine",
            "integrated": True,
            "note": "Built-in fallback engine used when external dependencies are unavailable.",
        },
        {
            "provider": "openbb",
            "display_name": "OpenBB",
            "module": "openbb",
            "package": "openbb",
            "version_pinned": "4.7.1",
            "github": "https://github.com/OpenBB-finance/OpenBB",
            "role": "multi_source_benchmark_connector",
            "integrated": True,
            "note": "Optional benchmark data source. Runtime usage requires openbb to be installed.",
        },
    ]

    def get_provider_statuses(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for item in self._CATALOG:
            provider = item["provider"]
            module_name = item.get("module")
            package_name = item.get("package")

            if provider == "native":
                available = True
                version = "builtin"
            else:
                available = ExternalAdapters.is_module_available(module_name)
                version = ExternalAdapters.package_version(package_name)

            rows.append(
                {
                    "provider": provider,
                    "package": package_name or "native",
                    "role": item["role"],
                    "available": available,
                    "version": version,
                    "note": item.get("note"),
                }
            )
        return rows

    def get_openbb_status(self) -> Dict[str, Any]:
        available = self.provider_available("openbb")
        return {
            "available": available,
            "integrated": True,
            "version": self.provider_version("openbb"),
            "note": "OpenBB benchmark integration is enabled when the openbb package is installed.",
        }

    def provider_available(self, provider: str) -> bool:
        item = self._catalog_item(provider)
        if item is None:
            return False
        if provider == "native":
            return True
        module_name = item.get("module")
        return ExternalAdapters.is_module_available(module_name)

    def provider_version(self, provider: str) -> Optional[str]:
        item = self._catalog_item(provider)
        if item is None:
            return None
        if provider == "native":
            return "builtin"
        package_name = item.get("package")
        return ExternalAdapters.package_version(package_name)

    def _catalog_item(self, provider: str) -> Optional[Dict[str, Any]]:
        for item in self._CATALOG:
            if item["provider"] == provider:
                return item
        return None
