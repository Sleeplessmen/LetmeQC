# Phase 1: Core Architecture Enhancements - Overview

## 📌 Summary

**Duration:** 3 weeks  
**Start Date:** 2026-10-15  
**End Date:** 2026-11-05  
**Status:** ⏳ Planned  
**Priority:** 🔴 HIGH

---

## 🎯 Objectives

Phase 1 builds the **foundational architecture** for the full LetmeQC tool:

1. **Database Layer** - Store QC results, job metadata, issues, and labeler metrics
2. **Enhanced API Layer** - New endpoints for job management, QC results, and reports
3. **Service Layer** - Job service, issue service, enhanced QC service
4. **Docker Setup** - Multi-container development environment

---

## 🏗️ Architecture Changes

### Before Phase 1
```
LetmeQC/
├── src/
│   ├── app/           # FastAPI routes
│   ├── clients/       # CVAT API client
│   ├── handlers/      # Webhook handlers
│   ├── services/      # QC & Report services
│   ├── config/        # Settings
│   ├── models/        # Data models
│   ├── utils/         # Utilities
│   └── rules/         # QC Rules
└── tests/
```

### After Phase 1
```
LetmeQC/
├── src/
│   ├── app/
│   ├── clients/
│   │   ├── cvat_client.py        # Existing
│   │   └── database_client.py    # NEW
│   ├── handlers/
│   │   ├── webhook_handlers.py   # Existing
│   │   └── api_handlers.py       # NEW
│   ├── services/
│   │   ├── qc_service.py         # Enhanced
│   │   ├── report_service.py     # Enhanced
│   │   ├── job_service.py        # NEW
│   │   └── issue_service.py      # NEW
│   ├── models/
│   │   ├── enums.py              # NEW
│   │   ├── frame.py              # Existing
│   │   ├── report.py             # Existing
│   │   ├── job.py                # NEW
│   │   ├── issue.py              # NEW
│   │   ├── qc_result.py          # NEW
│   │   └── labeler_metrics.py    # NEW
│   └── config/
│
├── database/             # NEW
│   ├── schemas/
│   │   ├── job.py
│   │   ├── qc_result.py
│   │   ├── issue.py
│   │   └── labeler_metrics.py
│   ├── session.py               # NEW
│   ├── repositories/
│   └── migrations/
│
└── docker-compose.dev.yml    # NEW
```

---

## 📋 Key Components

### 1. Database Layer
- **Tables:** jobs, qc_results, issues, labeler_metrics
- **ORM:** SQLAlchemy with Alembic migrations
- **Client:** Centralized database_client.py
- **See:** [phase-01-database.md](./phase-01-database.md)

### 2. API Layer
- **Endpoints:** /api/v1/jobs, /api/v1/qc-results, /api/v1/issues, /api/v1/reports
- **Models:** Pydantic models for all entities
- **See:** [phase-01-api.md](./phase-01-api.md)

### 3. Service Layer
- **Job Service:** Job lifecycle management
- **Issue Service:** Issue creation and management
- **QC Service:** Enhanced with database integration
- **Report Service:** Comprehensive metrics and reporting
- **See:** [phase-01-services.md](./phase-01-services.md)

### 4. Docker Setup
- **Backend:** FastAPI container
- **Database:** PostgreSQL container
- **Tools:** pgAdmin for database management
- **See:** [phase-01-docker.md](./phase-01-docker.md)

---

## 📅 Timeline

| Week | Focus Area | Tasks |
|------|------------|-------|
| Week 1 | Database & Models | DB design, SQLAlchemy models, migrations |
| Week 2 | API Layer | Endpoint implementation, Pydantic models |
| Week 3 | Services & Docker | Service layer, Docker setup, testing |

---

## ✅ Deliverables

| Deliverable | Description | Status |
|-------------|-------------|--------|
| Database Schema | Complete database design | ⏳ |
| SQLAlchemy Models | All database models | ⏳ |
| Alembic Migrations | Migration scripts | ⏳ |
| database_client.py | Centralized DB access | ⏳ |
| API Endpoints | Jobs, QC Results, Issues, Reports | ⏳ |
| Service Layer | Job, Issue, QC, Report services | ⏳ |
| Docker Setup | Multi-container dev environment | ⏳ |
| Unit Tests | Database, services, APIs | ⏳ |
| Integration Tests | API endpoints | ⏳ |
| Documentation | Updated docs | ⏳ |

---

## ✅ Acceptance Criteria

Phase 1 is **complete** when:

1. ✅ Database set up with all required tables
2. ✅ All SQLAlchemy models implemented and tested
3. ✅ database_client.py provides all CRUD operations
4. ✅ API endpoints working (Jobs, QC Results, Issues, Reports)
5. ✅ Service layer implemented (Job, Issue, QC, Report)
6. ✅ Docker multi-container setup works locally
7. ✅ Unit tests pass with > 80% coverage
8. ✅ Integration tests pass
9. ✅ Documentation updated

---

## 🔗 Related Documents

- [Main Development Plan](../README.md)
- [Phase 1 - Database Layer](./phase-01-database.md)
- [Phase 1 - API Layer](./phase-01-api.md)
- [Phase 1 - Services](./phase-01-services.md)
- [Phase 1 - Docker Setup](./phase-01-docker.md)
- [Phase 2: CVAT Integration](../phase-02-cvat-integration.md)

---

## 📝 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-15 | Senior Annotation Tool Engineer | Initial version |
