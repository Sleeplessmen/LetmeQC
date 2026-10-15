# Phase 1: API Layer

## 📌 Overview

**Component:** API Layer  
**Duration:** Week 2-3  
**Owner:** Backend Dev  
**Priority:** 🔴 HIGH  
**Estimate:** 7 days

---

## 🎯 Objectives

Build **enhanced API endpoints** for:
- Job management (CRUD operations)
- QC results retrieval
- Issue management
- Reports and metrics

---

## 📡 API Endpoints

### Base URL
```
Production: https://your-domain.com/api/v1
Development: http://localhost:8000/api/v1
```

### Endpoints Summary

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| POST | `/webhook/cvat` | Receive CVAT webhook events | WebhookResponse |
| GET | `/api/v1/jobs` | List all jobs | PaginatedResponse[JobResponse] |
| GET | `/api/v1/jobs/{job_id}` | Get job by ID | JobResponse |
| GET | `/api/v1/jobs/cvat/{cvat_job_id}` | Get job by CVAT ID | JobResponse |
| POST | `/api/v1/jobs` | Create a job | JobResponse |
| PUT | `/api/v1/jobs/{job_id}` | Update job | JobResponse |
| GET | `/api/v1/jobs/{job_id}/qc-results` | Get QC results | PaginatedResponse[QCResultResponse] |
| GET | `/api/v1/jobs/{job_id}/qc-results/summary` | Get QC summary | QCSummaryResponse |
| GET | `/api/v1/jobs/{job_id}/issues` | Get issues | PaginatedResponse[IssueResponse] |
| POST | `/api/v1/jobs/{job_id}/issues` | Create issue | IssueResponse |
| PUT | `/api/v1/issues/{issue_id}` | Update issue | IssueResponse |
| GET | `/api/v1/reports/metrics` | Get overall metrics | MetricsResponse |
| GET | `/api/v1/reports/daily-trends` | Get daily trends | PaginatedResponse[DailyTrend] |
| GET | `/api/v1/reports/labelers` | Get labeler metrics | PaginatedResponse[LabelerPerformance] |
| GET | `/api/v1/reports/jobs/{job_id}` | Get job report | ReportResponse |

---

## 📦 API Models (Pydantic)

### Enums

```python
# src/models/enums.py
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStage(str, Enum):
    ANNOTATION = "annotation"
    VALIDATION = "validation"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QC_FAILED = "qc_failed"
    QC_PASSED = "qc_passed"

class QCStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IssueStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    REJECTED = "rejected"
```

### Job Models

```python
# src/models/job.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from .enums import JobStatus, JobStage


class JobBase(BaseModel):
    """Base job model."""
    cvat_job_id: int = Field(..., description="CVAT job ID", ge=1)
    cvat_project_id: Optional[int] = Field(None, description="CVAT project ID", ge=1)
    name: str = Field(..., description="Job name", min_length=1, max_length=255)
    status: JobStatus = Field(default=JobStatus.PENDING, description="Job status")
    stage: JobStage = Field(default=JobStage.ANNOTATION, description="Job stage")
    config: Dict[str, Any] = Field(default_factory=dict, description="QC configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class JobCreate(JobBase):
    """Model for creating a job."""
    pass


class JobUpdate(BaseModel):
    """Model for updating a job."""
    status: Optional[JobStatus] = Field(None, description="Updated job status")
    stage: Optional[JobStage] = Field(None, description="Updated job stage")
    config: Optional[Dict[str, Any]] = Field(None, description="Updated QC configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class JobResponse(JobBase):
    """Job response model with ID and timestamps."""
    id: int = Field(..., description="Internal job ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
```

### QC Result Models

```python
# src/models/qc_result.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from .enums import QCStatus, Severity


class QCResultBase(BaseModel):
    """Base QC result model."""
    job_id: int = Field(..., description="Job ID", ge=1)
    frame_index: int = Field(..., description="Frame index", ge=0)
    annotation_id: Optional[int] = Field(None, description="CVAT annotation ID", ge=1)
    qc_status: QCStatus = Field(..., description="QC status")
    error_type: Optional[str] = Field(None, description="Error type", max_length=100)
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    severity: Severity = Field(default=Severity.MEDIUM, description="Error severity")
    rule_id: Optional[int] = Field(None, description="Rule ID that failed", ge=1)


class QCResultCreate(QCResultBase):
    """Model for creating a QC result."""
    pass


class QCResultResponse(QCResultBase):
    """QC result response model with ID and timestamp."""
    id: int = Field(..., description="Internal QC result ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class QCSummary(BaseModel):
    """Summary of QC results for a job."""
    total: int = Field(..., description="Total number of QC results")
    passed: int = Field(..., description="Number of passed QC results")
    failed: int = Field(..., description="Number of failed QC results")
    warnings: int = Field(..., description="Number of warning QC results")
    pass_rate: float = Field(..., description="Pass rate percentage")
    fail_rate: float = Field(..., description="Fail rate percentage")
    by_status: Dict[str, int] = Field(default_factory=dict, description="Count by status")
    by_error_type: Dict[str, int] = Field(default_factory=dict, description="Count by error type")
    by_severity: Dict[str, int] = Field(default_factory=dict, description="Count by severity")
```

### Issue Models

```python
# src/models/issue.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .enums import Severity, IssueStatus


class IssueBase(BaseModel):
    """Base issue model."""
    cvat_issue_id: Optional[int] = Field(None, description="CVAT issue ID", ge=1)
    job_id: int = Field(..., description="Job ID", ge=1)
    frame_index: int = Field(..., description="Frame index", ge=0)
    position: List[float] = Field(..., description="[x1, y1, x2, y2]", min_length=4, max_length=4)
    message: str = Field(..., description="Issue message", min_length=1, max_length=1000)
    assignee_id: Optional[int] = Field(None, description="CVAT user ID", ge=1)
    severity: Severity = Field(default=Severity.MEDIUM, description="Issue severity")


class IssueCreate(IssueBase):
    """Model for creating an issue."""
    pass


class IssueUpdate(BaseModel):
    """Model for updating an issue."""
    status: Optional[IssueStatus] = Field(None, description="Updated issue status")
    assignee_id: Optional[int] = Field(None, description="Updated assignee ID", ge=1)
    severity: Optional[Severity] = Field(None, description="Updated severity")


class IssueResponse(IssueBase):
    """Issue response model with all fields."""
    id: int = Field(..., description="Internal issue ID")
    status: IssueStatus = Field(default=IssueStatus.OPEN, description="Issue status")
    created_at: datetime = Field(..., description="Creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
```

### Pagination Model

```python
# src/models/pagination.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    total_count: int = Field(..., description="Total number of records", ge=0)
    limit: int = Field(..., description="Number of records per page", ge=1)
    offset: int = Field(..., description="Current offset", ge=0)
    data: List[T] = Field(default_factory=list, description="List of records")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "total_count": 100,
                    "limit": 20,
                    "offset": 0,
                    "data": []
                }
            ]
        }
```

### Webhook Models

```python
# src/models/webhook.py
from pydantic import BaseModel, Field
from typing import Optional

class WebhookResponse(BaseModel):
    """Webhook response model."""
    status: str = Field(..., description="Processing status (received, processing, skipped, error)")
    job_id: Optional[int] = Field(None, description="Job ID if applicable")
    cvat_job_id: Optional[int] = Field(None, description="CVAT job ID if applicable")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "status": "processing",
                    "job_id": 1,
                    "cvat_job_id": 12345,
                    "message": "QC processing started"
                }
            ]
        }
```

### Report Models

```python
# src/models/report.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from .qc_result import QCSummary
from .issue import IssueResponse


class LabelerPerformance(BaseModel):
    """Labeler performance metrics."""
    labeler_id: int
    labeler_name: str
    total_annotations: int
    qc_passed: int
    qc_failed: int
    avg_qc_score: float
    total_qc_errors: int


class DailyTrend(BaseModel):
    """Daily QC trends."""
    date: str
    jobs_created: int
    unique_jobs: int


class MetricsResponse(BaseModel):
    """Overall metrics and statistics."""
    total_jobs: int
    by_status: Dict[str, int]
    by_stage: Dict[str, int]
    total_annotations: int
    total_errors: int
    top_labelers: List[LabelerPerformance]
    daily_trends: List[DailyTrend]


class ReportResponse(BaseModel):
    """Detailed report for a specific job."""
    job_id: int
    job_name: str
    summary: QCSummary
    issues_count: int
    issues: List[IssueResponse]
    labeler_performance: List[LabelerPerformance]
    generated_at: datetime
```

---

## 🚀 API Router Implementation

### Directory Structure
```
src/app/api/v1/
├── __init__.py
├── main.py          # Main API router
└── routers/
    ├── __init__.py
    ├── jobs.py       # Job endpoints
    ├── qc_results.py # QC result endpoints
    ├── issues.py     # Issue endpoints
    └── reports.py    # Report endpoints
```

### Main API Router

```python
# src/app/api/v1/main.py
from fastapi import APIRouter

from src.app.api.v1.routers import jobs, qc_results, issues, reports, webhook

api_router = APIRouter()

# Include all routers
api_router.include_router(webhook.router)
api_router.include_router(jobs.router)
api_router.include_router(qc_results.router)
api_router.include_router(issues.router)
api_router.include_router(reports.router)
```

### Jobs Router

```python
# src/app/api/v1/routers/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from src.models.job import JobResponse, JobCreate, JobUpdate, JobStatus, JobStage
from src.models.pagination import PaginatedResponse
from src.services.job_service import JobService
from src.app.dependencies import get_db

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    stage: Optional[JobStage] = Query(None, description="Filter by job stage"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List all jobs with optional filters.
    
    **Parameters:**
    - `status`: Filter by job status (pending, processing, completed, failed)
    - `stage`: Filter by job stage (annotation, validation, accepted, rejected)
    - `limit`: Maximum number of results to return (1-1000)
    - `offset`: Number of results to skip for pagination
    
    **Returns:**
    Paginated response with total_count, limit, offset, and list of jobs
    """
    job_service = JobService(db)
    jobs, total_count = job_service.list_jobs_with_count(status=status, stage=stage, limit=limit, offset=offset)
    return PaginatedResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        data=jobs
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get job details by internal ID.
    
    **Path Parameters:**
    - `job_id`: Internal job ID
    
    **Returns:**
    Job object with all details
    """
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/cvat/{cvat_job_id}", response_model=JobResponse)
async def get_job_by_cvat_id(cvat_job_id: int, db: Session = Depends(get_db)):
    """
    Get job details by CVAT job ID.
    
    **Path Parameters:**
    - `cvat_job_id`: CVAT job ID
    
    **Returns:**
    Job object with all details
    """
    job_service = JobService(db)
    job = job_service.get_job_by_cvat_id(cvat_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """
    Create a new job.
    
    **Request Body:**
    - `cvat_job_id`: Required. CVAT job ID
    - `cvat_project_id`: Optional. CVAT project ID
    - `name`: Required. Job name
    - `status`: Optional. Job status (default: pending)
    - `stage`: Optional. Job stage (default: annotation)
    - `config`: Optional. QC configuration
    - `metadata`: Optional. Additional metadata
    
    **Returns:**
    Created job object with ID
    """
    job_service = JobService(db)
    
    # Check if job already exists
    existing = job_service.get_job_by_cvat_id(job_data.cvat_job_id)
    if existing:
        raise HTTPException(
            status_code=409, 
            detail=f"Job with CVAT ID {job_data.cvat_job_id} already exists"
        )
    
    return job_service.create_job(job_data)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int, 
    job_data: JobUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update job status and/or stage.
    
    **Path Parameters:**
    - `job_id`: Internal job ID
    
    **Request Body:**
    - `status`: Optional. Updated job status
    - `stage`: Optional. Updated job stage
    - `config`: Optional. Updated QC configuration
    - `metadata`: Optional. Updated metadata
    
    **Returns:**
    Updated job object
    """
    job_service = JobService(db)
    job = job_service.update_job(job_id, job_data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/run-qc", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def run_qc(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger QC processing for a job.
    
    **Path Parameters:**
    - `job_id`: Internal job ID
    
    **Returns:**
    Confirmation that QC processing has been triggered
    
    **Status Codes:**
    - 202: QC processing started in background
    - 404: Job not found
    """
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Trigger QC processing in background
    background_tasks.add_task(
        job_service.run_qc_processing,
        job_id=job_id
    )
    
    return {
        "status": "qc_started",
        "job_id": job_id,
        "cvat_job_id": job.cvat_job_id,
        "message": "QC processing triggered in background"
    }
```

### QC Results Router

```python
# src/app/api/v1/routers/qc_results.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from src.models.qc_result import QCResultResponse, QCSummary
from src.models.pagination import PaginatedResponse
from src.services.qc_service import QCService
from src.app.dependencies import get_db

router = APIRouter(prefix="/api/v1/jobs/{job_id}/qc-results", tags=["qc-results"])


@router.get("/", response_model=PaginatedResponse[QCResultResponse])
async def get_qc_results(
    job_id: int,
    frame_index: Optional[int] = Query(None, description="Filter by frame index"),
    qc_status: Optional[str] = Query(None, description="Filter by QC status"),
    limit: int = Query(1000, ge=1, le=10000, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get QC results for a job.
    
    **Path Parameters:**
    - `job_id`: Job ID
    
    **Query Parameters:**
    - `frame_index`: Optional. Filter by frame index
    - `qc_status`: Optional. Filter by QC status (pass, fail, warning)
    - `limit`: Maximum number of results (1-10000)
    - `offset`: Number of results to skip
    
    **Returns:**
    Paginated response with total_count, limit, offset, and list of QC results
    """
    qc_service = QCService(db)
    results, total_count = qc_service.get_qc_results_with_count(job_id, frame_index, qc_status, limit, offset)
    return PaginatedResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        data=results
    )


@router.get("/summary", response_model=QCSummary)
async def get_qc_summary(job_id: int, db: Session = Depends(get_db)):
    """
    Get QC summary statistics for a job.
    
    **Path Parameters:**
    - `job_id`: Job ID
    
    **Returns:**
    Summary statistics including:
    - Total, passed, failed, warnings count
    - Pass rate and fail rate percentages
    - Counts by error type and severity
    """
    qc_service = QCService(db)
    return qc_service.get_qc_summary(job_id)
```

### Issues Router

```python
# src/app/api/v1/routers/issues.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from src.models.issue import IssueResponse, IssueCreate, IssueUpdate
from src.models.pagination import PaginatedResponse
from src.services.issue_service import IssueService
from src.app.dependencies import get_db

router = APIRouter(tags=["issues"])


@router.get("/api/v1/jobs/{job_id}/issues", response_model=PaginatedResponse[IssueResponse])
async def get_issues(
    job_id: int,
    status: Optional[str] = Query(None, description="Filter by issue status"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get issues for a job.
    
    **Path Parameters:**
    - `job_id`: Job ID
    
    **Query Parameters:**
    - `status`: Optional. Filter by issue status (open, resolved, rejected)
    - `limit`: Maximum number of results (1-1000)
    - `offset`: Number of results to skip
    
    **Returns:**
    Paginated response with total_count, limit, offset, and list of issues
    """
    issue_service = IssueService(db)
    issues, total_count = issue_service.get_issues_by_job_with_count(job_id, status, limit, offset)
    return PaginatedResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        data=issues
    )


@router.post("/api/v1/jobs/{job_id}/issues", response_model=IssueResponse, status_code=201)
async def create_issue(
    job_id: int, 
    issue_data: IssueCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new issue for a job.
    
    **Path Parameters:**
    - `job_id`: Job ID
    
    **Request Body:**
    - `cvat_issue_id`: Optional. CVAT issue ID
    - `frame_index`: Required. Frame index
    - `position`: Required. Position object {x, y, width, height}
    - `message`: Required. Issue message
    - `assignee_id`: Optional. CVAT user ID
    - `severity`: Optional. Severity (default: medium)
    
    **Returns:**
    Created issue object
    """
    issue_service = IssueService(db)
    return issue_service.create_issue(job_id, issue_data)


@router.put("/api/v1/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    issue_data: IssueUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an issue.
    
    **Path Parameters:**
    - `issue_id`: Issue ID
    
    **Request Body:**
    - `status`: Optional. Updated issue status
    - `assignee_id`: Optional. Updated assignee ID
    - `severity`: Optional. Updated severity
    
    **Returns:**
    Updated issue object
    """
    issue_service = IssueService(db)
    issue = issue_service.update_issue(issue_id, issue_data)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue
```

### Reports Router

```python
# src/app/api/v1/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.report import MetricsResponse, ReportResponse, DailyTrend, LabelerPerformance
from src.services.report_service import ReportService
from src.app.dependencies import get_db

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get overall metrics and statistics.
    
    **Returns:**
    Metrics including:
    - Total jobs by status and stage
    - Total annotations and errors
    - Top labelers by performance
    - Daily trends
    """
    report_service = ReportService(db)
    return report_service.get_metrics()


@router.get("/daily-trends", response_model=List[DailyTrend])
async def get_daily_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get daily QC trends.
    
    **Query Parameters:**
    - `days`: Number of days to look back (1-365, default: 30)
    
    **Returns:**
    List of daily trend objects with date, jobs_created, and unique_jobs
    """
    report_service = ReportService(db)
    return report_service.get_daily_trends(days)


@router.get("/labelers", response_model=List[LabelerPerformance])
async def get_labeler_metrics(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    limit: int = Query(50, ge=1, le=100, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """
    Get labeler performance metrics.
    
    **Query Parameters:**
    - `job_id`: Optional. Filter by job ID
    - `limit`: Maximum number of results (1-100, default: 50)
    
    **Returns:**
    List of labeler performance objects sorted by average QC score
    """
    report_service = ReportService(db)
    return report_service.get_labeler_metrics(job_id, limit)


@router.get("/jobs/{job_id}", response_model=ReportResponse)
async def get_job_report(job_id: int, db: Session = Depends(get_db)):
    """
    Get detailed report for a specific job.
    
    **Path Parameters:**
    - `job_id`: Job ID
    
    **Returns:**
    Detailed report including:
    - Job information
    - QC summary
    - Issues list
    - Labeler performance
    - Generation timestamp
    """
    report_service = ReportService(db)
    report = report_service.get_job_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Job not found")
    return report
```

### Webhook Router

**CRITICAL**: Webhook endpoint for receiving CVAT events and triggering QC processing.

```python
# src/app/api/v1/routers/webhook.py
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.orm import Session
import logging

from src.handlers.webhook_handlers import handle_cvat_webhook
from src.app.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/cvat", status_code=status.HTTP_202_ACCEPTED)
async def cvat_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    db: Session = Depends(get_db)
):
    """
    Receive CVAT webhook events and trigger QC processing in background.
    
    This is the primary entry point for the entire QC workflow.
    
    **Headers:**
    - `X-Webhook-Secret`: Required. Secret for validating webhook requests
    
    **Request Body:**
    CVAT webhook payload with job status updates
    
    **Example Payload:**
    ```json
    {
      "action": "update",
      "resource": "job",
      "id": 12345,
      "name": "My Job",
      "status": "validation",
      "stage": "annotation",
      "assignee": {"id": 1, "username": "annotator1"},
      "frames_count": 100,
      "annotations_count": 50
    }
    ```
    
    **Returns:**
    JSON response confirming webhook was received and is processing in background
    
    **Status Codes:**
    - 202: Webhook accepted, QC processing started in background
    - 401: Invalid webhook secret
    - 400: Invalid payload
    """
    # Validate webhook secret
    from src.config.settings import get_settings
    settings = get_settings()
    
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        logger.warning(f"Invalid webhook secret from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret"
        )
    
    # Get request body
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Process webhook in background to avoid blocking the webhook response
    background_tasks.add_task(handle_cvat_webhook, payload, db)
    
    # Return immediately - processing happens in background
    return {"status": "processing_in_background", "message": "Webhook received, QC processing started"}
```

---

## 🔌 API Dependencies

```python
# src/app/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session

from database.session import SessionLocal


def get_db():
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🧪 Integration Tests

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.main import app
from database.schemas.base import Base
from database.session import SessionLocal


@pytest.fixture
def test_db():
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    # Override get_db dependency
    from src.app.dependencies import get_db
    
    def override_get_db():
        db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    return TestClient(app)


class TestJobs:
    """Test job endpoints."""
    
    def test_list_jobs_empty(self, client):
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_job(self, client):
        response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 123,
            "name": "Test Job",
            "status": "pending",
            "stage": "annotation"
        })
        assert response.status_code == 201
        assert response.json()["cvat_job_id"] == 123
        assert response.json()["name"] == "Test Job"
    
    def test_get_job(self, client):
        # Create a job first
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 456,
            "name": "Get Test Job"
        })
        job_id = create_response.json()["id"]
        
        # Get the job
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["id"] == job_id
    
    def test_get_job_by_cvat_id(self, client):
        # Create a job
        client.post("/api/v1/jobs", json={
            "cvat_job_id": 789,
            "name": "CVAT Test Job"
        })
        
        # Get by CVAT ID
        response = client.get("/api/v1/jobs/cvat/789")
        assert response.status_code == 200
        assert response.json()["cvat_job_id"] == 789
    
    def test_update_job(self, client):
        # Create a job
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 101,
            "name": "Update Test Job"
        })
        job_id = create_response.json()["id"]
        
        # Update the job
        response = client.put(f"/api/v1/jobs/{job_id}", json={
            "status": "completed",
            "stage": "accepted"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["stage"] == "accepted"
    
    def test_create_duplicate_job(self, client):
        # Create first job
        client.post("/api/v1/jobs", json={
            "cvat_job_id": 201,
            "name": "First Job"
        })
        
        # Try to create duplicate
        response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 201,
            "name": "Duplicate Job"
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


class TestQCResults:
    """Test QC result endpoints."""
    
    def test_get_qc_results_empty(self, client):
        # Create a job first
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 301,
            "name": "QC Test Job"
        })
        job_id = create_response.json()["id"]
        
        # Get QC results (should be empty)
        response = client.get(f"/api/v1/jobs/{job_id}/qc-results")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_qc_summary(self, client):
        # Create a job
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 302,
            "name": "Summary Test Job"
        })
        job_id = create_response.json()["id"]
        
        # Get summary
        response = client.get(f"/api/v1/jobs/{job_id}/qc-results/summary")
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["passed"] == 0
        assert response.json()["failed"] == 0


class TestIssues:
    """Test issue endpoints."""
    
    def test_create_issue(self, client):
        # Create a job first
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 401,
            "name": "Issue Test Job"
        })
        job_id = create_response.json()["id"]
        
        # Create an issue
        response = client.post(f"/api/v1/jobs/{job_id}/issues", json={
            "frame_index": 0,
            "position": {"x": 10, "y": 20, "width": 100, "height": 100},
            "message": "Test issue",
            "severity": "medium"
        })
        assert response.status_code == 201
        assert response.json()["job_id"] == job_id
        assert response.json()["message"] == "Test issue"
    
    def test_get_issues(self, client):
        # Create a job with an issue
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 402,
            "name": "Issues Test Job"
        })
        job_id = create_response.json()["id"]
        
        client.post(f"/api/v1/jobs/{job_id}/issues", json={
            "frame_index": 0,
            "position": {"x": 10, "y": 20, "width": 100, "height": 100},
            "message": "Test issue",
        })
        
        # Get issues
        response = client.get(f"/api/v1/jobs/{job_id}/issues")
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_update_issue(self, client):
        # Create a job with an issue
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 403,
            "name": "Update Issue Test Job"
        })
        job_id = create_response.json()["id"]
        
        issue_response = client.post(f"/api/v1/jobs/{job_id}/issues", json={
            "frame_index": 0,
            "position": {"x": 10, "y": 20, "width": 100, "height": 100},
            "message": "Test issue",
        })
        issue_id = issue_response.json()["id"]
        
        # Update issue
        response = client.put(f"/api/v1/issues/{issue_id}", json={
            "status": "resolved"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"


class TestReports:
    """Test report endpoints."""
    
    def test_get_metrics(self, client):
        response = client.get("/api/v1/reports/metrics")
        assert response.status_code == 200
        assert "total_jobs" in response.json()
        assert "by_status" in response.json()
        assert "by_stage" in response.json()
    
    def test_get_daily_trends(self, client):
        response = client.get("/api/v1/reports/daily-trends?days=7")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_labeler_metrics(self, client):
        response = client.get("/api/v1/reports/labelers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_job_report(self, client):
        # Create a job
        create_response = client.post("/api/v1/jobs", json={
            "cvat_job_id": 501,
            "name": "Report Test Job"
        })
        job_id = create_response.json()["id"]
        
        # Get report
        response = client.get(f"/api/v1/reports/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["job_id"] == job_id
        assert "summary" in response.json()
        assert "generated_at" in response.json()
```

---

## ✅ Acceptance Criteria

Phase 1 API Layer is **complete** when:

1. ✅ All API endpoints are implemented
2. ✅ All Pydantic models are defined
3. ✅ Request validation works correctly
4. ✅ Error handling is implemented
5. ✅ Integration tests pass
6. ✅ API documentation (Swagger) is available
7. ✅ All endpoints return correct response models

---

## 🔗 Related Documents

- [Phase 1 Overview](./phase-01-overview.md)
- [Phase 1 - Database Layer](./phase-01-database.md)
- [Phase 1 - Services](./phase-01-services.md)
- [Phase 1 - Docker Setup](./phase-01-docker.md)
- [Main Development Plan](../README.md)
