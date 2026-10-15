"""Configuration

This module provides both new Pydantic Settings and legacy configuration.
For new code, prefer using the Pydantic settings from src/config/settings.py
"""

from .settings import (
    QCSettings,
    CVATSettings,
    ServerSettings,
    WebhookSettings,
    Settings,
    get_qc_config,
    get_cvat_config,
    get_server_config,
    get_webhook_config,
    reset_config,
    QCConfig,
    CVATAPIConfig,
    qc_config,
    cvat_config
)
from .logging_config import setup_logging, get_logging_config, get_logger, RequestContextFilter

# Import get_headers from the parent config module
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Re-export get_headers for backward compatibility
def get_headers():
    """Get HTTP headers for CVAT API requests"""
    from src.config.settings import get_cvat_config
    config = get_cvat_config()
    headers = {
        "Authorization": f"Bearer {config.token}",
        "Content-Type": "application/json"
    }
    if config.org_slug:
        headers["X-Organization"] = config.org_slug
    return headers


__all__ = [
    # New Pydantic settings
    "QCSettings",
    "CVATSettings",
    "ServerSettings",
    "WebhookSettings",
    "Settings",
    # Legacy configs (for backward compatibility)
    "qc_config",
    "cvat_config",
    # Functions
    "get_qc_config",
    "get_cvat_config",
    "get_server_config",
    "get_webhook_config",
    "reset_config",
    "get_headers",
    # Logging
    "setup_logging",
    "get_logging_config",
    "get_logger",
    "RequestContextFilter",
    # Legacy classes
    "QCConfig",
    "CVATAPIConfig"
]
