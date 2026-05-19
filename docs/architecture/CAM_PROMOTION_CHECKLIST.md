# CAM Promotion Checklist

**Date:** 2026-05-09  
**Status:** ACTIVE CHECKLIST  
**Scope:** Required evidence for CAM module promotion

---

## Purpose

This document provides checklists for each promotion stage. All items must be verified before promotion.

---

## CANDIDATE → GOVERNED PREVIEW

### Documentation

- [ ] Coordinate system documented in module docstring
- [ ] Origin point specified (e.g., "workpiece center", "stock corner")
- [ ] Z-zero semantics documented (e.g., "top of stock", "spoilboard")
- [ ] Units documented (mm expected)

### Input Contract

- [ ] Input parameters defined via Pydantic schema or dataclass
- [ ] Required vs optional parameters clear
- [ ] Value constraints documented (min/max, valid ranges)
- [ ] Default values sensible

### Output Contract

- [ ] Return type documented
- [ ] Output structure documented
- [ ] Error conditions documented
- [ ] Warnings/issues structure defined

### Tests

- [ ] Dedicated test file exists
- [ ] Happy path tested
- [ ] At least one edge case tested
- [ ] Tests currently passing

### Preview Support

- [ ] Preview data can be generated without machine output
- [ ] Preview format documented (JSON structure or SVG format)
- [ ] Preview endpoint exists or can be added easily

### Safety Gates

- [ ] @safety_critical decorator on critical functions
- [ ] Input validation exists
- [ ] Depth vs stock thickness validated (if applicable)
- [ ] Tool vs slot width validated (if applicable)

### Route Provenance

- [ ] Generator can be traced from endpoint
- [ ] Router file identified
- [ ] Manifest entry exists (or documented why not)

---

## GOVERNED PREVIEW → GOVERNED EXPORT

### Export Governance

- [ ] Follows CAM_EXPORT_GOVERNANCE_POLICY.md
- [ ] No direct G-code emission without postprocessor
- [ ] Export requires explicit user action (not automatic)

### Postprocessor Separation

- [ ] G-code generation uses postprocessor interface
- [ ] Or: G-code generation is isolated in separate function
- [ ] Machine-specific codes not hardcoded in business logic

### Machine Profile Abstraction

- [ ] No hardcoded machine limits
- [ ] Feed rates configurable
- [ ] Spindle speed configurable
- [ ] Safe-Z configurable

### Manual Review Path

- [ ] User can preview before export
- [ ] Preview shows toolpath geometry
- [ ] User must explicitly request export

### Safe-Z Semantics

- [ ] safe_z_mm parameter exists
- [ ] Safe-Z used for all rapid moves
- [ ] Safe-Z documented in coordinate system

### Tool/Stock Validation

- [ ] Tool diameter vs feature width checked
- [ ] Cut depth vs stock thickness checked
- [ ] Tool reach vs cut depth checked (if applicable)

---

## GOVERNED EXPORT → MACHINE OUTPUT

### Machine Validation

- [ ] Machine envelope checked
- [ ] Feed rate vs machine max checked
- [ ] Rapid rate vs machine max checked
- [ ] Spindle RPM vs machine range checked

### Execution Governance

- [ ] RMOS run_id generated
- [ ] Input hashed for provenance
- [ ] Output hashed for verification
- [ ] Attachments persisted via put_*_attachment()

### Streaming Safety

- [ ] No direct serial/USB connection
- [ ] Output is downloadable file
- [ ] No automatic execution

### Operator Confirmation

- [ ] User must acknowledge machine selection
- [ ] User must confirm tool installation
- [ ] User must confirm stock secured

### Hardware Isolation

- [ ] G-code returned as string/file
- [ ] User manually loads to controller
- [ ] User manually starts execution

### Audit Trail

- [ ] Timestamp logged
- [ ] User ID logged
- [ ] Operation type logged
- [ ] Gate status logged
- [ ] Input/output hashes logged

---

## Evidence Documentation

For each checklist item, record:

| Item | Status | Evidence | Verified By | Date |
|------|--------|----------|-------------|------|
| Coordinate docs | ✓/✗/N/A | File:line or link | Reviewer | Date |

---

## Blockers

If any item cannot be checked, document as blocking issue:

| Blocker | Impact | Remediation |
|---------|--------|-------------|
| Description | Which promotion blocked | What needs to be done |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PROMOTION_FRAMEWORK.md` | Promotion stages |
| `CAM_MODULE_READINESS_SCORECARD.md` | Scoring criteria |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Export requirements |
| `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` | Quarantine rules |

---

*Checklist established: 2026-05-09*
