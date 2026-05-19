# C2-B Topology Namespace Arbitration Findings

**Date:** 2026-05-18  
**Status:** DRAFT — Terminal 2 Analysis  
**Phase:** C2-B Runtime Propagation Analysis  
**Depends On:** C2-A Geometry Authority (RATIFIED)

---

## Executive Summary

Terminal 2 runtime propagation analysis has identified a **namespace collision** around the term "continuity". Three distinct semantic domains use this term without canonical arbitration, creating a risk of silent ontology convergence through shared runtime paths.

---

## Namespace Collision: "continuity"

### Three Distinct Meanings

| Domain | Identifier | Semantic Meaning | Location |
|--------|------------|------------------|----------|
| **Manufacturing** | `ContinuityLevel.G0/G1/G2` | Surface tangency (positional→tangent→curvature) | `topology_builder/contracts.py:16` |
| **Governance** | `continuity_graph`, `continuity_integrity` | Review chain integrity, immutable ancestry | `translator_governance_continuity_graph.py` |
| **Vectorizer** | `continuity_score` | Vertex density per unit perimeter | `contour_scoring.py:507` |

### Registration Status

```python
# canonical_ontology_registry.py
# Registered: "topology" (MRP domain)
# NOT Registered: "continuity" (any domain)
```

**Gap**: The canonical ontology registry does NOT arbitrate the term "continuity".

---

## Detailed Analysis

### 1. Manufacturing Continuity (`ContinuityLevel`)

**Definition** (topology_builder/contracts.py:16-21):
```python
class ContinuityLevel(str, Enum):
    """Geometric continuity levels for surface junctions."""
    G0 = "G0"  # Positional continuity (touching)
    G1 = "G1"  # Tangent continuity (smooth)
    G2 = "G2"  # Curvature continuity (very smooth)
```

**Semantic domain**: Manufacturing/CAD surface quality
**Purpose**: Specifies required smoothness at shell junctions
**Usage**: `TopologyRequest.continuity_targets`, `ShellDescriptor.continuity`

### 2. Governance Continuity (`continuity_graph`)

**Definition** (translator_governance_continuity_graph.py:74-86):
```python
class TranslatorGovernanceContinuityGraph(BaseModel):
    """
    Governance continuity graph for deterministic replay.
    
    Connects governance review ledger entries into an immutable
    replay structure for ancestry traversal and integrity verification.
    """
```

**Semantic domain**: Governance/review chains
**Purpose**: Tracks review ancestry and integrity
**Usage**: CAM translator governance, review replay

### 3. Vectorizer Continuity (`continuity_score`)

**Definition** (contour_scoring.py:507-521):
```python
def _continuity_score(vertex_count: int, perimeter: float) -> float:
    """
    Score contour continuity - jagged/noisy contours have high vertex density.
    
    Clean contours have fewer vertices per unit perimeter.
    """
    density = vertex_count / perimeter
    # Too many vertices per unit perimeter often means jagged/noisy contour
```

**Semantic domain**: Blueprint vectorizer scoring
**Purpose**: Penalizes jagged/noisy contours
**Usage**: `ContourScore.continuity_score` field

---

## Runtime Collision Surfaces

### Potential Confusion Paths

| Surface | Risk | Current State |
|---------|------|---------------|
| `cad_semantics.py:continuity_target` | Could conflate governance and manufacturing | Explicitly refers to `ContinuityLevel` in docstring |
| `TopologyRequest` → Governance | Could pass governance continuity as manufacturing target | NO DIRECT PATH (separated) |
| `ContourScore` → `TopologyBuilder` | Could interpret vectorizer score as G0/G1/G2 | NO DIRECT PATH (separated) |

### Current Separation

The three continuity domains are currently **operationally separated**:

1. Manufacturing continuity stays within `topology_builder/`
2. Governance continuity stays within `cam/translator_governance_*`
3. Vectorizer continuity stays within `services/contour_scoring.py`

**However**: No formal namespace boundary prevents future conflation.

---

## Critical Question

> Does runtime behavior implicitly collapse morphology_topology and surface_topology through shared operational paths?

**Answer**: Not currently, but the infrastructure permits it.

The canonical ontology registry provides the mechanism for namespace protection, but "continuity" is unregistered. A future developer could:

1. Import `ContinuityLevel` into governance code
2. Interpret `continuity_score` as a G0/G1/G2 assessment
3. Pass governance `continuity_integrity` as a manufacturing constraint

Without canonical registration, nothing prevents these misinterpretations.

---

## Recommendations for C2-B Resolution

### R1. Register "continuity" with Namespace Qualifiers

Add three distinct canonical terms:

```python
# Proposed additions to INITIAL_CANONICAL_VOCABULARY

{
    "term": "manufacturing_continuity",
    "canonical_definition": (
        "Geometric surface tangency level (G0/G1/G2) at shell junctions, "
        "owned by Manufacturing domain and used by topology builders."
    ),
    "owning_domain": "Manufacturing",
    "owning_governance_tier": 2,
    "prohibited_reinterpretations": [
        "governance_continuity",
        "vectorizer_continuity_score",
        "review_chain_integrity",
    ],
    "aliases": ["surface_continuity", "G_continuity"],
},
{
    "term": "governance_continuity",
    "canonical_definition": (
        "Immutable review chain integrity for translator governance, "
        "owned by Governance domain and used by continuity graphs."
    ),
    "owning_domain": "Governance",
    "owning_governance_tier": 1,
    "prohibited_reinterpretations": [
        "manufacturing_continuity",
        "surface_tangency",
        "G0_G1_G2",
    ],
    "aliases": ["review_continuity", "ledger_continuity"],
},
{
    "term": "contour_continuity",
    "canonical_definition": (
        "Vectorizer scoring metric for contour smoothness based on "
        "vertex density per unit perimeter."
    ),
    "owning_domain": "Vectorizer",
    "owning_governance_tier": 3,
    "prohibited_reinterpretations": [
        "manufacturing_continuity",
        "governance_continuity",
    ],
    "aliases": ["jaggedness_score"],
},
```

### R2. Add Cross-Domain Import Guards

In `topology_builder/contracts.py`:
```python
# NAMESPACE BOUNDARY: ContinuityLevel is manufacturing-only
# Do NOT import governance continuity or vectorizer continuity_score
```

In `translator_governance_continuity_graph.py`:
```python
# NAMESPACE BOUNDARY: Governance continuity only
# Do NOT import ContinuityLevel or contour continuity_score
```

### R3. Rename Ambiguous Fields

Consider renaming for clarity:
- `ContinuityLevel` → `SurfaceContinuityLevel` or `G_ContinuityLevel`
- `continuity_score` → `smoothness_score` or `jaggedness_penalty`
- `continuity_graph` → (keep, but register as governance-owned)

---

## Topology Namespace Status

The canonical ontology registry correctly registers "topology":

```python
{
    "term": "topology",
    "canonical_definition": (
        "Semantic structure describing spatial relationships, regions, "
        "and connectivity under MRP governance."
    ),
    "owning_domain": "MRP",
    "owning_governance_tier": 2,
    "prohibited_reinterpretations": [
        "runtime_topology_inference",
        "automatic_region_detection",
    ],
    "aliases": ["body_topology", "spatial_topology"],
}
```

This provides namespace protection for "topology" but leaves the associated "continuity" concepts unprotected.

---

## Constitutional Principle Applied

> Shared runtime consumption does not imply shared semantic authority.

The three continuity domains currently share:
- The term "continuity"
- Python's namespace (importable from any module)
- The repository codebase

They do NOT share:
- Semantic authority
- Runtime execution paths (currently)
- Canonical registration (none have it)

C2-B must establish namespace separation BEFORE C2-C provenance decomposition can proceed safely.

---

## Decision Required

| Option | Description | Risk |
|--------|-------------|------|
| **A. Register all three** | Add manufacturing, governance, contour continuity to ontology | Low risk, high governance overhead |
| **B. Register two, rename one** | Register manufacturing + governance, rename `continuity_score` to `smoothness_score` | Medium risk, cleaner |
| **C. Document without registration** | Add warning comments, defer registration | Higher drift risk |

**Recommended**: Option B — Register manufacturing and governance continuity canonically, rename vectorizer `continuity_score` to `smoothness_score` to eliminate collision.

---

## Sequencing Confirmation

```
C2-A Geometry Authority           → RATIFIED
C2-B Topology Namespace Arbitration → FINDINGS COMPLETE (this document)
C2-C Provenance Boundary Decomposition → BLOCKED on C2-B resolution
C2-D Continuity Constitutional Integration → BLOCKED on B + C
```

C2-C cannot proceed until the "continuity" namespace collision is resolved, because provenance decomposition needs to know which semantic layer each type of continuity belongs to.

---

*C2-B_TOPOLOGY_NAMESPACE_ARBITRATION_FINDINGS.md — Terminal 2 Analysis — 2026-05-18*
