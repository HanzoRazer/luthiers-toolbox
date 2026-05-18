# C2 Geometry Arbitration Packet 001

```
C2-A — CONSTITUTIONAL ARBITRATION PHASE
PACKET 001 — GEOMETRY LAYER DECOMPOSITION
AUTHORITATIVE vs DERIVED vs PRESENTATION
```

**Phase:** C2-A  
**Owner:** Terminal 1 (Governance Lead) + Terminal 3 (Geometry Arbitration)  
**Date:** 2026-05-18  
**Status:** DECOMPOSITION COMPLETE — RATIFICATION NOT REQUIRED

---

## 1. Authority Statement

This packet documents geometry layer decomposition for constitutional arbitration.

This packet:
- Proposes layer boundaries
- Documents evidence
- Identifies candidates
- Surfaces tensions

This packet does NOT:
- Ratify authority
- Choose winners
- Mandate implementation
- Create enforcement

**Outcome Status:** May be unresolved, deferred, or partially decomposed.

---

## 2. Packet Subject

### Arbitration Question

```
How should the repository distinguish:
  - Authoritative geometry (canonical truth)
  - Derived geometry (computed interpretation)
  - Presentation geometry (display values)
```

### Why This Matters

C1 inventory discovered:
- Multiple systems producing geometry values
- No clear authoritative geometry origin
- Derived values potentially treated as canonical
- Presentation values potentially accumulating authority
- Sandbox geometry escaping to production

Without layer decomposition:
- Authority origin remains ambiguous
- Derived values may escalate to authority
- Presentation may become de facto truth
- Sandbox may silently federate

---

## 3. Frozen Evidence References

### C1 Strategic Findings

| Finding | Location | Relevance |
|---------|----------|-----------|
| Geometry authority risk surface | C1_STRATEGIC_FINDINGS.md §7 | Central blocking dependency |
| Consumer-without-authority pattern | C1_STRATEGIC_FINDINGS.md §3.A | Healthy consumption example |
| Provenance decomposition | C1_STRATEGIC_FINDINGS.md §5 | Derived values need provenance |
| IBG sandbox pressure | C1_STRATEGIC_FINDINGS.md §9 | Sandbox vocabulary risk |

### C1 Inventory Evidence

| Source | Location | Relevance |
|--------|----------|-----------|
| Geometry inventory | geometry_morphology_topology/SEMANTIC_INVENTORY.md | 16 terms inventoried |
| Acoustics inventory | acoustics_observational/SEMANTIC_INVENTORY.md | Healthy consumer pattern |
| Export inventory | export_serialization/SEMANTIC_INVENTORY.md | Propagation paths |

---

## 4. Collision References

### Primary Collisions

| ID | Term | Risk | Relevance |
|----|------|------|-----------|
| COLL-G001 | topology | High | Semantic divergence |
| COLL-G002 | morphology | High | Authority gap |
| COLL-E002 | IBG propagation | High | Sandbox escape |
| COLL-G003 | zone/region | Medium | Vocabulary overlap |
| COLL-G005 | primitive | Medium | Ungoverned vocabulary |

### Cross-Reference Collisions

| ID | Term | Risk | Relevance |
|----|------|------|-----------|
| COL-ACOU-001 | confidence | Medium | Derived value qualifier |
| COLL-E001 | serialization | Medium | Export authority boundary |

---

## 5. Authority Claimants

### Current Authority Assertions

| System | Claim | Evidence | Constitutional Status |
|--------|-------|----------|----------------------|
| IBG MorphologyDescriptor | De facto morphology authority | Creates classifications consumed downstream | SANDBOX — no constitutional registration |
| Instrument Spec JSON | Canonical dimensions | Contains user-provided measurements | USER INPUT — not system authority |
| Template Definition | Geometry constraints | User-created geometric boundaries | USER INPUT — not system authority |
| Vectorizer | Geometry extraction | Creates geometry from images | UNCLEAR — extraction vs creation ambiguous |
| MRP 7M Registry | Governance registration | Constitutional term registration | GOVERNANCE — documents, may not create |

**Status:** Multiple claimants, no single constitutional authority. IBG asserts de facto authority without registration.

---

## 7. Ownership Candidates

### For Authoritative Geometry

| Candidate | Evidence | Gaps |
|-----------|----------|------|
| **Instrument Spec JSON** | Contains canonical dimensions | User input, not system truth |
| **Template Definition** | User-created geometry constraints | User authority vs system authority |
| **Vectorizer Extraction** | Creates geometry from external source | Input is external, ownership unclear |
| **MRP 7M Registry** | Constitutional registration framework | Registry documents, may not create |
| **CAD Import** | External CAD file geometry | External origin, not repository truth |

**Status:** No clear single candidate. Geometry authority may be contextual.

### For Derived Geometry

| System | Derivation Type | Status |
|--------|-----------------|--------|
| Acoustics | Helmholtz estimates from aperture | HEALTHY — carries provenance |
| IBG | Zone radii from outline | SANDBOX — containment needed |
| Vectorizer | Scale computation | UNCLEAR — may be derivation or creation |
| Corpus | Classifications from analysis | ACCUMULATION — needs provenance |

### For Presentation Geometry

| System | Purpose | Status |
|--------|---------|--------|
| UI Components | Display rendering | HEALTHY — no authority claim |
| Preview Systems | Visual feedback | HEALTHY — ephemeral |
| SVG Renderers | Format output | HEALTHY — format-scoped |

---

## 8. Affected Domains

### Directly Affected

| Domain | Impact | Priority |
|--------|--------|----------|
| IBG | Sandbox containment | CRITICAL |
| Vectorizer | Authority boundary | HIGH |
| Export | Propagation control | HIGH |
| MRP | Registry clarification | MEDIUM |

### Indirectly Affected

| Domain | Impact | Priority |
|--------|--------|----------|
| Acoustics | Consumer pattern preservation | LOW |
| CAM Runtime | Operational boundary | LOW |
| Visualization | Presentation boundary | LOW |

---

## 9. Propagation Analysis Summary

### High-Risk Paths

| Path | Risk | Mechanism | Reference |
|------|------|-----------|-----------|
| IBG → Export | HIGH | IBGMorphologyExtension carries sandbox data to production output | C2_GEOMETRY_PROPAGATION_ANALYSIS.md §2.2 |
| IBG → Corpus | MEDIUM | Training data accumulates authority weight through ML pipelines | C2_GEOMETRY_PROPAGATION_ANALYSIS.md §2.3 |
| Derived → Cached | HIGH | Cached derived values escalate to de facto authority | C2_GEOMETRY_PROPAGATION_ANALYSIS.md §2.6 |

### Healthy Paths

| Path | Status | Evidence |
|------|--------|----------|
| CAM Runtime | Contained | Hard invariants enforce non-authority (`observationalOnly: Literal[True]`) |
| Export Translators | Contained | Quarantine enforcement (`serializer_invocation_allowed: false`) |
| Acoustics | Reference | Consumer-without-authority discipline, mandatory confidence |

### Full Analysis

See: `C2_GEOMETRY_PROPAGATION_ANALYSIS.md` for complete flow diagrams and containment recommendations.

---

## 10. Pattern Impact Assessment

### Patterns to Preserve

| Pattern | Source | Impact |
|---------|--------|--------|
| Consumer-without-authority | Acoustics | Must preserve |
| Mandatory confidence | Acoustics | Must preserve |
| Required assumptions | Acoustics | Must preserve |
| Provenance decomposition | C1 findings | Must preserve |
| Hard invariants | CAM Runtime | Must preserve |

### Patterns at Risk

| Pattern | Risk | Mitigation |
|---------|------|------------|
| IBG sandbox containment | Escape to production | Advisory-only flag |
| Derived provenance | Loss of derivation chain | Mandatory provenance |
| Authority boundary | Blurring | Explicit layer documentation |

---

## 11. Terminal Review Requirements

### Terminal 1 — Governance Integration (Complete)

- [x] Framework document created
- [x] Ownership topology mapped
- [x] Propagation analysis documented
- [x] Packet drafted

### Terminal 2 — Runtime/CAM (Pending)

- [ ] Review runtime geometry flow
- [ ] Validate operational boundaries
- [ ] Confirm hard invariant preservation
- [ ] Flag runtime leakage risks

### Terminal 3 — Geometry/Morphology/Topology (COMPLETE)

- [x] Review namespace collision decomposition — VALIDATED with additions
- [x] Validate IBG containment proposal — VALIDATED with recommendations
- [x] Confirm topology semantic split — CONFIRMED
- [x] Flag authority candidate gaps — 3 gaps identified

**Terminal 3 Review Document:** `C2_TOPOLOGY_NAMESPACE_SEPARATION_REVIEW.md`

**Key Findings:**
1. morphology_topology vs surface_topology split is ADEQUATE
2. Two additional collisions identified: `partition`, `boundary`
3. IBG containment requires namespace documentation beyond advisory flag
4. manufacturing_topology may be redundant with surface_topology (dissent recorded)

**Authority Candidate Gaps Flagged:**
- No authority candidate for spatial_partition vs manufacturing_partition
- No authority candidate for boundary disambiguation
- Unclear if manufacturing_topology is separate from surface_topology

### Terminal 4 — Provenance/Observational (Complete)

- [x] Validate consumer pattern preservation
- [x] Review derived geometry provenance requirements
- [x] Confirm confidence/assumptions patterns protected
- [x] Flag authority escalation risks

**Review Document:** `C2_PACKET_001_TERMINAL_4_PROVENANCE_REVIEW.md`  
**Status:** CONDITIONALLY APPROVED  
**Reviewer:** Terminal 1 (acting as Terminal 4)

### Terminal 5 — Export/Serialization (Pending)

- [ ] Review export propagation paths
- [ ] Validate serializer boundaries
- [ ] Confirm IBGMorphologyExtension containment
- [ ] Flag format authority risks

---

## 12. Ratification Criteria

### This Packet Does NOT Require Ratification

Per C2-A constitutional framing:
- Decomposition is arbitration preparation, not authority assignment
- Ratification deferred until federation phase
- Outcome may remain unresolved

### When Ratification Would Be Required

Ratification required if this packet:
- Assigns canonical geometry ownership → NOT DONE
- Mandates implementation changes → NOT DONE
- Creates enforcement rules → NOT DONE
- Federates vocabulary → NOT DONE

---

## 13. Federation Blockers

### Critical Blockers

| Blocker | Description | Resolution Path |
|---------|-------------|-----------------|
| Authoritative geometry origin unresolved | No single candidate has clear evidence for canonical ownership | Human arbitration required |
| IBG sandbox containment incomplete | IBGMorphologyExtension propagates sandbox vocabulary to production | Add advisory_only flag, document constraints |
| Vectorizer authority boundary undefined | Extraction vs creation semantics unclear | Vectorizer domain arbitration packet |

### Non-Blocking Issues

| Issue | Description | Status |
|-------|-------------|--------|
| Topology semantic split | morphology_topology vs surface_topology | Decomposed — namespace strategy defined |
| Zone/region vocabulary overlap | IBG zones vs MRP regions | Decomposed — namespace strategy defined |
| Tier terminology overload | Runtime vs governance vs execution tiers | Decomposed — domain-prefixed solution |

### Resolution Prerequisites

```
1. Terminal 2-5 complete packet review
2. IBG containment proposal accepted
3. Human arbitration on geometry authority origin
4. Governance graduation gate defined for sandbox escape
```

---

## 14. Decomposition Proposal

### Layer Boundaries

| Layer | Definition | Authority |
|-------|------------|-----------|
| **authoritative_geometry** | Canonical dimensional truth | UNRESOLVED — requires human arbitration |
| **derived_geometry** | Computed interpretation with provenance | NON-AUTHORITATIVE — must carry provenance |
| **presentation_geometry** | Display values for rendering | NON-AUTHORITATIVE — ephemeral |

### Propagation Rules

```
RULE 1: Derived geometry must carry provenance
RULE 2: Derived geometry must carry confidence/assumptions
RULE 3: Presentation geometry must not persist as authority
RULE 4: Sandbox geometry must not escape without governance
RULE 5: Serialization does not create authority
```

### IBG Containment Proposal

```
1. Mark IBGMorphologyExtension with advisory_only: true
2. Document downstream consumption constraints
3. Block sandbox vocabulary from authoritative paths
4. Require governance registration for sandbox graduation
```

---

## 15. Constitutional Risks

### Flattening Dangers

| Risk | Description | Mitigation |
|------|-------------|------------|
| Layer collapse | Merging derived into authoritative | Maintain explicit layer separation |
| Authority drift | Derived becoming de facto truth | Provenance requirements |
| Sandbox escape | IBG vocabulary in production | Advisory-only flag |
| Format authority | Serialization defining truth | Serializer role enforcement |

### Anti-Patterns to Avoid

```
ANTI-PATTERN 1: Derived values without provenance
ANTI-PATTERN 2: Presentation values becoming canonical
ANTI-PATTERN 3: Sandbox vocabulary treated as authoritative
ANTI-PATTERN 4: Format constraints becoming geometry truth
ANTI-PATTERN 5: Usage frequency implying authority
```

---

## 16. Escalation Triggers

### Tier 3 Escalations (Human Arbitration Required)

| Trigger | Evidence | Status |
|---------|----------|--------|
| Authoritative geometry origin | No single candidate with clear evidence | ACTIVE — requires human decision |
| Vectorizer extraction authority | Is extraction derivation or creation? | ACTIVE — requires human judgment |
| Template/user authority boundary | Does user input create system authority? | ACTIVE — requires human judgment |

### Tier 2 Escalations (Arbitration Packet Required)

| Trigger | Evidence | Status |
|---------|----------|--------|
| IBG sandbox escape | IBGMorphologyExtension propagates to export | ADDRESSED — containment proposal in packet |
| Derived value escalation | Cached/accumulated values becoming authority | ADDRESSED — provenance requirements proposed |
| Multiple topology semantics | morphology_topology vs surface_topology collision | ADDRESSED — namespace decomposition complete |

### Escalation Protocol

Per C2_ARBITRATION_FRAMEWORK.md:
1. Tier 2 escalations: Address via packet decomposition and proposals
2. Tier 3 escalations: Flag for human arbitration, document in packet
3. Tier 4 escalations: None identified for this packet

---

## 17. Dissent Surfaces

### Unresolved Disagreements

| Surface | Issue | Status |
|---------|-------|--------|
| Vectorizer authority | Is extraction derivation or creation? | UNRESOLVED |
| User input authority | Does template definition create system authority? | UNRESOLVED |
| Registry relationship | Does 7M registration create or document authority? | UNRESOLVED |
| IBG graduation | What governance gate enables sandbox escape? | UNRESOLVED |

### Deferred Questions

| Question | Reason Deferred |
|----------|-----------------|
| Who owns body outline? | No single candidate identified |
| Where does authority originate? | Context-dependent |
| Can derived become authoritative? | Requires human judgment |
| When can sandbox graduate? | Requires governance criteria |

---

## 18. Implementation Notes (Non-Binding)

### If Layer Decomposition Ratified

```
1. Add layer markers to geometry-producing systems
2. Require provenance on all derived geometry
3. Add advisory_only flag to IBG propagation
4. Document layer boundaries in code
5. Create layer validation checks (C3 enforcement)
```

### If IBG Containment Ratified

```
1. Add advisory_only: bool = True to IBGMorphologyExtension
2. Create IBGAdvisoryData type with explicit constraints
3. Document consumption constraints for translators
4. Log warnings on IBG data entering production paths
```

---

## 19. Next Steps

### Immediate (C2-A Completion)

- [ ] Terminal 2, 3, 4, 5 review this packet
- [ ] Document review findings
- [ ] Update packet with terminal feedback
- [ ] Surface additional dissent

### Deferred (C2 Federation)

- [ ] Human arbitration on authority origin
- [ ] IBG governance graduation criteria
- [ ] Vectorizer authority boundary decision
- [ ] Registry/implementation relationship clarification

---

## 20. Related Documents

### C2 Framework

- `C2_ARBITRATION_FRAMEWORK.md` — Constitutional arbitration structure
- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Layer definitions
- `C2_GEOMETRY_OWNERSHIP_TOPOLOGY.md` — Domain mapping
- `C2_GEOMETRY_NAMESPACE_COLLISIONS.md` — Term decomposition
- `C2_GEOMETRY_PROPAGATION_ANALYSIS.md` — Flow analysis

### C1 Foundation

- `C1_STRATEGIC_FINDINGS.md` — Cross-domain patterns
- `C1_SEMANTIC_INVENTORY_INDEX.md` — Inventory master index
- Domain collision logs — Evidence sources

### Pattern Preservation

- `CONSUMER_WITHOUT_AUTHORITY_PATTERN.md` — Healthy consumption
- `OBSERVATIONAL_SEMANTICS_BOUNDARY_NOTES.md` — Observation boundaries
- `ACOUSTICS_GOVERNANCE_REFERENCE_PATTERN.md` — Reference implementation

---

*C2-A Geometry Arbitration Packet 001 — Decomposition Complete*
