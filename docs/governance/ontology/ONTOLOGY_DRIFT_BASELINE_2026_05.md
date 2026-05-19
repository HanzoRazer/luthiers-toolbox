# Ontology Drift Baseline — May 2026

**Status:** Baseline Record  
**Date:** 2026-05-16  
**Sprint:** MRP-5K

---

## Purpose

This document captures the current state of ontology drift in the repository as of May 2026. Findings documented here represent **accepted legacy drift** and should NOT block CI.

New violations (not present in this baseline) may escalate based on severity.

---

## Baseline Summary

| Category | Count | Severity |
|----------|-------|----------|
| Duplicate enum values | 151 | Advisory |
| Cross-domain term usage | 7 | Advisory |
| Missing registrations | 1 | Warning |
| Authority naming inconsistencies | 2 | Advisory |
| Valid lifecycle usages | 50 | Informational |
| Alias usages | 4 | Informational |
| Potential lifecycle issues | 26 | Warning |

---

## Duplicate Enum Values (151)

These are enum values that appear in multiple files. Most are intentional (same concept in different contexts).

### By Category

| Category | Count | Example |
|----------|-------|---------|
| Instrument types | 15+ | CLASSICAL, DREADNOUGHT, PARLOR |
| Body styles | 10+ | STRATOCASTER, TELECASTER, LES_PAUL |
| Workflow states | 10+ | PENDING, APPROVED, REJECTED |
| Severities | 5+ | CRITICAL, WARNING, INFO |
| Material types | 5+ | SOFT, MEDIUM, HARD |
| Pattern types | 5+ | SOLID, HERRINGBONE, ROPE |
| AI providers | 3 | OPENAI, ANTHROPIC, LOCAL |

### Notable Examples

- `CLASSICAL` appears in InstrumentType AND BodyStyle
- `DREADNOUGHT` appears in BodyStyle AND AcousticBodyStyle
- `PENDING` appears in 10+ workflow/status enums
- `EXPERIMENTAL` appears in TranslatorMaturity AND ExecutionState
- `DEPRECATED` appears in TranslatorMaturity AND ExecutionState

### Assessment

Most duplicates are intentional domain-specific usage. No immediate action required. Future consolidation may introduce shared enums where appropriate.

---

## Cross-Domain Term Usage (7)

These lifecycle terms appear across 3+ domains:

| Term | Domains | Notes |
|------|---------|-------|
| blocking | cad, acoustic, topology, export | Failure severity across domains |
| warning | cad, acoustic, topology, export | Failure severity across domains |
| major | cad, acoustic, export, topology | Failure severity across domains |
| canonical | cad, topology, export, cam | Governance classification |
| governed | cad, topology, export | Governance classification |
| prototype | cad, acoustic, topology | Execution mode |
| research_required | cad, acoustic, topology | Runtime support classification |

### Assessment

Cross-domain usage is expected for governance vocabulary. Domain-qualified names documented in `lifecycle_registry.json` provide disambiguation.

---

## Missing Registrations (1)

| Term | Used In | Action |
|------|---------|--------|
| `unsupported` | cad_semantics | Add to lifecycle_registry.json |

---

## Authority Naming Inconsistencies (2)

These are naming differences between semantic_registry.json and authority_chain_registry.json:

| Term | Semantic Registry Owner | Authority Registry Owner |
|------|------------------------|-------------------------|
| morphology | Geometry Layer / MRP | Geometry Layer |
| feasibility | RMOS / Feasibility Layer | Feasibility Layer |

### Assessment

These are naming inconsistencies, not actual ownership conflicts. The same organizational unit is referenced with different names. Normalize in future sprint.

---

## Potential Lifecycle Issues (26)

These are string literals that look like lifecycle terms but aren't in the registry:

| Pattern | Count | Examples |
|---------|-------|----------|
| Error class names | 8 | UnsupportedTopologyError, ValidationError |
| Feature flags | 4 | supported_features, unsupported_features |
| Method names | 6 | classify_topology_runtime, get_supported_targets |
| Execution states | 4 | governed_execution, unsupported_entity |
| Other | 4 | warnings, production |

### Assessment

Most are false positives (class names, method names). Not lifecycle vocabulary violations.

---

## Accepted Baseline Violations

The following violations are EXPLICITLY ACCEPTED and should not block CI:

1. **All 151 duplicate enum values** — accepted as domain-specific usage
2. **All 7 cross-domain terms** — accepted with domain-qualified disambiguation
3. **2 authority naming inconsistencies** — accepted pending normalization
4. **26 potential lifecycle issues** — mostly false positives

---

## Machine-Readable Baseline

See: `ontology_drift_baseline_2026_05.json`

---

## Future Cleanup Opportunities

### High Value

1. Normalize authority registry naming to match semantic registry
2. Add `unsupported` to lifecycle registry
3. Consolidate shared status enums (PENDING, APPROVED, REJECTED)

### Medium Value

1. Create shared instrument type enum
2. Consolidate AI provider enums
3. Unify severity enums

### Low Priority

1. Review pattern type duplicates
2. Review material type duplicates

---

## Governance Notes

- This baseline represents accepted technical debt
- New violations should be evaluated against this baseline
- Violations present in baseline = advisory
- New violations not in baseline = escalate per severity rules
- Baseline should be updated quarterly or after major cleanup

---

## Related Documents

- `ontology_drift_baseline_2026_05.json` — machine-readable baseline
- `CI_GOVERNANCE_ENFORCEMENT_MODEL.md` — enforcement model
- `ontology_ci_policy.json` — CI policy
