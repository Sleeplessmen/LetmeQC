#!/usr/bin/env python3
"""
LetmeQC - Entry point for CVAT Webhook Server

This is the main entry point for running the FastAPI application.
The actual application logic has been moved to src/app/main.py

Usage:
    uvicorn app:app --reload  # Development
    uvicorn app:app --host 0.0.0.0 --port 8000  # Production

Or run directly:
    python app.py
"""

import os
import sys
import logging
import uvicorn

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize logging
from src.config.logging_config import setup_logging, get_logging_config

# Load configuration
from src.config.settings import get_server_config, get_webhook_config, get_cvat_config

# Setup logging before importing other modules
server_config = get_server_config()
webhook_config = get_webhook_config()
cvat_config = get_cvat_config()

# Determine if JSON logging should be used (from env var or default)
json_logging = os.getenv("JSON_LOGGING", "false").lower() == "true"
setup_logging(json_logging=json_logging)

# Import the app after path is set
from src.app.main import app, get_app

# Configuration from environment variables
SERVER_HOST = os.getenv("SERVER_HOST", server_config.host)
SERVER_PORT = int(os.getenv("SERVER_PORT", server_config.port))

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  LetmeQC - CVAT Webhook Server")
    logger.info("=" * 60)
    logger.info("  Server: http://%s:%s", SERVER_HOST, SERVER_PORT)
    logger.info("  Webhook: POST http://%s:%s/webhook/cvat", SERVER_HOST, SERVER_PORT)
    logger.info("  Health: GET http://%s:%s/health", SERVER_HOST, SERVER_PORT)
    logger.info("  Docs: http://%s:%s/docs", SERVER_HOST, SERVER_PORT)
    logger.info("  Config: GET http://%s:%s/config", SERVER_HOST, SERVER_PORT)
    logger.info("=" * 60)
    
    if not cvat_config.token:
        logger.warning("WARNING: CVAT_TOKEN not set - API calls will fail!")
        logger.warning("   Set CVAT_TOKEN environment variable or in .env file")
    
    if not webhook_config.secret:
        logger.warning("WARNING: WEBHOOK_SECRET not set - anyone can trigger webhook!")
    
    if not cvat_config.org_slug:
        logger.warning("WARNING: CVAT_ORG_SLUG not set - organization header will not be sent!")
    
    uvicorn.run(
        "app:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        reload=True
    )
