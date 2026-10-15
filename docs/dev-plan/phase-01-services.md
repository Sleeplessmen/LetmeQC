# Phase 1: Service Layer

## 📌 Overview

**Component:** Service Layer  
**Duration:** Week 3  
**Owner:** Backend Dev  
**Priority:** 🔴 HIGH  
**Estimate:** 7 days

---

## 🎯 Objectives

Implement **service layer** for business logic:
- Job Service: Job lifecycle management
- Issue Service: Issue creation and management
- QC Service: Enhanced with database integration
- Report Service: Comprehensive metrics and reporting

---

## 🏗️ Service Architecture

```
src/services/
├── __init__.py
├── job_service.py        # Job lifecycle management
├── issue_service.py      # Issue management
├── qc_service.py         # Enhanced QC processing
└── report_service.py     # Metrics and reporting
```

Each service:
- Uses database_client.py for data access
- Contains business logic
- Handles complex operations
- Returns domain models (not database models)

---

## 📦 Service Implementations

### 1. Job Service

Manages job lifecycle and metadata.

```python
# src/services/job_service.py
from typing import Optional, List
from sqlalchemy.orm import Session

from database.schemas.job import Job
from src.models.job import JobCreate, JobUpdate, JobResponse
from src.clients.database_client import DatabaseClient


class JobService:
    """Service for managing jobs."""
    
    def __init__(self, db: Session, db_client: Optional[DatabaseClient] = None):
        self.db = db
        # Pass db session directly to DatabaseClient instead of monkey patching
        self.db_client = db_client or DatabaseClient(db_session=db)
    
    def create_job(self, job_data: JobCreate) -> JobResponse:
        """
        Create a new job.
        
        Args:
            job_data: JobCreate model with job data
            
        Returns:
            JobResponse with created job data
        """
        job = self.db_client.create_job(
            cvat_job_id=job_data.cvat_job_id,
            cvat_project_id=job_data.cvat_project_id,
            name=job_data.name,
            status=job_data.status.value if job_data.status else "pending",
            stage=job_data.stage.value if job_data.stage else "annotation",
            config=job_data.config or {},
            metadata=job_data.metadata or {}
        )
        return JobResponse.model_validate(job)
    
    def get_job_by_id(self, job_id: int) -> Optional[JobResponse]:
        """
        Get a job by internal ID.
        
        Args:
            job_id: Internal job ID
            
        Returns:
            JobResponse or None if not found
        """
        job = self.db_client.get_job_by_id(job_id)
        if job:
            return JobResponse.model_validate(job)
        return None
    
    def get_job_by_cvat_id(self, cvat_job_id: int) -> Optional[JobResponse]:
        """
        Get a job by CVAT job ID.
        
        Args:
            cvat_job_id: CVAT job ID
            
        Returns:
            JobResponse or None if not found
        """
        job = self.db_client.get_job_by_cvat_id(cvat_job_id)
        if job:
            return JobResponse.model_validate(job)
        return None
    
    def update_job(self, job_id: int, job_data: JobUpdate) -> Optional[JobResponse]:
        """
        Update job status and/or stage.
        
        Args:
            job_id: Internal job ID
            job_data: JobUpdate with fields to update
            
        Returns:
            Updated JobResponse or None if not found
        """
        # Update status and/or stage
        status = job_data.status.value if job_data.status else None
        stage = job_data.stage.value if job_data.stage else None
        updated = self.db_client.update_job_status(job_id, status, stage)
        
        if not updated:
            return None
        
        # Get updated job
        job = self.get_job_by_id(job_id)
        
        # Update config and metadata if provided
        if job and job_data.config:
            job.config.update(job_data.config)
            self.db.commit()
        if job and job_data.metadata:
            job.metadata.update(job_data.metadata)
            self.db.commit()
        
        return job
    
    def list_jobs(self, status: Optional[str] = None, stage: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> List[JobResponse]:
        """
        List jobs with optional filters.
        
        Args:
            status: Filter by job status
            stage: Filter by job stage
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of JobResponse objects
        """
        jobs = self.db_client.list_jobs(status, stage, limit, offset)
        return [JobResponse.model_validate(job) for job in jobs]
    
    def list_jobs_with_count(self, status: Optional[str] = None, stage: Optional[str] = None,
                           limit: int = 100, offset: int = 0) -> Tuple[List[JobResponse], int]:
        """
        List jobs with total count for pagination.
        
        Args:
            status: Filter by job status
            stage: Filter by job stage
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Tuple of (list of JobResponse objects, total count)
        """
        jobs, total_count = self.db_client.list_jobs_with_count(status, stage, limit, offset)
        return [JobResponse.model_validate(job) for job in jobs], total_count
    
    def get_job_statistics(self) -> dict:
        """
        Get overall job statistics.
        
        Returns:
            Dictionary with job statistics
        """
        return self.db_client.get_job_statistics()
```

### 2. Issue Service

Manages QC issues.

```python
# src/services/issue_service.py
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from database.schemas.issue import Issue
from src.models.issue import IssueCreate, IssueUpdate, IssueResponse
from src.clients.database_client import DatabaseClient


class IssueService:
    """Service for managing QC issues."""
    
    def __init__(self, db: Session, db_client: Optional[DatabaseClient] = None):
        self.db = db
        # Pass db session directly to DatabaseClient instead of monkey patching
        self.db_client = db_client or DatabaseClient(db_session=db)
    
    def create_issue(self, job_id: int, issue_data: IssueCreate) -> IssueResponse:
        """
        Create a new issue for a job.
        
        Args:
            job_id: Job ID
            issue_data: IssueCreate with issue data
            
        Returns:
            IssueResponse with created issue
        """
        issue = self.db_client.create_issue(
            cvat_issue_id=issue_data.cvat_issue_id,
            job_id=job_id,
            frame_index=issue_data.frame_index,
            position=issue_data.position,
            message=issue_data.message,
            assignee_id=issue_data.assignee_id,
            severity=issue_data.severity.value if issue_data.severity else "medium"
        )
        return IssueResponse.model_validate(issue)
    
    def get_issue_by_id(self, issue_id: int) -> Optional[IssueResponse]:
        """
        Get an issue by ID.
        
        Args:
            issue_id: Issue ID
            
        Returns:
            IssueResponse or None if not found
        """
        issue = self.db_client.get_issue_by_id(issue_id)
        if issue:
            return IssueResponse.model_validate(issue)
        return None
    
    def get_issues_by_job(self, job_id: int, status: Optional[str] = None,
                          limit: int = 100, offset: int = 0) -> List[IssueResponse]:
        """
        Get issues for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            List of IssueResponse objects
        """
        issues = self.db_client.get_issues_by_job(job_id, status, limit, offset)
        return [IssueResponse.model_validate(issue) for issue in issues]
    
    def get_issues_by_job_with_count(self, job_id: int, status: Optional[str] = None,
                                       limit: int = 100, offset: int = 0) -> Tuple[List[IssueResponse], int]:
        """
        Get issues for a job with total count for pagination.
        
        Args:
            job_id: Job ID
            status: Filter by issue status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Tuple of (list of IssueResponse objects, total count)
        """
        issues, total_count = self.db_client.get_issues_by_job_with_count(job_id, status, limit, offset)
        return [IssueResponse.model_validate(issue) for issue in issues], total_count
            status: Filter by issue status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of IssueResponse objects
        """
        self.db_client.SessionLocal = lambda: self.db
        issues = self.db_client.get_issues_by_job(job_id, status, limit, offset)
        return [IssueResponse.model_validate(issue) for issue in issues]
    
    def update_issue(self, issue_id: int, issue_data: IssueUpdate) -> Optional[IssueResponse]:
        """
        Update an issue.
        
        Args:
            issue_id: Issue ID
            issue_data: IssueUpdate with fields to update
            
        Returns:
            Updated IssueResponse or None if not found
        """
        self.db_client.SessionLocal = lambda: self.db
        
        # Update status if provided
        if issue_data.status:
            self.db_client.update_issue_status(issue_id, issue_data.status.value)
        
        # Get updated issue
        issue = self.db_client.get_issue_by_id(issue_id)
        if issue:
            # Update other fields if provided
            if issue_data.assignee_id is not None:
                issue.assignee_id = issue_data.assignee_id
            if issue_data.severity is not None:
                issue.severity = issue_data.severity.value
            issue.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(issue)
            return IssueResponse.model_validate(issue)
        return None
    
    def count_issues(self, job_id: int, status: Optional[str] = None) -> int:
        """
        Count issues for a job.
        
        Args:
            job_id: Job ID
            status: Filter by issue status
            
        Returns:
            Number of issues
        """
        self.db_client.SessionLocal = lambda: self.db
        return self.db_client.count_issues(job_id, status)
```

### 3. QC Service (Enhanced)

Enhanced QC service with database integration.

```python
# src/services/qc_service.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from database.schemas.job import Job
from database.schemas.qc_result import QCResult
from src.models.frame import Frame, Bbox, Polygon
from src.models.qc_result import QCStatus, Severity
from src.clients.database_client import DatabaseClient
from src.clients.cvat_client import CVATClient
from src.rules.qc_rules import QCRuleEngine

logger = logging.getLogger(__name__)


class QCService:
    """Enhanced QC service with database integration."""
    
    def __init__(self, db: Session, cvat_client: Optional[CVATClient] = None,
                 db_client: Optional[DatabaseClient] = None):
        self.db = db
        # Pass db session directly to DatabaseClient instead of monkey patching
        self.db_client = db_client or DatabaseClient(db_session=db)
        self.cvat_client = cvat_client or CVATClient()
        self.rule_engine = QCRuleEngine()
    
    def fetch_job_data(self, cvat_job_id: int) -> Optional[Job]:
        """
        Fetch job data from CVAT and create/update job record.
        
        Args:
            cvat_job_id: CVAT job ID
            
        Returns:
            Job object or None if failed
        """
        try:
            # Get job info from CVAT
            job_info = self.cvat_client.get_job_info(cvat_job_id)
            
            # Create or update job in database
            job = self.db_client.get_job_by_cvat_id(cvat_job_id)
            if not job:
                job = self.db_client.create_job(
                    cvat_job_id=cvat_job_id,
                    cvat_project_id=job_info.get('project_id'),
                    name=job_info.get('name', f'Job {cvat_job_id}'),
                    status='pending',
                    stage=job_info.get('stage', 'annotation'),
                    metadata=job_info
                )
            else:
                # Update existing job
                self.db_client.update_job_status(
                    job_id=job.id,
                    status='processing',
                    stage=job_info.get('stage', job.stage)
                )
                job = self.db_client.get_job_by_id(job.id)
            
            return job
        except Exception as e:
            logger.error(f"Failed to fetch job data for CVAT job {cvat_job_id}: {e}")
            return None
    
    def run_qc(self, cvat_job_id: int) -> Dict[str, Any]:
        """
        Run QC on a job and store results in database.
        
        Args:
            cvat_job_id: CVAT job ID
            
        Returns:
            Dictionary with QC results summary
        """
        self.db_client.SessionLocal = lambda: self.db
        
        # Get or create job
        job = self.fetch_job_data(cvat_job_id)
        if not job:
            return {"status": "failed", "error": "Job not found or created"}
        
        try:
            # Update job status to processing
            self.db_client.update_job_status(job.id, 'processing', job.stage)
            
            # Get annotations from CVAT
            annotations_data = self.cvat_client.get_job_annotations(cvat_job_id)
            frames = self._parse_annotations_to_frames(annotations_data)
            
            # Run QC on frames
            qc_results = []
            frame_index = 0
            
            for frame in frames:
                frame_errors = self.rule_engine.run_qc(frame)
                
                # Store QC results for each annotation
                for annotation in frame.annotations:
                    if annotation.id in frame_errors:
                        for error in frame_errors[annotation.id]:
                            self._create_qc_result(
                                job_id=job.id,
                                frame_index=frame_index,
                                annotation_id=annotation.id,
                                qc_status=QCStatus.FAIL,
                                error_type=error.get('type'),
                                error_details=error,
                                severity=error.get('severity', 'medium'),
                                rule_id=error.get('rule_id')
                            )
                    else:
                        self._create_qc_result(
                            job_id=job.id,
                            frame_index=frame_index,
                            annotation_id=annotation.id,
                            qc_status=QCStatus.PASS,
                            severity=Severity.LOW
                        )
                
                frame_index += 1
            
            # Update job status based on QC results
            total_errors = self.db_client.count_qc_results(job.id, 'fail')
            
            if total_errors > 0:
                job_status = 'failed'
                job_stage = 'qc_failed'
            else:
                job_status = 'completed'
                job_stage = job.stage  # Keep original stage
            
            self.db_client.update_job_status(job.id, job_status, job_stage)
            
            # Update labeler metrics
            self._update_labeler_metrics(job.id)
            
            return {
                "status": "success",
                "job_id": job.id,
                "cvat_job_id": cvat_job_id,
                "total_frames": frame_index,
                "total_annotations": self.db_client.count_qc_results(job.id),
                "total_errors": total_errors
            }
            
        except Exception as e:
            logger.error(f"QC failed for job {cvat_job_id}: {e}")
            self.db_client.update_job_status(job.id, 'failed', job.stage)
            return {"status": "failed", "error": str(e)}
    
    def _create_qc_result(self, job_id: int, frame_index: int, annotation_id: Optional[int],
                         qc_status: QCStatus, error_type: Optional[str] = None,
                         error_details: Optional[Dict] = None, severity: str = "medium",
                         rule_id: Optional[int] = None) -> None:
        """Helper to create QC result."""
        self.db_client.create_qc_result(
            job_id=job_id,
            frame_index=frame_index,
            annotation_id=annotation_id,
            qc_status=qc_status.value,
            error_type=error_type,
            error_details=error_details,
            severity=severity,
            rule_id=rule_id
        )
    
    def _parse_annotations_to_frames(self, annotations_data: Dict) -> List[Frame]:
        """Parse CVAT annotations data to Frame objects."""
        from src.utils.parser import parse_cvat_annotations
        return parse_cvat_annotations(annotations_data)
    
    def _update_labeler_metrics(self, job_id: int) -> None:
        """Update labeler metrics based on QC results.
        
        NOTE: This method now requires the job to have assignee_id from CVAT metadata.
        If assignee_id is not available, metrics will not be created to avoid
        polluting the database with fake data.
        """
        # Get job to retrieve actual labeler info from CVAT metadata
        job = self.db_client.get_job_by_id(job_id)
        if not job or not job.metadata:
            # Cannot create metrics without labeler info
            return
        
        # Extract labeler info from job metadata (set by CVAT webhook)
        assignee_id = job.metadata.get('assignee', {}).get('id')
        assignee_name = job.metadata.get('assignee', {}).get('username', 'Unknown')
        cvat_project_id = job.cvat_project_id
        
        if not assignee_id:
            # No labeler assigned, skip metrics
            return
        
        qc_results = self.db_client.get_qc_results_by_job(job_id)
        
        # Update metrics aggregated by project, not by job
        self.db_client.create_or_update_labeler_metrics(
            labeler_id=assignee_id,
            labeler_name=assignee_name,
            cvat_project_id=cvat_project_id,
            total_annotations=len(qc_results),
            qc_passed=len([r for r in qc_results if r.qc_status == 'pass']),
            qc_failed=len([r for r in qc_results if r.qc_status == 'fail']),
            total_qc_errors=len([r for r in qc_results if r.qc_status == 'fail'])
        )
    
    def get_qc_results(self, job_id: int, frame_index: Optional[int] = None,
                        qc_status: Optional[str] = None, limit: int = 1000,
                        offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get QC results for a job.
        
        Args:
            job_id: Job ID
            frame_index: Optional filter by frame index
            qc_status: Optional filter by QC status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of QC result dictionaries
        """
        results = self.db_client.get_qc_results_by_job(job_id, frame_index, qc_status, limit, offset)
        
        return [
            {
                "id": r.id,
                "job_id": r.job_id,
                "frame_index": r.frame_index,
                "annotation_id": r.annotation_id,
                "qc_status": r.qc_status,
                "error_type": r.error_type,
                "error_details": r.error_details,
                "severity": r.severity,
                "rule_id": r.rule_id,
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]
    
    def get_qc_results_with_count(self, job_id: int, frame_index: Optional[int] = None,
                                  qc_status: Optional[str] = None, limit: int = 1000,
                                  offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get QC results for a job with total count for pagination.
        
        Args:
            job_id: Job ID
            frame_index: Optional filter by frame index
            qc_status: Optional filter by QC status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Tuple of (list of QC result dictionaries, total count)
        """
        results, total_count = self.db_client.get_qc_results_by_job_with_count(
            job_id, frame_index, qc_status, limit, offset
        )
        
        return [
            {
                "id": r.id,
                "job_id": r.job_id,
                "frame_index": r.frame_index,
                "annotation_id": r.annotation_id,
                "qc_status": r.qc_status,
                "error_type": r.error_type,
                "error_details": r.error_details,
                "severity": r.severity,
                "rule_id": r.rule_id,
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ], total_count
    
    def get_qc_summary(self, job_id: int) -> Dict[str, Any]:
        """
        Get QC summary for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Dictionary with QC summary statistics
        """
        summary = self.db_client.get_qc_summary(job_id)
        
        # Convert to response format
        return {
            "total": summary['total'],
            "passed": summary['passed'],
            "failed": summary['failed'],
            "warnings": summary['warnings'],
            "pass_rate": summary['pass_rate'],
            "fail_rate": summary['fail_rate'],
            "by_status": summary['by_status'],
            "by_error_type": summary['by_error_type'],
            "by_severity": summary['by_severity']
        }
    
    def process_failure(self, cvat_job_id: int) -> Dict[str, Any]:
        """
        Process failed QC and create issues in CVAT.
        
        Args:
            cvat_job_id: CVAT job ID
            
        Returns:
            Dictionary with processing results
        """
        # Run QC first
        result = self.run_qc(cvat_job_id)
        
        if result.get('status') == 'success' and result.get('total_errors', 0) > 0:
            self.db_client.SessionLocal = lambda: self.db
            
            # Get job
            job = self.db_client.get_job_by_cvat_id(cvat_job_id)
            if not job:
                return {"status": "failed", "error": "Job not found"}
            
            # Get failed QC results
            qc_results = self.db_client.get_qc_results_by_job(job.id)
            fail_results = [r for r in qc_results if r.qc_status == 'fail']
            
            # Create issues in CVAT and database
            issues_created = []
            for qc_result in fail_results:
                try:
                    # Create issue in CVAT
                    issue = self.cvat_client.create_issue(
                        job_id=cvat_job_id,
                        frame=qc_result.frame_index,
                        position=qc_result.error_details.get('position', {}),
                        message=qc_result.error_details.get('message', 'QC Error'),
                        assignee_id=None  # Could be set based on labeler
                    )
                    
                    # Create issue in database
                    db_issue = self.db_client.create_issue(
                        cvat_issue_id=issue.get('id'),
                        job_id=job.id,
                        frame_index=qc_result.frame_index,
                        position=qc_result.error_details.get('position', {}),
                        message=qc_result.error_details.get('message', 'QC Error'),
                        severity=qc_result.severity
                    )
                    issues_created.append(db_issue)
                    
                except Exception as e:
                    logger.error(f"Failed to create issue for job {cvat_job_id}, frame {qc_result.frame_index}: {e}")
            
            # Update job status
            self.db_client.update_job_status(job.id, 'failed', 'qc_failed')
            
            return {
                "status": "success",
                "job_id": job.id,
                "total_issues": len(issues_created),
                "issues": issues_created
            }
        
        return {"status": "failed", "error": "No QC failures to process"}
    
    def process_success(self, cvat_job_id: int) -> Dict[str, Any]:
        """
        Process successful QC.
        
        Args:
            cvat_job_id: CVAT job ID
            
        Returns:
            Dictionary with processing results
        """
        result = self.run_qc(cvat_job_id)
        
        if result.get('status') == 'success' and result.get('total_errors', 0) == 0:
            self.db_client.SessionLocal = lambda: self.db
            job = self.db_client.get_job_by_cvat_id(cvat_job_id)
            if job:
                self.db_client.update_job_status(job.id, 'completed', job.stage)
                return {"status": "success", "job_id": job.id, "message": "QC passed"}
        
        return {"status": "failed", "error": "QC did not pass"}
```

### 4. Report Service

Provides comprehensive metrics and reporting.

```python
# src/services/report_service.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.report import MetricsResponse, ReportResponse, DailyTrend, LabelerPerformance
from src.clients.database_client import DatabaseClient


class ReportService:
    """Service for generating reports and metrics."""
    
    def __init__(self, db: Session):
        self.db = db
        self.db_client = DatabaseClient()
    
    def get_metrics(self) -> MetricsResponse:
        """
        Get overall metrics and statistics.
        
        Returns:
            MetricsResponse with all metrics
        """
        self.db_client.SessionLocal = lambda: self.db
        stats = self.db_client.get_job_statistics()
        top_labelers = self.get_labeler_metrics(limit=10)
        daily_trends = self.get_daily_trends(days=30)
        
        return MetricsResponse(
            total_jobs=stats['total_jobs'],
            by_status=stats['by_status'],
            by_stage=stats['by_stage'],
            total_annotations=stats['total_annotations'],
            total_errors=stats['total_errors'],
            top_labelers=top_labelers,
            daily_trends=daily_trends
        )
    
    def get_daily_trends(self, days: int = 30) -> List[DailyTrend]:
        """
        Get daily QC trends.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of DailyTrend objects
        """
        self.db_client.SessionLocal = lambda: self.db
        trends = self.db_client.get_daily_trends(days)
        return [DailyTrend(**t) for t in trends]
    
    def get_labeler_metrics(self, job_id: Optional[int] = None, limit: int = 50) -> List[LabelerPerformance]:
        """
        Get labeler performance metrics.
        
        Args:
            job_id: Optional filter by job ID
            limit: Maximum number of results
            
        Returns:
            List of LabelerPerformance objects
        """
        self.db_client.SessionLocal = lambda: self.db
        metrics = self.db_client.get_labeler_metrics(job_id, limit)
        
        return [
            LabelerPerformance(
                labeler_id=m.labeler_id,
                labeler_name=m.labeler_name or f"Labeler {m.labeler_id}",
                total_annotations=m.total_annotations,
                qc_passed=m.qc_passed,
                qc_failed=m.qc_failed,
                avg_qc_score=m.avg_qc_score,
                total_qc_errors=m.total_qc_errors
            )
            for m in metrics
        ]
    
    def get_job_report(self, job_id: int) -> Optional[ReportResponse]:
        """
        Get detailed report for a specific job.
        
        Args:
            job_id: Job ID
            
        Returns:
            ReportResponse or None if job not found
        """
        self.db_client.SessionLocal = lambda: self.db
        
        job = self.db_client.get_job_by_id(job_id)
        if not job:
            return None
        
        summary = self.db_client.get_qc_summary(job_id)
        issues = self.db_client.get_issues_by_job(job_id)
        labeler_metrics = self.db_client.get_labeler_metrics(job_id)
        
        return ReportResponse(
            job_id=job.id,
            job_name=job.name,
            summary=summary,
            issues_count=len(issues),
            issues=[
                {
                    "id": i.id,
                    "cvat_issue_id": i.cvat_issue_id,
                    "frame_index": i.frame_index,
                    "position": i.position,
                    "message": i.message,
                    "status": i.status,
                    "severity": i.severity,
                    "created_at": i.created_at.isoformat()
                }
                for i in issues
            ],
            labeler_performance=[
                LabelerPerformance(
                    labeler_id=m.labeler_id,
                    labeler_name=m.labeler_name or f"Labeler {m.labeler_id}",
                    total_annotations=m.total_annotations,
                    qc_passed=m.qc_passed,
                    qc_failed=m.qc_failed,
                    avg_qc_score=m.avg_qc_score,
                    total_qc_errors=m.total_qc_errors
                )
                for m in labeler_metrics
            ],
            generated_at=datetime.utcnow()
        )
```

---

## 🧪 Unit Tests

```python
# tests/unit/test_services.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.schemas.base import Base
from src.services.job_service import JobService
from src.services.issue_service import IssueService
from src.services.qc_service import QCService
from src.services.report_service import ReportService
from src.models.job import JobCreate, JobUpdate
from src.models.issue import IssueCreate, IssueUpdate


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestJobService:
    def test_create_job(self, test_db):
        service = JobService(test_db)
        job_data = JobCreate(
            cvat_job_id=123,
            name="Test Job",
            status="pending",
            stage="annotation"
        )
        job = service.create_job(job_data)
        assert job is not None
        assert job.cvat_job_id == 123
        assert job.name == "Test Job"
    
    def test_get_job_by_id(self, test_db):
        service = JobService(test_db)
        job_data = JobCreate(cvat_job_id=456, name="Get Test")
        job = service.create_job(job_data)
        
        retrieved = service.get_job_by_id(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id
    
    def test_list_jobs(self, test_db):
        service = JobService(test_db)
        service.create_job(JobCreate(cvat_job_id=1, name="Job 1"))
        service.create_job(JobCreate(cvat_job_id=2, name="Job 2"))
        
        jobs = service.list_jobs()
        assert len(jobs) == 2


class TestIssueService:
    def test_create_issue(self, test_db):
        job_service = JobService(test_db)
        job = job_service.create_job(JobCreate(cvat_job_id=100, name="Issue Test"))
        
        service = IssueService(test_db)
        issue_data = IssueCreate(
            frame_index=0,
            position={"x": 10, "y": 20, "width": 100, "height": 100},
            message="Test issue",
            severity="high"
        )
        issue = service.create_issue(job.id, issue_data)
        assert issue is not None
        assert issue.job_id == job.id
        assert issue.message == "Test issue"
    
    def test_get_issues_by_job(self, test_db):
        job_service = JobService(test_db)
        job = job_service.create_job(JobCreate(cvat_job_id=200, name="Issues Test"))
        
        service = IssueService(test_db)
        service.create_issue(job.id, IssueCreate(
            frame_index=0,
            position={},
            message="Issue 1"
        ))
        service.create_issue(job.id, IssueCreate(
            frame_index=1,
            position={},
            message="Issue 2"
        ))
        
        issues = service.get_issues_by_job(job.id)
        assert len(issues) == 2


class TestReportService:
    def test_get_metrics(self, test_db):
        job_service = JobService(test_db)
        job_service.create_job(JobCreate(cvat_job_id=300, name="Metrics Test"))
        
        service = ReportService(test_db)
        metrics = service.get_metrics()
        
        assert metrics.total_jobs >= 1
        assert "by_status" in metrics.dict()
        assert "by_stage" in metrics.dict()
    
    def test_get_job_report(self, test_db):
        job_service = JobService(test_db)
        job = job_service.create_job(JobCreate(cvat_job_id=400, name="Report Test"))
        
        service = ReportService(test_db)
        report = service.get_job_report(job.id)
        
        assert report is not None
        assert report.job_id == job.id
        assert report.job_name == job.name
```

---

## ✅ Acceptance Criteria

Phase 1 Service Layer is **complete** when:

1. ✅ Job Service implemented with all methods
2. ✅ Issue Service implemented with all methods
3. ✅ QC Service enhanced with database integration
4. ✅ Report Service implemented with metrics
5. ✅ All services use database_client.py
6. ✅ Unit tests pass with > 80% coverage
7. ✅ Services handle errors appropriately
8. ✅ Services return correct data types

---

## 🔗 Related Documents

- [Phase 1 Overview](./phase-01-overview.md)
- [Phase 1 - Database Layer](./phase-01-database.md)
- [Phase 1 - API Layer](./phase-01-api.md)
- [Phase 1 - Docker Setup](./phase-01-docker.md)
- [Main Development Plan](../README.md)
