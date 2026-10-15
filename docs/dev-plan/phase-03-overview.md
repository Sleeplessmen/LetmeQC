# Phase 3: Dashboard UI Development - Overview

## 📌 Summary

**Duration:** 5 weeks  
**Start Date:** 2026-12-03  
**End Date:** 2026-01-07  
**Status:** ⏳ Planned  
**Priority:** 🔴 HIGH

---

## 🎯 Objectives

Build a **complete dashboard UI** for:
- Viewing QC metrics and reports
- Managing jobs and issues
- Analyzing labeler performance
- Configuring rule sets
- Deep linking to CVAT

---

## 🏗️ UI Architecture

### Tech Stack

| Component | Technology | Version | Reason |
|-----------|------------|---------|--------|
| Framework | React | 18+ | Modern, popular |
| Language | TypeScript | Latest | Type safety |
| UI Library | Ant Design | 5.x | Enterprise-ready |
| State Management | Redux Toolkit + RTK Query | Latest | Best practice |
| Charts | Recharts | Latest | Flexible, good docs |
| Routing | React Router | 6+ | Standard |
| HTTP Client | Axios | Latest | Interceptors, error handling |
| Styling | CSS Modules / SCSS | Latest | Maintainable |
| Bundler | Vite | Latest | Fast builds |

### Directory Structure

```
frontend/
├── public/                  # Static assets
├── src/
│   ├── components/         # Reusable components
│   │   ├── Layout/
│   │   ├── Dashboard/
│   │   ├── Jobs/
│   │   ├── Reports/
│   │   ├── Labelers/
│   │   ├── Issues/
│   │   ├── Rules/
│   │   └── Common/
│   │
│   ├── pages/              # Route-based pages
│   │   ├── DashboardPage.tsx
│   │   ├── JobsPage.tsx
│   │   ├── ReportsPage.tsx
│   │   ├── LabelersPage.tsx
│   │   ├── IssuesPage.tsx
│   │   └── RulesPage.tsx
│   │
│   ├── services/           # API service layer
│   ├── hooks/              # Custom hooks
│   ├── utils/              # Utilities
│   ├── styles/             # CSS/SCSS
│   ├── types/              # TypeScript types
│   ├── store/              # Redux store (optional)
│   ├── App.tsx
│   └── main.tsx
│
├── package.json
├── vite.config.ts
├── tsconfig.json
└── .env
```

---

## 🎨 UI Design

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LETMEQC Dashboard                     [User] [Settings] [Logout]        │
├─────────────────────┬──────────────────────────────────────────────────┤
│                     │                                                      │
│  SIDEBAR             │  MAIN CONTENT                                        │
│  ───────             │  ────────────                                        │
│                     │                                                      │
│  📊 Dashboard        │  ┌──────────────┬──────────────┬──────────────┐ │
│  📋 Jobs             │  │ Total Jobs    │ QC Pass Rate │ QC Fail Rate │ │
│  📄 Reports          │  │ 1,250        │ 85%         │ 15%         │ │
│  👥 Labelers         │  └──────────────┴──────────────┴──────────────┘ │
│  ⚠️ Issues           │                                                      │
│  ⚙️ Rule Engine      │  Error Type Distribution (Bar Chart)               │
│                     │  ┌─────────────────────────────────────────────┐  │
│  🔗 CVAT Link        │  │ [Bounding Box] [Polygon] [Label] [Duplicate]  │  │
│                     │  │     ████████     ████           ██            │  │
│                     │  └─────────────────────────────────────────────┘  │
│                     │                                                      │
│                     │  Daily QC Trend (Bar Chart)                       │
│                     │  ┌─────────────────────────────────────────────┐  │
│                     │  │  100 │                    ██                    │  │
│                     │  │  80  │        ██          ██████               │  │
│                     │  │  60  │    ██  ██          ██                  │  │
│                     │  │  40  │    ██  ██                                      │  │
│                     │  │  20  │    ██  ██                                      │  │
│                     │  │   0  └──────────────────────────────────────│  │
│                     │  │      Mon   Tue   Wed   Thu   Fri   Sat   Sun │  │
│                     │  └─────────────────────────────────────────────┘  │
│                     │                                                      │
│                     │  Labeler Performance (Table)                      │
│                     │  ┌─────────────────────────────────────────────┐  │
│                     │  │ #  │ Labeler │ Jobs │ Pass Rate │ Avg Score   │  │
│                     │  │ 1  │ User A  │ 50   │ 95%       │ 9.2        │  │
│                     │  │ 2  │ User B  │ 45   │ 88%       │ 8.7        │  │
│                     │  └─────────────────────────────────────────────┘  │
│                     │                                                      │
└─────────────────────┴──────────────────────────────────────────────────┘
```

---

## 📅 Timeline

| Week | Focus Area | Tasks |
|------|------------|-------|
| Week 1 | Project Setup & Layout | React project, sidebar, header, footer |
| Week 2 | Dashboard Components | Summary cards, error chart, trend chart, labeler table |
| Week 3 | API Services & Hooks | API services, custom hooks, types |
| Week 4 | Jobs & Reports Pages | Job list, job detail, reports |
| Week 5 | Final Pages & Styling | Issues, rules, responsive design, styling |

---

## 📋 Key Components

### 1. Setup
- React + TypeScript + Vite project initialization
- Configuration files (vite.config.ts, tsconfig.json)
- Package.json with all dependencies

### 2. Layout
- Sidebar with navigation
- Header with user info and notifications
- Footer with version info
- Responsive design

### 3. Dashboard
- Summary cards (total jobs, pass rate, fail rate, etc.)
- Error type distribution chart
- Daily QC trends chart
- Labeler performance table
- Real-time updates

### 4. Jobs
- Job list with filtering and pagination
- Job detail view
- Deep linking to CVAT

### 5. Reports
- Report list
- Report detail view
- Export functionality

### 6. Labelers
- Labeler list
- Performance metrics
- Leaderboard

### 7. Issues
- Issue list
- Issue detail
- Filtering

### 8. Rules
- Rule set list
- Rule editor
- Rule set management

### 9. API Layer
- Axios configuration
- Service files for all API endpoints
- Custom hooks using React Query

### 10. Styling
- Global styles
- Component styles
- Responsive design
- Theme variables

---

## ✅ Deliverables

| Deliverable | Description | Status |
|-------------|-------------|--------|
| React Project | Full project setup with Vite | ⏳ |
| Layout Components | Sidebar, header, footer | ⏳ |
| Dashboard Components | All charts, cards, tables | ⏳ |
| API Services | Axios, all API service files | ⏳ |
| Custom Hooks | React Query hooks | ⏳ |
| Type Definitions | All TypeScript types | ⏳ |
| All Pages | Dashboard, jobs, reports, labelers, issues, rules | ⏳ |
| Styling | Global and component styles | ⏳ |
| Responsive Design | Mobile/tablet support | ⏳ |
| Unit Tests | Component and hook tests | ⏳ |

---

## ✅ Acceptance Criteria

Phase 3 is **complete** when:

1. ✅ React + TypeScript project set up and working
2. ✅ Layout (sidebar, header, footer) implemented
3. ✅ Dashboard with all charts and tables working
4. ✅ Job list with filtering and pagination
5. ✅ Job detail view with deep linking to CVAT
6. ✅ API services layer implemented
7. ✅ Custom hooks implemented
8. ✅ TypeScript types defined
9. ✅ All pages (dashboard, jobs, reports, labelers, issues, rules) working
10. ✅ Styling applied and responsive
11. ✅ Unit tests pass with > 80% coverage

---

## 🔗 Related Documents

- [Phase 3 - Setup & Configuration](./phase-03-setup.md)
- [Phase 3 - Layout Components](./phase-03-layout.md)
- [Phase 3 - Dashboard Components](./phase-03-dashboard.md)
- [Phase 3 - Jobs Page](./phase-03-jobs.md)
- [Phase 3 - API Services & Hooks](./phase-03-services.md)
- [Phase 3 - Styling](./phase-03-styles.md)
- [Phase 1: Core Architecture](../phase-01-overview.md)
- [Phase 2: CVAT Integration & Workflow Automation](../phase-02-cvat-integration.md)
- [Phase 4: Custom Rule Engine & Guideline Integration](../phase-04-rule-engine.md)
- [Phase 5: Testing, Optimization & Deployment](../phase-05-testing-deployment.md)
- [Main Development Plan](../README.md)

---

## 📝 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-15 | Senior Annotation Tool Engineer | Initial version |
