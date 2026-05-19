# Governance Classification Model

**Status:** Authoritative  
**Date:** 2026-05-16  
**Sprint:** MRP-5J

---

## Purpose

This document unifies the maturity, runtime, and governance classification vocabularies across all repository domains into a coherent model.

---

## Classification Dimensions

### Dimension 1: Governance Tier

Indicates the level of governance authority.

| Tier | Name | Scope | Authority |
|------|------|-------|-----------|
| 1 | Structural Invariants | Repository-wide | Code placement, migration discipline |
| 2 | Domain Governance | Domain-specific | Domain operations, boundaries |
| 3 | Operational Policies | Runtime behavior | Execution within tier 2 boundaries |

**Source:** `GOVERNANCE_AUTHORITY_HIERARCHY.md`

### Dimension 2: Runtime Support

Indicates execution capability.

| Classification | Meaning | Output |
|----------------|---------|--------|
| SUPPORTED | Full runtime capability | Yes |
| SUPPORTED_PROTOTYPE | Prototype-tier runtime | Yes (with warnings) |
| PARTIAL_PROTOTYPE | Some features supported | Partial |
| SEMANTIC_ONLY | Schema valid, no runtime | No |
| UNSUPPORTED_RUNTIME | Cannot generate | No (rejection) |
| RESEARCH_REQUIRED | Future capability | No (blocked) |

**Note:** Different domains use overlapping terms. See `lifecycle_registry.json` for domain-qualified definitions.

### Dimension 3: Lifecycle State

Indicates artifact or term maturity.

| State | Meaning | Stability |
|-------|---------|-----------|
| canonical | Ratified, authoritative | Frozen or Stable |
| governed | Subject to governance | Stable |
| governed_experimental | Governed but experimental | May change |
| experimental | Not yet governed | No guarantees |
| quarantine | Isolated pending review | Blocked |
| deprecated | Scheduled for removal | Sunsetting |

### Dimension 4: Execution Mode

Indicates runtime context.

| Mode | Meaning | Validation |
|------|---------|------------|
| prototype | Relaxed validation | G0 acceptable |
| production | Strict validation | G1 required |
| validation_only | Report only | No output |
| preview_only | Visualization | Not machine-ready |

### Dimension 5: Failure Severity

Indicates error handling.

| Severity | Impact | Handling |
|----------|--------|----------|
| blocking | Cannot proceed | Rejection |
| major | Tier-dependent | Prototype: warn; Production: block |
| warning | Minor issue | Logged |
| acceptable | Expected variance | Ignored |

---

## Classification Matrix

### Body Category → Runtime Support

| Body Category | cad_semantics | topology_builder |
|---------------|---------------|------------------|
| flat_body | SUPPORTED | SUPPORTED_PROTOTYPE |
| acoustic_flat_top | SEMANTIC_ONLY | SUPPORTED_PROTOTYPE |
| hollow_electric | SEMANTIC_ONLY | PARTIAL_PROTOTYPE |
| archtop | SEMANTIC_ONLY | RESEARCH_REQUIRED |
| acoustic_arched_top | SEMANTIC_ONLY | RESEARCH_REQUIRED |
| resonator | UNSUPPORTED | RESEARCH_REQUIRED |
| unknown | UNSUPPORTED | UNSUPPORTED_RUNTIME |

### Feature → Runtime Support (topology_builder)

| Feature | Support Level |
|---------|---------------|
| thickness_uniform | SUPPORTED_PROTOTYPE |
| thickness_component | SUPPORTED_PROTOTYPE |
| thickness_zonal | PARTIAL_PROTOTYPE |
| thickness_continuous | RESEARCH_REQUIRED |
| profile_flat | SUPPORTED_PROTOTYPE |
| profile_uniform_arch | PARTIAL_PROTOTYPE |
| profile_graduated_arch | RESEARCH_REQUIRED |
| continuity_g0 | SUPPORTED_PROTOTYPE |
| continuity_g1 | PARTIAL_PROTOTYPE |
| continuity_g2 | RESEARCH_REQUIRED |

---

## Cross-Domain Classification Mapping

### When cad_semantics meets topology_builder

| cad_semantics | topology_builder | Combined Outcome |
|---------------|------------------|------------------|
| SUPPORTED | SUPPORTED_PROTOTYPE | Full prototype generation |
| SUPPORTED | PARTIAL_PROTOTYPE | Partial generation with warnings |
| SEMANTIC_ONLY | SUPPORTED_PROTOTYPE | Topology possible despite semantic-only |
| SEMANTIC_ONLY | UNSUPPORTED_RUNTIME | No generation |
| UNSUPPORTED | any | No generation |

### Resolution Rule

When combining classifications:
1. Most restrictive classification wins
2. If any dimension is UNSUPPORTED/BLOCKING, result is blocked
3. Warnings propagate through to output

---

## Classification Usage Patterns

### Pattern 1: Capability Check

```python
# Check if topology can be generated
support = classify_topology_runtime(body_category, cad_semantics)
if support in (SUPPORTED_PROTOTYPE, PARTIAL_PROTOTYPE):
    # Can proceed
else:
    # Reject with classification
```

### Pattern 2: Tier-Dependent Handling

```python
# Handle based on execution tier
if tier == PROTOTYPE:
    if severity == MAJOR:
        # Log warning, continue
elif tier == PRODUCTION:
    if severity == MAJOR:
        # Block execution
```

### Pattern 3: Governance Gate

```python
# Check governance compliance
if lifecycle_state == QUARANTINE:
    # Cannot proceed
if governance_tier < required_tier:
    # Escalate to higher tier
```

---

## Anti-Patterns

### Anti-Pattern 1: Implicit Classification

**Wrong:** Inferring classification from behavior  
**Right:** Explicit classification declaration

### Anti-Pattern 2: Runtime Redefining Classification

**Wrong:** Runtime system changing its own classification  
**Right:** Classification determined by governance

### Anti-Pattern 3: Silent Fallback

**Wrong:** Silently degrading to lower capability  
**Right:** Explicit rejection with classification reason

---

## Related Documents

- `lifecycle_registry.json` - Lifecycle classifications
- `authority_chain_registry.json` - Authority chains
- `GOVERNANCE_AUTHORITY_HIERARCHY.md` - Tier definitions
- `TOPOLOGY_FAILURE_CLASSIFICATION.md` - Failure severities
- `ACOUSTIC_RUNTIME_LIMITATIONS.md` - Runtime limitations
