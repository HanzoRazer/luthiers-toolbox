# MRP-5J: Canonical Ontology Reconciliation & Semantic Registry Stabilization

**Sprint:** MRP-5J  
**Status:** Complete  
**Date:** 2026-05-16

---

## Summary

MRP-5J establishes machine-readable ontology infrastructure for semantic governance. The sprint creates authoritative registries for lifecycle vocabulary, authority chains, semantic terms, and alias mappings. It adds utility scripts for detecting drift and validating compliance.

---

## Deliverables

### JSON Registries (docs/governance/ontology/)

| File | Purpose |
|------|---------|
| `semantic_registry.json` | Canonical term definitions with owner domains, authority tiers, allowed/prohibited meanings |
| `lifecycle_registry.json` | Normalized lifecycle state vocabulary across all domains |
| `authority_chain_registry.json` | Machine-readable authority chains (6 chains, 8 domain ownerships) |
| `ontology_alias_registry.json` | Maps aliases to canonical terms (16 aliases) |

### Markdown Standards (docs/governance/ontology/)

| File | Purpose |
|------|---------|
| `LIFECYCLE_VOCABULARY_STANDARD.md` | Normalizes lifecycle vocabulary across domains |
| `SEMANTIC_FREEZE_PROTOCOL.md` | Defines freeze levels (FROZEN, STABLE, CANDIDATE, DEPRECATED) and versioning rules |
| `GOVERNANCE_CLASSIFICATION_MODEL.md` | Unifies maturity, runtime, and governance classifications with 5 dimensions |

### Utility Scripts (scripts/governance/)

| Script | Purpose |
|--------|---------|
| `detect_semantic_drift.py` | Detects duplicate definitions, conflicting meanings, missing registrations |
| `validate_lifecycle_terms.py` | Validates lifecycle terms against canonical registry |
| `audit_authority_chains.py` | Verifies authority chain completeness and ownership |
| `list_semantic_owners.py` | Lists semantic term owners from registry |

---

## Architecture Decisions

### 1. Registry-First Design

All ontology definitions are machine-readable JSON. Human-readable markdown documents reference but do not duplicate the registries. This prevents drift between documentation and implementation.

### 2. Domain-Qualified Vocabulary

Terms may have different meanings in different domains. The registry uses domain-qualified names (e.g., `topology_builder:supported_prototype` vs `cad_semantics:supported`) to prevent ambiguity.

### 3. Authority Chain as Data

Authority chains are explicit data structures, not prose. The registry defines:
- Sequence of authority nodes
- Invariants that must hold
- Source document references

### 4. Alias Lifecycle

Aliases are first-class concepts with lifecycle states (ACTIVE, TRANSITIONAL, RETIRED). The alias registry tracks canonical mappings and provides migration paths.

---

## Classification Model

### Five Dimensions

1. **Governance Tier** — Structural Invariants (1), Domain Governance (2), Operational Policies (3)
2. **Runtime Support** — SUPPORTED, SUPPORTED_PROTOTYPE, PARTIAL_PROTOTYPE, SEMANTIC_ONLY, UNSUPPORTED_RUNTIME, RESEARCH_REQUIRED
3. **Lifecycle State** — canonical, governed, governed_experimental, experimental, quarantine, deprecated
4. **Execution Mode** — prototype, production, validation_only, preview_only
5. **Failure Severity** — blocking, major, warning, acceptable

### Resolution Rule

When classifications conflict:
1. Most restrictive classification wins
2. If any dimension is UNSUPPORTED/BLOCKING, result is blocked
3. Warnings propagate through to output

---

## Usage

### Validate Lifecycle Terms

```bash
python scripts/governance/validate_lifecycle_terms.py
python scripts/governance/validate_lifecycle_terms.py --json
python scripts/governance/validate_lifecycle_terms.py --strict  # Exit non-zero on issues
```

### Detect Semantic Drift

```bash
python scripts/governance/detect_semantic_drift.py
python scripts/governance/detect_semantic_drift.py --json
```

### Audit Authority Chains

```bash
python scripts/governance/audit_authority_chains.py
python scripts/governance/audit_authority_chains.py --json
```

### List Semantic Owners

```bash
python scripts/governance/list_semantic_owners.py
python scripts/governance/list_semantic_owners.py --domain governance
python scripts/governance/list_semantic_owners.py --tier 1
python scripts/governance/list_semantic_owners.py --term topology
```

---

## Integration with Governance Check Suite

Add to `scripts/governance/check_all.py`:

```python
# MRP-5J ontology checks
("validate_lifecycle_terms", "python scripts/governance/validate_lifecycle_terms.py --strict", "ci"),
("detect_semantic_drift", "python scripts/governance/detect_semantic_drift.py", "ci"),
("audit_authority_chains", "python scripts/governance/audit_authority_chains.py", "ci"),
```

---

## Known Issues

### 1. Duplicate Enum Values

`detect_semantic_drift.py` reports 90+ duplicate enum value names across the codebase. Most are intentional (same concept in different enums, e.g., `CLASSICAL` in both `InstrumentType` and `BodyStyle`). Review report for actual conflicts.

### 2. Cross-Domain Term Usage

Terms like `blocking`, `warning`, `canonical` appear across 3+ domains. This is expected but flagged by the drift detector. The lifecycle registry documents domain-qualified meanings.

### 3. Missing Registration

The term `unsupported` (used in docs) is not in `lifecycle_registry.json`. Either add it or update docs to use `unsupported_runtime`.

---

## Related Documents

- `docs/governance/CANONICAL_ONTOLOGY_VOCABULARY.md` — existing vocabulary doc (not moved)
- `docs/governance/CANONICAL_AUTHORITY_MAP.md` — existing authority map (not moved)
- `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md` — tier definitions
- `docs/handoffs/MRP_5H_TOPOLOGY_BUILDER_IMPLEMENTATION.md` — preceding sprint

---

## Next Steps (MRP-5K)

1. Add ontology checks to CI pipeline
2. Resolve duplicate enum value conflicts
3. Add `unsupported` to lifecycle registry
4. Wire semantic validation to pre-commit hooks
