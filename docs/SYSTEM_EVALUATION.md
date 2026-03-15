# Luthiers-Toolbox — System Evaluation

> **Date:** February 2026  
> **Scope:** Full-stack audit of architecture, UX, testing, observability, operational risks, and edge cases.  
> **Verdict:** The backend engineering is strong — boundary enforcement, test isolation, remediation discipline are real. The frontend is structurally broken in multiple places. Operational readiness for anything beyond single-instance dev use is not there.

---

## Table of Contents

1. [Architecture & Data Flow](#1-architecture--data-flow)
2. [Backend Assessment](#2-backend-assessment)
3. [Frontend & UX Assessment](#3-frontend--ux-assessment)
4. [Testing & Coverage](#4-testing--coverage)
5. [Observability](#5-observability)
6. [Operational Risks](#6-operational-risks)
7. [Security](#7-security)
8. [CNC Safety-Critical Path](#8-cnc-safety-critical-path)
9. [Edge Cases in Core Logic](#9-edge-cases-in-core-logic)
10. [Dashboard Evaluation](#10-dashboard-evaluation)
11. [UX Component Evaluation](#11-ux-component-evaluation)
12. [Ranked Recommendations](#12-ranked-recommendations)
13. [Re-Review Checklist](#13-re-review-checklist)

---

## 1. Architecture & Data Flow

### Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Vue 3, Pinia (29 stores), Vite | `<script setup lang="ts">`, custom CSS design tokens |
| Backend | FastAPI, Python 3.11+ | 88 router mounts (85 from manifest + 3 direct), ~262 active routes |
| Storage | SQLite (WAL mode) + file-system JSON | Dual strategy — structured data in SQLite, RMOS runs as date-partitioned JSON files |
| Deployment | Docker Compose (dev + prod), Nginx reverse proxy | Railway for hosting |
| CI | GitHub Actions, 54 workflow files | 7-step boundary fence, 17+ specialized gates |

### Data Flow

```
Vue SPA → SDK layer (4 namespaces: cam, rmos, operations, art)
       → FastAPI (88 routers, 5 middleware layers)
       → CAM pipeline / RMOS orchestration / Saw Lab
       → JSON artifacts, DXF files, or G-code output
```

### Key Subsystems

| Subsystem | Purpose | Location |
|-----------|---------|----------|
| **RMOS** | Manufacturing run orchestration. SPEC → PLAN → DECISION → EXECUTE → EXPORT → FEEDBACK lifecycle. SHA256 audit chain. | `app/rmos/` |
| **CAM** | Toolpath generation — adaptive, helical, trochoidal, polygon offset, biarc. DXF input → algorithm → post-processing → G-code. | `app/cam/` |
| **Saw Lab** | Reference-governed operations with feasibility gates. | `app/saw_lab/` |
| **Art Studio** | SVG/headstock design. Separate SQLite database. | `app/art_studio/` |
| **Data Registry** | 472-species wood database, machine profiles, tool libraries. | `app/data_registry/` |

### Boundary Enforcement

8 profiles in `FENCE_REGISTRY.json`, CI-enforced via `check_boundary_imports`:

1. External boundary (ToolBox ↔ Analyzer)
2. RMOS ↔ CAM domain isolation
3. Operation lane compliance (OPERATION vs UTILITY)
4. AI sandbox boundaries (3 scripts: imports, forbidden calls, write paths)
5. Artifact authority — no direct `RunArtifact()` construction
6. CAM Intent schema hash validation
7. Legacy usage budget (≤10 legacy paths in frontend)
8. Deprecation sunset guard

**This is genuinely well-engineered.** Most codebases this size have zero boundary enforcement. This one has 8 profiles, pre-commit hooks, and CI gates. The discipline is real.

### What's Missing

- No service mesh or message queue for async work
- No distributed locking — all concurrency protection is process-local `threading.Lock()`
- No cache layer (Redis/Memcached) between API and storage
- No background task queue for long-running CAM operations

---

## 2. Backend Assessment

### Strengths

| Area | Evidence |
|------|----------|
| **Remediation discipline** | Scored 4.7/10, actively fixing: bare `except:` → 0 (was 97), routes 262 (was 1,060), god objects → 0 (was 30+) |
| **Test isolation** | 659-line `conftest.py` with autouse fixtures, per-test `tmp_path` + `monkeypatch.setenv()`, singleton resets, mandatory `X-Request-Id` enforcement |
| **Router decomposition** | Phase 9 decomposed `main.py` from ~500 lines to ~250. RouterSpec manifest manages 85 entries. Try/except loading for graceful degradation. |
| **DXF validation** | File size limits, entity count limits, operation timeouts, self-intersection detection, zero-area polygon rejection |
| **Atomic file writes** | RMOS store uses temp file + `os.replace()` — correct pattern for crash safety |

### Weaknesses

| Area | Issue | Severity |
|------|-------|----------|
| **Singleton stores** | Module-level `_store = None` globals in constraint_profiles, learned_overrides, advisory store, RMOS deps. Each process gets its own copy. Multi-instance deployment breaks everything. | 🔴 CRITICAL |
| **Try/except router loading** | 85 routers load in try/except blocks. If a router fails to import, the system continues silently with missing endpoints. No alarm, no health check degradation signal. | 🟠 HIGH |
| **Broad exception handling** | Bare `except:` is down to 0, but 1,622 `except Exception` blocks remain. In safety paths (cam/, rmos/, saw_lab/), the instruction says fail-closed with `raise`, but broad catches still swallow specifics. | 🟠 HIGH |
| **No retry logic** | Zero retry mechanisms in any critical path. Single transient I/O failure (disk full, network blip) crashes the operation permanently. | 🟡 MEDIUM |
| **Orphaned artifacts** | No cleanup mechanism for failed run artifacts, temporary upload files, or corrupt JSON index entries. Disk grows unbounded. | 🟡 MEDIUM |

---

## 3. Frontend & UX Assessment

### Strengths

| Area | Evidence |
|------|----------|
| **Design token system** | `styles/design-tokens.css` with CSS custom properties for colors, spacing, typography, breakpoints |
| **SDK layer** | 4 namespaces (`cam`, `rmos`, `operations`, `art`), typed endpoints, `X-Request-Id` injection |
| **Undo/redo** | Present in `useRosetteGeometryStore.ts` and `useGeometryStore.ts` via history arrays + push/pop |
| **Composable quality** | `useAsyncAction`, `useFetchTransform`, `useCompareState`, `useFormState` — solid patterns |

### Broken Things

| Issue | Detail | Severity |
|-------|--------|----------|
| **Tailwind classes used without Tailwind installed** | 10+ components use `class="flex items-center gap-2"` etc., but Tailwind is NOT in `package.json`, NOT in `vite.config.ts`, NOT in `postcss.config.js`. These classes do nothing. Styles are visually broken in production. | 🔴 CRITICAL |
| **Duplicate toast systems** | Both `ToastNotification.vue` (custom) and `vue-toastification` (library) coexist. Some stores import one, some import the other. User sees inconsistent notification styling. | 🟠 HIGH |
| **`window.confirm()` everywhere** | 10+ places use native `window.confirm()` despite `SmallModal.vue` existing. Inconsistent UX: some destructive actions get a styled modal, others get a browser alert box. | 🟠 HIGH |
| **SDK bypass** | Multiple stores call `api()` or `apiFetch()` directly instead of going through the SDK namespace layer. Breaks the abstraction the SDK was built to enforce. | 🟠 HIGH |
| **No global error boundary** | No `onErrorCaptured` root handler, no `app.config.errorHandler`. Unhandled promise rejections and component errors crash silently or show a white screen. | 🟠 HIGH |
| **No auth guards on most routes** | `router/index.ts` has ~75 routes. Auth guard checking appears on a handful of admin routes. Most routes are unprotected even when they should require login. | 🟠 HIGH |
| **No empty state components** | Views that load data show nothing when data is absent — no "no results" illustration, no "get started" prompt. User sees a blank screen and doesn't know if it's loading, empty, or broken. | 🟡 MEDIUM |
| **Inconsistent store patterns** | Some stores use composition API (setup stores), some use options API. Some use `defineStore('name', () => {})`, others use `defineStore('name', { state, actions })`. No enforced convention. | 🟡 MEDIUM |

### UX Gaps

| Feature | Status |
|---------|--------|
| **Tooltips / mouseover guidance** | Absent. No tooltip component, no hover hints. New users get zero contextual help. |
| **Keyboard shortcuts** | None outside the `CommandPalette.vue` (Ctrl+K). No keyboard navigation for CAM operations, no shortcuts for common actions. |
| **Loading states** | Inconsistent. Some views use `v-if="loading"` with a spinner, many don't. No skeleton loaders. |
| **Responsive design** | Design tokens define breakpoints, but no systematic responsive testing. Many views use fixed-width layouts. |
| **Accessibility** | No ARIA labels found on interactive elements, no focus management, no screen-reader support. |
| **Confirmation on destructive actions** | Mix of `window.confirm()`, `SmallModal.vue`, and sometimes nothing at all. No consistent pattern. |

---

## 4. Testing & Coverage

### Backend (pytest)

| Metric | Value |
|--------|-------|
| Test files | 149 |
| Tests passing | 1,069 |
| Tests failing | 0 |
| Tests skipped | 8 |
| Markers | 12 (unit, integration, smoke, slow, router, geometry, adaptive, bridge, helical, cam, export, ai_context) |
| Coverage scope | Entire `app` module with branch coverage |
| Coverage threshold | **None** — `--cov-fail-under` is NOT configured |

**Good:**
- Golden snapshot tests validate manufacturing G-code intent
- Baseline N18 tests provide geometry → G-code parity checks
- `conftest.py` enforces `X-Request-Id` on every test response via autouse fixture
- Endpoint shadow stats generate deprecation-budget data for CI

**Bad:**
- No coverage floor. Coverage is tracked and reported but there's nothing preventing it from declining.
- `tests/routers/` directory exists but is empty — router endpoint tests are mixed into other files
- No property-based testing (hypothesis) for geometry edge cases
- No chaos testing for storage failures

### Frontend (Vitest)

| Metric | Value |
|--------|-------|
| Test files | 27 |
| Framework | Vitest + jsdom |
| Coverage scope | `src/sdk/**/*.ts` **only** |
| Coverage threshold | **None** |

**27 test files for the entire Vue SPA** — that's about one test file per three routes. Coverage is scoped exclusively to the SDK layer; components, stores, views, composables outside `src/sdk/` have zero coverage tracking.

**What's tested:** Composables (6), SDK/core (3), components (7), services (1), utils (2), audio analyzer (4), features (1), evidence (1), generic (2).

**What's not tested:** Route guards, auth flows, store interactions, form validation, error states, empty states, modal behaviors, toast notifications, responsive breakpoints.

---

## 5. Observability

### What Exists

| Layer | Implementation | Status |
|-------|---------------|--------|
| **Request ID propagation** | ContextVar-based `X-Request-Id` on every response. Middleware in `main.py`, filter injected into root logger. | ✅ Solid |
| **Logging** | `logging` stdlib with `%(request_id)s` format. Plain text, not structured. | 🟡 Functional but limited |
| **Metrics (governance)** | Prometheus text exposition at `/metrics`. Thread-safe counters with cardinality guardrail (max 2,000 series). | ✅ Good |
| **Metrics (RMOS CAM)** | Custom Counter/Histogram classes. Tracks intent requests, issues, rejects, latency. | ✅ Good |
| **OpenTelemetry** | Optional, lazy, metrics-only, disabled by default. No tracing. | 🟡 Stub |
| **Health endpoints** | Three: `/health` (basic), `/api/health` (router summary), `/api/health/detailed` (full). | ✅ Good |

### What Doesn't Exist

| Layer | Impact |
|-------|--------|
| **Structured logging (JSON)** | Can't aggregate logs in ELK/Loki without parsing regex. |
| **Distributed tracing** | Can't follow a request across middleware → router → CAM → store. |
| **Alerting rules** | Prometheus endpoint exists but no Grafana dashboards, no alert configurations, no PagerDuty/Slack integration. |
| **Error tracking** | No Sentry, no Rollbar, no error aggregation service. Errors disappear into log files. |
| **Frontend observability** | Zero. No browser error tracking, no performance monitoring, no user session replay. |
| **Monitoring dashboards** | No Grafana JSON, no dashboard configs anywhere in the repo. |
| **Uptime monitoring** | No external health check pinging the production URL. |
| **Audit logging** | RMOS has SHA256 audit chain on artifacts (good), but no general audit trail for who did what when. |

---

## 6. Operational Risks

### Horizontal Scaling — 🔴 BLOCKER

The system **cannot scale to multiple instances**. Period.

| Component | Problem |
|-----------|---------|
| Singleton stores | `_store = None` globals in constraint_profiles, learned_overrides, advisory store, RMOS deps. Each process maintains its own copy. |
| File locks | `threading.Lock()` protects threads within one process. Useless across containers. |
| File-system storage | RMOS runs stored as JSON files on local disk. Two replicas cannot share the same filesystem without NFS/EFS and distributed locking. |
| Metrics registries | In-process counters. Each replica tracks its own numbers. |

**Consequence:** This is permanently single-instance until stores are refactored to use a shared backend (Redis, PostgreSQL, or at minimum a shared filesystem with proper locking).

### Data Loss Scenarios

| Scenario | Protection |
|----------|-----------|
| SQLite corruption | WAL mode (good), but no backup mechanism, no point-in-time recovery |
| File-system JSON corruption | Atomic writes via `os.replace()` (good), but no backup or versioning |
| Golden .nc file overwrite | Only protection is human review before running regenerate script. No immutable storage. |
| Failed run artifacts | No cleanup. Disk grows unbounded. |
| Docker volume loss | Named volumes in production compose, but no backup policy documented |

### Long-Running Operations

CAM operations on complex geometry can take significant time. There is no:
- Background task queue (Celery, ARQ, or similar)
- WebSocket progress reporting
- Cancellation mechanism
- Timeout enforcement on all geometry endpoints (timeout wrapper exists but is optional)

Nginx has 60-second proxy timeouts. A complex toolpath operation that takes 90 seconds will 502 through the proxy.

---

## 7. Security

### Critical Findings

| Finding | Severity | Detail |
|---------|----------|--------|
| **`v-html` XSS via SVG** | 🔴 HIGH | 10+ components render SVG via `v-html` without sanitization. If attacker controls DXF input → SVG generation → `v-html`, they can execute JavaScript in user's browser. |
| **Dev auth mode** | 🔴 HIGH | Default `AUTH_MODE=header` reads `x-user-role` and `x-user-id` from request headers. Any client can impersonate any role. This is fine for dev but must not be the production default. |
| ~~No rate limiting~~ | ✅ RESOLVED | Rate limiting implemented via slowapi middleware (commit 1ce75797). Tiers: public 30/min, auth 60/min, pro 300/min, AI 10/min, CAM 20/min. |
| **CORS env var injection** | 🟠 HIGH | `CORS_ORIGINS` env var is parsed and appended to allowed origins without validation. Malformed value could whitelist unintended origins. |
| **No CSRF tokens** | 🟡 MEDIUM | CORS preflight provides browser-level protection, but explicit CSRF tokens would be safer given `allow_credentials=True`. |
| **No file upload size limit** | 🟡 MEDIUM | Analyzer upload endpoint accepts arbitrary-sized files. DXF upload guard has limits, but the upload boundary doesn't enforce them before reading the full file into memory. |
| **Missing security headers** | 🟡 MEDIUM | Nginx has basic headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection) but missing HSTS, Content-Security-Policy, and X-Permitted-Cross-Domain-Policies. |
| **localStorage exposure** | 🟢 LOW | Stores non-sensitive data (toolpath player state, compare baselines). No auth tokens in localStorage. Low risk. |

### Positive Security Features

- DXF parsing has file size limits, entity count limits, operation timeouts
- Shapely-based geometry validation catches self-intersections and degenerate polygons
- RMOS artifact integrity via SHA256 audit chain
- AI sandbox boundaries prevent AI code from accessing RMOS authority functions
- Pre-commit hooks enforce sandbox import isolation

---

## 8. CNC Safety-Critical Path

This is the most consequential subsystem in the entire application. Bad G-code can damage machines, destroy workpieces, and injure people.

### What's Protected

| Guard | Implementation |
|-------|---------------|
| Chipload limits | ≤0.30 mm/tooth (configurable) |
| Stepover limits | ≤ tool diameter |
| Feed rate limits | Per machine profile `max_feed` |
| RPM limits | Per machine profile `max_rpm` |
| Helical pitch | Validated > 0 |
| Saw blade feed | Per-operation validator with limits |
| Geometry validation | Self-intersection, zero-length, degenerate polygon rejection |
| Fail-safe default | Falls back to GRBL profile if machine profile is missing |

### What's NOT Protected

| Gap | Risk |
|-----|------|
| **Zero RPM** | G-code could generate `S0` (spindle stop) — tool drags through material without cutting |
| **Negative RPM** | Not validated, could generate nonsensical spindle commands |
| **Machine capability overflow** | If user requests 30K RPM on a machine with 24K max, system doesn't block — uses machine profile clamp, but the clamp logic is only in `whatif_opt.py`, not enforced at G-code emission |
| **Division by zero** | Chipload = feed / (rpm × flutes). If `num_flutes=0` in tool definition, unhandled `ZeroDivisionError` |
| **Min ≤ max validation** | Feed rate bounds from machine profile don't validate that `min_feed ≤ max_feed`. Misconfigured profile produces nonsensical values. |
| **Optional geometry validation** | DXF advanced validation runs only via preflight endpoint. It is NOT enforced before G-code export. User can skip preflight and export unchecked geometry. |
| **Fail-open design** | System always returns G-code. There is no "refuse to generate" mode for dangerous parameter combinations. |

**The philosophy is "fail-open" — always produce output.** For a CNC system, this is the wrong default. If parameters are outside safe bounds, the system should refuse to generate G-code and explain why.

---

## 9. Edge Cases in Core Logic

| Area | Edge Case | Status |
|------|-----------|--------|
| **DXF coordinates** | Extremely large X/Y values (millions of mm) | ❌ No bounds check |
| **DXF coordinates** | NaN/Infinity | ✅ Checked and rejected |
| **DXF polygons** | Very small (<0.1 mm² area) | ✅ Rejected, but may be too aggressive for inlay work |
| **DXF polygons** | Self-intersecting | ✅ Detected with O(n²) overlap check |
| **Unit conversion** | Unknown units | ⚠️ Silent fallback to mm — no user warning |
| **Unit conversion** | Roundtrip precision (mm→in→mm) | ❌ No documented precision preservation |
| **Geometry timeout** | Complex geometry stalls processing | ⚠️ Timeout wrapper exists but is not enforced on all endpoints |
| **Graph algorithms** | Cycles in adjacency map | ✅ `find_cycles_iterative()` handles this |
| **Graph algorithms** | Disconnected geometry | ❌ Not documented how this is handled |
| **Wood species** | Acoustic data gaps (null values) | ⚠️ 4 major species (both rosewoods, both traditional ebonies) have null speed_of_sound and acoustic_impedance |
| **Machine profiles** | Invalid profile combinations | ⚠️ Min/max validation missing |
| **CITES compliance** | No CITES status field in wood database | ❌ Not present — legal risk for regulated species |

---

## 10. Dashboard Evaluation

**Location:** `packages/client/src/views/AppDashboardView.vue`

### Current State: Completely Static

The dashboard displays hardcoded statistics and placeholder content. It does not:
- Query any API endpoints for real data
- Track actual user activity or project status
- Show real manufacturing run history
- Display machine utilization or job queue status

### What It Shows

| Widget | Data Source | Real? |
|--------|-----------|-------|
| Project count | Hardcoded number | ❌ |
| Recent activity | Hardcoded list | ❌ |
| Quick actions | Static links | ⚠️ Links work, data is fake |
| System status | Not present | ❌ |

### What It Should Show

For a CNC lutherie platform, the dashboard should surface:
1. Active manufacturing runs (from RMOS) with status indicators
2. Machine profiles configured with last-used timestamps
3. Recent G-code exports with success/failure status
4. Wood species used in recent projects
5. System health summary (from `/api/health/detailed`)
6. Quick action: "Start new run" → RMOS wizard

**Verdict:** The dashboard is a static placeholder. It provides zero operational value.

---

## 11. UX Component Evaluation

### Feature-by-Feature Assessment

| Feature | Status | Detail |
|---------|--------|--------|
| **Undo/Redo** | ✅ Present (partial) | Implemented in `useRosetteGeometryStore.ts` and `useGeometryStore.ts` via history arrays. NOT present in other stores (art studio, CNC settings). Pattern is not reusable — each store reimplements its own history. |
| **Tooltips / Mouseover** | ❌ Absent | No tooltip system, no contextual help, no hover hints. Users must guess what controls do. |
| **Loading States** | ⚠️ Inconsistent | Some views check a `loading` ref and show a spinner. Many views don't. No skeleton loaders. No shared `LoadingOverlay` component. |
| **Error States** | ❌ Absent | No error boundary component. Errors crash silently or produce a white screen. No "something went wrong, try again" fallback. |
| **Empty States** | ❌ Absent | Lists and tables that receive empty arrays show nothing. No "no data yet" illustrations or guidance. |
| **Confirmation Dialogs** | ⚠️ Inconsistent | `SmallModal.vue` exists but is used in ~5 places. 10+ other places use `window.confirm()`. No consistent pattern for destructive actions. |
| **Keyboard Shortcuts** | ❌ Nearly absent | Only `CommandPalette.vue` (Ctrl+K). No keyboard navigation for CAM workflows, no Escape-to-close modals, no arrow-key navigation. |
| **Toast Notifications** | ⚠️ Broken | Two systems coexist: custom `ToastNotification.vue` and `vue-toastification` library. Different styling, different APIs, different stores use different ones. |
| **Responsive Design** | ⚠️ Partial | Design tokens define breakpoints. No evidence of systematic responsive testing. CAM views use fixed-width layouts that don't adapt. |
| **Accessibility** | ❌ Absent | No ARIA labels on interactive elements, no focus management, no `role` attributes, no skip-navigation, no screen-reader announcements. |
| **Dark Mode** | ❌ Absent | Design tokens are light-only. No theme switching. |
| **Offline Support** | ❌ Absent | No service worker, no offline cache, no "you're offline" indicator. |
| **Breadcrumbs / Navigation** | ⚠️ Partial | Some views have breadcrumbs. No consistent navigation pattern across the app. |
| **Search** | ❌ Absent | No global search for projects, runs, species, or tools. |
| **Drag & Drop** | ❌ Absent | DXF upload is file-picker only. No drag-and-drop zone. |

---

## 12. Ranked Recommendations

Ordered by impact × effort balance. Fix #1 first.

### Tier 1 — Fix Now (blocking production readiness)

| # | Recommendation | Why | Effort |
|---|---------------|-----|--------|
| **1** | **Install Tailwind or remove Tailwind classes** | 10+ components have broken styles because Tailwind is referenced but not installed. Users see misaligned, unstyled UI elements right now. | 2 hours |
| **2** | **Add SVG sanitization before `v-html`** | XSS vector. Use DOMPurify on all SVG strings before rendering. 10+ components affected. | 4 hours |
| **3** | **Add global Vue error boundary** | Currently, any unhandled error produces a white screen with no recovery. Add `app.config.errorHandler` + `<ErrorBoundary>` wrapper. | 3 hours |
| **4** | **Enforce DXF validation before G-code export** | Currently optional. User can skip preflight and export unchecked geometry. Make advanced validation mandatory on the export path. | 4 hours |
| **5** | **Set `AUTH_MODE=jwt` as production default** | Default is `header` mode where anyone can set `x-user-role`. Production envs must default to JWT. | 1 hour |

### Tier 2 — Fix Soon (quality and reliability)

| # | Recommendation | Why | Effort |
|---|---------------|-----|--------|
| **6** | **Consolidate toast notifications** | Pick one system. Remove the other. Users see two different notification styles. | 2 hours |
| **7** | **Replace all `window.confirm()` with `SmallModal`** | Inconsistent UX on destructive actions. Native browser dialogs break the design language. | 3 hours |
| **8** | **Add `--cov-fail-under=70` to pytest CI** | Coverage is tracked but not gated. It will silently decline without a floor. | 15 min |
| **9** | **Add CNC parameter validation (zero RPM, zero flutes, min≤max)** | Division-by-zero in chipload calc, nonsensical G-code from zero spindle speed. These are safety bugs. | 4 hours |
| **10** | **Add rate limiting middleware** | Exists only for RMOS deletes. All upload and CAM endpoints are unprotected against abuse. | 4 hours |
| **11** | **Add frontend error tracking (Sentry or equivalent)** | Errors currently vanish. No one knows when the frontend breaks for a user. | 2 hours |

### Tier 3 — Improve (scaling and robustness)

| # | Recommendation | Why | Effort |
|---|---------------|-----|--------|
| **12** | **Refactor singleton stores to dependency injection** | Required for horizontal scaling. Currently each process has its own state. Use FastAPI `Depends()` with shared backend. | 2-3 days |
| **13** | **Add structured logging (JSON)** | Plain-text logs can't be parsed by ELK/Loki/Datadog without regex. Switch to structlog or python-json-logger. | 1 day |
| **14** | **Add orphaned artifact cleanup** | Failed runs leave files on disk forever. Add a TTL-based cleanup job. | 4 hours |
| **15** | **Expand frontend test coverage** | 27 test files for 75 routes. At minimum, cover auth flows, store interactions, route guards, form validation. | 1-2 weeks |
| **16** | **Add empty state and loading state components** | Users see blank screens when data is absent or loading. Create reusable `<EmptyState>` and `<LoadingState>` components. | 1 day |
| **17** | **Add CITES compliance field to wood database** | Legal risk. Users can unknowingly select restricted species (Brazilian Rosewood is CITES Appendix I). | 1 day |
| **18** | **Add monitoring dashboards** | Prometheus endpoint exists but nothing reads it. Set up Grafana with basic panels: request rate, error rate, latency, RMOS run counts. | 1 day |
| **19** | **Add silent-unit-fallback warning** | Unknown unit types silently default to mm. A DXF in inches uploaded without conversion produces geometry 25.4× wrong. At minimum, warn the user. | 2 hours |
| **20** | **Make the dashboard real** | Replace hardcoded placeholder data with actual API queries against RMOS runs, health status, recent activity. | 2-3 days |

---

## 13. Re-Review Checklist

Use this after making changes. Check each item and record pass/fail.

### Architecture & Boundaries

- [ ] `make check-boundaries` passes (7-step fence)
- [ ] `make api-verify` passes (scope + boundaries + tests)
- [ ] No new cross-domain imports (RMOS ↔ CAM, AI sandbox)
- [ ] New routers registered in `router_registry/manifest.py` (not ad-hoc in `main.py`)
- [ ] `FENCE_REGISTRY.json` updated if boundary rules changed

### Backend Quality

- [ ] `pytest tests/ -v` — 0 failures, 0 errors
- [ ] `pytest --cov=app --cov-fail-under=70` — passes coverage floor (once set)
- [ ] No new bare `except:` (run `grep -rn "except:" services/api/app/`)
- [ ] No new `except Exception` in safety paths (`cam/`, `rmos/`, `saw_lab/`, `calculators/`)
- [ ] New endpoints return `X-Request-Id` header
- [ ] Golden G-code snapshots unchanged (or deliberately regenerated with review)

### Frontend Quality

- [ ] `npm run test` — Vitest passes
- [ ] `npm run build` — no TypeScript errors, no build warnings
- [ ] Tailwind is installed AND configured, OR all Tailwind classes are removed
- [ ] No new `v-html` without DOMPurify sanitization
- [ ] No new `window.confirm()` — use `SmallModal.vue`
- [ ] No new direct `api()` / `apiFetch()` calls — use SDK layer
- [ ] Toast notifications use ONE system (whichever was chosen)
- [ ] New views have loading states and empty states

### Security

- [ ] `AUTH_MODE` is `jwt` in production environment files
- [ ] No hardcoded secrets in source code (run `grep -rn "API_KEY\|SECRET\|PASSWORD" --include="*.py" --include="*.ts" services/ packages/`)
- [ ] CORS origins are explicit domains (not `*`) in production config
- [ ] File upload endpoints validate size before reading into memory
- [ ] New `v-html` usage sanitizes input with DOMPurify

### CNC Safety

- [ ] No G-code generation with RPM ≤ 0
- [ ] No G-code generation with flutes ≤ 0
- [ ] Machine profile min/max values are validated (min ≤ max)
- [ ] DXF advanced validation is mandatory before G-code export (not just preflight)
- [ ] Chipload and stepover limits are enforced at G-code emission (not just in what-if optimizer)

### Observability

- [ ] `/api/health/detailed` returns accurate feature counts
- [ ] `/metrics` endpoint includes new router metrics
- [ ] Error logs include request ID and stack trace
- [ ] Failed router loads are visible in health check output

### Deployment

- [ ] `docker compose up --build` succeeds and passes smoke test
- [ ] Production compose has health checks on ALL services (including nginx)
- [ ] `.env.example` documents all required environment variables
- [ ] No secrets in Docker build layers (`docker history` shows no credentials)

### Documentation

- [ ] `ROUTER_MAP.md` updated if routers changed
- [ ] `ENDPOINT_TRUTH_MAP.md` updated if API surface changed
- [ ] `REMEDIATION_PLAN.md` status updated if remediation items resolved
- [ ] `CHANGELOG.md` updated for user-facing changes

---

## Appendix: Remediation Progress

For reference — current status as of this evaluation:

| Phase | Target | Status | Result |
|-------|--------|--------|--------|
| Phase 0 — Dead Code Purge | Remove stale directories | ✅ COMPLETE | Done |
| Phase 1 — Exception Hardening | Bare `except:` → 0, triage broad catches | 🟡 PARTIAL | 0 bare (was 97), 1,622 `except Exception` remain |
| Phase 2 — API Surface Reduction | Routes < 300 | ✅ COMPLETE | 262 routes (was 1,060) |
| Phase 3 — God-Object Decomposition | 0 files > 500 lines | ✅ COMPLETE | Done (was 30+) |
| Phase 4 — Documentation Triage | < 50 docs | ✅ COMPLETE | 30 docs (was 685) |
| Phase 5 — Quick Cut Mode | 3-step wizard | ✅ COMPLETE | Done |
| Phase 6 — Health/Observability | `/api/health/detailed` | ✅ COMPLETE | Done |

**Next priority per this evaluation:** Tier 1 items (Tailwind, SVG sanitization, error boundary, DXF validation enforcement, auth default).
