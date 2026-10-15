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
    # Logging
    "setup_logging",
    "get_logging_config",
    "get_logger",
    "RequestContextFilter",
    # Legacy classes
    "QCConfig",
    "CVATAPIConfig"
]
