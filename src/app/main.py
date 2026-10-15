"""FastAPI Application for LetmeQC"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

from src.config import qc_config, cvat_config
from src.config.settings import get_qc_config, get_cvat_config, get_webhook_config
from src.clients.cvat_client import CVATAPI
from src.handlers.webhook_handlers import (
    validate_request,
    handle_ping,
    handle_skip_event,
    handle_non_validation,
    init_webhook_handler
)
from src.services.qc_service import QCService
from src.monitoring import (
    metrics,
    REQUEST_COUNTER,
    REQUEST_TIMER,
    ERROR_COUNTER,
    JOB_PROCESSED_COUNTER,
    JOB_FAILED_COUNTER,
    JOB_PASSED_COUNTER,
    ISSUES_CREATED_COUNTER,
    get_health_summary,
    timed
)
from src.exceptions import LetmeQCException, get_current_context, set_current_context, clear_current_context, RequestContext

logger = logging.getLogger(__name__)

# Load configuration
qc_settings = get_qc_config()
cvat_settings = get_cvat_config()
webhook_settings = get_webhook_config()

# Initialize CVAT API client
cvat_api: Optional[CVATAPI] = None
if cvat_settings.token:
    cvat_api = CVATAPI(
        base_url=cvat_settings.base_url,
        token=cvat_settings.token,
        org_slug=cvat_settings.org_slug,
        timeout=cvat_settings.timeout
    )
    logger.info("CVAT API client initialized")
else:
    logger.warning("CVAT_TOKEN not set - API calls will fail")

# Initialize webhook handler
init_webhook_handler(webhook_secret=webhook_settings.secret)

# Initialize QC Service
qc_service: Optional[QCService] = None
if cvat_api:
    qc_service = QCService(
        cvat_api=cvat_api,
        qc_config={
            'min_box_area': qc_settings.min_box_area,
            'iou_threshold': qc_settings.iou_threshold,
            'duplicate_iou_threshold': qc_settings.duplicate_iou_threshold,
            'min_polygon_points': qc_settings.min_polygon_points,
            'max_aspect_ratio': qc_settings.max_aspect_ratio,
            'min_aspect_ratio': qc_settings.min_aspect_ratio,
            'mask_tolerance': qc_settings.mask_tolerance,
            'bbox_tolerance': qc_settings.bbox_tolerance
        }
    )

# Configuration from environment variables
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
UPDATE_JOB_STATUS_ERROR = "Failed to update job status for job %s"

# Create FastAPI app
app = FastAPI(
    title="LetmeQC - CVAT Webhook Server",
    description="Webhook endpoint for CVAT to trigger automatic Quality Control checks",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Middleware for request tracking
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Middleware for request tracking and metrics"""
    start_time = time.perf_counter()
    
    # Extract request info
    request_id = request.headers.get("X-Request-ID", str(id(request)))
    correlation_id = request.headers.get("X-Correlation-ID")
    user_agent = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else "unknown"
    
    # Create request context
    context = RequestContext(
        request_id=request_id,
        correlation_id=correlation_id,
        user_agent=user_agent,
        ip_address=client_ip
    )
    set_current_context(context)
    
    # Increment request counter
    REQUEST_COUNTER.increment()
    
    try:
        response = await call_next(request)
        
        # Record request duration
        duration = time.perf_counter() - start_time
        REQUEST_TIMER.record(duration)
        
        # Add correlation ID to response headers
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    except HTTPException as e:
        ERROR_COUNTER.increment()
        duration = time.perf_counter() - start_time
        REQUEST_TIMER.record(duration)
        raise
    except Exception as e:
        ERROR_COUNTER.increment()
        duration = time.perf_counter() - start_time
        REQUEST_TIMER.record(duration)
        logger.exception("Unexpected error processing request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        clear_current_context()


@app.post("/webhook/cvat",
         responses={
             200: {"description": "Webhook processed successfully"},
             400: {"description": "Invalid JSON payload"},
             401: {"description": "Invalid webhook secret"},
             500: {"description": "Internal server error"}
         })
async def cvat_webhook(request: Request):
    """CVAT Webhook Endpoint"""
    JOB_PROCESSED_COUNTER.increment()
    
    try:
        payload = await request.json()
        logger.info("Received webhook payload")

        is_valid, event, error_response = validate_request(request, payload)
        if not is_valid:
            return error_response

        if event == "ping":
            return handle_ping()

        if event != "update:job":
            return handle_skip_event(event)

        job = payload.get("job", {})
        job_id = job.get("id")
        job_name = job.get("name", "unknown")
        job_status = job.get("status")
        assignee = job.get("assignee") or {}
        assignee_id = assignee.get("id")

        logger.info("Job Update: ID=%s | Name='%s' | Status='%s'",
                   job_id, job_name, job_status)

        if job_status != "validation":
            return handle_non_validation(job_id, job_status)

        logger.info("Starting automatic QC process for job %s", job_id)

        if not cvat_api:
            logger.error("CVAT API not configured - cannot fetch annotations")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CVAT API not configured. Please set CVAT_TOKEN environment variable."
            )

        if not qc_service:
            logger.error("QC Service not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="QC Service not initialized"
            )

        job_info, raw_data, frames, fetch_error = qc_service.fetch_data(job_id)

        if fetch_error:
            return fetch_error

        errors = qc_service.run_qc(frames)

        if errors:
            JOB_FAILED_COUNTER.increment()
            ISSUES_CREATED_COUNTER.increment(len(errors))
            return qc_service.process_failure(job_id, job_name, errors, assignee_id, raw_data, frames, job_info)
        else:
            JOB_PASSED_COUNTER.increment()
            return qc_service.process_success(job_id, job_name, frames, assignee_id, raw_data, job_info)

    except json.JSONDecodeError:
        logger.exception("Invalid JSON payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error processing webhook")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/")
async def root():
    """Health check and service info"""
    return {
        "status": "running",
        "service": "LetmeQC CVAT Webhook Server",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "webhook_endpoint": "/webhook/cvat",
        "metrics": "/metrics"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cvat_api_configured": cvat_settings.token is not None and cvat_settings.token != "",
        "qc_engine_ready": True,
        "qc_service_ready": qc_service is not None,
        "health_details": get_health_summary()
    }


@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    return metrics.get_metrics()


@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "cvat_api_url": cvat_settings.base_url,
        "cvat_token_set": cvat_settings.token is not None and cvat_settings.token != "",
        "cvat_org_slug": cvat_settings.org_slug,
        "min_box_area": qc_settings.min_box_area,
        "iou_threshold": qc_settings.iou_threshold,
        "webhook_secret_set": webhook_settings.secret is not None
    }


def get_app():
    """Get the FastAPI application instance"""
    return app
