# C2 Continuity Arbitration Packet 003

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
PACKET 003 — CONTINUITY SEMANTIC DECOMPOSITION
GEOMETRIC vs GOVERNANCE vs SEMANTIC CONTINUITY
```

**Phase:** C2-C  
**Owner:** Terminal 1 (Governance Lead) + Terminal 3 (Geometry Arbitration)  
**Date:** 2026-05-18  
**Status:** DECOMPOSITION COMPLETE — TERMINAL REVIEW PENDING

---

## 1. Authority Statement

This packet documents continuity semantic decomposition for constitutional arbitration.

This packet:
- Decomposes continuity semantic domains
- Documents evidence
- Identifies collision surfaces
- Proposes layer boundaries

This packet does NOT:
- Ratify authority
- Choose winners
- Mandate implementation
- Create enforcement

**Outcome Status:** Decomposition complete, terminal review pending.

---

## 2. Packet Subject

### Arbitration Question

```
How should the repository distinguish:
  - Geometric continuity (G0/G1/G2 surface smoothness)
  - Governance continuity (immutable review chain integrity)
  - Semantic continuity (advisory CAD construction hints)
  - Manufacturing continuity (tier-based validation strictness)
```

### Why This Matters

C1 inventory and C2-B topology review discovered:
- "continuity" term used across 5+ distinct semantic domains
- No namespace prefixing to distinguish meanings
- ContinuityLevel (enforcement) vs ContinuityTarget (advisory) collision
- Governance continuity vocabulary isolated but terminology shared

Without layer decomposition:
- "continuity" becomes semantically overloaded
- Advisory hints may be confused with enforcement
- Geometric and governance domains may blur
- Process continuity remains undefined

---

## 3. Frozen Evidence References

### C2 Arbitration Documents

| Finding | Location | Relevance |
|---------|----------|-----------|
| Topology semantic split | C2_TOPOLOGY_NAMESPACE_SEPARATION_REVIEW.md | Pattern reference |
| Geometry layer framework | C2_GEOMETRY_AUTHORITY_FRAMEWORK.md | Layer model |
| Namespace collision pattern | C2_GEOMETRY_NAMESPACE_COLLISIONS.md | Decomposition model |

### Code Evidence

| Source | Location | Relevance |
|--------|----------|-----------|
| ContinuityLevel | topology_builder/contracts.py:16-21 | Geometric continuity |
| ContinuityTarget | export/cad_semantics.py:50-55 | Semantic continuity |
| ContinuityGraph | translator_governance_continuity_graph.py:74 | Governance continuity |
| TopologyTier | topology_builder/contracts.py:33-37 | Manufacturing continuity |

---

## 4. Collision References

### Primary Collisions

| ID | Term | Risk | Relevance |
|----|------|------|-----------|
| COLL-C001 | continuity | High | 5-domain semantic overload |
| COLL-C002 | ContinuityLevel vs ContinuityTarget | Medium | Type duplication |
| COLL-C003 | continuity_graph | Low | Governance-specific |
| COLL-C004 | continuity validation | Medium | Advisory vs enforcement |

### Cross-Reference Collisions

| ID | Term | Risk | Relevance |
|----|------|------|-----------|
| COLL-G004 | tier | Medium | TopologyTier overlaps governance tier |

---

## 5. Authority Claimants

### Current Authority Assertions

| System | Claim | Evidence | Constitutional Status |
|--------|-------|----------|----------------------|
| CAM topology_builder | Geometric continuity (G0/G1/G2) | ContinuityLevel enum, validate_continuity() | CLEAR — single authority |
| Governance ledger | Governance continuity (hash chains) | TranslatorGovernanceContinuityGraph, 7L invariants | CLEAR — single authority |
| cad_semantics | Semantic continuity (CAD hints) | ContinuityTarget enum, RimSemantics | WEAK — advisory, consumption unclear |
| CAM runtime | Manufacturing continuity (tier) | TopologyTier enum, validation behavior | MEDIUM — tier collision |

**Status:** Unlike geometry (multiple claimants), continuity has clear single authorities per domain. Risk is terminology collision, not authority ambiguity.

---

## 6. Ownership Candidates

### For Geometric Continuity

| Candidate | Evidence | Gaps |
|-----------|----------|------|
| **CAM topology_builder** | ContinuityLevel, ContinuityMetadata, validate_continuity() | None — clear authority |

**Status:** Single candidate, strong evidence.

### For Governance Continuity

| Candidate | Evidence | Gaps |
|-----------|----------|------|
| **Governance ledger (7L)** | TranslatorGovernanceContinuityGraph, 7L invariants, replay_governance_trace() | None — clear authority |

**Status:** Single candidate, strong evidence with model-enforced invariants.

### For Semantic Continuity

| Candidate | Evidence | Gaps |
|-----------|----------|------|
| **cad_semantics** | ContinuityTarget, RimSemantics | Consumption path unclear |

**Status:** Single candidate, weak due to advisory-only status and consumption gap.

### For Manufacturing Continuity

| Candidate | Evidence | Gaps |
|-----------|----------|------|
| **CAM runtime** | TopologyTier, tier-based validation | Tier term collision (COLL-G004) |

**Status:** Single candidate, medium due to tier collision.

---

## 7. Affected Domains

### Directly Affected

| Domain | Impact | Priority |
|--------|--------|----------|
| CAM topology_builder | Owns geometric continuity | LOW (already clear) |
| Governance ledger | Owns governance continuity | LOW (already clear) |
| cad_semantics | Advisory continuity | MEDIUM (document status) |
| CAM runtime | TopologyTier disambiguation | MEDIUM (tier collision) |

### Indirectly Affected

| Domain | Impact | Priority |
|--------|--------|----------|
| Export/Serialization | May consume ContinuityTarget | LOW |
| CAD translators | May consume ContinuityTarget | LOW |

---

## 8. Propagation Analysis Summary

### Healthy Paths

| Path | Status | Evidence |
|------|--------|----------|
| Geometric continuity | HEALTHY | Contained in topology_builder |
| Governance continuity | HEALTHY | 7L invariants enforce isolation |
| Validation flow | HEALTHY | Clear tier-based behavior |

### Unclear Paths

| Path | Risk | Mechanism |
|------|------|-----------|
| ContinuityTarget → ??? | MEDIUM | Advisory hint consumption path unknown |

### Full Analysis

See: `C2_CONTINUITY_PROPAGATION_ANALYSIS.md` for complete flow diagrams.

---

## 9. Pattern Impact Assessment

### Patterns to Preserve

| Pattern | Source | Impact |
|---------|--------|--------|
| 7L invariants | Governance continuity | Must preserve |
| Geometric G0/G1/G2 semantics | topology_builder | Must preserve |
| Tier-based validation | CAM runtime | Must preserve |

### Patterns at Risk

| Pattern | Risk | Mitigation |
|---------|------|------------|
| Terminology overload | Reader confusion | Namespace prefixing |
| Advisory vs enforcement | False confidence | Documentation |
| Tier collision | Semantic drift | Domain prefix |

---

## 10. Constitutional Risks

### Flattening Dangers

| Risk | Description | Mitigation |
|------|-------------|------------|
| Geometric/governance collapse | G0/G1/G2 confused with hash chains | Namespace separation |
| Advisory escalation | ContinuityTarget assumed to enforce | Document advisory status |
| Tier overload | TopologyTier confused with governance tier | Domain prefix |

### Anti-Patterns to Avoid

```
ANTI-PATTERN 1: Unprefixed "continuity" in ambiguous contexts
ANTI-PATTERN 2: Assuming ContinuityTarget enforces validation
ANTI-PATTERN 3: Conflating governance continuity with surface smoothness
ANTI-PATTERN 4: Using "tier" without domain prefix
ANTI-PATTERN 5: Treating advisory hints as requirements
```

---

## 11. Terminal Review Requirements

### Terminal 1 — Governance Integration (Complete)

- [x] Framework document created
- [x] Collision decomposition complete
- [x] Propagation analysis documented
- [x] Packet drafted

### Terminal 2 — Runtime/CAM (COMPLETE)

- [x] Review geometric continuity scope — CONTAINED in topology_builder
- [x] Validate TopologyTier boundaries — RUNTIME-SCOPED only
- [x] Confirm validation containment — STRONG containment
- [x] Flag runtime leakage risks — NONE detected

**Terminal 2 Review Document:** `C2_CONTINUITY_RUNTIME_REVIEW.md`

**Status:** APPROVED — CONTINUITY CONTAINMENT VALIDATED

**Key Findings:**
1. ContinuityTarget has NO runtime consumption path — verified by grep search
2. ContinuityLevel/ContinuityMetadata fully contained in topology_builder
3. TopologyTier is strictly runtime classification (not governance tier)
4. No bridge code between advisory (ContinuityTarget) and enforcement (ContinuityLevel)
5. Hard invariants preserved — continuity validation is internal, not serializer invocation

**Confirmed Boundaries:**
```
geometric_continuity (runtime) ≠ semantic_continuity (advisory)   CONFIRMED
validation_continuity ⊂ geometric_continuity                      CONFIRMED
runtime_tier (TopologyTier) ≠ governance_tier (1/2/3)             CONFIRMED
ContinuityMetadata is runtime-scoped                               CONFIRMED
ContinuityTarget has no runtime consumer                           CONFIRMED
```

### Terminal 3 — Geometry/Morphology/Topology (COMPLETE)

- [x] Identify continuity semantic domains — 6 IDENTIFIED
- [x] Map collision surfaces — 4 COLLISIONS DOCUMENTED
- [x] Document propagation paths — 3 PATHS ANALYZED
- [x] Classify flattening risks — 3 RISKS IDENTIFIED
- [x] Propose namespace strategy — DOMAIN PREFIXING PROPOSED

**Terminal 3 Review Documents:**
- `C2_CONTINUITY_SEMANTIC_DECOMPOSITION.md`
- `C2_CONTINUITY_NAMESPACE_COLLISIONS.md`
- `C2_CONTINUITY_PROPAGATION_ANALYSIS.md`
- `C2_CONTINUITY_LAYER_CANDIDATES.md`

**Key Findings:**
1. Unlike geometry, continuity domains have clear single authorities
2. Risk is terminology collision, not authority ambiguity
3. ContinuityTarget advisory nature needs documentation
4. Process continuity remains undefined (deferred)

### Terminal 4 — Provenance/Observational (COMPLETE)

- [x] Validate governance continuity isolation — CONFIRMED
- [x] Confirm 7L invariant coverage — STRONG
- [x] Review process continuity need — DEFERRED (implicit sufficient)
- [x] Flag governance/geometric blurring — BLOCKED via documentation

**Terminal 4 Review Document:** `C2_CONTINUITY_PROVENANCE_REVIEW.md`

**Status:** APPROVED WITH PROVENANCE CONDITIONS

**Key Findings:**
1. ContinuityTarget lacks provenance fields — acceptable for advisory hints
2. Advisory/validation continuity structurally distinct — impossible to confuse
3. Authority confusion blocked via explicit docstring
4. Acoustics consumer-without-authority pattern preserved

**Conditions:**
1. Continuity hints may propagate only when advisory authority-state remains visible
2. If ContinuityTarget is cached externally, caching system must preserve advisory classification

**Confirmed Boundaries:**
```
advisory continuity ≠ validation continuity   CONFIRMED
advisory continuity ≠ geometric continuity    CONFIRMED
advisory continuity ≠ authority provenance    CONFIRMED
```

### Terminal 5 — Export/Serialization (Pending)

- [ ] Identify ContinuityTarget consumers
- [ ] Validate advisory-only status
- [ ] Review CAD translator requirements
- [ ] Flag semantic→enforcement confusion

---

## 12. Ratification Criteria

### This Packet Does NOT Require Ratification

Per C2-A constitutional framing:
- Decomposition is arbitration preparation, not authority assignment
- Authority is already clear for primary domains
- Ratification deferred until federation phase

### When Ratification Would Be Required

Ratification required if this packet:
- Assigns new continuity ownership → NOT DONE
- Mandates implementation changes → NOT DONE
- Creates enforcement rules → NOT DONE
- Federates vocabulary → NOT DONE

---

## 13. Federation Blockers

### No Critical Blockers

Unlike Packet 001 (geometry), continuity has clear single authorities per domain.

### Non-Blocking Issues

| Issue | Description | Status |
|-------|-------------|--------|
| ContinuityTarget consumption | Advisory path unclear | Document, monitor |
| TopologyTier collision | Tier term overloaded | Namespace prefix |
| Process continuity undefined | No formal definition | Defer |

### Resolution Prerequisites

```
1. Terminal 2, 4, 5 complete packet review
2. ContinuityTarget advisory nature documented
3. TopologyTier namespace strategy defined
4. Process continuity formally deferred
```

---

## 14. Decomposition Proposal

### Layer Boundaries

| Layer | Definition | Authority |
|-------|------------|-----------|
| **geometric_continuity** | G0/G1/G2 surface junction smoothness | CAM topology_builder |
| **governance_continuity** | Immutable hash-linked review ancestry | Governance ledger (7L) |
| **semantic_continuity** | Advisory CAD construction hints | cad_semantics (advisory only) |
| **manufacturing_continuity** | Tier-based validation strictness | CAM runtime |
| **process_continuity** | Chain of custody integrity | UNDEFINED (deferred) |

### Namespace Rules

```
RULE 1: Use domain prefix when "continuity" appears in ambiguous context
RULE 2: ContinuityTarget is advisory only — document this explicitly
RULE 3: ContinuityLevel is enforcement — distinct from ContinuityTarget
RULE 4: TopologyTier is runtime_tier — distinct from governance_tier
RULE 5: Governance continuity is isolated — no geometric semantics
```

### Documentation Proposal

```
1. Add advisory docstring to ContinuityTarget
2. Add namespace guidance to module docstrings
3. Document tier disambiguation in COLL-G004 resolution
4. Formally defer process_continuity definition
```

---

## 15. Dissent Surfaces

### Unresolved Disagreements

| Surface | Issue | Status |
|---------|-------|--------|
| ContinuityTarget naming | Should it be renamed to ContinuityHint? | DEFERRED to C3 |
| Process continuity | Should it be formally defined? | DEFERRED — implicit sufficient |
| Validation as layer | Is validation_continuity a separate layer? | RESOLVED — subordinate |

### Deferred Questions

| Question | Reason Deferred |
|----------|-----------------|
| Should ContinuityTarget connect to topology_builder? | Advisory status is appropriate |
| Should process continuity be formalized? | Existing invariants sufficient |
| Why does ContinuityTarget omit G2? | Intentional — acoustic rarely needs G2 |

---

## 16. Escalation Triggers

### No Tier 3 Escalations (Human Arbitration)

Unlike geometry, continuity has clear authorities. No human arbitration required.

### Tier 2 Escalations (Addressed in Packet)

| Trigger | Evidence | Status |
|---------|----------|--------|
| Terminology overload | COLL-C001 | ADDRESSED — namespace strategy |
| Type duplication | COLL-C002 | ADDRESSED — document distinction |
| Tier collision | COLL-G004 | ADDRESSED — domain prefix |

---

## 17. Implementation Notes (Non-Binding)

### If Layer Decomposition Ratified

```
1. Add advisory docstring to ContinuityTarget
2. Add namespace guidance to topology_builder docstrings
3. Document TopologyTier as runtime_tier in COLL-G004 resolution
4. Add note about G2 intentional omission in ContinuityTarget
```

### If ContinuityTarget Renamed (C3)

```
1. Rename ContinuityTarget → ContinuityHint
2. Update RimSemantics.continuity_target → continuity_hint
3. Add deprecation notice for old name
4. Update documentation
```

---

## 18. Next Steps

### Immediate (C2-C Completion)

- [ ] Terminal 2, 4, 5 review this packet
- [ ] Document review findings
- [ ] Update packet with terminal feedback
- [ ] Surface additional dissent

### Deferred (C3 Enforcement)

- [ ] Consider ContinuityTarget → ContinuityHint rename
- [ ] Add lint rule for unprefixed "continuity"
- [ ] Document tier disambiguation
- [ ] Formalize process_continuity if needed

---

## 19. Related Documents

### C2-C Framework

- `C2_CONTINUITY_SEMANTIC_DECOMPOSITION.md` — Semantic domain analysis
- `C2_CONTINUITY_NAMESPACE_COLLISIONS.md` — Collision decomposition
- `C2_CONTINUITY_PROPAGATION_ANALYSIS.md` — Flow analysis
- `C2_CONTINUITY_LAYER_CANDIDATES.md` — Layer enumeration

### C2 Foundation

- `C2_ARBITRATION_FRAMEWORK.md` — Constitutional arbitration structure
- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Layer definitions
- `C2_TOPOLOGY_NAMESPACE_SEPARATION_REVIEW.md` — Topology split reference

### Code References

- `topology_builder/contracts.py` — ContinuityLevel, ContinuityMetadata, TopologyTier
- `topology_builder/validation.py` — validate_continuity()
- `translator_governance_continuity_graph.py` — Governance continuity
- `export/cad_semantics.py` — ContinuityTarget, RimSemantics

---

*C2-C Continuity Arbitration Packet 003 — Decomposition Complete*
