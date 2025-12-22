# Legacy Code Assessment & Migration Plan
## Executive Summary - Luthier's ToolBox API

**Assessment Date:** December 22, 2025  
**Analyst:** GitHub Copilot AI Assistant  
**Scope:** Backend API Services (`services/api/app/`)

---

## 1. Executive Overview

The Luthier's ToolBox API is a **FastAPI-based CAM (Computer-Aided Manufacturing) system** for guitar builders, featuring 116 working routers across 19 major feature waves. The codebase demonstrates **incremental evolution** with **controlled technical debt** through a phased architecture. Recent consolidation efforts (Waves 18-19, December 2025) show **active modernization**.

### Key Findings
- ✅ **116 working routers** (93 committed, 23+ experimental)
- ⚠️ **~10-15% legacy code** in experimental staging areas
- ✅ **Feature flag system** enables safe v1→v2 migrations
- ⚠️ **Dual-mode architecture** creates maintenance overhead
- ✅ **Recent cleanup**: 84 phantom imports removed, 9 broken routers fixed

---

## 2. Legacy Code Inventory

### 2.1 Primary Legacy Areas

#### A. **`_experimental/` Directory** ⚠️ HIGH PRIORITY
**Location:** `services/api/app/_experimental/`

**Components Identified:**
- `ai_cam_router.py` - AI-powered CAM planning (Wave 9)
- `joblog_router.py` - Job telemetry logging (Wave 9)
- `ai_graphics/` module - Vision engine, advisory, teaching loops (Wave 14)
  - `api/vision_routes.py`
  - `api/advisory_routes.py`
  - `api/teaching_routes.py`
  - `image_providers.py`
  - `image_transport.py`
  - `rosette_generator.py`
  - `services/llm_client.py`
  - `services/training_data_generator.py`
- CNC production modules (learn/dashboard routers)

**Status:** Functional but not production-hardened  
**Integration:** Wrapped in try/except with fallback warnings  
**Risk Level:** MEDIUM - isolated failures don't crash main app

---

#### B. **RMOS Runs v1 (Legacy Single-File)** ⚠️ MEDIUM PRIORITY
**Location:** `services/api/app/rmos/runs/api_runs.py`

**Feature Flag:** `RMOS_RUNS_V2_ENABLED` (default: `true`)  
**Default Behavior:** v2 (governance-compliant, date-partitioned)  
**Rollback Path:** Set env var `RMOS_RUNS_V2_ENABLED=false`

**Technical Details:**
```python
# Current implementation (main.py lines 318-333)
_RMOS_RUNS_V2_ENABLED = os.getenv("RMOS_RUNS_V2_ENABLED", "true").lower() == "true"

if _RMOS_RUNS_V2_ENABLED:
    from .rmos.runs_v2.api_runs import router as rmos_runs_router
    print("RMOS Runs: Using v2 (governance-compliant)")
else:
    from .rmos.runs.api_runs import router as rmos_runs_router  # LEGACY
    print("RMOS Runs: Using v1 (legacy single-file)")
```

**Migration Status:** v2 is production default, v1 retained for emergency rollback  
**Risk Level:** LOW - feature-flagged with clear deprecation path

---

#### C. **Import Consolidation Legacy Routes** ⚠️ LOW PRIORITY
**Location:** Wave 13 (pre-consolidation) router duplicates

**Context:**
- Wave 18: CAM routers → `cam/routers/` (63 routes consolidated)
- Wave 19: Compare routers → `compare/routers/` (14 routes consolidated)

**Issue:** Old individual router imports coexist with new aggregators:
```python
# Legacy individual imports (Wave 13)
from .routers.cam_compare_diff_router import router as cam_compare_diff_router

# New consolidated import (Wave 19)
from .compare.routers import compare_router  # Aggregates all compare routes
```

**Current State:** Both patterns live side-by-side (see line 715: "These provide the new organized endpoints alongside legacy routes for transition")

**Risk Level:** LOW - redundant endpoints but no functionality impact

---

### 2.2 Experimental Code Statistics

| Category | Count | Status | Risk |
|----------|-------|--------|------|
| Core Routers (Waves 1-13) | 93 | ✅ Production | Low |
| Experimental Routers (`_experimental/`) | ~8-12 | ⚠️ Staging | Medium |
| Feature-Flagged (v1/v2) | 2 | ✅ Controlled | Low |
| Consolidated Aggregators (Wave 18-19) | 2 | ✅ Active Migration | Low |
| Broken/Phantom Imports | 0 | ✅ Cleaned (Dec 2024) | None |

---

## 3. Risk Assessment

### 3.1 Technical Risks

#### **HIGH RISK** 🔴
*None identified.* The codebase shows mature error handling patterns.

#### **MEDIUM RISK** 🟡
1. **`_experimental/` Module Instability**
   - **Impact:** Vision engine, AI-CAM, job logging failures
   - **Mitigation:** Try/except wrappers prevent cascading failures
   - **Current Handling:** Graceful degradation with console warnings
   - **Recommendation:** Promote to production modules or sunset

2. **Dependency Drift in Experimental Code**
   - **Impact:** LLM client updates may break AI graphics module
   - **Evidence:** Recent LF→CRLF warnings on experimental files
   - **Recommendation:** Pin dependency versions, add integration tests

#### **LOW RISK** 🟢
1. **RMOS Runs v1 Retention**
   - **Impact:** Dead code accumulation
   - **Timeline:** Safe to remove 6 months after v2 adoption (est. mid-2026)

2. **Dual Routing Patterns (Wave 18-19 transition)**
   - **Impact:** API documentation bloat, minor maintenance overhead
   - **Timeline:** Complete deprecation by Wave 20

---

### 3.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Experimental features leak to production** | Low | Medium | Feature flags + isolated routing |
| **v1→v2 rollback needed under load** | Very Low | Low | Tested rollback path via env var |
| **Incomplete Wave 18-19 consolidation** | Medium | Low | Parallel routes ensure zero downtime |
| **AI graphics module abandonment** | Medium | Medium | Document intent: productionize or archive |

---

## 4. Pros & Cons Analysis

### 4.1 Current Architecture Strengths ✅

1. **Phased Evolution Model**
   - 19 documented "waves" enable incremental complexity growth
   - Each wave is auditable, testable, and reversible

2. **Defense-in-Depth Error Handling**
   - Try/except wrappers on experimental imports
   - Router-level isolation prevents system-wide failures
   - Request ID middleware for debugging (C# HttpContext.Items equivalent)

3. **Feature Flag Discipline**
   - `RMOS_RUNS_V2_ENABLED` demonstrates safe v1→v2 patterns
   - Environment-driven config enables A/B testing

4. **Recent Cleanup Discipline**
   - 84 phantom imports removed (Dec 2024)
   - 9 broken routers fixed proactively
   - No silent failures (all import errors logged)

5. **Consolidation Maturity (Wave 18-19)**
   - CAM/Compare routers aggregated by domain
   - Reduces cognitive load, improves discoverability

---

### 4.2 Current Architecture Weaknesses ⚠️

1. **`_experimental/` Directory Limbo**
   - **Issue:** No clear promotion criteria (when does experimental → production?)
   - **Impact:** 8-12 routers in indefinite staging
   - **Technical Debt:** Accumulating untested/undocumented code

2. **Dual v1/v2 Maintenance**
   - **Issue:** RMOS Runs v1 still in codebase despite v2 being default
   - **Cost:** Security patches, dependency updates apply to dead code
   - **Timeline Risk:** Forgotten code becomes "unknown unknowns"

3. **Import Sprawl (Pre-Wave 18-19)**
   - **Issue:** 93 individual router imports clutter `main.py`
   - **Cognitive Load:** 777-line main.py file
   - **Discovery:** New developers struggle to find relevant routers

4. **Inconsistent Versioning Patterns**
   - Some routers: `cam_post_v155_router`, `cam_smoke_v155_router`
   - Others: No version suffix
   - Unclear when versions are incremented vs. replaced

5. **Governance Contract Sprawl (Wave 16)**
   - Multiple contracts mentioned in comments:
     - `SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md`
     - `RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md`
     - `RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md`
     - `RUN_DIFF_VIEWER_CONTRACT_v1.md`
   - **Risk:** Contract drift from implementation

---

## 5. Migration Strategy

### 5.1 Recommended Approach: **Incremental Sunset**

**Philosophy:** Avoid "big bang" rewrites. Migrate in 3 waves over 6-9 months.

---

### **Phase 1: Triage & Documentation (Q1 2026 - Weeks 1-4)**

#### Goals
1. Catalog all `_experimental/` modules
2. Define promotion criteria
3. Identify sunset candidates
4. Document v1 removal timeline

#### Actions
| Task | Owner | Output | Deadline |
|------|-------|--------|----------|
| Create `_experimental/README.md` | Tech Lead | Promotion criteria doc | Week 1 |
| Inventory AI graphics module usage | Dev Team | Usage metrics (API calls/week) | Week 2 |
| Survey: Which experimental features are in production? | Product | Feature adoption matrix | Week 3 |
| Document RMOS Runs v1 removal plan | Backend Lead | Deprecation RFC | Week 4 |

#### Decision Matrix: Promote vs. Sunset
```
                High Usage               Low Usage
               ┌──────────────────────┬──────────────────────┐
High Quality   │ PROMOTE → Production │ MAINTAIN (useful)    │
               ├──────────────────────┼──────────────────────┤
Low Quality    │ REFACTOR → Production│ SUNSET → Archive     │
               └──────────────────────┴──────────────────────┘
```

---

### **Phase 2: Promote High-Value Modules (Q1-Q2 2026 - Weeks 5-16)**

#### 2A. AI Graphics Module (Weeks 5-10)
**Assumption:** High strategic value (Vision Engine, Advisory routes)

**Migration Steps:**
1. **Add Integration Tests** (Week 5-6)
   - Vision route regression tests
   - Advisory route API contract tests
   - Teaching loop end-to-end tests

2. **Refactor for Production** (Week 7-9)
   - Extract `_experimental.ai_graphics` → `app.ai_graphics`
   - Remove try/except wrappers (make imports required)
   - Add OpenAPI documentation
   - Pin LLM client dependencies

3. **Deploy with Monitoring** (Week 10)
   - Enable error tracking (Sentry/Azure Monitor)
   - Add performance metrics (response time P95/P99)
   - Gradual rollout via feature flag `AI_GRAPHICS_ENABLED=true`

**Rollback Plan:** Revert import path, redeploy previous container

---

#### 2B. AI-CAM Router (Weeks 11-14)
**Assumption:** Medium strategic value (automation opportunity)

**Migration Steps:**
1. **Stakeholder Validation** (Week 11)
   - Confirm AI-CAM is used in production
   - If unused → move to sunset list

2. **If Promoted:**
   - Same pattern as AI Graphics (tests → refactor → deploy)
   - Timeline: Weeks 12-14

---

#### 2C. JobLog Router (Weeks 15-16)
**Assumption:** Telemetry infrastructure

**Quick Win:**
- Telemetry is typically low-risk (write-only, no business logic)
- Move to `app.telemetry.joblog_router` in single PR
- Add log retention policy

---

### **Phase 3: Sunset Legacy Code (Q2-Q3 2026 - Weeks 17-36)**

#### 3A. Remove RMOS Runs v1 (Weeks 17-18)
**Preconditions:**
- v2 has been default for 6+ months
- No rollback incidents in last 90 days
- Product confirms zero v1 usage

**Steps:**
1. Delete `rmos/runs/api_runs.py` (v1 file)
2. Remove feature flag code from `main.py`
3. Update documentation
4. Deploy + monitor (no expected impact)

---

#### 3B. Deprecate Pre-Consolidation Routes (Weeks 19-28)
**Scope:** Wave 13 individual router imports replaced by Wave 18-19 aggregators

**Strategy: Soft Deprecation**
1. **Add Deprecation Warnings** (Week 19)
   ```python
   @router.get("/api/cam/compare/diff")
   async def legacy_endpoint():
       logger.warning("DEPRECATED: Use /api/cam/consolidated/diff")
       return await new_consolidated_endpoint()
   ```

2. **Monitor Usage** (Weeks 20-24)
   - Track deprecated endpoint calls
   - Notify API consumers of migration path

3. **Remove Dead Endpoints** (Week 25-28)
   - After 30 days of zero traffic, delete legacy routes
   - Remove old router imports from `main.py`

---

#### 3C. Archive Unused Experimental Modules (Weeks 29-36)
**Candidates:**
- Modules with zero API calls in 90-day window
- Modules without product owner

**Actions:**
1. Move to `_archived/` directory with README explaining context
2. Update main.py to remove imports
3. Document in changelog

---

### 5.2 Success Metrics

| Metric | Baseline (Dec 2025) | Target (Q3 2026) |
|--------|---------------------|------------------|
| Production routers | 93 | 105+ |
| Experimental routers | 8-12 | 0 |
| Feature-flagged code paths | 2 (v1/v2) | 0 |
| `main.py` line count | 777 | <400 (via aggregators) |
| Import try/except blocks | 15+ | <3 |
| Documented migration RFCs | 0 | 5+ |

---

## 6. Cost-Benefit Analysis

### 6.1 Migration Costs

| Phase | Engineering Weeks | Risk | Dependencies |
|-------|------------------|------|--------------|
| Phase 1: Triage | 4 weeks (1 FTE) | Low | None |
| Phase 2: Promote | 12 weeks (2 FTE) | Medium | Product validation |
| Phase 3: Sunset | 20 weeks (1 FTE) | Low | API consumer migration |
| **Total** | **36 weeks** | **Medium** | Cross-team coordination |

**Estimated Cost:** ~$150K-$200K (assuming $100-$120/hr blended rate × 3 FTE-months)

---

### 6.2 Benefits

#### Immediate (Q1 2026)
- ✅ **Clarity:** Documented promotion/sunset criteria
- ✅ **Risk Reduction:** Known state of experimental code
- ✅ **Faster Onboarding:** Clear production vs. experimental boundaries

#### Medium-Term (Q2-Q3 2026)
- ✅ **Reduced Maintenance:** 10-15% less code to patch/test
- ✅ **Faster Builds:** Fewer dependencies to resolve
- ✅ **Simplified Debugging:** No dual v1/v2 code paths

#### Long-Term (Q4 2026+)
- ✅ **Architectural Flexibility:** Room for Wave 20+ features
- ✅ **Security Posture:** No forgotten legacy code with unpatched CVEs
- ✅ **Recruitment:** Modern codebase attracts senior engineers

**Estimated Savings:** $50K-$75K/year (reduced bug triage, faster feature development)  
**Payback Period:** ~18-24 months

---

## 7. Recommendations Summary

### **Immediate Actions (This Sprint)**
1. ✅ **Commit current work** (DONE: 27 files, 3,857 insertions)
2. 🟡 **Create `_experimental/README.md`** defining promotion criteria
3. 🟡 **Schedule stakeholder review** of AI Graphics module usage

### **Short-Term (Q1 2026)**
1. 🟡 **Implement Phase 1 Triage** (4-week effort)
2. 🟡 **Document RMOS Runs v1 sunset timeline**
3. 🟡 **Add deprecation warnings** to pre-Wave 18 routes

### **Medium-Term (Q2-Q3 2026)**
1. 🟡 **Promote AI Graphics → Production** (10-week effort)
2. 🟡 **Remove RMOS Runs v1** after validation period
3. 🟡 **Complete Wave 18-19 consolidation** (deprecate old routes)

### **Long-Term (Q4 2026)**
1. 🟡 **Achieve zero experimental code** (all promoted or archived)
2. 🟡 **Reduce `main.py` to <400 lines** via aggregator pattern
3. 🟡 **Establish governance review** for future "waves"

---

## 8. Appendices

### Appendix A: Wave Architecture Overview
```
Wave 1-6:   Foundation (CAM core, RMOS, Rosette)
Wave 7-13:  Feature Expansion (93 routers)
Wave 14:    AI Integration (Vision, Advisory, Teaching)
Wave 15:    Art Studio Maturity (Patterns, Generators, Preview)
Wave 16:    Governance (Feasibility, Artifacts, Workflow)
Wave 17:    Persistence (SQLite sessions)
Wave 18:    CAM Consolidation (63 routes → aggregator)
Wave 19:    Compare Consolidation (14 routes → aggregator)
Wave 20+:   TBD (recommendation: focus on cleanup, not new features)
```

### Appendix B: Key Files for Review
- `services/api/app/main.py` - Central router registry (777 lines)
- `services/api/app/_experimental/` - Staging area (8-12 modules)
- `services/api/app/rmos/runs/api_runs.py` - v1 legacy implementation
- `services/api/app/rmos/runs_v2/api_runs.py` - v2 production implementation
- `services/api/app/cam/routers/` - Wave 18 consolidated routers
- `services/api/app/compare/routers/` - Wave 19 consolidated routers

### Appendix C: Feature Flag Reference
```python
# RMOS Runs v1/v2 Toggle
RMOS_RUNS_V2_ENABLED=true   # Production default (governance-compliant)
RMOS_RUNS_V2_ENABLED=false  # Rollback to legacy single-file

# Database Migrations
RUN_MIGRATIONS_ON_STARTUP=false  # Default: manual migrations
MIGRATIONS_DRY_RUN=false         # Default: apply changes
MIGRATIONS_FAIL_HARD=true        # Default: block startup on failure
```

### Appendix D: Contact & Governance
- **Codebase Owner:** Development Team
- **Architecture Review:** Required for Phase 2 promotions
- **API Deprecation Policy:** 90-day notice minimum
- **Emergency Rollback Authority:** Tech Lead + SRE on-call

---

## Document Control
- **Version:** 1.0
- **Last Updated:** December 22, 2025
- **Next Review:** Q1 2026 (align with Phase 1 completion)
- **Distribution:** Engineering, Product, Leadership

---

**END OF EXECUTIVE SUMMARY**
