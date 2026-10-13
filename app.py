from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import QC modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from src.parser import parse_coco_json
from src.rules import QCRulesEngine
from src.models import Frame

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
MIN_BOX_AREA = float(os.getenv("MIN_BOX_AREA", "100"))
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.95"))
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
    """Helper class for CVAT API interactions"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {"Authorization": f"Token {token}"}
    
    def get_job_annotations(self, job_id: int) -> Dict:
        """Fetch annotations for a job in COCO format"""
        url = f"{self.base_url}/jobs/{job_id}/annotations"
        logger.info(f"Fetching annotations from: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch annotations for job {job_id}: {e}")
            raise
    
    def create_issue(self, job_id: int, frame_name: str, comment: str, assignee_id: Optional[int] = None) -> Dict:
        """Create a QC issue in CVAT"""
        url = f"{self.base_url}/issues"
        issue_data = {
            "job": job_id,
            "frame": frame_name,
            "comment": comment,
            "status": "open"
        }
        
        if assignee_id:
            issue_data["assignee"] = assignee_id
        
        logger.info(f"Creating issue for job {job_id}, frame {frame_name}: {comment}")
        
        try:
            response = requests.post(url, json=issue_data, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create issue: {e}")
            raise
    
    def update_job_status(self, job_id: int, status: str) -> Dict:
        """Update job status"""
        url = f"{self.base_url}/jobs/{job_id}"
        update_data = {"status": status}
        
        logger.info(f"Updating job {job_id} status to: {status}")
        
        try:
            response = requests.patch(url, json=update_data, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update job status: {e}")
            raise
    
    def get_job_info(self, job_id: int) -> Dict:
        """Get job information"""
        url = f"{self.base_url}/jobs/{job_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get job info: {e}")
            raise


# Initialize CVAT API client (will use token from env)
cvat_api = None
if CVAT_TOKEN:
    cvat_api = CVATAPI(CVAT_API_URL, CVAT_TOKEN)
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
        # 1. Nhận gói tin từ CVAT
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
            logger.info("✅ Kết nối Webhook thành công! Đã nhận được Ping từ CVAT.")
            return {"message": "Ping received"}
        
        # 2. Chỉ xử lý sự kiện cập nhật Job
        if event != "update:job":
            logger.info(f"Skipping event: {event}")
            return {"message": f"Skipped event: {event}", "status": "skipped"}
        
        job = payload.get("job", {})
        job_id = job.get("id")
        status = job.get("status")
        job_name = job.get("name", "unknown")
        assignee = job.get("assignee", {})
        assignee_id = assignee.get("id")
        
        logger.info(f"🔔 Job Update: ID={job_id} | Name='{job_name}' | Status='{status}' | Assignee={assignee_id}")
        
        # 3. Chỉ trigger QC khi status là 'validation'
        if status != "validation":
            logger.info(f"Status is '{status}' - no QC action required")
            return {
                "message": f"Job {job_id} status update received",
                "job_id": job_id,
                "status": status,
                "action": "none"
            }
        
        # 4. KÍCH HOẠT QC CHECK
        logger.info(f"🚀 Starting automatic QC process for Job {job_id}...")
        
        if not cvat_api:
            logger.error("CVAT API not configured - cannot fetch annotations")
            raise HTTPException(
                status_code=500, 
                detail="CVAT API not configured. Please set CVAT_TOKEN environment variable."
            )
        
        # 4a. Lấy thông tin job
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
        
        # 4b. Lấy annotations từ CVAT API
        try:
            logger.info(f"Fetching annotations for Job {job_id}...")
            raw_data = cvat_api.get_job_annotations(job_id)
            
            # Kiểm tra nếu có annotations
            if not raw_data or not isinstance(raw_data, dict):
                logger.warning(f"No annotations found for Job {job_id}")
                return {
                    "message": "No annotations found",
                    "job_id": job_id,
                    "status": "no_annotations",
                    "action": "skipped"
                }
            
            logger.info(f"Received annotations with {len(raw_data.get('annotations', []))} annotations")
            
        except Exception as e:
            logger.error(f"Failed to fetch annotations: {e}")
            return {
                "message": f"Failed to fetch annotations: {str(e)}",
                "job_id": job_id,
                "status": "error",
                "action": "failed"
            }
        
        # 4c. Parse COCO JSON
        try:
            logger.info(f"Parsing COCO JSON...")
            frames: List[Frame] = parse_coco_json(raw_data)
            logger.info(f"✓ Successfully parsed {len(frames)} frames")
            
        except Exception as e:
            logger.error(f"Failed to parse COCO JSON: {e}")
            return {
                "message": f"Failed to parse annotations: {str(e)}",
                "job_id": job_id,
                "status": "parse_error",
                "action": "failed"
            }
        
        # 4d. Chạy QC checks
        try:
            logger.info(f"Running QC checks...")
            qc_engine = QCRulesEngine(
                min_box_area=MIN_BOX_AREA,
                iou_threshold=IOU_THRESHOLD
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
        
        # 5. XỬ LÝ KẾT QUẢ QC
        if errors:
            # 5a. Có lỗi - Tạo issues trong CVAT
            logger.warning(f"❌ QC FAILED: {len(errors)} errors found")
            
            # Group errors by frame
            frame_errors: Dict[str, List[Dict]] = {}
            for error in errors:
                frame_name = error.get("Frame", "unknown")
                if frame_name not in frame_errors:
                    frame_errors[frame_name] = []
                frame_errors[frame_name].append(error)
            
            # Tạo 1 issue cho mỗi frame có lỗi
            created_issues = []
            for frame_name, errors_in_frame in frame_errors.items():
                error_types = [e["Error_Type"] for e in errors_in_frame]
                error_count = len(errors_in_frame)
                
                # Tạo comment tóm tắt
                comment = f"QC Check Failed: {error_count} error(s) found\n"
                comment += f"Error types: {', '.join(set(error_types))}\n"
                comment += f"Frame: {frame_name}"
                
                try:
                    issue = cvat_api.create_issue(
                        job_id=job_id,
                        frame_name=frame_name,
                        comment=comment,
                        assignee_id=assignee_id
                    )
                    created_issues.append(issue)
                    logger.info(f"✓ Created issue for frame {frame_name}")
                except Exception as e:
                    logger.error(f"Failed to create issue for frame {frame_name}: {e}")
            
            # 5b. Đổi status job về 'annotation' để annotator sửa
            try:
                cvat_api.update_job_status(job_id, "annotation")
                logger.info(f"✓ Job {job_id} status changed back to 'annotation'")
            except Exception as e:
                logger.error(f"Failed to update job status: {e}")
            
            return {
                "message": f"QC failed - {len(errors)} errors found",
                "job_id": job_id,
                "total_errors": len(errors),
                "frames_with_errors": len(frame_errors),
                "created_issues": len(created_issues),
                "errors": errors,
                "action": "rejected",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 5c. Không lỗi - QC passed
            logger.info(f"✅ QC PASSED: No errors found in Job {job_id}")
            
            return {
                "message": "QC passed - No errors found",
                "job_id": job_id,
                "frames_checked": len(frames),
                "total_bboxes": sum(len(f.bboxes) for f in frames),
                "total_polygons": sum(len(f.polygons) for f in frames),
                "action": "approved",
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
        "min_box_area": MIN_BOX_AREA,
        "iou_threshold": IOU_THRESHOLD,
        "webhook_secret_set": WEBHOOK_SECRET is not None
    }


if __name__ == "__main__":
    # Chạy server
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
    
    uvicorn.run(
        "app:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        reload=True
    )
