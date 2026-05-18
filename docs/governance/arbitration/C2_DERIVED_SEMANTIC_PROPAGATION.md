# C2 Derived Semantic Propagation

```
C2-E — CONSTITUTIONAL ARBITRATION PHASE
DERIVED SEMANTIC INFLUENCE PROPAGATION
HOW SEMANTIC INFLUENCE SPREADS THROUGH SYSTEMS
```

**Phase:** C2-E  
**Owner:** Terminal 4 (Provenance) + Terminal 1 (Governance)  
**Date:** 2026-05-18  
**Status:** Analysis Complete — Awaiting Cross-Terminal Review

---

## 1. Purpose

This document analyzes how semantic influence propagates through derived semantic systems.

This document:
- Maps influence propagation paths
- Identifies propagation amplification risks
- Establishes propagation provenance requirements
- Prevents silent authority accumulation

This document does NOT:
- Implement propagation controls
- Assign propagation ownership
- Mandate specific implementations

---

## 2. Propagation Principle

### 2.1 Core Insight

```
Semantic influence propagates through operational paths.
Each propagation step can accumulate apparent authority.
Without provenance tracking, propagated semantics become orphaned.
Orphaned semantics silently harden into authority.
```

### 2.2 Propagation vs Authority

| Property | Propagation | Authority |
|----------|-------------|-----------|
| Spreads semantics | YES | N/A |
| Creates semantics | NO | YES |
| Accumulates influence | YES | N/A |
| Creates legitimacy | NO | YES |
| Requires provenance | YES | YES |

### 2.3 Constitutional Rule

```
Propagation of semantic influence
does not create semantic authority.

But propagation without provenance
creates the appearance of authority.
```

---

## 3. Propagation Path Analysis

### 3.1 Path Types

| Path Type | Description | Risk Level |
|-----------|-------------|------------|
| Linear | A → B → C | MEDIUM |
| Branching | A → B, A → C | HIGH |
| Converging | A → C, B → C | HIGH |
| Cyclic | A → B → A | CRITICAL |
| Cross-domain | Domain X → Domain Y | HIGH |

### 3.2 Linear Propagation

```
Source → System A → System B → Consumer

Each step:
- Inherits provenance from previous
- May transform representation
- May add derivation

Risk: Provenance chain becomes invisible at end.
```

### 3.3 Branching Propagation

```
Source → System A → Consumer 1
      └─→ System B → Consumer 2

Risk: Consumers receive same semantics
      with different provenance chains.
      Comparison reveals provenance divergence.
```

### 3.4 Converging Propagation

```
Source A → Aggregator → Consumer
Source B ───┘

Risk: Aggregation flattens provenance.
      Consumer cannot distinguish sources.
      Authority ambiguity emerges.
```

### 3.5 Cyclic Propagation

```
System A → System B → System A

Risk: Semantic influence amplifies.
      Provenance loops create confusion.
      Authority becomes circular.
```

### 3.6 Cross-Domain Propagation

```
Domain X (Geometry) → Translator → Domain Y (Acoustics)

Risk: Domain authority boundaries crossed.
      Consumer-without-authority may be violated.
      Semantic meaning may mutate.
```

---

## 4. Propagation Through Categories

### 4.1 Evaluator Propagation

```
Source → Evaluator → Evaluation Result → Consumer

Provenance requirement:
  Result carries PROV_DERIVATION
  Result references evaluated source
  Result does NOT claim authority over source
```

**Risk paths:**
| Path | Risk |
|------|------|
| Evaluation → Downstream validator | Evaluation becomes validation criterion |
| Evaluation → Cache | Evaluation hardens into cached truth |
| Evaluation → Export | Evaluation propagates beyond scope |

### 4.2 Validator Propagation

```
Source → Validator → Approval/Rejection → Consumer

Provenance requirement:
  Decision carries constraint provenance
  Decision references validation criteria source
  Decision does NOT define semantic validity
```

**Risk paths:**
| Path | Risk |
|------|------|
| Validation → Gate | Validation becomes semantic law |
| Validation → Analyzer | Validation influences analysis |
| Validation → Cache | Validation status hardens |

### 4.3 Analyzer Propagation

```
Source → Analyzer → Derived Insight → Consumer

Provenance requirement:
  Insight carries PROV_DERIVATION + PROV_EPISTEMIC
  Insight references analyzed source
  Insight carries confidence/uncertainty markers
```

**Risk paths:**
| Path | Risk |
|------|------|
| Analysis → Cache | Derived value becomes cached authority |
| Analysis → Validator | Derived value becomes validation criterion |
| Analysis → Export | Derived value propagates as truth |

### 4.4 Translator Propagation

```
Source Format → Translator → Target Format → Consumer

Provenance requirement:
  Output carries PROV_TRANSFORMATION
  Output references source format and version
  Output documents transformation rules applied
```

**Risk paths:**
| Path | Risk |
|------|------|
| Translation → External system | External treats output as canonical |
| Translation → Re-import | Translated form becomes source |
| Translation → Archive | Format becomes historical authority |

### 4.5 Cache Propagation

```
Source → Cache → Cached Copy → Consumer

Provenance requirement:
  Copy MUST preserve source provenance
  Copy MUST preserve source authority-state
  Copy carries temporal marker (when cached)
```

**Risk paths:**
| Path | Risk |
|------|------|
| Cache → Multiple consumers | Cache becomes de facto authority |
| Cache → Long-term storage | Cached value outlives source validity |
| Cache → Derivation | Cache feeds into derivation chain |

### 4.6 Serializer Propagation

```
Source → Serializer → Serialized Form → Storage/Transmission → Consumer

Provenance requirement:
  Serialized form carries PROV_TRANSFORMATION + PROV_ARCHIVE
  Serialized form documents encoding format
  Export quarantine enforced
```

**Risk paths:**
| Path | Risk |
|------|------|
| Serialization → External consumption | External treats as authoritative |
| Serialization → Archive | Archive becomes source of truth |
| Serialization → Re-import | Serialized form replaces source |

---

## 5. Propagation Amplification

### 5.1 Amplification Mechanism

```
Each propagation step can amplify apparent authority:

Step 1: Source (authority-state: derived)
Step 2: Cached (authority-state: derived, but "always available")
Step 3: Validated (authority-state: derived, but "passed validation")
Step 4: Exported (authority-state: derived, but "official export")
Step 5: Consumed externally (authority-state: assumed canonical)
```

### 5.2 Amplification Factors

| Factor | Amplification Effect |
|--------|---------------------|
| Frequency of access | "Often used" → "must be authoritative" |
| Validation passage | "Passed checks" → "must be correct" |
| Export inclusion | "In official export" → "must be canonical" |
| Cache persistence | "Always available" → "must be stable truth" |
| Cross-system consumption | "Used by X" → "authoritative for X" |

### 5.3 Amplification Prevention

| Prevention | Mechanism |
|------------|-----------|
| Provenance persistence | Authority-state visible at each step |
| Non-authority markers | Explicit "NOT authoritative" at each step |
| Scope limitation | Propagation scope documented |
| Temporal markers | When propagated, not "when true" |

---

## 6. High-Risk Propagation Paths

### 6.1 Critical Path: Derived → Cached → Exported → External

```
MOST DANGEROUS PROPAGATION PATH:

1. Authoritative source
2. → Derived value computed (PROV_DERIVATION)
3. → Derived value cached (provenance may be lost)
4. → Cached value exported (PROV_TRANSFORMATION added)
5. → External system imports
6. → External treats as authoritative

At step 6, derived value appears canonical.
```

**Prevention:**
- Cache MUST preserve PROV_DERIVATION
- Export MUST preserve source authority-state
- Export documentation MUST state non-canonical status

### 6.2 Critical Path: Validation → Gate → Semantic Law

```
1. Validation criteria established
2. → Validator enforces criteria
3. → Validation becomes deployment gate
4. → "Must pass validation" becomes "semantically correct"
5. → Validation criteria become semantic law

At step 5, operational constraint becomes ontology.
```

**Prevention:**
- Constraint source explicitly documented
- Validation ≠ semantic definition explicit
- Operational scope limitation enforced

### 6.3 Critical Path: Analysis → Repeated Use → Authority

```
1. Source analyzed
2. → Derived insight produced
3. → Insight used repeatedly
4. → Insight cached for convenience
5. → "Always used" becomes "must be authoritative"

At step 5, usage frequency implies authority.
```

**Prevention:**
- PROV_DERIVATION persists through usage
- PROV_EPISTEMIC markers maintained
- Non-authority markers at each consumption point

### 6.4 Critical Path: Translation → Re-Import → Source Replacement

```
1. Authoritative source
2. → Translator produces external format
3. → External format archived
4. → Original source lost or outdated
5. → Translated format re-imported
6. → Re-import becomes new source

At step 6, translation has replaced authority.
```

**Prevention:**
- PROV_TRANSFORMATION prevents authority claim
- Re-import carries "translated origin" marker
- Original source reference preserved

---

## 7. Cross-Domain Propagation

### 7.1 Domain Boundary Crossing

```
Semantic influence crossing domain boundaries
is particularly risky because:
- Consumer-without-authority may be violated
- Domain-specific meaning may mutate
- Authority ownership becomes ambiguous
```

### 7.2 Cross-Domain Examples

| From Domain | To Domain | Risk |
|-------------|-----------|------|
| Geometry | Acoustics | Geometry semantics consumed as acoustic authority |
| Topology | Manufacturing | Topology relationships become manufacturing constraints |
| Morphology | Export | Morphology classification becomes export category |
| Runtime | Governance | Runtime state becomes governance truth |

### 7.3 Cross-Domain Requirements

| Requirement | Purpose |
|-------------|---------|
| Domain boundary explicit | Where semantics crossed |
| Consumer interface used | Not direct authority access |
| Domain authority preserved | Consuming domain does not claim ownership |
| Transformation documented | How semantics were adapted |

---

## 8. Propagation Provenance Requirements

### 8.1 Minimum Provenance at Each Step

| Step Type | Required Provenance |
|-----------|---------------------|
| Derivation | PROV_DERIVATION |
| Transformation | PROV_TRANSFORMATION |
| Caching | Source provenance preserved + temporal marker |
| Validation | Constraint provenance |
| Export | PROV_TRANSFORMATION + scope documentation |

### 8.2 Provenance Chain Visibility

```
At any point in propagation, it must be possible to answer:
1. Where did this semantic value originate?
2. What transformations occurred?
3. What derivations were computed?
4. What authority-state applies?
5. What is NOT claimed by this value?
```

### 8.3 Provenance Loss Detection

```
If at any propagation step:
- Source cannot be identified → PROVENANCE LOSS
- Authority-state cannot be determined → PROVENANCE LOSS
- Transformation history is invisible → PROVENANCE LOSS

Provenance loss creates authority ambiguity.
Authority ambiguity enables silent escalation.
```

---

## 9. Propagation Rules

### 9.1 Preservation Rules

```
RULE PP1: Source provenance must propagate with data
RULE PP2: Authority-state must persist through propagation
RULE PP3: Transformations must be documented
RULE PP4: Derivations must be visible
RULE PP5: Non-authority markers must propagate
```

### 9.2 Prohibition Rules

```
RULE PN1: Propagation cannot create authority
RULE PN2: Propagation cannot escalate authority-state
RULE PN3: Propagation cannot erase provenance
RULE PN4: Cross-domain propagation cannot violate consumer-without-authority
RULE PN5: Cyclic propagation cannot create circular authority
```

### 9.3 Documentation Rules

```
RULE PD1: High-risk propagation paths must be documented
RULE PD2: Cross-domain propagation must be explicit
RULE PD3: Amplification factors must be acknowledged
RULE PD4: Propagation scope must be limited and documented
```

---

## 10. Propagation Monitoring

### 10.1 Detection Signals

| Signal | Indicates |
|--------|-----------|
| Provenance missing at consumption | Propagation chain broken |
| Authority-state changed without governance | Silent escalation |
| Cross-domain consumption without interface | Consumer-without-authority violated |
| Cyclic reference detected | Circular authority risk |
| Cache treated as source | Hardening occurring |

### 10.2 Structural Detection

```python
# Detection: Propagation without provenance
if semantic_value.propagated and not semantic_value.has_propagation_provenance():
    raise PropagationViolation("Propagated value missing provenance chain")

# Detection: Authority escalation through propagation
if source.authority_state == "derived" and target.authority_state == "canonical":
    raise PropagationViolation("Propagation cannot escalate authority-state")

# Detection: Cross-domain without consumer interface
if source.domain != target.domain and not target.uses_consumer_interface():
    raise PropagationViolation("Cross-domain propagation requires consumer interface")
```

---

## 11. Terminal Responsibilities

### Terminal 4 — Provenance (Primary for Propagation)

- [x] Propagation path analysis complete
- [x] Provenance requirements documented
- [x] Amplification factors identified
- [ ] Cross-terminal review integration

### Terminal 1 — Governance

- [ ] Propagation rule validation
- [ ] Cross-domain boundary review
- [ ] Authority escalation prevention verification

---

## 12. Related Documents

### C2-E Documents

- `C2_DERIVED_SEMANTIC_SYSTEMS.md` — Primary framework
- `C2_DERIVED_SEMANTIC_CLASSIFICATIONS.md` — Category decomposition
- `C2_DERIVED_SEMANTIC_RISKS.md` — Escalation surfaces
- `packets/C2_DERIVED_SEMANTIC_ARBITRATION_PACKET_005.md` — Formal packet

### C2-C Foundation

- `C2_PROVENANCE_PROPAGATION_REQUIREMENTS.md` — General provenance propagation

---

*C2-E Derived Semantic Propagation — How Semantic Influence Spreads Through Systems*
