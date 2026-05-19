# C2 Continuity Semantic Decomposition

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
CONTINUITY SEMANTIC DECOMPOSITION
PRESERVING SEMANTIC NON-EQUIVALENCE
```

**Phase:** C2-C  
**Owner:** Terminal 3 (Geometry/Morphology/Topology Arbitration)  
**Date:** 2026-05-18  
**Status:** DECOMPOSITION IN PROGRESS

---

## 1. Authority Statement

This document decomposes "continuity" semantics for constitutional arbitration.

This document:
- Identifies distinct continuity semantic domains
- Maps continuity usage across the codebase
- Classifies continuity collision surfaces
- Prepares arbitration surface decomposition

This document does NOT:
- Choose winners between continuity semantics
- Normalize continuity globally
- Federate continuity vocabulary
- Mandate implementation changes

---

## 2. Core Constitutional Principle

```
SHARED TERMINOLOGY DOES NOT IMPLY SHARED ONTOLOGY
```

"Continuity" appears in at least 6 distinct semantic domains.
These domains answer fundamentally different questions:

| Domain | Question Answered |
|--------|-------------------|
| Geometric Continuity | "How smooth is this surface junction?" |
| Governance Continuity | "What is the immutable review ancestry?" |
| Semantic Continuity | "What CAD construction hints apply?" |
| Manufacturing Continuity | "Can this be machined at this tier?" |
| Runtime Continuity | "What validation strictness applies?" |
| Process Continuity | "Has the workflow chain been unbroken?" |

**Flattening these into one "continuity" concept would corrupt all six domains.**

---

## 3. Continuity Semantic Inventory

### 3.1 Geometric Continuity (surface_continuity)

**Source:** `topology_builder/contracts.py:16-21`

**Definition:**
```python
class ContinuityLevel(str, Enum):
    G0 = "G0"  # Positional continuity (touching)
    G1 = "G1"  # Tangent continuity (smooth)
    G2 = "G2"  # Curvature continuity (very smooth)
```

**Semantic Content:**
| Level | Meaning | Manufacturing Impact |
|-------|---------|---------------------|
| G0 | Surfaces touch at junction | Visible seam, sharp edge |
| G1 | Tangent planes match | Smooth visual transition |
| G2 | Curvature continuous | High-quality surface finish |

**Authority:** CAM domain — manufacturing continuity requirements
**Status:** CLEAR — well-defined mathematical semantics

---

### 3.2 Governance Continuity (governance_continuity_graph)

**Source:** `translator_governance_continuity_graph.py:1-25`

**Definition:**
```
Immutable governance continuity layer connecting governance review
ledger entries into deterministic replayable continuity graphs.
```

**Semantic Content:**
| Concept | Meaning | Purpose |
|---------|---------|---------|
| continuity_graph | Hash-linked review ancestry | Governance replay |
| continuity_integrity | Chain unbroken | Audit verification |
| continuity_state | Current review state | Governance routing |
| deterministic_continuity_hash | Canonical identity | Replay verification |

**7L Invariants (model-enforced):**
```
replayable = true (always)
immutable = true (always)
execution_authorized = false (always)
machine_output_allowed = false (always)
```

**Authority:** CAM governance domain — review chain integrity
**Status:** CLEAR — governance-specific, no geometric meaning

---

### 3.3 Semantic Continuity (cad_semantics)

**Source:** `export/cad_semantics.py:50-55`

**Definition:**
```python
class ContinuityTarget(str, Enum):
    G0 = "G0"  # Positional continuity
    G1 = "G1"  # Tangent continuity
```

**Semantic Content:**
| Concept | Meaning | Status |
|---------|---------|--------|
| ContinuityTarget | Hint for CAD translator | SEMANTIC_ONLY |
| rim.continuity_target | Plate-rim junction hint | Advisory |

**Authority:** Export/CAD domain — construction hints (not enforcement)
**Status:** COLLISION — duplicates ContinuityLevel with different purpose

---

### 3.4 Manufacturing Continuity (TopologyTier)

**Source:** `topology_builder/contracts.py:33-37`

**Definition:**
```python
class TopologyTier(str, Enum):
    PROTOTYPE = "PROTOTYPE"  # G0 acceptable, warnings allowed
    PRODUCTION = "PRODUCTION"  # G1 required, strict validation
```

**Semantic Content:**
| Tier | G0 | G1 | Non-manifold |
|------|----|----|--------------|
| PROTOTYPE | Acceptable | Warning | Warning |
| PRODUCTION | BLOCKING | Required | BLOCKING |

**Authority:** CAM runtime — validation strictness
**Status:** COLLISION — "tier" overlaps with governance tier, execution tier

---

### 3.5 Validation Continuity (topology validation)

**Source:** `topology_builder/validation.py:190-233`

**Definition:**
```
Continuity validation rules applied per tier:
- PROTOTYPE: G0 acceptable, G1 produces warning
- PRODUCTION: G1 required, G0 is BLOCKING
```

**Semantic Content:**
| Function | Purpose | Domain |
|----------|---------|--------|
| validate_continuity() | Check junction smoothness | Runtime validation |
| ContinuityMetadata | Track target vs achieved | Result reporting |
| met_target | Boolean achievement check | Pass/fail gate |

**Authority:** CAM runtime — enforcement mechanism
**Status:** CLEAR — implementation of geometric continuity rules

---

### 3.6 Process Continuity (workflow)

**Evidence:** Implicit in various workflow systems

**Definition:**
```
Whether a manufacturing workflow has maintained unbroken
chain of custody and approval from design to production.
```

**Semantic Content:**
| Concept | Meaning | Status |
|---------|---------|--------|
| Chain of custody | Geometry not mutated | BOE invariant |
| Approval chain | Governance sign-offs | Review ledger |
| Execution chain | G-code to machine | Translator boundary |

**Authority:** Cross-domain — process integrity
**Status:** IMPLICIT — not formally defined, embedded in multiple systems

---

## 4. Collision Matrix

### 4.1 Term Collision: "continuity"

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| continuity (geometric) | CAM topology | G0/G1/G2 surface smoothness | contracts.py |
| continuity (governance) | Governance | Review chain integrity | translator_governance_continuity_graph.py |
| continuity (semantic) | CAD hints | Construction target | cad_semantics.py |
| continuity (process) | Workflow | Chain of custody | Implicit |

**Risk Level:** HIGH — four distinct meanings share one term

---

### 4.2 Term Collision: "ContinuityLevel" vs "ContinuityTarget"

| Type | Location | Values | Purpose |
|------|----------|--------|---------|
| ContinuityLevel | contracts.py:16 | G0, G1, G2 | Topology validation |
| ContinuityTarget | cad_semantics.py:50 | G0, G1 | CAD construction hints |

**Risk:** Semantic drift — same G0/G1 values but different authority

**Evidence:**
- ContinuityLevel controls runtime validation (hard enforcement)
- ContinuityTarget is advisory hint (no enforcement)
- Confusion between "target" and "level" may cause false confidence

---

### 4.3 Term Collision: "tier"

| Usage | Domain | Values | Evidence |
|-------|--------|--------|----------|
| TopologyTier | CAM runtime | PROTOTYPE, PRODUCTION | contracts.py:33 |
| governance_tier | MRP | 1, 2, 3 | 7M registry |
| execution_tier | CI | precommit, ci, nightly, manual | check_all.py |

**Risk Level:** MEDIUM — already identified in COLL-G004, propagates to continuity

---

### 4.4 Cross-Domain Collision: Governance vs Geometric

| Aspect | Geometric | Governance |
|--------|-----------|------------|
| Unit | G0/G1/G2 levels | Hash chains |
| Validation | Surface smoothness | Chain integrity |
| Output | Pass/warning/fail | Valid/invalid |
| Immutability | Can retry | Always immutable |
| Authority | CAM runtime | Governance ledger |

**Flattening Risk:** HIGH

If "continuity" is used without namespace:
- "Check continuity" — geometric or governance?
- "Continuity is valid" — surface or chain?
- "Continuity target" — hint or requirement?

---

## 5. Semantic Boundary Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GEOMETRIC CONTINUITY DOMAIN                       │
│                                                                      │
│   "Is this surface junction G1-smooth?"                              │
│   "Does this shell meet PRODUCTION continuity?"                      │
│   "What continuity was achieved at the rim?"                         │
│                                                                      │
│   Answer: SURFACE SMOOTHNESS LEVELS (G0/G1/G2)                       │
│   Authority: CAM Topology Builder                                    │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           │ SEMANTIC BOUNDARY
                           │ Different questions, different answers
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE CONTINUITY DOMAIN                      │
│                                                                      │
│   "Is the governance review chain unbroken?"                         │
│   "What is the deterministic continuity hash?"                       │
│   "Can we replay the governance ancestry?"                           │
│                                                                      │
│   Answer: IMMUTABLE HASH CHAINS                                      │
│   Authority: Translator Governance Ledger                            │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           │ SEMANTIC BOUNDARY
                           │ Different questions, different answers
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SEMANTIC CONTINUITY DOMAIN                        │
│                                                                      │
│   "What continuity should the CAD translator target?"                │
│   "Is G1 recommended for this rim junction?"                         │
│                                                                      │
│   Answer: ADVISORY HINTS (no enforcement)                            │
│   Authority: CAD Semantics Layer                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Decomposition Proposal

### 6.1 Namespace Prefixing Strategy

| Namespace | Purpose | Domain |
|-----------|---------|--------|
| `geometric_continuity` | G0/G1/G2 surface smoothness | CAM topology |
| `governance_continuity` | Review chain integrity | Governance ledger |
| `semantic_continuity` | CAD construction hints | Export/CAD |
| `manufacturing_continuity` | Tier-based validation | CAM runtime |
| `process_continuity` | Workflow chain custody | Cross-domain |

### 6.2 Type Consolidation Proposal

**Option A — Preserve Duplication:**
Keep ContinuityLevel and ContinuityTarget as separate types.
Add documentation clarifying different authority.

**Option B — Unify with Authority Marker:**
```python
class ContinuityLevel(str, Enum):
    G0 = "G0"
    G1 = "G1"
    G2 = "G2"

@dataclass
class ContinuityRequirement:
    level: ContinuityLevel
    authority: Literal["enforcement", "advisory", "target"]
    source: str  # "topology_builder", "cad_semantics", etc.
```

**Terminal 3 Recommendation:** Option A (preserve duplication) with namespace documentation. Premature unification risks authority blurring.

---

## 7. Propagation Paths

### 7.1 Geometric Continuity Flow

```
ContinuityLevel (contracts.py)
    ↓
TopologyRequest.continuity_targets (contracts.py)
    ↓
ContinuityMetadata (contracts.py)
    ↓
ShellDescriptor.continuity[] (contracts.py)
    ↓
validate_continuity() (validation.py)
    ↓
TopologyResult (contracts.py)
```

**Containment:** HEALTHY — confined to topology_builder domain

### 7.2 Governance Continuity Flow

```
TranslatorGovernanceReviewLedgerEntry
    ↓
build_governance_continuity_graph() (translator_governance_continuity_graph.py)
    ↓
TranslatorGovernanceContinuityGraph
    ↓
replay_governance_trace() (translator_governance_continuity_graph.py)
    ↓
GovernanceReplayResult
```

**Containment:** HEALTHY — confined to governance domain, immutable invariants enforced

### 7.3 Semantic Continuity Flow

```
ContinuityTarget (cad_semantics.py)
    ↓
RimSemantics.continuity_target (cad_semantics.py)
    ↓
AcousticSemantics.rim (cad_semantics.py)
    ↓
CadSemantics (cad_semantics.py)
    ↓
??? (consumption path unclear)
```

**Containment:** UNCLEAR — semantic hints may not be consumed consistently

---

## 8. Authority Candidate Matrix

| Continuity Type | Current Authority | Candidates | Arbitration Required |
|-----------------|-------------------|------------|---------------------|
| geometric_continuity | CAM topology_builder | CAM (single claimant) | NO |
| governance_continuity | Governance ledger | Governance (single claimant) | NO |
| semantic_continuity | cad_semantics | CAD hints (single claimant) | NO |
| manufacturing_continuity | TopologyTier | CAM runtime (single claimant) | NO |
| process_continuity | UNDEFINED | Multiple implicit claimants | YES |

**Key Finding:** Unlike geometry and topology, continuity domains have clear single authorities. The risk is not authority ambiguity but **semantic blurring** from shared terminology.

---

## 9. Flattening Risks

### 9.1 RISK: Geometric/Governance Collapse

**Severity:** HIGH

**Scenario:**
Code uses `continuity` without namespace prefix, reader assumes wrong domain.

**Example:**
```python
# In governance code:
if continuity.is_valid:  # Which continuity?
    proceed()
```

**Mitigation:**
- Require domain-prefixed references where ambiguity possible
- Document namespace requirement at module boundaries

### 9.2 RISK: ContinuityLevel/ContinuityTarget Confusion

**Severity:** MEDIUM

**Scenario:**
Developer uses ContinuityTarget thinking it enforces validation.

**Evidence:**
- Both use G0/G1 string values
- Different locations (contracts.py vs cad_semantics.py)
- Different authority (enforcement vs advisory)

**Mitigation:**
- Add docstring clarifying advisory nature of ContinuityTarget
- Consider renaming to `ContinuityHint` to clarify non-enforcement

### 9.3 RISK: Process Continuity Undefined

**Severity:** MEDIUM

**Scenario:**
"Process continuity" invoked without formal definition, different interpretations emerge.

**Mitigation:**
- Either formally define or explicitly defer
- Do not allow implicit process continuity claims

---

## 10. Dissent Surfaces

### 10.1 Unresolved: Should ContinuityTarget Be Renamed?

**Position A — Rename to ContinuityHint:**
- Clarifies advisory nature
- Reduces confusion with ContinuityLevel
- Semantic improvement

**Position B — Preserve ContinuityTarget:**
- "Target" already implies aspiration, not guarantee
- Breaking change for existing consumers
- CAD terminology uses "target"

**Terminal 3 Assessment:** Position A is semantically cleaner but Position B avoids breaking changes. Defer to C3 enforcement phase.

### 10.2 Unresolved: G2 Coverage Gap

**Observation:**
- ContinuityLevel supports G2 (curvature continuity)
- ContinuityTarget only supports G0, G1 (no G2)

**Question:**
Is G2 omission in ContinuityTarget intentional or oversight?

**Terminal 3 Assessment:** Likely intentional — acoustic bodies rarely require G2. Document as explicit scope limitation, not gap.

---

## 11. Constitutional Risks

### 11.1 Layer Collapse Prevention

| Risk | Description | Mitigation |
|------|-------------|------------|
| Geometric → Governance | G0/G1/G2 terms bleeding into governance | Namespace prefixing |
| Governance → Geometric | "continuity_graph" implying surface meaning | Domain documentation |
| Semantic → Enforcement | Advisory hints treated as requirements | Authority documentation |

### 11.2 Anti-Patterns to Avoid

```
ANTI-PATTERN 1: Unprefixed "continuity" in code comments
ANTI-PATTERN 2: Assuming ContinuityTarget enforces validation
ANTI-PATTERN 3: Conflating governance continuity with surface smoothness
ANTI-PATTERN 4: Implicit process continuity without formal definition
ANTI-PATTERN 5: Treating TopologyTier as governance tier
```

---

## 12. Terminal Review Requirements

### Terminal 3 — Geometry/Morphology/Topology (THIS DOCUMENT)

- [x] Identify continuity semantic domains
- [x] Map collision surfaces
- [x] Document propagation paths
- [x] Classify flattening risks
- [x] Propose namespace strategy

### Terminal 2 — Runtime/CAM (PENDING)

- [ ] Review geometric continuity enforcement paths
- [ ] Validate TopologyTier scope boundaries
- [ ] Confirm validation.py containment
- [ ] Flag runtime leakage risks

### Terminal 4 — Provenance/Observational (PENDING)

- [ ] Review governance continuity graph integrity
- [ ] Validate immutability invariants
- [ ] Confirm 7L guardrail enforcement
- [ ] Flag governance/geometric blurring risks

### Terminal 5 — Export/Serialization (PENDING)

- [ ] Review cad_semantics consumption paths
- [ ] Validate ContinuityTarget usage
- [ ] Confirm advisory-only status
- [ ] Flag semantic→enforcement confusion risks

---

## 13. Related Documents

### C2 Framework

- `C2_ARBITRATION_FRAMEWORK.md` — Constitutional arbitration structure
- `C2_GEOMETRY_NAMESPACE_COLLISIONS.md` — Geometry collision decomposition
- `C2_TOPOLOGY_NAMESPACE_SEPARATION_REVIEW.md` — Topology semantic split

### Code References

- `topology_builder/contracts.py` — ContinuityLevel, TopologyTier
- `topology_builder/validation.py` — validate_continuity()
- `translator_governance_continuity_graph.py` — Governance continuity
- `export/cad_semantics.py` — ContinuityTarget, RimSemantics

---

*C2-C Continuity Semantic Decomposition — Terminal 3 Initial Draft*
