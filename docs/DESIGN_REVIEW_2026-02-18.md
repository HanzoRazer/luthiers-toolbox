# Critical Systems Design Review: luthiers-toolbox

**Date:** 2026-02-18
**Reviewer Role:** Top 1% Critical Systems Design Reviewer
**Project:** Luthier's ToolBox (CNC Guitar Manufacturing Platform)

---

## Reviewer Assumptions

1. **Target User**: Professional luthiers, guitar manufacturers, CNC operators needing parametric design + safe G-code generation

2. **Deployment Context**: Workshop/factory, Windows/Linux, connected to CNC machines (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)

3. **Maturity Stage**: Pre-production (zero live CNC tests, zero external users per review)

4. **Criticality Level**: HIGH - unsafe G-code can damage expensive machinery, waste materials ($200-2000/billet), or cause injury

5. **Competitive Benchmark**: Fusion 360 CAM ($500/yr), VCarve Pro ($700), custom shop solutions

---

## Evaluation

### 1. Purpose Clarity
**Score: 5/10**

**Justification:**
- Clear technical mission: Generate safe G-code for CNC guitar manufacturing
- Strong domain expertise (fret math, chipload physics, multi-post support)
- RMOS safety architecture is well-conceived

**Gaps:**
- **Unclear product boundary**: 671 API routes - what's actually shipped?
- Smart Guitar, Audio Analyzer, IoT backend - are these part of product?
- No elevator pitch for cold visitors

**Improvements:**
1. Define shipped product scope: "Core = DXF→G-code + RMOS safety"
2. Add `docs/PRODUCT_SCOPE.md` listing included vs experimental features
3. Feature flags to hide non-production modules

---

### 2. User Fit
**Score: 4/10**

**Justification:**
- Domain-expert friendly (RMOS, feasibility concepts)
- Multi-post support covers real machine diversity

**Gaps:**
- 671 routes overwhelms newcomers
- No "Quick Cut" onboarding path
- Pro vs Standard mode not implemented
- RMOS concepts (GREEN/YELLOW/RED) unexplained to new users

**Improvements:**
1. Build Quick Cut: 3-screen workflow (Upload DXF → Pick machine → Download G-code)
2. Feature registry with Pro Mode toggle
3. Tooltips explaining safety concepts
4. User personas: (a) Production shop, (b) Custom builder, (c) Hobbyist

---

### 3. Usability
**Score: 3/10**

**Justification:**
- Vue 3 + Vite modern stack
- FastAPI auto-docs available

**Gaps:**
- **671 routes always visible** - no feature flags
- Exception swallowing hides real errors from users
- 25+ Vue components exceed 800 LOC (god objects)
- No first-run wizard or onboarding

**Improvements:**
1. Feature registry to hide experimental routes
2. Honest error messages (stop swallowing exceptions)
3. Decompose god-object Vue components
4. First-run wizard: "What machine do you have?"

---

### 4. Reliability
**Score: 4/10**

**Justification:**
- RMOS architecture is sound (30+ safety rules, audit trail)
- Fail-closed override policy (RED requires explicit auth)

**Gaps:**
- **1,622 `except Exception` blocks** - could mask safety failures
- **6 bare `except:` blocks** - catches unhandleable signals
- 36% actual test coverage (README claims 100%)
- No mandatory G-code simulation gate

**Improvements:**
1. Replace broad exceptions with specific types in safety paths
2. Add `@safety_critical` decorator (fail-closed, never swallows)
3. Fix README coverage claims (36% actual)
4. Make simulation mandatory before G-code export

---

### 5. Manufacturability/Maintainability
**Score: 3/10**

**Justification:**
- Modular domain architecture (RMOS, CAM, Saw Lab, Art Studio)
- Clean Python packaging with pyproject.toml
- 57 CI workflows

**Gaps:**
- **30+ Python files >500 LOC** (god objects)
- **25+ Vue components >800 LOC** (god objects)
- **200+ backup/archive files in VCS**
- 1,500+ line main.py with 47 try/except import blocks
- Two directories named `client/` (confusion)

**Improvements:**
1. Delete dead code: `.bak` files, `__ARCHIVE__/`, stale `client/`
2. Split god objects (e.g., `batch_router.py` at 2,724 LOC)
3. Refactor main.py to <200 LOC with declarative feature registry
4. Add architecture diagram

---

### 6. Cost
**Score: 5/10**

**Justification:**
- Open source - no licensing fees
- Appropriate tech stack (FastAPI, Vue 3)
- Railway deployment configured

**Gaps:**
- 671 routes = 3x typical API surface = maintenance burden
- Feature bloat adds deployment complexity
- No BOM or deployment cost documentation

**Improvements:**
1. Cull unused routes (target <300)
2. Lazy-load modules to reduce memory footprint
3. Document deployment costs (Railway tier, expected usage)

---

### 7. Safety
**Score: 5/10**

**Justification:**
- **RMOS architecture is excellent:**
  - 30+ feasibility rules (F001-F040)
  - Risk bucketing (GREEN/YELLOW/RED)
  - Immutable audit trail
  - Fail-closed override policy
- Multi-post support with machine-specific safety

**Gaps:**
- **1,622 broad exception handlers could bypass safety gates**
- If feasibility check throws → caught silently → could return GREEN for RED operation
- G-code validation not mandatory before export
- 278 broad handlers in safety-critical modules (RMOS, CAM, calculators)

**Improvements:**
1. `@safety_critical` decorator on all safety functions
2. Mandatory simulation gate before G-code export
3. Replace broad handlers with specific exceptions
4. Add CI check blocking new broad handlers in safety modules

---

### 8. Scalability
**Score: 5/10**

**Justification:**
- Appropriate for pre-production stage
- SQLite local + optional PostgreSQL
- Docker deployment ready

**Gaps:**
- Single-developer project - no multi-user coordination
- No batch processing for production QC
- 10+ concurrent users untested

**Improvements:**
1. Document scaling limits
2. Add batch mode for production shops
3. Consider multi-tenant architecture for SaaS path

---

### 9. Aesthetics
**Score: 4/10**

**Justification:**
- Vue 3 + Vite modern frontend
- Dark theme available
- Consistent use of Tailwind/component library

**Gaps:**
- 25+ oversized Vue components (2,987-line manufacturing list)
- Backup files in repo (`.bak`, `__ARCHIVE__/`)
- No design system documentation
- No component library/Storybook

**Improvements:**
1. Delete backup files from VCS
2. Decompose god-object components
3. Add Storybook for component documentation
4. Create design system guidelines

---

## Summary Scorecard

| Category | Score | Priority Fix |
|----------|-------|--------------|
| Purpose Clarity | 5/10 | Define product boundary |
| User Fit | 4/10 | Quick Cut onboarding |
| Usability | 3/10 | **Feature flags, honest errors** |
| Reliability | 4/10 | **Exception hardening** |
| Maintainability | 3/10 | **Dead code purge, split god objects** |
| Cost | 5/10 | Route culling |
| Safety | 5/10 | **@safety_critical decorator** |
| Scalability | 5/10 | Document limits |
| Aesthetics | 4/10 | Delete backups, decompose components |

**Overall: 4.2/10** — Strong domain expertise undermined by architectural complexity and safety implementation gaps

---

## Top 5 Critical Actions

### 1. Exception Hardening (P0 - SAFETY)
**Problem:** 1,622 broad `except Exception` blocks could mask safety gate failures
**Fix:** Replace with specific exceptions + `@safety_critical` decorator in RMOS/CAM/calculators
**Risk if not fixed:** Unsafe G-code generated silently

### 2. Dead Code Purge (P0)
**Problem:** 200+ backup/archive files polluting repo
**Fix:** Delete `.bak`, `__ARCHIVE__/`, stale `client/`, `streamlit_demo/`
**Impact:** Cleaner repo, reduced confusion

### 3. Fix README Coverage Claims (P0)
**Problem:** README claims "100% Coverage" - actual is 36%
**Fix:** Run `pytest --cov`, update badges with real numbers
**Impact:** Honest documentation, trust

### 4. API Surface Reduction (P1)
**Problem:** 671 routes = 3x typical, overwhelming
**Fix:** Instrument usage → classify → cull unused (target <300)
**Impact:** Maintainability, onboarding

### 5. Quick Cut Onboarding (P2)
**Problem:** No path for newcomers to reach G-code
**Fix:** 3-screen workflow (DXF → machine → G-code) in <5 minutes
**Impact:** User adoption

---

## Projected Remediation Impact

| Dimension | Current | Post-Fix | Delta |
|-----------|---------|----------|-------|
| Purpose | 5/10 | 7/10 | +2 |
| User Fit | 4/10 | 6/10 | +2 |
| Usability | 3/10 | 6/10 | +3 |
| Reliability | 4/10 | 6/10 | +2 |
| Maintainability | 3/10 | 6/10 | +3 |
| Cost | 5/10 | 6/10 | +1 |
| **Safety** | 5/10 | **8/10** | **+3** |
| Scalability | 5/10 | 5/10 | 0 |
| Aesthetics | 4/10 | 5/10 | +1 |
| **Overall** | **4.2/10** | **6.1/10** | **+1.9** |

---

## Key Metrics (Verified)

| Metric | Value |
|--------|-------|
| Backend Python files | 987 |
| Backend Python LOC | 51,649 |
| Frontend Vue/TS files | 533 |
| Frontend Vue/TS LOC | 152,076 |
| Total codebase LOC | ~203,725 |
| API routes | 671 |
| Test files | 95 |
| Actual test coverage | 36% |
| Broad exception handlers | 1,622 |
| Bare except blocks | 6 |
| Python files >500 LOC | 30+ |
| Vue files >800 LOC | 25+ |
| CI workflows | 57 |
| Documentation files | 54 |

---

## Conclusion

**Luthier's ToolBox demonstrates exceptional domain expertise** in CNC lutherie - the RMOS safety architecture, multi-post G-code generation, and parametric design tools are professionally conceived.

**However, rapid feature growth has created critical technical debt:**
- 1,622 broad exception handlers threaten safety gate integrity
- 671 API routes obscure product boundary
- God objects and dead code impede maintainability

**The path forward is clear:**
1. Harden exception handling in safety-critical paths (Week 1)
2. Purge dead code and fix documentation claims (Week 1)
3. Reduce API surface and add feature flags (Weeks 2-3)
4. Build Quick Cut onboarding (Week 4)

**With disciplined execution, the project can reach 6.1/10 within 4 weeks** - sufficient for controlled production deployment with ongoing improvement path to 7.0+/10.

---

*Review conducted as top-1% critical systems reviewer. Scores reflect professional-grade expectations for safety-critical manufacturing software.*
