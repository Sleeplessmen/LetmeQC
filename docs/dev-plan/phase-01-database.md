# Phase 1: Database Layer

## 📌 Overview

**Component:** Database Layer  
**Duration:** Week 1-2  
**Owner:** Backend Dev  
**Priority:** 🔴 HIGH  
**Estimate:** 8 days

---

## 🎯 Objectives

Build a **comprehensive database layer** to store:
- Job metadata and lifecycle information
- QC results for all frames and annotations
- QC issues created in CVAT
- Labeler performance metrics

---

## 🏗️ Database Schema

### Tables Design

#### 1. Jobs Table
Stores all CVAT jobs processed by LetmeQC

```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    cvat_job_id INTEGER UNIQUE NOT NULL,
    cvat_project_id INTEGER,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed
    stage VARCHAR(50) NOT NULL,   -- annotation, validation, accepted, rejected
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    config JSONB,  -- QC configuration for this job
    metadata JSONB  -- Additional job metadata from CVAT
);

CREATE INDEX idx_jobs_cvat_id ON jobs(cvat_job_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_stage ON jobs(stage);
```

#### 2. QC Results Table
Stores QC validation results for each annotation

```sql
CREATE TABLE qc_results (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    frame_index INTEGER NOT NULL,
    annotation_id INTEGER,  -- CVAT annotation ID
    qc_status VARCHAR(20) NOT NULL,  -- pass, fail, warning
    error_type VARCHAR(100),
    error_details JSONB,
    severity VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, critical
    rule_id INTEGER,  -- Reference to rule that failed
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_qc_results_job_id ON qc_results(job_id);
CREATE INDEX idx_qc_results_frame_index ON qc_results(frame_index);
CREATE INDEX idx_qc_results_status ON qc_results(qc_status);
CREATE INDEX idx_qc_results_job_frame ON qc_results(job_id, frame_index);
CREATE INDEX idx_qc_results_status_severity ON qc_results(qc_status, severity);
```

#### 3. Issues Table
Stores QC issues (synced with CVAT issues)

```sql
CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    cvat_issue_id INTEGER UNIQUE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    frame_index INTEGER NOT NULL,
    position JSONB NOT NULL,  -- {x, y, width, height}
    message TEXT NOT NULL,
    assignee_id INTEGER,  -- CVAT user ID
    status VARCHAR(50) DEFAULT 'open',  -- open, resolved, rejected
    severity VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_issues_job_id ON issues(job_id);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_frame_index ON issues(frame_index);
```

#### 4. Labeler Metrics Table
Stores performance metrics for each labeler

```sql
CREATE TABLE labeler_metrics (
    id SERIAL PRIMARY KEY,
    labeler_id INTEGER NOT NULL,  -- CVAT user ID
    labeler_name VARCHAR(255),
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    total_annotations INTEGER DEFAULT 0,
    qc_passed INTEGER DEFAULT 0,
    qc_failed INTEGER DEFAULT 0,
    avg_qc_score FLOAT DEFAULT 0,
    total_qc_errors INTEGER DEFAULT 0,
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(labeler_id, job_id)
);

CREATE INDEX idx_labeler_metrics_labeler_id ON labeler_metrics(labeler_id);
CREATE INDEX idx_labeler_metrics_job_id ON labeler_metrics(job_id);
```

---

## 📦 SQLAlchemy Models

### Base Model

```python
# database/schemas/base.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

### Job Model

```python
# database/schemas/job.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    cvat_job_id = Column(Integer, unique=True, nullable=False, index=True)
    cvat_project_id = Column(Integer, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    stage = Column(String(50), nullable=False, index=True)
    config = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    qc_results = relationship("QCResult", back_populates="job", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="job", cascade="all, delete-orphan")
    labeler_metrics = relationship("LabelerMetrics", back_populates="job", cascade="all, delete-orphan")
```

### QC Result Model

```python
# database/schemas/qc_result.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class QCResult(Base):
    __tablename__ = "qc_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    frame_index = Column(Integer, nullable=False, index=True)
    annotation_id = Column(Integer, index=True)
    qc_status = Column(String(20), nullable=False, index=True)
    error_type = Column(String(100))
    error_details = Column(JSON)
    severity = Column(String(20), default="medium")
    rule_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="qc_results")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_qc_results_job_frame', 'job_id', 'frame_index'),
        Index('idx_qc_results_status_severity', 'qc_status', 'severity'),
    )
```

### Issue Model

```python
# database/schemas/issue.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    cvat_issue_id = Column(Integer, unique=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    frame_index = Column(Integer, nullable=False, index=True)
    position = Column(JSON, nullable=False)
    message = Column(String, nullable=False)
    assignee_id = Column(Integer)
    status = Column(String(50), default="open", index=True)
    severity = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="issues")
```

### Labeler Metrics Model

```python
# database/schemas/labeler_metrics.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class LabelerMetrics(Base):
    __tablename__ = "labeler_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    labeler_id = Column(Integer, nullable=False, index=True)
    labeler_name = Column(String(255))
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    total_annotations = Column(Integer, default=0)
    qc_passed = Column(Integer, default=0)
    qc_failed = Column(Integer, default=0)
    avg_qc_score = Column(Float, default=0)
    total_qc_errors = Column(Integer, default=0)
    last_activity = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="labeler_metrics")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('labeler_id', 'job_id', name='uq_labeler_job'),
    )
```

---

## 🛠️ Database Client

Centralized database access layer for all CRUD operations.

```python
# src/clients/database_client.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, desc
from datetime import datetime, timedelta

from database.schemas.job import Job
from database.schemas.qc_result import QCResult
from database.schemas.issue import Issue
from database.schemas.labeler_metrics import LabelerMetrics
from database.session import SessionLocal


class DatabaseClient:
    """Centralized database access layer for LetmeQC."""
    
    def __init__(self):
        self.SessionLocal = SessionLocal
    
    def get_db_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    # ==================== JOB OPERATIONS ====================
    
    def create_job(self, cvat_job_id: int, name: str, cvat_project_id: Optional[int] = None, 
                   status: str = "pending", stage: str = "annotation", 
                   config: Optional[Dict] = None, metadata: Optional[Dict] = None) -> Job:
        """Create a new job record."""
        db = self.get_db_session()
        try:
            job = Job(
                cvat_job_id=cvat_job_id,
                cvat_project_id=cvat_project_id,
                name=name,
                status=status,
                stage=stage,
                config=config or {},
                metadata=metadata or {}
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        finally:
            db.close()
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Get a job by internal ID."""
        db = self.get_db_session()
        try:
            return db.query(Job).filter(Job.id == job_id).first()
        finally:
            db.close()
    
    def get_job_by_cvat_id(self, cvat_job_id: int) -> Optional[Job]:
        """Get a job by CVAT job ID."""
        db = self.get_db_session()
        try:
            return db.query(Job).filter(Job.cvat_job_id == cvat_job_id).first()
        finally:
            db.close()
    
    def update_job_status(self, job_id: int, status: str, stage: Optional[str] = None) -> bool:
        """Update job status and/or stage."""
        db = self.get_db_session()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = status
                if stage:
                    job.stage = stage
                job.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def list_jobs(self, status: Optional[str] = None, stage: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> List[Job]:
        """List jobs with optional filters."""
        db = self.get_db_session()
        try:
            query = db.query(Job)
            if status:
                query = query.filter(Job.status == status)
            if stage:
                query = query.filter(Job.stage == stage)
            return query.order_by(desc(Job.created_at)).offset(offset).limit(limit).all()
        finally:
            db.close()
    
    # ==================== QC RESULT OPERATIONS ====================
    
    def create_qc_result(self, job_id: int, frame_index: int, annotation_id: Optional[int],
                         qc_status: str, error_type: Optional[str] = None,
                         error_details: Optional[Dict] = None, severity: str = "medium",
                         rule_id: Optional[int] = None) -> QCResult:
        """Create a QC result record."""
        db = self.get_db_session()
        try:
            result = QCResult(
                job_id=job_id,
                frame_index=frame_index,
                annotation_id=annotation_id,
                qc_status=qc_status,
                error_type=error_type,
                error_details=error_details,
                severity=severity,
                rule_id=rule_id
            )
            db.add(result)
            db.commit()
            db.refresh(result)
            return result
        finally:
            db.close()
    
    def get_qc_results_by_job(self, job_id: int, frame_index: Optional[int] = None,
                              qc_status: Optional[str] = None, limit: int = 1000,
                              offset: int = 0) -> List[QCResult]:
        """Get QC results for a job."""
        db = self.get_db_session()
        try:
            query = db.query(QCResult).filter(QCResult.job_id == job_id)
            if frame_index is not None:
                query = query.filter(QCResult.frame_index == frame_index)
            if qc_status:
                query = query.filter(QCResult.qc_status == qc_status)
            return query.offset(offset).limit(limit).all()
        finally:
            db.close()
    
    def count_qc_results(self, job_id: int, qc_status: Optional[str] = None) -> int:
        """Count QC results for a job."""
        db = self.get_db_session()
        try:
            query = db.query(QCResult).filter(QCResult.job_id == job_id)
            if qc_status:
                query = query.filter(QCResult.qc_status == qc_status)
            return query.count()
        finally:
            db.close()
    
    def get_qc_summary(self, job_id: int) -> Dict[str, Any]:
        """Get summary statistics for QC results of a job."""
        db = self.get_db_session()
        try:
            total = self.count_qc_results(job_id)
            passed = self.count_qc_results(job_id, 'pass')
            failed = self.count_qc_results(job_id, 'fail')
            warnings = self.count_qc_results(job_id, 'warning')
            
            # Count by error type
            error_counts = db.query(
                QCResult.error_type,
                func.count(QCResult.id).label('count')
            ).filter(
                QCResult.job_id == job_id,
                QCResult.qc_status == 'fail'
            ).group_by(QCResult.error_type).all()
            
            # Count by severity
            severity_counts = db.query(
                QCResult.severity,
                func.count(QCResult.id).label('count')
            ).filter(
                QCResult.job_id == job_id,
                QCResult.qc_status == 'fail'
            ).group_by(QCResult.severity).all()
            
            return {
                'total': total,
                'passed': passed,
                'failed': failed,
                'warnings': warnings,
                'pass_rate': (passed / total * 100) if total > 0 else 0,
                'fail_rate': (failed / total * 100) if total > 0 else 0,
                'by_error_type': {r.error_type: r.count for r in error_counts},
                'by_severity': {r.severity: r.count for r in severity_counts}
            }
        finally:
            db.close()
    
    # ==================== ISSUE OPERATIONS ====================
    
    def create_issue(self, cvat_issue_id: Optional[int], job_id: int, frame_index: int,
                    position: Dict, message: str, assignee_id: Optional[int] = None,
                    severity: str = "medium") -> Issue:
        """Create an issue record."""
        db = self.get_db_session()
        try:
            issue = Issue(
                cvat_issue_id=cvat_issue_id,
                job_id=job_id,
                frame_index=frame_index,
                position=position,
                message=message,
                assignee_id=assignee_id,
                severity=severity
            )
            db.add(issue)
            db.commit()
            db.refresh(issue)
            return issue
        finally:
            db.close()
    
    def get_issue_by_id(self, issue_id: int) -> Optional[Issue]:
        """Get an issue by ID."""
        db = self.get_db_session()
        try:
            return db.query(Issue).filter(Issue.id == issue_id).first()
        finally:
            db.close()
    
    def get_issues_by_job(self, job_id: int, status: Optional[str] = None,
                          limit: int = 100, offset: int = 0) -> List[Issue]:
        """Get issues for a job."""
        db = self.get_db_session()
        try:
            query = db.query(Issue).filter(Issue.job_id == job_id)
            if status:
                query = query.filter(Issue.status == status)
            return query.order_by(desc(Issue.created_at)).offset(offset).limit(limit).all()
        finally:
            db.close()
    
    def count_issues(self, job_id: int, status: Optional[str] = None) -> int:
        """Count issues for a job."""
        db = self.get_db_session()
        try:
            query = db.query(Issue).filter(Issue.job_id == job_id)
            if status:
                query = query.filter(Issue.status == status)
            return query.count()
        finally:
            db.close()
    
    def update_issue_status(self, issue_id: int, status: str) -> bool:
        """Update issue status."""
        db = self.get_db_session()
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            if issue:
                issue.status = status
                if status == 'resolved':
                    issue.resolved_at = datetime.utcnow()
                issue.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    # ==================== LABELER METRICS OPERATIONS ====================
    
    def create_or_update_labeler_metrics(self, labeler_id: int, labeler_name: str,
                                         job_id: int, total_annotations: int,
                                         qc_passed: int, qc_failed: int,
                                         total_qc_errors: int) -> LabelerMetrics:
        """Create or update labeler metrics for a job."""
        db = self.get_db_session()
        try:
            metrics = db.query(LabelerMetrics).filter(
                LabelerMetrics.labeler_id == labeler_id,
                LabelerMetrics.job_id == job_id
            ).first()
            
            avg_score = (qc_passed / total_annotations * 100) if total_annotations > 0 else 0
            
            if metrics:
                metrics.labeler_name = labeler_name
                metrics.total_annotations = total_annotations
                metrics.qc_passed = qc_passed
                metrics.qc_failed = qc_failed
                metrics.avg_qc_score = avg_score
                metrics.total_qc_errors = total_qc_errors
                metrics.updated_at = datetime.utcnow()
            else:
                metrics = LabelerMetrics(
                    labeler_id=labeler_id,
                    labeler_name=labeler_name,
                    job_id=job_id,
                    total_annotations=total_annotations,
                    qc_passed=qc_passed,
                    qc_failed=qc_failed,
                    avg_qc_score=avg_score,
                    total_qc_errors=total_qc_errors
                )
                db.add(metrics)
            
            db.commit()
            db.refresh(metrics)
            return metrics
        finally:
            db.close()
    
    def get_labeler_metrics(self, job_id: Optional[int] = None, labeler_id: Optional[int] = None,
                             limit: int = 50) -> List[LabelerMetrics]:
        """Get labeler metrics with optional filters."""
        db = self.get_db_session()
        try:
            query = db.query(LabelerMetrics)
            if job_id:
                query = query.filter(LabelerMetrics.job_id == job_id)
            if labeler_id:
                query = query.filter(LabelerMetrics.labeler_id == labeler_id)
            return query.order_by(desc(LabelerMetrics.avg_qc_score)).limit(limit).all()
        finally:
            db.close()
    
    # ==================== STATISTICS & REPORTS ====================
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get overall job statistics."""
        db = self.get_db_session()
        try:
            total_jobs = db.query(Job).count()
            
            jobs_by_status = db.query(
                Job.status,
                func.count(Job.id).label('count')
            ).group_by(Job.status).all()
            
            jobs_by_stage = db.query(
                Job.stage,
                func.count(Job.id).label('count')
            ).group_by(Job.stage).all()
            
            total_annotations = db.query(func.sum(QCResult.id)).scalar() or 0
            total_errors = db.query(QCResult).filter(QCResult.qc_status == 'fail').count()
            
            return {
                'total_jobs': total_jobs,
                'by_status': {r.status: r.count for r in jobs_by_status},
                'by_stage': {r.stage: r.count for r in jobs_by_stage},
                'total_annotations': total_annotations,
                'total_errors': total_errors
            }
        finally:
            db.close()
    
    def get_daily_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily QC trends for the last N days."""
        db = self.get_db_session()
        try:
            date_filter = datetime.utcnow() - timedelta(days=days)
            
            daily_stats = db.query(
                func.date_trunc('day', Job.created_at).label('date'),
                func.count(Job.id).label('jobs_created'),
                func.count(distinct(Job.cvat_job_id)).label('unique_jobs')
            ).filter(Job.created_at >= date_filter).group_by('date').all()
            
            return [
                {
                    'date': r.date.strftime('%Y-%m-%d'),
                    'jobs_created': r.jobs_created,
                    'unique_jobs': r.unique_jobs
                }
                for r in daily_stats
            ]
        finally:
            db.close()
```

---

## 🧪 Unit Tests

```python
# tests/unit/test_database_client.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.schemas.base import Base
from database.schemas.job import Job
from database.schemas.qc_result import QCResult
from database.schemas.issue import Issue
from database.schemas.labeler_metrics import LabelerMetrics
from src.clients.database_client import DatabaseClient


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override SessionLocal
    original = DatabaseClient.SessionLocal
    DatabaseClient.SessionLocal = lambda: SessionLocal()
    
    yield
    
    DatabaseClient.SessionLocal = original
    Base.metadata.drop_all(bind=engine)


def test_create_job(test_db):
    db_client = DatabaseClient()
    job = db_client.create_job(
        cvat_job_id=123,
        name="Test Job",
        status="pending",
        stage="annotation"
    )
    assert job is not None
    assert job.cvat_job_id == 123
    assert job.name == "Test Job"


def test_get_job_by_cvat_id(test_db):
    db_client = DatabaseClient()
    job = db_client.create_job(cvat_job_id=456, name="Test Job 2")
    retrieved = db_client.get_job_by_cvat_id(456)
    assert retrieved is not None
    assert retrieved.id == job.id


def test_create_qc_result(test_db):
    db_client = DatabaseClient()
    job = db_client.create_job(cvat_job_id=789, name="QC Test Job")
    result = db_client.create_qc_result(
        job_id=job.id,
        frame_index=0,
        annotation_id=1,
        qc_status="pass",
        severity="low"
    )
    assert result is not None
    assert result.job_id == job.id
    assert result.qc_status == "pass"


def test_get_qc_summary(test_db):
    db_client = DatabaseClient()
    job = db_client.create_job(cvat_job_id=101, name="Summary Test")
    
    db_client.create_qc_result(job_id=job.id, frame_index=0, annotation_id=1, qc_status="pass")
    db_client.create_qc_result(job_id=job.id, frame_index=0, annotation_id=2, qc_status="fail",
                                error_type="bbox_min_area", severity="high")
    db_client.create_qc_result(job_id=job.id, frame_index=1, annotation_id=3, qc_status="pass")
    
    summary = db_client.get_qc_summary(job.id)
    assert summary['total'] == 3
    assert summary['passed'] == 2
    assert summary['failed'] == 1
    assert summary['by_error_type']['bbox_min_area'] == 1


def test_create_issue(test_db):
    db_client = DatabaseClient()
    job = db_client.create_job(cvat_job_id=201, name="Issue Test")
    issue = db_client.create_issue(
        cvat_issue_id=1,
        job_id=job.id,
        frame_index=0,
        position={"x": 10, "y": 20, "width": 100, "height": 100},
        message="Test issue",
        severity="high"
    )
    assert issue is not None
    assert issue.job_id == job.id
    assert issue.message == "Test issue"
```

---

## 📊 Alembic Migrations Setup

### Install Alembic
```bash
pip install alembic
alembic init database
```

### Configure alembic.ini
```ini
[alembic]
script_location = database/migrations
sqlalchemy.url = postgresql://letmeqc:letmeqc@localhost:5432/letmeqc_dev

[post_write_hooks]
[post_write_hooks.lint]
hooks = black,ruff
black_options = --line-length=100
ruff_options = --fix --line-length=100
```

### Configure env.py
```python
# database/migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import your Base and models
from database.schemas.base import Base
from database.schemas.job import Job
from database.schemas.qc_result import QCResult
from database.schemas.issue import Issue
from database.schemas.labeler_metrics import LabelerMetrics

# This is the Alembic Config object
config = context.config

# Add your model's MetaData object here
target_metadata = Base.metadata

# Other values from the config
config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=[],
        dialect_opts={{"paramstyle": "named"}},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {{}}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Create Initial Migration
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## ✅ Acceptance Criteria

Phase 1 Database Layer is **complete** when:

1. ✅ All tables are designed and documented
2. ✅ SQLAlchemy models are implemented for all tables
3. ✅ Alembic migrations are set up and tested
4. ✅ database_client.py provides all required CRUD operations
5. ✅ Unit tests pass with > 80% coverage
6. ✅ Database can be initialized and used locally

---

## 🔗 Related Documents

- [Phase 1 Overview](./phase-01-overview.md)
- [Phase 1 - API Layer](./phase-01-api.md)
- [Phase 1 - Services](./phase-01-services.md)
- [Phase 1 - Docker Setup](./phase-01-docker.md)
- [Main Development Plan](../README.md)
