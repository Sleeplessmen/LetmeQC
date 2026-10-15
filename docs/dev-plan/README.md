# LetmeQC - Development Plan

## 📋 Overview

This folder contains the detailed development plan for transforming **LetmeQC from a background web service (webhook pure API) into a complete QC tool with dashboard UI**, featuring:

- Dual-system integration with CVAT (API + Webhook)
- Automated QC workflow
- Custom rule engine with guideline integration
- Comprehensive dashboard with metrics and reporting
- Deep linking to CVAT UI

---

## 🎯 Objectives

### Current State
- ✅ Backend: FastAPI modular architecture
- ✅ CVAT Integration: Webhook API + CVAT Client
- ✅ QC Engine: Rule-based validation
- ✅ Reporting: Report generation service

### Target State
- 🎯 **Full QC Tool**: Web service + Dashboard UI
- 🎯 **Dual-System Integration**: Parallel integration via API & Webhook with CVAT
- 🎯 **Automated Workflow**: Auto QC → Create issues → Update status
- 🎯 **Custom Rule Engine**: Guideline integration with custom rule sets
- 🎯 **Deep Linking**: Dashboard → CVAT UI (correct frame & issue)

---

## 📁 File Structure

```
docs/dev-plan/
├── README.md                  # This file - Overview
├── phase-01-overview.md       # Phase 1: Architecture Overview
├── phase-01-database.md       # Phase 1: Database Layer Design
├── phase-01-api.md            # Phase 1: API Endpoints & Models
├── phase-01-services.md       # Phase 1: Service Layer Implementation
├── phase-01-docker.md         # Phase 1: Docker & Development Setup
├── phase-02-cvat-integration.md    # Phase 2: CVAT Integration & Workflow Automation
├── phase-03-overview.md       # Phase 3: Dashboard UI Overview
├── phase-04-rule-engine.md    # Phase 4: Custom Rule Engine & Guideline Integration
└── phase-05-testing-deployment.md  # Phase 5: Testing, Optimization & Deployment
```

---

## 📅 Timeline & Milestones

| Phase | Duration | Start Date | End Date | Status |
|-------|----------|------------|----------|--------|
| Phase 1: Core Architecture | 3 weeks | 2026-10-15 | 2026-11-05 | ⏳ Planned |
| Phase 2: CVAT Integration | 4 weeks | 2026-11-05 | 2026-12-03 | ⏳ Planned |
| Phase 3: Dashboard UI | 5 weeks | 2026-12-03 | 2026-01-07 | ⏳ Planned |
| Phase 4: Rule Engine | 3 weeks | 2026-01-07 | 2026-01-28 | ⏳ Planned |
| Phase 5: Testing & Deployment | 3 weeks | 2026-01-28 | 2026-02-18 | ⏳ Planned |

**Total Estimated Duration: ~18 weeks (4.5 months)**

---

## 🏗️ Target Architecture

```
LetmeQC (Full Tool)
├── Backend (FastAPI - Existing + Enhanced)
│   ├── src/
│   │   ├── app/              # FastAPI routes & dependencies
│   │   ├── clients/          # CVAT API + Internal DB client
│   │   │   ├── cvat_client.py
│   │   │   └── database_client.py (NEW)
│   │   ├── handlers/         # Webhook + API handlers
│   │   ├── services/         # Core business logic
│   │   │   ├── qc_service.py
│   │   │   ├── report_service.py
│   │   │   ├── job_service.py (NEW)
│   │   │   └── issue_service.py (NEW)
│   │   ├── models/           # Data models
│   │   │   ├── frame.py
│   │   │   ├── report.py
│   │   │   ├── job.py (NEW)
│   │   │   ├── issue.py (NEW)
│   │   │   └── rule.py (NEW)
│   │   ├── config/           # Settings
│   │   ├── utils/            # Utilities
│   │   └── rules/            # QC Rules (CUSTOMIZABLE)
│   │       ├── default_rules.py
│   │       ├── custom_rules/ (NEW)
│   │       └── rule_engine.py (NEW)
│   │
│   └── database/ (NEW)      # Database layer
│       ├── schemas/
│       ├── repositories/
│       └── migrations/
│
├── Frontend (NEW - Dashboard UI)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── utils/
│   │   └── styles/
│   └── package.json
│
├── Integration Layer (NEW)
│   ├── cvat_webhook/
│   ├── letmeqc_api/
│   └── deep_linking/
│
└── DevOps (Enhanced)
    ├── docker/
    ├── k8s/
    └── ci_cd/
```

---

## 🔄 Dual-System Integration Model

### Integration Points

| Direction | Component | Method | Purpose | Frequency |
|------------|-----------|--------|---------|------------|
| CVAT → LetmeQC | CVAT Webhook | POST `/webhook/cvat` | Trigger QC when job status changes | Event-driven |
| LetmeQC → CVAT | CVAT API Client | `create_issue()` | Create QC issue on CVAT | On-demand |
| LetmeQC → CVAT | CVAT API Client | `update_job_status()` | Update job status/stage | On-demand |
| Dashboard → LetmeQC | Internal API | GET `/api/reports` | Fetch QC reports | On-demand |
| Dashboard → CVAT | Deep Link | URL redirect | Open CVAT UI at correct frame & issue | On-click |
| LetmeQC → DB | Database Client | CRUD operations | Store QC results, metrics | Continuous |

---

## 👥 Team Structure

| Role | Responsibilities | Team Size | Skills Required |
|------|------------------|-----------|------------------|
| Backend Lead | Architecture, API design, Database, Rule Engine | 1-2 | Python, FastAPI, SQL, Rule Engine Design |
| Frontend Lead | UI/UX design, React development, State management | 1-2 | React, TypeScript, Ant Design, Charting libraries |
| Integration Specialist | CVAT integration, Webhook handling, Deep linking | 1 | CVAT API, Webhook patterns, URL structure |
| DevOps Engineer | Docker, CI/CD, Monitoring, Deployment | 1 | Docker, Kubernetes, CI/CD, Monitoring tools |
| QA Engineer | Testing strategy, Test implementation, Bug tracking | 1 | pytest, Jest, Cypress, Testing methodologies |
| Technical Writer | Documentation, User guides | 1 | Markdown, Documentation tools |

**Recommended Team: 5-7 members**

---

## 📊 Success Criteria & KPIs

### Technical KPIs
| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (avg) | < 200ms | Prometheus |
| QC Processing Time (1000 frames) | < 5 minutes | Benchmark |
| Database Query Time (avg) | < 50ms | Prometheus |
| Frontend Load Time | < 2s | Lighthouse |
| Uptime | > 99.9% | Monitoring |
| Test Coverage | > 80% | pytest-cov, Jest |

### Business KPIs
| Metric | Target | Measurement |
|--------|--------|-------------|
| QC Accuracy | > 95% | Manual audit |
| False Positive Rate | < 5% | Manual audit |
| Annotator Productivity | +20% | Time per job |
| Reviewer Efficiency | +30% | Time to review |

---

## 🚀 Quick Start

### For Project Manager
1. Review this development plan
2. Assign team members to each role
3. Setup project management (Jira, GitHub Projects, etc.)
4. Create repository branches for each phase

### For Development Team
1. **Week 1-3 (Phase 1):** Start with database design & implementation
2. **Week 4-7 (Phase 2):** Focus on CVAT integration
3. **Week 8-12 (Phase 3):** Develop dashboard UI
4. **Week 13-15 (Phase 4):** Implement rule engine
5. **Week 16-18 (Phase 5):** Testing, optimization, deployment

---

## 📚 References

- [CVAT Documentation](https://docs.cvat.ai/)
- [CVAT API Reference](https://docs.cvat.ai/en/latest/api/)
- [CVAT Webhook Documentation](https://docs.cvat.ai/en/latest/advanced/webhooks/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Redux Toolkit Documentation](https://redux-toolkit.js.org/)

---

## 📝 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-15 | Senior Annotation Tool Engineer | Initial development plan |

---

## 💬 Contact & Support

For questions or clarifications about this development plan:
- Open an issue in the GitHub repository
- Contact the project lead
- Refer to individual phase documents for detailed information
