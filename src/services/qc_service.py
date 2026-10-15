"""QC Processing Service for LetmeQC"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.models import Frame
from src.parser import parse_cvat_api_json
from src.rules import QCRulesEngine
from src.reports import QCReport
from src.clients.cvat_client import CVATAPI

logger = logging.getLogger(__name__)


class QCService:
    """Service for handling QC processing logic"""

    def __init__(self, cvat_api: CVATAPI, qc_config: Dict):
        """
        Initialize QC Service
        
        Args:
            cvat_api: CVATAPI client instance
            qc_config: Dictionary with QC configuration parameters
        """
        self.cvat_api = cvat_api
        self.qc_config = qc_config
        self.update_job_status_error = "Failed to update job status for job %s"

    def fetch_data(self, job_id: int) -> Tuple[Optional[Dict], Optional[Dict], Optional[List[Frame]], Dict]:
        """Fetch job info, annotations, labels. Returns (job_info, raw_data, frames, error)"""
        try:
            logger.info("Getting job info for job %s", job_id)
            job_info = self.cvat_api.get_job_info(job_id)
            logger.info("Job Info received")
        except Exception as e:
            logger.exception("Failed to get job info for job %s", job_id)
            return None, None, None, {
                "message": "Failed to get job info: " + str(e),
                "job_id": job_id,
                "status": "error",
                "action": "failed"
            }

        try:
            logger.info("Fetching annotations for job %s", job_id)
            raw_data = self.cvat_api.get_job_annotations(job_id)

            if not raw_data or not isinstance(raw_data, dict):
                logger.warning("No annotations found for job %s", job_id)
                return None, None, None, {
                    "message": "No annotations found",
                    "job_id": job_id,
                    "status": "no_annotations",
                    "action": "skipped"
                }

            logger.info("Received %s shapes", len(raw_data.get('shapes', [])))

        except Exception as e:
            logger.exception("Failed to fetch annotations for job %s", job_id)
            return None, None, None, {
                "message": "Failed to fetch annotations: " + str(e),
                "job_id": job_id,
                "status": "error",
                "action": "failed"
            }

        try:
            logger.info("Fetching label mapping for job %s", job_id)
            labels_mapping = self.cvat_api.get_job_labels(job_id)
            logger.info("Parsing CVAT API JSON Data...")
            frames = parse_cvat_api_json(raw_data, labels_mapping)
            logger.info("Successfully parsed %s frames", len(frames))
            return job_info, raw_data, frames, None

        except Exception as e:
            logger.exception("Failed to parse CVAT JSON for job %s", job_id)
            return None, None, None, {
                "message": "Failed to parse annotations: " + str(e),
                "job_id": job_id,
                "status": "parse_error",
                "action": "failed"
            }

    def run_qc(self, frames: List[Frame]) -> List[Dict]:
        """Run QC checks on frames"""
        try:
            logger.info("Running QC checks...")
            qc_engine = QCRulesEngine(
                min_box_area=self.qc_config.get('min_box_area', 100.0),
                iou_threshold=self.qc_config.get('iou_threshold', 0.95),
                duplicate_iou_threshold=self.qc_config.get('duplicate_iou_threshold', 0.98),
                min_polygon_points=self.qc_config.get('min_polygon_points', 3),
                max_aspect_ratio=self.qc_config.get('max_aspect_ratio', 10.0),
                min_aspect_ratio=self.qc_config.get('min_aspect_ratio', 0.1),
                mask_tolerance=self.qc_config.get('mask_tolerance', 2.0),
                bbox_tolerance=self.qc_config.get('bbox_tolerance', 2.0)
            )
            errors = qc_engine.run_qc_check(frames)
            logger.info("QC Result: %s errors found", len(errors))
            return errors

        except Exception:
            logger.exception("QC check failed")
            raise

    def process_failure(self, job_id: int, job_name: str, errors: List[Dict],
                        assignee_id: Optional[int], raw_data: Dict, frames: List[Frame],
                        job_info: Optional[Dict] = None) -> Dict:
        """Process QC failure - create issues and update job status"""
        logger.warning("QC FAILED: %s errors found", len(errors))

        report = QCReport(job_id=job_id, job_name=job_name)

        # Add job information from API
        if job_info:
            report.project_id = job_info.get('project', {}).get('id')
            report.project_name = job_info.get('project', {}).get('name')
            report.assignee_id = assignee_id
            report.assignee_name = job_info.get('assignee', {}).get('username') if job_info.get('assignee') else None
            report.job_created_date = job_info.get('created')
            report.job_updated_date = job_info.get('updated')
            report.job_stage = job_info.get('stage')
            report.job_state = job_info.get('state')

        # Add annotation statistics from raw_data
        if raw_data:
            meta = raw_data.get('meta', {})
            size = meta.get('size', {})
            report.image_width = size.get('width')
            report.image_height = size.get('height')
            report.total_shapes = len(raw_data.get('shapes', []))
            report.total_tracks = len(raw_data.get('tracks', []))
            report.total_tags = len(raw_data.get('tags', []))
            report.frame_count = len(meta.get('frames', []))

        report.total_frames = len(frames)
        report.total_annotations = len(raw_data.get('shapes', [])) + len(raw_data.get('tracks', []))

        for error in errors:
            report.add_error(error.get("Error_Type", "UNKNOWN"), error.get("Message", ""))
        report.status = "failed"

        created_issues = []
        for error in errors:
            position = error.get("Position", [0, 0, 0, 0])
            message = error.get("Message", "Unknown error")
            frame_name = error.get("Frame", "0")

            try:
                issue = self.cvat_api.create_issue(
                    job_id=job_id,
                    frame=int(frame_name),
                    position=position,
                    message=message,
                    assignee_id=assignee_id
                )
                created_issues.append(issue)
                report.issues_created += 1
                logger.info("Created issue for frame %s", frame_name)
            except Exception:
                report.failed_issue_creations += 1
                logger.exception("Failed to create issue for frame %s", frame_name)

        try:
            self.cvat_api.update_job_status(
                job_id=job_id,
                stage="annotation",
                state="rejected",
                assignee_id=assignee_id
            )
            report.job_status_updated = "rejected"
            logger.info("Job %s status updated to rejected", job_id)
        except Exception:
            logger.exception(self.update_job_status_error, job_id)

        report_path = report.save()

        return {
            "message": "QC failed - " + str(len(errors)) + " errors found",
            "job_id": job_id,
            "total_errors": len(errors),
            "error_types": report.get_error_type_counts(),
            "created_issues": len(created_issues),
            "action": "rejected",
            "report_path": report_path,
            "timestamp": datetime.now().isoformat()
        }

    def process_success(self, job_id: int, job_name: str, frames: List[Frame],
                        assignee_id: Optional[int], raw_data: Dict, job_info: Optional[Dict] = None) -> Dict:
        """Process QC success - update job status"""
        logger.info("QC PASSED: No errors found in job %s", job_id)

        report = QCReport(job_id=job_id, job_name=job_name)

        # Add job information from API
        if job_info:
            report.project_id = job_info.get('project', {}).get('id')
            report.project_name = job_info.get('project', {}).get('name')
            report.assignee_id = assignee_id
            report.assignee_name = job_info.get('assignee', {}).get('username') if job_info.get('assignee') else None
            report.job_created_date = job_info.get('created')
            report.job_updated_date = job_info.get('updated')
            report.job_stage = job_info.get('stage')
            report.job_state = job_info.get('state')

        # Add annotation statistics from raw_data
        if raw_data:
            meta = raw_data.get('meta', {})
            size = meta.get('size', {})
            report.image_width = size.get('width')
            report.image_height = size.get('height')
            report.total_shapes = len(raw_data.get('shapes', []))
            report.total_tracks = len(raw_data.get('tracks', []))
            report.total_tags = len(raw_data.get('tags', []))
            report.frame_count = len(meta.get('frames', []))

        report.total_frames = len(frames)
        report.total_annotations = len(raw_data.get('shapes', [])) + len(raw_data.get('tracks', []))
        report.status = "passed"

        try:
            self.cvat_api.update_job_status(
                job_id=job_id,
                stage="validation",
                state="",
                assignee_id=assignee_id
            )
            report.job_status_updated = "validation"
            logger.info("Job %s status confirmed as validation", job_id)
        except Exception:
            logger.exception(self.update_job_status_error, job_id)

        report_path = report.save()

        total_bboxes = sum(len(f.bboxes) for f in frames)
        total_polygons = sum(len(f.polygons) for f in frames)

        return {
            "message": "QC passed - No errors found",
            "job_id": job_id,
            "job_name": job_name,
            "frames_checked": len(frames),
            "total_bboxes": total_bboxes,
            "total_polygons": total_polygons,
            "action": "passed",
            "report_path": report_path,
            "timestamp": datetime.now().isoformat()
        }
