# Production Shop — Safety Case

> **Last Updated:** 2026-03-19
> **Status:** ACTIVE
> **Review Cycle:** Quarterly or after safety-critical changes

## Scope

This safety case covers software-layer safety controls in the Production Shop platform.

**This is NOT a machine-integrated safety system.**

The platform is operator-assistive, not authoritative. All G-code must be reviewed by a qualified operator before execution.

---

## Hazard Analysis

| Hazard | Likelihood | Severity | Control |
|--------|-----------|----------|---------|
| Tool depth exceeds stock | Medium | High | preflight_gate depth check |
| Feed rate exceeds machine envelope | Medium | High | BCamMachineSpec feed limits |
| Tool radius violates minimum feature | Low | Medium | feasibility engine constraint |
| Missing stock dimensions | High | High | preflight blocks on unknown stock |
| Incorrect scale length in fret calc | Low | High | golden test fixtures |
| Sagitta formula error in fret slots | Low | High | fixed 2024-03, tested |
| Break angle below Carruth minimum | Medium | Medium | Carruth gate RED <4° |
| CAM job without machine profile | Medium | High | preflight requires machine_id |

---

## Control Mapping

| Control | Implementation | Tests |
|---------|---------------|-------|
| Preflight gate | `app/safety/cnc_preflight.py` | 99% coverage |
| RMOS feasibility | `app/rmos/feasibility/engine.py` | 97% coverage |
| Saw CAM guard | `app/rmos/saw_cam_guard.py` | 100% coverage |
| Machine spec validation | `app/cam/machines.py` | `test_machines.py` |
| Break angle gate | `app/calculators/bridge_break_angle.py` | 15 tests |
| Constraint search | `app/rmos/services/constraint_search.py` | 100% coverage |

---

## Residual Risk Register

| Risk | Residual Level | Acceptance Rationale |
|------|----------------|---------------------|
| Software-layer only | Medium | Operator review required before execution |
| Single-instance, no audit log | Low | Single shop context, operator is accountable |
| Experimental modules near core | Low | `_experimental/` graduated or isolated |

---

## Validation Evidence

- **3,834** automated tests passing
- **96.59%** coverage on safety-critical paths
- Safety-critical paths: `preflight`, `RMOS`, `saw_cam_guard`
- Golden test fixtures for G-code output
- All broad `except` blocks audited (WP-1 complete)
- `@safety_critical` decorator applied to G-code generation, feasibility scoring

---

## Operator Responsibilities

**The platform does NOT replace operator judgment.**

Before executing any G-code output:

1. Review preflight report
2. Verify stock dimensions match job
3. Verify tool selection
4. Verify machine profile is current
5. Run dry pass if unfamiliar with operation

---

## Limitations

- No real-time machine feedback
- No spindle/axis encoder integration
- G-code correctness is software-validated only
- Material properties are user-supplied
- Edge cases in novel geometry may not be caught

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-19 | Initial safety case created | Claude Code |

---

*This document addresses red-team review finding: safety logic exists but needs documented validation evidence and residual risk register.*
