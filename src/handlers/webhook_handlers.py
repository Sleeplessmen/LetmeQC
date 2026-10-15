"""Webhook Handlers for CVAT events"""
import logging
from typing import Dict, Tuple

from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# Import config at module level - will be initialized later
WEBHOOK_SECRET = None


def init_webhook_handler(webhook_secret: str = None):
    """Initialize webhook handler with configuration"""
    global WEBHOOK_SECRET
    WEBHOOK_SECRET = webhook_secret
    logger.info("Webhook handler initialized with secret: %s", "set" if WEBHOOK_SECRET else "not set")


def validate_request(request: Request, payload: Dict) -> Tuple[bool, str, Dict]:
    """Validate webhook request. Returns (is_valid, event, error_response)"""
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-CVAT-Webhook-Secret")
        if secret and secret != WEBHOOK_SECRET:
            logger.error("Invalid webhook secret")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret",
                headers={"WWW-Authenticate": "Bearer"}
            )
        elif not secret:
            logger.warning("WEBHOOK_SECRET is set but no secret header provided")

    event = payload.get("event", "")
    return True, event, {}


def handle_ping() -> Dict:
    """Handle ping event"""
    logger.info("Connection successful! Received Ping from CVAT.")
    return {"message": "Ping received"}


def handle_skip_event(event: str) -> Dict:
    """Handle non-job events"""
    logger.info("Skipping event: %s", event)
    return {"message": "Skipped event: " + event, "status": "skipped"}


def handle_non_validation(job_id: int, job_status: str) -> Dict:
    """Handle non-validation status"""
    logger.info("Status is '%s' - no QC action required", job_status)
    return {
        "message": "Job " + str(job_id) + " status update received",
        "job_id": job_id,
        "status": job_status,
        "action": "none"
    }
