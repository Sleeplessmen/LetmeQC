"""Pydantic Settings for LetmeQC

Uses pydantic v2 with pydantic-settings for BaseSettings functionality.
"""
import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class QCSettings(BaseSettings):
    """Quality Control configuration settings"""
    
    # Bounding box validation
    min_box_area: float = Field(default=100.0, ge=0, le=100000, description="Minimum bounding box area in pixels")
    min_polygon_points: int = Field(default=3, ge=3, le=100, description="Minimum number of polygon points")
    
    # Overlap detection
    iou_threshold: float = Field(default=0.95, ge=0, le=1, description="IoU threshold for overlap detection")
    duplicate_iou_threshold: float = Field(default=0.98, ge=0, le=1, description="IoU threshold for duplicate detection")
    
    # Aspect ratio validation
    max_aspect_ratio: float = Field(default=10.0, gt=0, description="Maximum aspect ratio (width/height)")
    min_aspect_ratio: float = Field(default=0.1, gt=0, description="Minimum aspect ratio (width/height)")
    
    # Mask validation
    mask_tolerance: float = Field(default=2.0, ge=0, description="Mask tolerance for validation in pixels")
    bbox_tolerance: float = Field(default=2.0, ge=0, description="Bounding box tolerance in pixels")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class CVATSettings(BaseSettings):
    """CVAT API configuration settings"""
    
    base_url: str = Field(default="https://app.cvat.ai/api", description="CVAT API base URL")
    token: str = Field(default="", description="CVAT API authentication token")
    org_slug: Optional[str] = Field(default=None, description="CVAT organization slug for X-Organization header")
    timeout: int = Field(default=30, ge=1, le=300, description="API request timeout in seconds")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class ServerSettings(BaseSettings):
    """Server configuration settings"""
    
    host: str = Field(default="0.0.0.0", description="Server host to bind")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port to bind")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class WebhookSettings(BaseSettings):
    """Webhook configuration settings"""
    
    secret: Optional[str] = Field(default=None, description="Secret for validating webhook requests")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class Settings(BaseSettings):
    """Main application settings combining all configurations"""
    
    qc: QCSettings = Field(default_factory=QCSettings, description="Quality Control settings")
    cvat: CVATSettings = Field(default_factory=CVATSettings, description="CVAT API settings")
    server: ServerSettings = Field(default_factory=ServerSettings, description="Server settings")
    webhook: WebhookSettings = Field(default_factory=WebhookSettings, description="Webhook settings")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global settings instances (lazy loaded)
_qc_config: Optional[QCSettings] = None
_cvat_config: Optional[CVATSettings] = None
_server_config: Optional[ServerSettings] = None
_webhook_config: Optional[WebhookSettings] = None


def get_qc_config() -> QCSettings:
    """Get QC configuration (lazy loaded)"""
    global _qc_config
    if _qc_config is None:
        _qc_config = QCSettings()
    return _qc_config


def get_cvat_config() -> CVATSettings:
    """Get CVAT configuration (lazy loaded)"""
    global _cvat_config
    if _cvat_config is None:
        _cvat_config = CVATSettings()
    return _cvat_config


def get_server_config() -> ServerSettings:
    """Get server configuration (lazy loaded)"""
    global _server_config
    if _server_config is None:
        _server_config = ServerSettings()
    return _server_config


def get_webhook_config() -> WebhookSettings:
    """Get webhook configuration (lazy loaded)"""
    global _webhook_config
    if _webhook_config is None:
        _webhook_config = WebhookSettings()
    return _webhook_config


def reset_config():
    """Reset all configuration instances (useful for testing)"""
    global _qc_config, _cvat_config, _server_config, _webhook_config
    _qc_config = None
    _cvat_config = None
    _server_config = None
    _webhook_config = None


# Backward compatibility - keep the old config format
class QCConfig:
    """Legacy QC configuration class for backward compatibility"""
    def __init__(self, **kwargs):
        config = get_qc_config()
        self.min_box_area = kwargs.get('min_box_area', config.min_box_area)
        self.min_polygon_points = kwargs.get('min_polygon_points', config.min_polygon_points)
        self.iou_threshold = kwargs.get('iou_threshold', config.iou_threshold)
        self.duplicate_iou_threshold = kwargs.get('duplicate_iou_threshold', config.duplicate_iou_threshold)
        self.max_aspect_ratio = kwargs.get('max_aspect_ratio', config.max_aspect_ratio)
        self.min_aspect_ratio = kwargs.get('min_aspect_ratio', config.min_aspect_ratio)
        self.mask_tolerance = kwargs.get('mask_tolerance', config.mask_tolerance)
        self.bbox_tolerance = kwargs.get('bbox_tolerance', config.bbox_tolerance)
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls()


class CVATAPIConfig:
    """Legacy CVAT API configuration class for backward compatibility"""
    def __init__(self, **kwargs):
        config = get_cvat_config()
        self.base_url = kwargs.get('base_url', config.base_url)
        self.token = kwargs.get('token', config.token)
        self.org_slug = kwargs.get('org_slug', config.org_slug)
        self.timeout = kwargs.get('timeout', config.timeout)
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls()


# Initialize legacy configs for backward compatibility
qc_config = QCConfig()
cvat_config = CVATAPIConfig()
