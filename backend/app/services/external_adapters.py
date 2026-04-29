"""
External adapter helpers for optional third-party dependencies.
"""
from __future__ import annotations

import importlib.util
from importlib import metadata
from typing import Optional


class ExternalAdapters:
    """Small utility layer for dependency availability/version checks."""

    @staticmethod
    def is_module_available(module_name: str) -> bool:
        if not module_name:
            return False
        return importlib.util.find_spec(module_name) is not None

    @staticmethod
    def package_version(package_name: str) -> Optional[str]:
        if not package_name:
            return None
        try:
            return metadata.version(package_name)
        except Exception:
            return None
