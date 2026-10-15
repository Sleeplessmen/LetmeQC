"""Logging Configuration for LetmeQC"""
import json
import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field


class FileHandlerConfig(BaseModel):
    """Configuration for file logging handler"""
    filename: str = Field(default="logs/app.log", description="Log file path")
    max_bytes: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    backup_count: int = Field(default=5, description="Number of backup files")
    encoding: str = Field(default="utf-8", description="File encoding")


class LoggingLevelConfig(BaseModel):
    """Logging levels for different modules"""
    root: str = Field(default="INFO", description="Root logger level")
    app: str = Field(default="INFO", description="App module level")
    handlers: str = Field(default="INFO", description="Handlers module level")
    services: str = Field(default="INFO", description="Services module level")
    clients: str = Field(default="INFO", description="Clients module level")
    config: str = Field(default="INFO", description="Config module level")


class LoggingConfig(BaseModel):
    """Main logging configuration"""
    
    # Enable/disable features
    enable_json_logging: bool = Field(default=False, description="Enable JSON formatted logging")
    enable_file_logging: bool = Field(default=True, description="Enable file logging")
    enable_console_logging: bool = Field(default=True, description="Enable console logging")
    
    # Log levels
    levels: LoggingLevelConfig = Field(default_factory=LoggingLevelConfig)
    
    # File handler config
    file_handler: FileHandlerConfig = Field(default_factory=FileHandlerConfig)
    
    # Log directory
    log_dir: str = Field(default="logs", description="Log directory path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global logging config instance
_logging_config: Optional[LoggingConfig] = None


def get_logging_config() -> LoggingConfig:
    """Get logging configuration (lazy loaded)"""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    return _logging_config


def setup_logging(config: Optional[LoggingConfig] = None, json_logging: bool = False):
    """
    Setup logging configuration for the application.
    
    Args:
        config: LoggingConfig instance or None to use default
        json_logging: Force JSON logging format (overrides config)
    """
    if config is None:
        config = get_logging_config()
    
    # Ensure log directory exists
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine if we should use JSON logging
    use_json = json_logging or config.enable_json_logging
    
    # Build logging config dictionary
    logging_dict: Dict[str, Union[str, int, Dict, logging.Handler]] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {},
        "handlers": {},
        "loggers": {}
    }
    
    # Create formatter(s)
    if use_json:
        class JSONFormatter(logging.Formatter):
            """Custom formatter for JSON logging"""
            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                
                # Add extra fields
                if hasattr(record, "correlation_id"):
                    log_data["correlation_id"] = record.correlation_id
                
                return json.dumps(log_data, default=str)
        
        logging_dict["formatters"]["json"] = JSONFormatter()
    else:
        logging_dict["formatters"]["standard"] = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    
    # Add console handler
    if config.enable_console_logging:
        formatter_key = "json" if use_json else "standard"
        logging_dict["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": config.levels.root,
            "formatter": formatter_key,
            "stream": "ext://sys.stdout"
        }
    
    # Add file handler
    if config.enable_file_logging:
        formatter_key = "json" if use_json else "standard"
        logging_dict["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": config.levels.root,
            "formatter": formatter_key,
            "filename": config.file_handler.filename,
            "maxBytes": config.file_handler.max_bytes,
            "backupCount": config.file_handler.backup_count,
            "encoding": config.file_handler.encoding
        }
    
    # Configure root logger
    handlers = []
    if config.enable_console_logging:
        handlers.append("console")
    if config.enable_file_logging:
        handlers.append("file")
    
    logging_dict["root"] = {
        "level": config.levels.root,
        "handlers": handlers
    }
    
    # Configure module-specific loggers
    module_levels = {
        "src.app": config.levels.app,
        "src.handlers": config.levels.handlers,
        "src.services": config.levels.services,
        "src.clients": config.levels.clients,
        "src.config": config.levels.config,
    }
    
    for module, level in module_levels.items():
        logging_dict["loggers"][module] = {
            "level": level,
            "propagate": True
        }
    
    # Apply configuration
    try:
        logging.config.dictConfig(logging_dict)
        logging.info("Logging configuration applied successfully")
    except Exception as e:
        # Fallback to basic config if dictConfig fails
        logging.basicConfig(
            level=config.levels.root,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logging.warning("Failed to apply advanced logging config: %s. Using basic config.", e)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        if self.correlation_id:
            record.correlation_id = self.correlation_id
        return True


def get_logger(name: str, correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with optional correlation ID context.
    
    Args:
        name: Logger name (typically __name__)
        correlation_id: Optional correlation ID for request tracing
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if correlation_id:
        # Add context filter
        for handler in logger.handlers:
            handler.addFilter(RequestContextFilter(correlation_id))
    
    return logger
