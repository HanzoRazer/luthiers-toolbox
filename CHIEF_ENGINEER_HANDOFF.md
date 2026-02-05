# Luthier's ToolBox — Chief Engineer Handoff

**Classification:** Internal — Engineering Leadership
**Date:** 2026-02-05
**Prepared by:** Outgoing technical lead (via verified automated audit)
**Intended audience:** Incoming Chief Engineer + assigned remediation team
**Supporting artifacts:**
- `luthiers-toolbox-design-review.md` — Independent design review (scored 5.15/10 claimed; 4.7/10 corrected)
- `luthiers-toolbox-design-review-factcheck.md` — Verification of every quantitative claim in the review
- `REMEDIATION_PLAN.md` — Detailed technical implementation plan (6 phases, 20 work items)

---

## 1. Executive Summary

Luthier's ToolBox is a FastAPI + Vue 3 monorepo that generates CNC G-code for guitar manufacturing. The core domain logic — fret mathematics, chipload physics, multi-post G-code generation, and CNC safety gates — is sound engineering built by someone who actually builds guitars.

The codebase has a growth problem. An independent design review scored it 5.15/10. Our own verification found the review was **systematically generous** — the corrected score is **4.7/10**. Every aggregate metric the review undercounted favors the project: the real API surface is 46% larger, the exception handling problem is 2.3x worse, and the bare `except:` count the review praised as "only 1" is actually 97.

The system works. It generates valid G-code. But it has accumulated mass without pruning, and the governance infrastructure built to manage that mass has itself become a maintenance burden. The path to a shippable product is **subtraction, not addition**.

**The bottom line:** This project needs a disciplined cleanup to become the tool its domain expertise deserves. The remediation plan is 6 phases. Phases 0 and 1 are non-negotiable (dead code and safety). Phases 2-6 are where engineering judgment applies.

---

## 2. Verified Baseline — What You're Inheriting

These numbers are filesystem-verified, not estimated. Every figure was produced by direct `wc -l`, `grep -r`, or `find` commands against the current HEAD.

### 2.1 Scale

| Metric | Count | Context |
|--------|-------|---------|
| Python files | 1,358 | across `services/api/app/` and supporting scripts |
| Python LOC | 265,128 | production code (excludes tests) |
| TypeScript/Vue LOC | 146,183 | `packages/client/src/` |
| Total codebase | ~411,000 LOC | single-developer project |
| Test files | 262 | `services/api/tests/` |
| Test LOC | 45,141 | ~17% test-to-code ratio |

### 2.2 API Surface

| Metric | Count | Assessment |
|--------|-------|------------|
| Route decorators (`@router.get/post/...`) | 1,060 | Unusable surface for any consumer |
| Router registrations in `main.py` | 123 | Each wrapped in try/except |
| `try:` blocks in `main.py` | 47 | Silent degradation on import failure |
| Modules with routes | 33 | Spread across 199 router files |
| Legacy flat routers in `routers/` | 107 | Many duplicated by domain modules |

### 2.3 Exception Handling (the critical finding)

| Metric | Count | Severity |
|--------|-------|----------|
| `except Exception` blocks | 1,622 | High — masks bugs in safety paths |
| Bare `except:` blocks | 97 | Critical — catches SystemExit/KeyboardInterrupt |
| Safety-critical modules affected | `rmos/` (197), `cam/` (35), `saw_lab/` (32), `calculators/` (14) | These modules control CNC machinery |

### 2.4 Technical Debt Artifacts

| Artifact | Count/Size | Status |
|----------|-----------|--------|
| Backup files in VCS | 7 `.vue` + 2 `.py` + 1 `.bak` | Should not exist on main branch |
| Phase-numbered duplicates | `RiskDashboardCrossLab_Phase28_16.vue` (1,878 lines alongside 2,062-line original) | Dead weight |
| Archive directories | 5 (`__ARCHIVE__/`, `__REFERENCE__/`, `.archive_app_app_20251214/`, `docs/ARCHIVE/`, `server/`) | Committed development archaeology |
| Stale `client/` directory | 190 files | Duplicate of `packages/client/` (498 files) |
| Stale `streamlit_demo/` | 2,358-line `app.py` | Zero config references, duplicates Vue frontend |
| Docs directory | 685 .md files, 12 MB | Session logs, AI protocols, audit artifacts mixed with actual docs |
| README "100% Coverage" claims | 4 badges | Misleading — actual line coverage is likely <30% |

### 2.5 God-Object Files (top 5 each)

**Python (>500 line limit):**

| File | Lines |
|------|-------|
| `saw_lab/batch_router.py` | 2,724 |
| `instrument_geometry/body/detailed_outlines.py` | 2,088 |
| `rmos/runs_v2/api_runs.py` | 1,845 |
| `rmos/runs_v2/store.py` | 1,733 |
| `cam/rosette/pattern_generator.py` | 1,683 |
| *(25 more files exceed 500 lines)* | |

**Vue (>800 line limit):**

| File | Lines |
|------|-------|
| `ManufacturingCandidateList.vue` | 2,987 |
| `AdaptivePocketLab.vue` | 2,418 |
| `RiskDashboardCrossLab.vue` | 2,062 |
| `ScaleLengthDesigner.vue` | 1,955 |
| `DxfToGcodeView.vue` | 1,846 |
| *(20 more files exceed 800 lines)* | |

### 2.6 What's Actually Good

This is not a failing project. These strengths are real:

- **Domain modeling depth:** Fret slot calculations (Rule of 18 vs equal temperament), chipload physics, tool deflection analysis, saw kerf accounting — this is rare, hard-won domain knowledge.
- **Multi-post G-code:** GRBL, Mach4, LinuxCNC, PathPilot, MASSO. Machine-specific output, not generic G-code.
- **Safety architecture intent:** RMOS feasibility scoring, risk bucketing (GREEN/YELLOW/RED), replay gate policy, CamIntentV1 schema freeze. The *design* of the safety system is mature.
- **Contract system:** `contracts/` with versioned JSON schemas and SHA-256 checksums. Cross-repo validation with `tap_tone_pi`.
- **Active debt fighting:** January 2026 cleanup deleted 19 legacy routers and ~4,000 lines. Someone is aware of the problem.

---

## 3. Work Packages

Six phases, ordered by dependency and risk. Phases 0 and 1 are non-negotiable prerequisites. Phases 2-6 have defined entry/exit criteria.

### WP-0: Dead Code Purge

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — do first, blocks nothing |
| **Risk** | None |
| **Effort** | 1 engineer, small (single PR) |
| **Dependencies** | None |
| **Validates** | `git ls-files` shows zero backup/archive artifacts |

**Scope:** Delete 200+ tracked files that should never have been committed. Backup `.vue` files, `.bak` files, `__ARCHIVE__/`, `__REFERENCE__/`, stale `server/` directory, stale `client/` directory (after verifying `packages/client/` is canonical), `streamlit_demo/` (zero config references). Update `.gitignore` to prevent recurrence.

**Exit gate:** Zero results from `git ls-files | grep -iE 'backup|BACKUP|\.bak|__ARCHIVE__|__REFERENCE__|^server/|^client/|^streamlit_demo/'`

---

### WP-1: Exception Handling Hardening

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 — safety imperative |
| **Risk** | Medium (exposing latent bugs is the point) |
| **Effort** | 1-2 engineers, medium-large (97 bare except + 278 safety-critical except Exception) |
| **Dependencies** | None |
| **Validates** | Zero bare `except:` blocks; zero broad handlers in safety modules |

**Scope in three tiers:**

| Tier | Sites | Work |
|------|-------|------|
| 1A: Bare `except:` | 97 | Mechanical: replace with `except Exception` + logging. Every one is a bug. |
| 1B: Safety-critical `except Exception` | 278 (rmos: 197, cam: 35, saw_lab: 32, calculators: 14) | Replace with specific exception types. These modules control CNC machinery — a swallowed exception here can produce unsafe G-code. |
| 1C: All other `except Exception` | 1,344 | Iterative: triage per-module. API handlers can keep broad handlers with structured logging. Internal code should use specific types. |

**New artifact:** `@safety_critical` decorator (fail-closed, never swallows) applied to `compute_feasibility()`, G-code generation functions, feeds/speeds calculations.

**Exit gate:**
- `grep -rP '^\s*except\s*:' services/api/app/ | wc -l` returns 0
- All functions in `rmos/feasibility/`, `rmos/gates/`, `cam/` core generation, `calculators/feeds_speeds` decorated with `@safety_critical`
- CI check blocks new bare `except:` or `except Exception` in safety-critical paths

---

### WP-2: API Surface Reduction

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 — high impact across 4 scoring categories |
| **Risk** | Medium-High (must audit frontend before deleting routes) |
| **Effort** | 1-2 engineers, large |
| **Dependencies** | WP-0 complete (stale routers already removed) |
| **Validates** | Route count <300; main.py <200 lines |

**Scope:**

1. **Instrument** (week 1-2): Deploy `RouteUsageMiddleware` to log every route hit. Any route with zero hits after 2 weeks of normal use is a cull candidate.

2. **Classify** (week 3): Assign every route to a tier:
   - **Core** (~200): rmos, cam, calculators, art_studio — stable API, document
   - **Power** (~150): saw_lab, compare, vision — behind feature flag
   - **Internal** (~300): legacy routers, governance, ci — move to `/api/internal/` prefix
   - **Cull** (~400): _experimental, sandboxes, cost_attribution, redundant legacy — delete

3. **Refactor main.py** (week 4): Replace 47 try/except import blocks with declarative feature registry. Add `/api/features` endpoint.

4. **Consolidate legacy routers/** (week 4-5): The flat `routers/` directory (107 files, 435 routes) predates the domain-organized modules. Deduplicate against `rmos/`, `cam/`, `art_studio/`, etc. Target: ≤10 files remaining in `routers/`.

**Exit gate:**
- `grep -rc '@\w\+\.\(get\|post\|put\|delete\|patch\)' services/api/app/ | awk -F: '{s+=$2} END{print s}'` returns <300
- `wc -l services/api/app/main.py` returns <200
- `GET /api/features` returns JSON with enabled/failed status for all modules
- `ls services/api/app/routers/*.py | wc -l` returns ≤10

---

### WP-3: God-Object Decomposition

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 |
| **Risk** | Medium (refactoring large files needs test coverage) |
| **Effort** | 2 engineers, large (30 Python + 25 Vue files) |
| **Dependencies** | WP-2 complete (know which routers survive before splitting them) |
| **Validates** | No file exceeds size limit, or baseline-locked with ratchet |

**Scope:** Split all Python files >500 lines and all Vue files >800 lines. Detailed decomposition strategies for top 10 of each are in `REMEDIATION_PLAN.md` §3.1 and §3.2.

**Enforcement:** Add `ci/check_file_sizes.sh` to CI in baseline-ratchet mode (block new violations, allow existing until resolved).

**Exit gate:** CI check passes with zero new violations; baseline file shrinks monotonically.

---

### WP-4: Documentation Triage

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 (can run in parallel with WP-1) |
| **Risk** | None (docs don't affect runtime) |
| **Effort** | 1 engineer, small-medium |
| **Dependencies** | None |
| **Validates** | docs/ ≤50 files; README honest |

**Scope:**

| Category | Current Count | Action |
|----------|--------------|--------|
| Session logs | 6 | Move to `dev-journal` repo or delete |
| AI protocol docs (CBSP*) | 23 | Move to `dev-journal` repo or delete |
| Handoff/bundle docs | 61 | Move to `dev-journal` repo or delete |
| Audit/governance | 36 | Keep 5 essential, archive rest |
| ADRs | 4 | Keep all |
| docs/ARCHIVE/ | ~100+ | `git rm -r` |
| Remaining ~455 | — | Triage: keep ≤50 user/contributor-facing docs |

Create 10 essential documents (README, CONTRIBUTING, ARCHITECTURE, API_REFERENCE, DEPLOYMENT, SAFETY_MODEL, CAM_PIPELINE, RMOS_OVERVIEW, MACHINE_PROFILES, CHANGELOG).

Fix README: replace "100% Coverage" badges with actual `pytest --cov` numbers.

**Exit gate:** `find docs -name '*.md' | wc -l` returns ≤50; `grep -i '100.*coverage' README.md` returns 0.

---

### WP-5: Quick Cut Onboarding

| Attribute | Value |
|-----------|-------|
| **Priority** | P2 — highest user-facing impact |
| **Risk** | Low (additive, no existing code modified) |
| **Effort** | 1 frontend + 1 backend engineer, medium |
| **Dependencies** | None (uses existing API endpoints) |
| **Validates** | 3-screen workflow completes DXF→G-code |

**Scope:** Build a `QuickCutView.vue` — three screens (upload DXF, pick machine+material, preview+download G-code). No RMOS pipeline, no governance, no feasibility scoring. Uses 3-4 existing endpoints. Add Pro Mode toggle to hide advanced features from default navigation.

**Exit gate:** A person with no prior exposure to the system can go from DXF file to G-code download without encountering RMOS, feasibility scoring, or governance concepts.

---

### WP-6: Health and Observability

| Attribute | Value |
|-----------|-------|
| **Priority** | P2 |
| **Risk** | Low (additive) |
| **Effort** | 1 engineer, small |
| **Dependencies** | WP-2 (feature registry) |
| **Validates** | `/api/health/detailed` returns complete status |

**Scope:** Add `/api/health/detailed` endpoint reporting loaded/failed features, database status, uptime, version. Replace all silent `pass` blocks in main.py router registration with tracked failures.

**Exit gate:** `curl /api/health/detailed` returns JSON with all module statuses; zero silent `pass` blocks in main.py.

---

## 4. Dependency Graph

```
WP-0 (Dead Code)  ───────────────┐
   |                              |
   v                              |
WP-2 (API Reduction)             |
   |                              |
   v                              |
WP-3 (God-Object Decomposition)  |
   |                              |
   v                              |
WP-6 (Health/Observability)      |
                                  |
WP-1 (Exception Hardening) ──────┤  (independent, start immediately)
                                  |
WP-4 (Documentation) ────────────┤  (independent, start immediately)
                                  |
WP-5 (Quick Cut) ────────────────┘  (independent, start anytime)
```

**Three independent tracks can run in parallel:**
- Track A: WP-0 → WP-2 → WP-3 → WP-6 (the structural refactoring spine)
- Track B: WP-1 (safety hardening — can start day 1)
- Track C: WP-4 + WP-5 (documentation + onboarding — can start day 1)

---

## 5. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Exception hardening exposes latent bugs that break existing tests | High | Medium | Run full test suite after each batch of changes. Latent bugs surfacing is the *desired outcome* — fix them, don't re-suppress them. |
| R2 | Route culling breaks frontend features | Medium | High | Instrument usage BEFORE culling. Cross-reference every deleted route against `packages/client/src/` imports. Run full frontend build after each batch. |
| R3 | God-object decomposition introduces regressions | Medium | Medium | Only decompose files with existing test coverage. Add tests for uncovered files before splitting. |
| R4 | `client/` directory deletion breaks something not in `packages/client/` | Low | High | Check docker-compose.yml, pnpm-workspace.yaml, Makefile, CI workflows before deleting. The `packages/client/` is confirmed canonical by all config files. |
| R5 | Documentation triage accidentally deletes something an external consumer references | Low | Medium | Check `tap_tone_pi` and `sg-spec` repos for cross-references before deleting any doc. |
| R6 | Team unfamiliar with domain (fret math, chipload physics) breaks safety logic during refactor | Medium | Critical | WP-1 and WP-3 work on safety modules requires domain review. The `@safety_critical` decorator provides a guardrail but doesn't replace understanding. |

---

## 6. Projected Impact

| Category | Current (corrected) | After All WPs | Primary Driver |
|----------|-------------------|---------------|----------------|
| Purpose Clarity | 5/10 | 7/10 | Quick Cut mode, honest README |
| User Fit | 4/10 | 6/10 | Quick Cut flow, Pro Mode toggle |
| Usability | 3/10 | 6/10 | 1,060→<300 routes, feature flags, `/api/features` |
| Reliability | 4/10 | 6/10 | Exception hardening, health endpoint |
| Maintainability | 3/10 | 6/10 | Dead code purge, god-object split, docs triage |
| Cost / Efficiency | 5/10 | 6/10 | Streamlit deletion, lazy loading |
| Safety | 5/10 (corrected from 7) | 8/10 | `@safety_critical`, 97 bare except eliminated, fail-closed |
| Scalability | 5/10 | 5/10 | (No changes — appropriate for current stage) |
| Aesthetics | 4/10 | 5/10 | Backup deletion, component decomposition |
| **Weighted Average** | **4.7/10** | **6.3/10** | |

---

## 7. Critical Questions for the Receiving Team

These must be answered before or during Phase execution. Unanswered questions represent unresolved risk.

### Architecture & Scope

**Q1. What is the shipped product boundary?**
The codebase contains a CNC G-code platform, a Smart Guitar IoT backend, an acoustic analysis platform, a rosette art studio, a financial calculator, a materials database, and AI advisory features. Which of these are in the shipped product vs. which are R&D experiments? The API cull (WP-2) cannot proceed without a definitive answer. If the answer is "all of it," the 1,060-route API surface is intentional and the reduction target changes.

**Q2. Is there a second frontend consumer of the API?**
We found 1,060 route decorators but only 29 client-side routes. Either ~970 routes are unused, or there is a consumer we haven't identified (mobile app, external integration, CLI tool, Streamlit demo being used somewhere). Confirm all API consumers before culling routes.

**Q3. Is `client/` vs `packages/client/` fully understood?**
The root `client/` directory (190 files) appears to be a stale pre-monorepo copy of `packages/client/` (498 files). All config files point to `packages/client/`. But: does any deployment target, CI workflow, or external tool reference `client/` directly? A broken deployment from deleting the wrong directory is a P0 incident.

### Safety & CNC

**Q4. Has unsafe G-code ever been generated in production?**
The exception handling audit reveals 278 broad `except Exception` blocks in safety-critical paths (RMOS feasibility, CAM, calculators). If a safety gate throws an unexpected error and gets silently caught, the system could return GREEN for a RED operation. Has this ever happened? Are there incident reports? This determines whether WP-1 is "fix before shipping" or "fix before using."

**Q5. Is simulation mandatory before G-code export?**
The review noted G-code simulation exists at `/api/cam/sim` but couldn't determine if it's enforced. If a user can skip simulation and send unvalidated G-code to a CNC machine, that's a safety gap. What is the current enforcement policy? Should WP-1 add a mandatory simulation gate?

**Q6. Who validates feeds-and-speeds correctness?**
The chipload physics, tool deflection, and material property calculations are genuinely sophisticated. But CNC feeds/speeds that are mathematically correct can still be operationally dangerous for specific machines (spindle runout, rigidity, coolant). Is there a domain expert who has validated the output against real cuts on real machines? If not, the safety score should be lower than 5/10.

### Operations & Deployment

**Q7. What is the actual test coverage percentage?**
The README claims "100% Backend Coverage," "100% Frontend Coverage," and "100% Test Coverage." The actual test/code ratio is ~17% by LOC. Running `pytest --cov` will produce the real number. What is it? This determines whether WP-3 (god-object decomposition) can proceed safely or needs test backfill first.

**Q8. What is the production deployment target?**
Railway deployment config exists. Docker Compose exists. Are users running this locally on a workshop PC, on a Raspberry Pi, on Railway, or somewhere else? The answer affects WP-2 (API reduction — can we lazy-load?), WP-6 (health endpoint — who reads it?), and general performance requirements.

**Q9. How many active users does this system have?**
If the answer is zero external users, the remediation can be aggressive (break APIs freely). If there are users, we need deprecation periods and migration guides. The 2-week route instrumentation (WP-2.1) will answer this empirically, but knowing the expected answer upfront prevents surprises.

### Process & Resources

**Q10. Is there a staging environment?**
The remediation plan involves deleting 200+ files, restructuring 1,297-line main.py, splitting 55 god-object files, and culling ~700 API routes. If there's no staging environment to validate against before merging to main, the risk of each WP increases significantly. What is the current deployment pipeline?

**Q11. Does the team have CNC/lutherie domain knowledge?**
WP-1 (exception hardening) in safety-critical paths and WP-3 (god-object decomposition) in `cam/`, `calculators/`, and `rmos/feasibility/` require understanding *what the code does physically*. A software engineer who doesn't know what chipload means could refactor `feeds_speeds.py` into clean code that generates dangerous G-code. Is domain review available for safety-critical PRs?

**Q12. What is the rollback strategy?**
Each WP should be a discrete set of commits (or a single squash-merge PR) with a tagged pre-state. But: is `main` protected? Are there branch protection rules? Can a bad merge be reverted within minutes, or does it require a manual process? The answer determines how aggressively we batch changes.

**Q13. Are there cross-repo consumers that depend on specific API shapes?**
We confirmed `tap_tone_pi` consumes ToolBox via `tap_tone.ingest.toolbox`. The `sg-spec` repo provides contract schemas. Are there other repos (string_master, sg-coach, sg-ai, sg-agentd) that import from or call into ToolBox? Breaking their integration during WP-2 is a blocking incident for those teams.

### Prioritization

**Q14. What is the ship date or milestone this remediation is targeting?**
The 6 WPs can be executed in different configurations depending on urgency:
- **"Ship in 2 weeks"**: WP-0 + WP-1 Tier 1A only + WP-4 (README fix only). Minimum viable cleanup.
- **"Ship in 6 weeks"**: WP-0 through WP-2. Structural cleanup complete.
- **"Ship in 12 weeks"**: All 6 WPs. Full remediation.
Which configuration matches the business timeline?

**Q15. Is the score target 6.3/10 (plan outcome) or higher?**
The plan as written targets 6.3/10 weighted. Reaching 7.0+ would require additional work not in this plan: design system for UI consistency, Repository pattern for storage abstraction, Storybook for component documentation, and comprehensive integration test suite. Should these be scoped into a Phase 2 plan?

---

## 8. Handoff Checklist

Before the receiving team begins work:

- [x] All 15 questions in Section 7 have initial answers — see Section 10 (5 RESOLVED, 10 OPEN)
- [ ] 10 OPEN questions resolved with product owner (see Section 10 resolution table)
- [ ] `pytest` runs green on current HEAD (establish baseline)
- [ ] `npm run build` succeeds on current HEAD (establish baseline)
- [ ] Team has read `REMEDIATION_PLAN.md` (detailed technical implementation)
- [ ] Team has read `luthiers-toolbox-design-review-factcheck.md` (verified numbers)
- [ ] Staging environment is available (or risk acceptance for direct-to-main)
- [x] Domain expert identified for safety-critical PR reviews (Q6, Q11) — product owner is domain expert
- [x] Cross-repo consumers identified and notified (Q13) — ToolBox is consumer, not provider; low risk
- [ ] Ship date / milestone confirmed (Q14) — OPEN
- [ ] Docker client Dockerfile updated from `client/` to `packages/client/` (required before WP-0)

---

## 9. Document Index

| File | Purpose | Read Order |
|------|---------|------------|
| `CHIEF_ENGINEER_HANDOFF.md` | This document. Start here. | 1 |
| `luthiers-toolbox-design-review.md` | Independent design review with scoring | 2 |
| `luthiers-toolbox-design-review-factcheck.md` | Verification of review claims (every number checked) | 3 |
| `REMEDIATION_PLAN.md` | Detailed implementation plan with code examples | 4 |

---

## 10. Q&A Response Log (from Product Owner, 2026-02-05)

Answers provided by the project owner. Questions marked **RESOLVED** have actionable answers. Questions marked **OPEN** require the owner's direct input before the receiving team can execute the affected work package.

### Architecture & Scope

**Q1. What is the shipped product boundary?** — OPEN

*Owner assessment:* Core shipped product is CNC G-code generation for guitar lutherie. Secondary systems identified:
- Smart Guitar IoT backend (depends on `sg-spec` from GitHub)
- Acoustic analysis integration (`tap_tone_pi` artifacts)
- Rosette Art Studio
- Blueprint AI reader

**Action required:** Owner must declare which secondaries are in-scope vs. R&D. This is a **gate for WP-2** (API reduction) — the cull target changes if "all of it" is the answer.

---

**Q2. Is there a second frontend consumer of the API?** — OPEN

*Owner assessment:* Three known entry points:
- `packages/client/` (Vue 3 SPA) — canonical frontend
- `client/` (190 files) — stale pre-monorepo duplicate
- `streamlit_demo/` (2,358-line app.py) — separate entry point, zero config references

**Action required:** Owner must confirm: (a) Is Streamlit demo actively used by anyone? (b) Is there a mobile app, CLI tool, or external integration consuming the API? If no to both, WP-0 deletes Streamlit and the stale `client/`.

---

**Q3. Is `client/` vs `packages/client/` fully understood?** — RESOLVED

*Owner assessment:* `client/` is a stale pre-monorepo copy. `pnpm-workspace.yaml` only references `packages/*`. Docker client Dockerfile references `client/` (legacy path).

**Resolution:** Verify no CI workflow or deployment script references `client/` directly, then delete in WP-0. The Docker client Dockerfile at `docker/client/Dockerfile` copies from `client/` — this must be updated to `packages/client/` before deletion.

---

### Safety & CNC

**Q4. Has unsafe G-code ever been generated in production?** — OPEN

*Owner assessment:* No incident reports found in the codebase. RMOS feasibility scoring with risk bucketing (GREEN/YELLOW/RED) exists. However, 97 bare `except:` blocks and 1,622 `except Exception` blocks could theoretically mask safety gate failures.

**Action required:** Owner must confirm whether generated G-code has been run on real machines and whether unexpected behavior was ever observed. This determines whether WP-1 is "fix before shipping" or "fix before anyone uses it."

---

**Q5. Is simulation mandatory before G-code export?** — RESOLVED

*Owner assessment:* Simulation exists at `/api/cam/sim` but there is no enforcement gate blocking export without simulation. Users can skip straight to download.

**Resolution:** Simulation is available but not mandatory. The `@safety_critical` decorator proposed in WP-1 could add a mandatory simulation flag. Receiving team should propose a simulation gate in WP-1 scope.

---

**Q6. Who validates feeds-and-speeds correctness?** — OPEN

*Owner assessment:* The codebase has sophisticated chipload physics, tool deflection, and material property calculations. The owner is the domain expert (single-developer project, builds guitars).

**Action required:** Owner must confirm whether these calculations have been validated against real cuts on real machines. Mathematical correctness does not guarantee operational safety (spindle runout, rigidity, coolant vary by machine).

---

### Operations & Deployment

**Q7. What is the actual test coverage percentage?** — OPEN

*Owner assessment:* `coverage.json` exists but is empty. 262 test files with ~45K LOC against ~265K production Python LOC. README claims "100% Coverage" — confirmed misleading.

**Action required:** Run `cd services/api && pytest --cov=app --cov-report=term-missing` and record the actual number. This determines whether WP-3 (god-object decomposition) can proceed safely or needs test backfill first. Can be done immediately after Docker restart.

---

**Q8. What is the production deployment target?** — RESOLVED

*Owner assessment:* Two deployment paths confirmed:
- Railway cloud (`railway.toml`, `railway.json` exist)
- Local Docker (`docker-compose.yml`, `docker-compose.production.yml`)

**Resolution:** Primary targets are Railway and local Docker. No Raspberry Pi or bare-metal deployment. This confirms lazy-loading (WP-2) is feasible and the health endpoint (WP-6) should target both environments.

---

**Q9. How many active users does this system have?** — OPEN

*Owner assessment:* Cannot determine from codebase alone. The 2-week route instrumentation (WP-2.1) would answer this empirically.

**Action required:** Owner must confirm whether this is deployed with external users or still in development/private use. If zero external users, the remediation can be aggressive (break APIs freely, no deprecation periods needed).

---

### Process & Resources

**Q10. Is there a staging environment?** — OPEN

*Owner assessment:* No explicit staging configuration found. `docker-compose.production.yml` exists but no staging equivalent.

**Action required:** Owner must confirm whether a staging environment exists or if changes go direct to main/production. Without staging, each WP carries higher risk. The team may need to create a staging branch or environment before beginning WP-2.

---

**Q11. Does the team have CNC/lutherie domain knowledge?** — RESOLVED

*Owner assessment:* Yes. Single-developer project — the owner is the domain expert with deep manufacturing knowledge (fret math, chipload physics, multi-post G-code).

**Resolution:** The owner must review all PRs touching safety-critical paths (feasibility scoring, G-code generation, feeds/speeds). No one else has the domain knowledge to validate these changes. This is a **bottleneck risk** for WP-1 and WP-3 in safety modules.

---

**Q12. What is the rollback strategy?** — OPEN

*Owner assessment:* Git-based. No explicit rollback documentation found.

**Action required:** Owner must confirm whether `main` has branch protection rules and whether a bad merge can be reverted within minutes. If no protections exist, the receiving team should add branch protection before beginning WP-2.

---

**Q13. Are there cross-repo consumers that depend on specific API shapes?** — RESOLVED

*Owner assessment:*
- `sg-spec` — ToolBox depends ON it (not reverse)
- `tap_tone_pi` — ToolBox consumes artifacts FROM it via RMOS acoustics import
- No evidence of other repos importing FROM ToolBox

**Resolution:** Cross-repo risk is low. ToolBox is a consumer, not a provider. WP-2 route culling can proceed without notifying external teams. The `tap_tone_pi` integration path should be verified after WP-2 completes.

---

### Prioritization

**Q14. What is the ship date or milestone this remediation is targeting?** — OPEN

*Owner presented three options:*
- **2 weeks:** WP-0 + partial WP-1 + README fix only
- **6 weeks:** WP-0 through WP-2 (structural cleanup complete)
- **12 weeks:** All 6 WPs (full remediation)

**Action required:** Owner must select a timeline. This determines team size and which WPs to execute.

---

**Q15. Is the score target 6.3/10 (plan outcome) or higher?** — OPEN

*Owner assessment:* 6.3/10 is the plan's projected outcome. Reaching 7.0+ would require scoping additional work: design system, Storybook, Repository pattern, integration test suite.

**Action required:** Owner must confirm whether 6.3/10 is acceptable or if a Phase 2 plan targeting 7.0+ should be scoped.

---

### Resolution Summary

| # | Question | Status | Blocks WP |
|---|----------|--------|-----------|
| Q1 | Shipped product boundary | **OPEN** | WP-2 |
| Q2 | Second frontend consumer | **OPEN** | WP-0, WP-2 |
| Q3 | `client/` vs `packages/client/` | RESOLVED | — |
| Q4 | Unsafe G-code ever generated | **OPEN** | WP-1 priority |
| Q5 | Simulation mandatory | RESOLVED | — |
| Q6 | Feeds/speeds validated on real cuts | **OPEN** | WP-1 safety scope |
| Q7 | Actual test coverage | **OPEN** | WP-3 |
| Q8 | Production deployment target | RESOLVED | — |
| Q9 | Active users | **OPEN** | WP-2 aggressiveness |
| Q10 | Staging environment | **OPEN** | All WPs (risk level) |
| Q11 | Domain knowledge | RESOLVED | — |
| Q12 | Rollback strategy | **OPEN** | All WPs (risk level) |
| Q13 | Cross-repo consumers | RESOLVED | — |
| Q14 | Ship date | **OPEN** | All WPs (scope) |
| Q15 | Score target | **OPEN** | Phase 2 scoping |

**5 of 15 resolved. 10 require the product owner's direct answer.**

The receiving team can begin **WP-0** (dead code purge) and **WP-1 Tier 1A** (bare `except:` elimination) immediately — these are blocked by zero open questions. All other WPs have at least one open dependency.

---

*This handoff is designed to be self-contained. A competent engineering team should be able to read these four documents, review the Q&A log, resolve the 10 open questions with the product owner, and begin execution without further input from the original developer.*
