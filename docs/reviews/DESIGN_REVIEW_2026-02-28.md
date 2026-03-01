# Critical Systems Design Review: luthiers-toolbox

**Review Date:** 2026-02-28
**Reviewer:** Critical Systems Design Reviewer (Top 1%)
**Methodology:** Source code analysis, documentation review, architecture assessment

---

## Stated Assumptions

1. **Domain**: This is a CNC manufacturing control system for guitar lutherie, generating G-code that drives physical cutting machines
2. **Criticality Level**: Medium-high — incorrect outputs can destroy workpieces ($50-$5000), damage tools ($20-$500), and potentially cause machine damage or operator injury
3. **User Profile**: Luthiers with varying CNC experience, from hobbyists to professionals
4. **Deployment Model**: Self-hosted or cloud-hosted FastAPI backend + Vue frontend
5. **Regulatory Environment**: No explicit ISO/CE compliance mentioned; assumed hobbyist/small-shop use
6. **Scale**: Single-user to small-team (not enterprise multi-tenant)
7. **Maturity**: Active development, post-MVP, pre-production hardening phase

---

## Evaluation

### 1. Purpose Clarity
**Score: 8/10**

**Justification:**
- README clearly states "CNC guitar lutherie platform with parametric design tools, CAM workflows, and manufacturing safety controls"
- Feature catalog endpoint (`/api/features/catalog`) documents capabilities
- RMOS (Run Manufacturing Operations System) concept is well-defined
- Subsystem boundaries are explicit (Art Studio, Saw Lab, Adaptive Pocketing)

**Weaknesses:**
- No explicit user stories or persona documentation found
- Mission-critical vs. nice-to-have features not differentiated
- "Beta" vs "Stable" distinction unclear in practice

**Improvements:**
1. Add `docs/USER_PERSONAS.md` defining target users and their workflows
2. Create a feature maturity matrix with clear graduation criteria
3. Add `docs/MISSION_STATEMENT.md` with non-goals explicitly stated

---

### 2. User Fit
**Score: 6/10**

**Justification:**
- Domain-specific calculations (fret slots, scale length) show deep lutherie understanding
- Multi-post support (GRBL, Mach4, LinuxCNC, PathPilot, MASSO) covers hobby to prosumer machines
- Risk levels (GREEN/YELLOW/RED) provide clear operator guidance

**Weaknesses:**
- 530 Vue components suggests UI complexity that may overwhelm novice users
- No progressive disclosure pattern evident — all features appear equally prominent
- No onboarding flow or guided workflow documentation
- Error messages are technical (rule IDs like "F021") rather than user-friendly

**Improvements:**
1. Implement a "Guided Mode" that walks through DXF → G-code with guardrails
2. Add plain-English explanations alongside rule IDs: "F021: Your cut depth is too aggressive for this tool"
3. Create role-based views: "Beginner" hides advanced CAM parameters
4. Add contextual help tooltips referencing `docs/` content

---

### 3. Usability
**Score: 5/10**

**Justification:**
- API documentation via Swagger is available
- Quick-start examples in README show key workflows
- 76 routers with 552 endpoints indicates comprehensive API surface

**Weaknesses:**
- 552 endpoints is overwhelming — discovery is difficult
- No API versioning evident in routes (`/api/v1/` pattern not used)
- Frontend appears to be a direct mirror of backend complexity
- No batch operation support evident for multi-file workflows
- `STUB_ANALYSIS` documents show 37 unimplemented endpoints still exposed

**Improvements:**
1. Implement API versioning: `/api/v2/cam/pocket/plan`
2. Create a "Golden Path" SDK with 10-15 key operations
3. Add batch endpoints: `/api/cam/batch/process` for multi-DXF workflows
4. Remove or gate stub endpoints behind feature flags
5. Add request/response examples to all Swagger endpoints

---

### 4. Reliability
**Score: 7/10**

**Justification:**
- 746 tests passing (31% coverage)
- 53 CI workflows provide multi-layer verification
- `@safety_critical` decorator enforces fail-open → fail-closed behavior
- Immutable audit trail for manufacturing runs
- Router registry with health checks at startup

**Weaknesses:**
- 31% test coverage is low for safety-critical code
- No chaos/fault injection testing evident
- No circuit breaker pattern for external service failures
- No explicit timeout handling in many endpoints
- Coverage report shows `relief_kernels.py` at 6% — core CAM code undertested

**Improvements:**
1. Target 80%+ coverage on `app/rmos/`, `app/safety/`, `app/cam/` modules
2. Add integration tests that verify G-code output against known-good fixtures
3. Implement request timeout middleware (max 30s for CAM operations)
4. Add retry logic with exponential backoff for transient failures
5. Create `tests/chaos/` for deliberate failure injection

---

### 5. Manufacturability/Maintainability
**Score: 7/10**

**Justification:**
- Router registry pattern (`ROUTER_MANIFEST`) enables modular loading
- Boundary enforcement (`check_boundary_imports.py`, fence baselines)
- Technical debt tracking with ratchet pattern (endpoints can only decrease)
- Dead code recovery process documented and executed
- 30+ documentation files in `docs/`

**Weaknesses:**
- 85,000 lines of Python in a monolithic `app/` directory
- Some files exceed 500 lines (complexity hotspots)
- Two `safety_critical` implementations exist (`app/core/safety.py` and `app/safety/__init__.py`)
- No explicit module ownership (CODEOWNERS is sparse)
- Circular import issues required manual fixes

**Improvements:**
1. Split `app/` into bounded contexts: `app/cam/`, `app/art/`, `app/rmos/` as separate packages
2. Consolidate duplicate implementations (e.g., `safety_critical`)
3. Add complexity limits to CI: fail on >300 line files, >20 cyclomatic complexity
4. Expand CODEOWNERS to require domain expert review
5. Add architecture decision records (ADRs) for major choices

---

### 6. Cost
**Score: 7/10**

**Justification:**
- MIT license — no licensing cost
- Self-hostable on commodity hardware
- Railway deployment configured for cloud option
- No external paid API dependencies evident (AI features are optional)

**Weaknesses:**
- 53 CI workflows likely incur significant GitHub Actions minutes
- Docker compose includes multiple services — resource overhead unclear
- No resource consumption benchmarks documented
- No cost-per-operation metrics for cloud deployment

**Improvements:**
1. Add `docs/RESOURCE_REQUIREMENTS.md` with CPU/RAM/disk benchmarks
2. Consolidate CI workflows — 53 is excessive; target 15-20
3. Add cost estimation for cloud deployment ($/month at X operations)
4. Profile memory usage of key endpoints under load

---

### 7. Safety
**Score: 8/10**

**Justification:**
- 22 feasibility rules with explicit RED (blocking) and YELLOW (warning) levels
- Adversarial detection rules (F020-F029) block dangerous parameters
- `@safety_critical` decorator prevents silent exception swallowing
- Risk-based gating: RED operations are blocked, not just warned
- Override mechanism requires explicit acknowledgment and audit trail
- Material hardness, tool deflection, thermal risk all considered

**Weaknesses:**
- No hardware interlock integration (E-stop awareness)
- No real-time machine feedback loop — open-loop G-code generation
- No explicit consideration of electrical/fire safety
- Validation protocol referenced but file not found
- No penetration testing or security audit documented

**Improvements:**
1. Add `docs/SAFETY_LIMITATIONS.md` explicitly stating what the system does NOT protect against
2. Implement G-code simulation/verification before download
3. Add checksums to G-code output for integrity verification
4. Consider signed G-code for traceability
5. Document emergency procedures if generated G-code causes machine fault

---

### 8. Scalability
**Score: 5/10**

**Justification:**
- Stateless API design allows horizontal scaling
- SQLite-based stores are mentioned (portable, low-overhead)
- Docker support enables containerized deployment

**Weaknesses:**
- SQLite does not scale horizontally
- No caching layer evident (Redis, Memcached)
- No queue system for long-running CAM operations
- In-memory job stores (`_batch_jobs: Dict` in `photo_batch_router.py`)
- No rate limiting or request throttling
- 552 endpoints load on every request (no lazy loading)

**Improvements:**
1. Add Redis for session/cache and Celery for async CAM jobs
2. Implement database abstraction to swap SQLite → PostgreSQL
3. Add request rate limiting (100 req/min per IP)
4. Lazy-load router modules on first access
5. Add horizontal scaling documentation with load balancer config

---

### 9. Aesthetics
**Score: 6/10**

**Justification:**
- Code organization follows reasonable patterns
- Consistent naming conventions (snake_case Python, kebab-case routes)
- Swagger UI provides visual API exploration
- Badge generation for CI status

**Weaknesses:**
- 530 Vue components suggests potential UI inconsistency
- No design system or component library documented
- Frontend screenshots not in README
- No dark mode mentioned despite being standard UX

**Improvements:**
1. Add screenshots/GIFs to README showing key workflows
2. Document UI component library (if exists) or create one
3. Add Storybook for Vue component documentation
4. Implement consistent error/success toast patterns

---

## Summary Scorecard

| Category | Score | Priority |
|----------|-------|----------|
| Purpose Clarity | 8/10 | Low |
| User Fit | 6/10 | High |
| Usability | 5/10 | High |
| Reliability | 7/10 | Medium |
| Maintainability | 7/10 | Medium |
| Cost | 7/10 | Low |
| **Safety** | **8/10** | **Critical** |
| Scalability | 5/10 | Medium |
| Aesthetics | 6/10 | Low |

**Overall: 6.6/10**

---

## Top 5 Critical Improvements (Ranked)

1. **Increase test coverage to 80%+ on safety-critical paths** — Current 31% is unacceptable for code that generates physical machine instructions

2. **Add G-code simulation/verification layer** — Users should see simulated toolpaths before downloading G-code

3. **Simplify user experience with guided workflows** — Progressive disclosure, beginner mode, contextual help

4. **Document safety limitations explicitly** — What the system does NOT protect against (E-stop, electrical, etc.)

5. **Add async job queue for CAM operations** — In-memory dicts don't survive restarts; long operations block requests

---

## Codebase Statistics (at review time)

| Metric | Value |
|--------|-------|
| Python LOC | ~85,000 |
| Vue Components | 530 |
| API Routers | 76 |
| API Endpoints | 552 |
| Tests | 746 passing |
| Test Coverage | 31% |
| CI Workflows | 53 |
| Feasibility Rules | 22 |
| Documentation Files | 30+ |
