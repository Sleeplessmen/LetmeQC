from fastapi import FastAPI, Request, HTTPException
import uvicorn
import json
import logging
import os
from typing import Optional, Dict, List
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from src.parser import parse_cvat_api_json
from src.rules import QCRulesEngine
from src.models import Frame
from src.config import cvat_config, qc_config, get_headers
from src.reports import QCReport

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
CVAT_API_URL = os.getenv("CVAT_API_URL", "https://app.cvat.ai/api")
CVAT_TOKEN = os.getenv("CVAT_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", None)
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

app = FastAPI(
    title="LetmeQC - CVAT Webhook Server",
    description="Webhook endpoint for CVAT to trigger automatic Quality Control checks on COCO format annotations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


class CVATAPI:
    """Helper class for CVAT API interactions with X-Organization header support"""
    
    def __init__(self, base_url: str, token: str, org_slug: str = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.org_slug = org_slug
        self.timeout = 30
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with Authorization and X-Organization if configured"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        if self.org_slug:
            headers["X-Organization"] = self.org_slug
        return headers
    
    def get_job_annotations(self, job_id: int) -> Dict:
        """Fetch annotations for a job in COCO format"""
        url = f"{self.base_url}/jobs/{job_id}/annotations"
        logger.info(f"Fetching annotations from: {url}")
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch annotations for job {job_id}: {e}")
            raise
    
    def create_issue(self, job_id: int, frame: int, position: List[float],
                     message: str, assignee_id: Optional[int] = None) -> Dict:
        """
        Create a QC issue in CVAT with position [x1, y1, x2, y2]
        POST /api/issues
        """
        url = f"{self.base_url}/issues"
        issue_data = {
            "frame": int(frame),
            "position": position,  # [x1, y1, x2, y2]
            "job": job_id,
            "message": message,
            "resolved": False
        }
        
        if assignee_id:
            issue_data["assignee"] = assignee_id
        
        logger.info(f"Creating issue for job {job_id}, frame {frame}: {message}")
        
        try:
            response = requests.post(url, json=issue_data, 
                                    headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create issue. CVAT Response: {e.response.text if hasattr(e, 'response') else ''}")
            raise
    
    def update_job_status(self, job_id: int, stage: str, state: str, 
                          assignee_id: Optional[int] = None) -> Dict:
        """
        Update job status via PATCH /api/jobs/{id}
        For REJECTED: stage="annotation", state="rejected"
        For PASSED: stage="validation", state="" (keep validation)
        """
        url = f"{self.base_url}/jobs/{job_id}"
        payload = {"stage": stage, "state": state}
        
        if assignee_id:
            payload["assignee"] = assignee_id
        
        try:
            response = requests.patch(url, json=payload,
                                     headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update job status: {e}")
            raise
    
    def get_job_info(self, job_id: int) -> Dict:
        """Get job information - GET /api/jobs/{id}"""
        url = f"{self.base_url}/jobs/{job_id}"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get job info: {e}")
            raise

    def get_job_labels(self, job_id: int) -> Dict[int, str]:
        """Fetch labels metadata for mapping ID to Name - GET /api/labels?job_id={id}"""
        url = f"{self.base_url}/labels?job_id={job_id}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            results = response.json().get("results", [])
            # Return dict: { 3: "car", 4: "pedestrian" }
            return {item["id"]: item["name"] for item in results}
        except Exception as e:
            logger.error(f"Failed to fetch labels: {e}")
            return {}


# Initialize CVAT API client (will use config from cvat_config)
cvat_api = None
if CVAT_TOKEN:
    cvat_api = CVATAPI(CVAT_API_URL, CVAT_TOKEN, cvat_config.org_slug)
    logger.info("CVAT API client initialized")
else:
    logger.warning("CVAT_TOKEN not set - API calls will fail")


@app.post("/webhook/cvat")
async def cvat_webhook(request: Request):
    """
    CVAT Webhook Endpoint
    
    Receives webhook notifications from CVAT and triggers QC checks.
    
    Expected payload:
    {
        "event": "update:job",
        "job": {
            "id": 123,
            "status": "validation",
            "name": "job_name",
            "assignee": {"id": 456}
        }
    }
    """
    try:
        # 1. Receive payload from CVAT
        payload = await request.json()
        logger.info(f"📥 Received webhook payload")
        
        # Verify secret key if configured
        if WEBHOOK_SECRET:
            secret = request.headers.get("X-CVAT-Webhook-Secret")
            if secret and secret != WEBHOOK_SECRET:
                logger.error("Invalid webhook secret")
                raise HTTPException(status_code=401, detail="Invalid webhook secret")
            elif not secret:
                logger.warning("WEBHOOK_SECRET is set but no secret header provided")
        
        event = payload.get("event")

        # Handle ping event for connection testing
        if event == "ping":
            logger.info("✅ Connection successful! Received Ping from CVAT.")
            return {"message": "Ping received"}
        
        # 2. Only process job update events
        if event != "update:job":
            logger.info(f"Skipping event: {event}")
            return {"message": f"Skipped event: {event}", "status": "skipped"}
        
        job = payload.get("job", {})
        job_id = job.get("id")
        job_name = job.get("name", "unknown")
        status = job.get("status")
        assignee = job.get("assignee") or {}
        assignee_id = assignee.get("id")
        
        logger.info(f"🔔 Job Update: ID={job_id} | Name='{job_name}' | Status='{status}' | Assignee={assignee_id}")
        
        # 3. Only trigger QC when status is 'validation'
        if status != "validation":
            logger.info(f"Status is '{status}' - no QC action required")
            return {
                "message": f"Job {job_id} status update received",
                "job_id": job_id,
                "status": status,
                "action": "none"
            }
        
        # 4. TRIGGER QC CHECK
        logger.info(f"🚀 Starting automatic QC process for Job {job_id}...")
        
        if not cvat_api:
            logger.error("CVAT API not configured - cannot fetch annotations")
            raise HTTPException(
                status_code=500, 
                detail="CVAT API not configured. Please set CVAT_TOKEN environment variable."
            )
        
        # 4a. Get job info
        try:
            job_info = cvat_api.get_job_info(job_id)
            logger.info(f"Job Info: {json.dumps(job_info, indent=2)}")
        except Exception as e:
            logger.error(f"Failed to get job info: {e}")
            return {
                "message": f"Failed to get job info: {str(e)}",
                "job_id": job_id,
                "status": "error",
                "action": "failed"
            }
        
        # 4b. Fetch annotations from CVAT API
        try:
            logger.info(f"Fetching annotations for Job {job_id}...")
            raw_data = cvat_api.get_job_annotations(job_id)
            
            # Check if annotations exist
            if not raw_data or not isinstance(raw_data, dict):
                logger.warning(f"No annotations found for Job {job_id}")
                return {
                    "message": "No annotations found",
                    "job_id": job_id,
                    "status": "no_annotations",
                    "action": "skipped"
                }
            
            logger.info(f"Received annotations with {len(raw_data.get('shapes', []))} shapes")
            
        except Exception as e:
            logger.error(f"Failed to fetch annotations: {e}")
            return {
                "message": f"Failed to fetch annotations: {str(e)}",
                "job_id": job_id,
                "status": "error",
                "action": "failed"
            }
        
        # 4c. Get label mapping and parse CVAT JSON
        try:
            logger.info(f"Fetching label mapping for Job {job_id}...")
            labels_mapping = cvat_api.get_job_labels(job_id)
            
            logger.info(f"Parsing CVAT API JSON Data...")
            frames: List[Frame] = parse_cvat_api_json(raw_data, labels_mapping)
            logger.info(f"✓ Successfully parsed {len(frames)} frames")
            
        except Exception as e:
            logger.error(f"Failed to parse CVAT JSON: {e}")
            return {
                "message": f"Failed to parse annotations: {str(e)}",
                "job_id": job_id,
                "status": "parse_error",
                "action": "failed"
            }
        
        # 4d. Run QC checks with all Phase 1-3 rules
        try:
            logger.info(f"Running QC checks...")
            qc_engine = QCRulesEngine(
                min_box_area=qc_config.min_box_area,
                iou_threshold=qc_config.iou_threshold,
                duplicate_iou_threshold=qc_config.duplicate_iou_threshold,
                min_polygon_points=qc_config.min_polygon_points,
                max_aspect_ratio=qc_config.max_aspect_ratio,
                min_aspect_ratio=qc_config.min_aspect_ratio,
                mask_tolerance=qc_config.mask_tolerance,
                bbox_tolerance=qc_config.bbox_tolerance
            )
            errors = qc_engine.run_qc_check(frames)
            
            logger.info(f"QC Result: {len(errors)} errors found")
            
        except Exception as e:
            logger.error(f"QC check failed: {e}")
            return {
                "message": f"QC check failed: {str(e)}",
                "job_id": job_id,
                "status": "qc_error",
                "action": "failed"
            }
        
        # 5. INITIALIZE REPORT
        report = QCReport(job_id=job_id, job_name=job_name)
        report.total_frames = len(frames)
        report.total_annotations = len(raw_data.get('shapes', []))
        
        for error in errors:
            report.add_error(error.get("Error_Type", "UNKNOWN"), error.get("Message", ""))
        
        # 5. PROCESS QC RESULTS
        if errors:
            # 5a. Errors found - Create individual issues for each error
            logger.warning(f"❌ QC FAILED: {len(errors)} errors found")
            report.status = "failed"
            
            created_issues = []
            for error in errors:
                position = error.get("Position", [0, 0, 0, 0])
                message = error.get("Message", "Unknown error")
                frame_name = error.get("Frame", "0")
                
                try:
                    issue = cvat_api.create_issue(
                        job_id=job_id,
                        frame=int(frame_name),
                        position=position,
                        message=message,
                        assignee_id=assignee_id
                    )
                    created_issues.append(issue)
                    report.issues_created += 1
                    logger.info(f"✓ Created issue for frame {frame_name}")
                except Exception as e:
                    report.failed_issue_creations += 1
                    logger.error(f"Failed to create issue for frame {frame_name}: {e}")
            
            # Update job status to REJECTED: stage="annotation", state="rejected"
            try:
                cvat_api.update_job_status(
                    job_id=job_id, 
                    stage="annotation", 
                    state="rejected",
                    assignee_id=assignee_id
                )
                report.job_status_updated = "rejected"
                logger.info(f"✓ Job {job_id} status updated to rejected")
            except Exception as e:
                logger.error(f"Failed to update job status: {e}")
            
            # Save report
            report_path = report.save()
            
            return {
                "message": f"QC failed - {len(errors)} errors found",
                "job_id": job_id,
                "total_errors": len(errors),
                "error_types": report.get_error_type_counts(),
                "created_issues": len(created_issues),
                "action": "rejected",
                "report_path": report_path,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 5b. No errors - QC passed
            logger.info(f"✅ QC PASSED: No errors found in Job {job_id}")
            report.status = "passed"
            
            # Update job status to keep validation stage
            try:
                cvat_api.update_job_status(
                    job_id=job_id,
                    stage="validation",
                    state="",
                    assignee_id=assignee_id
                )
                report.job_status_updated = "validation"
                logger.info(f"✓ Job {job_id} status confirmed as validation")
            except Exception as e:
                logger.error(f"Failed to update job status: {e}")
            
            # Save report
            report_path = report.save()
            
            return {
                "message": "QC passed - No errors found",
                "job_id": job_id,
                "job_name": job_name,
                "frames_checked": len(frames),
                "total_bboxes": sum(len(f.bboxes) for f in frames),
                "total_polygons": sum(len(f.polygons) for f in frames),
                "action": "passed",
                "report_path": report_path,
                "timestamp": datetime.now().isoformat()
            }
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Health check and service info"""
    return {
        "status": "running",
        "service": "LetmeQC CVAT Webhook Server",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "webhook_endpoint": "/webhook/cvat"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cvat_api_configured": CVAT_TOKEN is not None and CVAT_TOKEN != "",
        "qc_engine_ready": True
    }


@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "cvat_api_url": CVAT_API_URL,
        "cvat_token_set": CVAT_TOKEN is not None and CVAT_TOKEN != "",
        "cvat_org_slug": cvat_config.org_slug,
        "min_box_area": qc_config.min_box_area,
        "iou_threshold": qc_config.iou_threshold,
        "webhook_secret_set": WEBHOOK_SECRET is not None
    }


if __name__ == "__main__":
    # Run server
    logger.info("=" * 60)
    logger.info("  LetmeQC - CVAT Webhook Server")
    logger.info("=" * 60)
    logger.info(f"  Server: http://{SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"  Webhook: POST http://{SERVER_HOST}:{SERVER_PORT}/webhook/cvat")
    logger.info(f"  Health: GET http://{SERVER_HOST}:{SERVER_PORT}/health")
    logger.info(f"  Docs: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    logger.info(f"  Config: GET http://{SERVER_HOST}:{SERVER_PORT}/config")
    logger.info("=" * 60)
    
    if not CVAT_TOKEN:
        logger.warning("⚠️  WARNING: CVAT_TOKEN not set - API calls will fail!")
        logger.warning("   Set CVAT_TOKEN environment variable or in .env file")
    
    if not WEBHOOK_SECRET:
        logger.warning("⚠️  WARNING: WEBHOOK_SECRET not set - anyone can trigger webhook!")
    
    if not cvat_config.org_slug:
        logger.warning("⚠️  WARNING: CVAT_ORG_SLUG not set - organization header will not be sent!")
    
    uvicorn.run(
        "app:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        reload=True
    )