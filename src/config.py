"""Central configuration management

This module provides both legacy dataclass-based configuration and new Pydantic Settings.
For new code, prefer using the Pydantic settings from src/config/settings.py
"""
import os
from dataclasses import dataclass

from .config.settings import get_qc_config, get_cvat_config, QCConfig, CVATAPIConfig

# Re-export for backward compatibility
qc_config = QCConfig()
cvat_config = CVATAPIConfig()


def get_headers():
    """
    Get HTTP headers for CVAT API requests
    Includes Authorization and X-Organization if org_slug is configured
    """
    headers = {
        "Authorization": f"Bearer {cvat_config.token}",
        "Content-Type": "application/json"
    }
    if cvat_config.org_slug:
        headers["X-Organization"] = cvat_config.org_slug
    return headers
