# CAM Module Readiness Scorecard

**Date:** 2026-05-09  
**Status:** ACTIVE SCORING MODEL  
**Scope:** Candidate CAM module evaluation

---

## Purpose

This document defines the weighted scoring system for evaluating CAM module readiness for promotion. Total score is 0-100.

---

## Scoring Criteria

| Criteria | Weight | Description |
|----------|--------|-------------|
| Coordinate Documentation | 15 | Origin, axes, Z-zero semantics documented |
| Tests | 20 | Dedicated tests exist and pass |
| Safety Gates | 20 | @safety_critical or explicit validation |
| Preview Support | 15 | JSON/SVG preview path available |
| Provenance Clarity | 10 | Clear route-to-generator path |
| Export Separation | 20 | Postprocessor boundary respected |

**Total: 100 points**

---

## Scoring Rubric

### Coordinate Documentation (15 points)

| Score | Criteria |
|-------|----------|
| 15 | Full documentation: origin, axes, Z-zero, units in docstring or dedicated doc |
| 10 | Partial documentation: some parameters documented but incomplete |
| 5 | Implicit: coordinate handling exists but undocumented |
| 0 | None: no coordinate documentation |

### Tests (20 points)

| Score | Criteria |
|-------|----------|
| 20 | Comprehensive: dedicated test file, boundary conditions, gate evaluation |
| 15 | Good: dedicated tests covering happy path and some edge cases |
| 10 | Smoke: basic smoke tests exist and pass |
| 5 | Incidental: tested only as part of integration tests |
| 0 | None: no tests |

### Safety Gates (20 points)

| Score | Criteria |
|-------|----------|
| 20 | Full: @safety_critical + structured validation + GREEN/YELLOW/RED gates |
| 15 | Good: @safety_critical + input validation |
| 10 | Basic: @safety_critical decorator present |
| 5 | Partial: some validation but no decorator |
| 0 | None: no safety measures |

### Preview Support (15 points)

| Score | Criteria |
|-------|----------|
| 15 | Full: dedicated preview endpoint returning JSON/SVG |
| 10 | Good: preview data available but not via dedicated endpoint |
| 5 | Partial: data could be visualized but no preview path |
| 0 | None: no preview capability |

### Provenance Clarity (10 points)

| Score | Criteria |
|-------|----------|
| 10 | Full: clear route → service → generator chain documented |
| 7 | Good: route exists and generator is identifiable |
| 4 | Partial: generator exists but route path unclear |
| 0 | None: no clear provenance |

### Export Separation (20 points)

| Score | Criteria |
|-------|----------|
| 20 | Full: uses postprocessor interface, machine profile abstraction |
| 15 | Good: postprocessor-ready but not fully integrated |
| 10 | Basic: G-code generation separated from business logic |
| 5 | Partial: some separation but tightly coupled |
| 0 | None: G-code generation embedded in business logic |

---

## Informational Sub-Metrics (Non-Scored)

These metrics provide additional context but do not affect the readiness score:

### RMOS Readiness

| Level | Description |
|-------|-------------|
| High | Uses run_id, attachment persistence, SHA hashing |
| Medium | Some RMOS integration but incomplete |
| Low | No RMOS integration |

### Frontend/API Normalization Readiness

| Level | Description |
|-------|-------------|
| High | Standard request/response schemas, TypeScript SDK integration |
| Medium | Pydantic schemas exist but frontend not wired |
| Low | Ad-hoc schemas or none |

### Route Provenance Maturity

| Level | Description |
|-------|-------------|
| High | Registered in router manifest, documented in handoffs |
| Medium | Route exists but not in manifest |
| Low | No route or route unclear |

---

## Promotion Thresholds

| Target Status | Minimum Score | Additional Requirements |
|---------------|---------------|------------------------|
| GOVERNED PREVIEW | 60 | All scored criteria ≥ 5 |
| GOVERNED EXPORT | 75 | Export separation ≥ 15, safety gates ≥ 15 |
| MACHINE OUTPUT | 90 | All criteria ≥ 15, RMOS readiness = High |

---

## Evaluation Template

```markdown
## Module: [name]

**Category:** [geometry_generator | preview_generator | export_generator | ...]
**Evaluated:** [date]

### Scored Criteria

| Criteria | Score | Evidence |
|----------|-------|----------|
| Coordinate Documentation | /15 | |
| Tests | /20 | |
| Safety Gates | /20 | |
| Preview Support | /15 | |
| Provenance Clarity | /10 | |
| Export Separation | /20 | |

**Total: /100**

### Informational Metrics

| Metric | Level | Notes |
|--------|-------|-------|
| RMOS Readiness | | |
| Frontend/API Readiness | | |
| Route Provenance Maturity | | |

### Blocking Issues

- [ ] Issue 1
- [ ] Issue 2

### Promotion Target

[governed_preview | governed_export | machine_output]

### Recommended Actions

1. Action 1
2. Action 2
```

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PROMOTION_FRAMEWORK.md` | Promotion stages |
| `CAM_PROMOTION_CHECKLIST.md` | Required evidence |
| `CAM_CANDIDATE_EVALUATION_2026-05-09.md` | Applied evaluations |

---

*Scorecard established: 2026-05-09*
