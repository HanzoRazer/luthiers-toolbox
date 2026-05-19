# Lifecycle Vocabulary Standard

**Status:** Authoritative  
**Date:** 2026-05-16  
**Sprint:** MRP-5J

---

## Purpose

This document normalizes lifecycle state vocabulary across all repository domains. It establishes canonical meanings for lifecycle terms and reconciles conflicts between domain-specific vocabularies.

**Machine-readable registry:** `lifecycle_registry.json`

---

## Canonical Lifecycle Classifications

### Runtime Support Classifications

| Term | Canonical Meaning | Domain |
|------|-------------------|--------|
| `supported` | Full runtime generation capability | cad_semantics |
| `supported_prototype` | Prototype-tier runtime support | topology_builder |
| `semantic_only` | Valid schema, no runtime topology | cad_semantics |
| `partial_prototype` | Some features supported with warnings | topology_builder |
| `unsupported_runtime` | Cannot generate, clean rejection | topology_builder |
| `unsupported` | Not supported | cad_semantics |
| `research_required` | Future capability needed | topology_builder |

### Governance Classifications

| Term | Canonical Meaning | Domain |
|------|-------------------|--------|
| `canonical` | Ratified, authoritative form | governance |
| `governed` | Subject to governance constraints | export_lifecycle |
| `governed_experimental` | Governed but explicitly experimental | governance |
| `experimental` | Not yet governed, subject to change | governance |
| `quarantine` | Isolated pending review | governance |

### Execution Mode Classifications

| Term | Canonical Meaning | Domain |
|------|-------------------|--------|
| `prototype` | Relaxed validation tier | topology_builder |
| `production` | Strict validation tier | topology_builder |
| `validation_only` | No output, report only | validation |
| `preview_only` | Visualization, not machine-ready | cam_export |
| `machine_candidate` | Pending authorization | cam_export |

### Failure Severity Classifications

| Term | Canonical Meaning | Domain |
|------|-------------------|--------|
| `blocking` | Cannot proceed, no output | topology_failure |
| `major` | Tier-dependent handling | topology_failure |
| `warning` | Minor issue, output produced | topology_failure |
| `acceptable` | Expected variance | topology_failure |

---

## Vocabulary Reconciliation Rules

### Rule 1: Domain Scope

Each domain owns its vocabulary within its scope. Cross-domain terminology must be explicitly mapped.

**Example:**
- `supported` (cad_semantics) ≠ `supported_prototype` (topology_builder)
- Both are valid within their domains
- Cross-domain references must use domain-qualified names

### Rule 2: Alias Resolution

Aliases must map to exactly one canonical term within a domain.

**Example:**
- `SUPPORTED_PROTOTYPE` → `supported_prototype` (topology_builder)
- `RESEARCH_ONLY` → `research_required` (documentation transitional)

### Rule 3: Conflict Detection

When the same term appears with different meanings:
1. Identify the owning domain for each usage
2. Determine if meanings are compatible or conflicting
3. If conflicting, create distinct canonical terms
4. Document the conflict and resolution

### Rule 4: Deprecation

Deprecated terms must specify:
- Replacement term
- Deprecation date
- Reason for deprecation

---

## Known Vocabulary Conflicts

### semantic_only vs unsupported

**Nature:** Both indicate lack of runtime support but differ in schema validity.

**Resolution:**
- `semantic_only`: Schema validates, topology not generated
- `unsupported`: May indicate schema itself is invalid or category unrecognized

### supported vs supported_prototype

**Nature:** Different domains use similar terms.

**Resolution:**
- `supported`: cad_semantics domain, indicates translator capability
- `supported_prototype`: topology_builder domain, indicates prototype-tier capability

These are not aliases; they are distinct terms in different domains.

---

## Adding New Lifecycle Terms

### Requirements

1. **Domain owner approval** required
2. **Unique within domain** - no collision with existing terms
3. **Clear canonical definition** - not ambiguous
4. **Machine-readable registration** - add to `lifecycle_registry.json`

### Process

1. Propose term with definition
2. Check for conflicts with existing terms
3. Obtain domain owner approval
4. Add to lifecycle registry
5. Document in governance if tier 1/2

---

## Cross-Domain Mapping

When referencing terms across domains, use qualified names:

```
topology_builder:supported_prototype
cad_semantics:semantic_only
topology_failure:blocking
```

This prevents ambiguity when the same term has different meanings in different domains.

---

## Related Documents

- `lifecycle_registry.json` - Machine-readable registry
- `ontology_alias_registry.json` - Alias mappings
- `GOVERNANCE_AUTHORITY_HIERARCHY.md` - Tier definitions
- `TOPOLOGY_FAILURE_CLASSIFICATION.md` - Failure severities
