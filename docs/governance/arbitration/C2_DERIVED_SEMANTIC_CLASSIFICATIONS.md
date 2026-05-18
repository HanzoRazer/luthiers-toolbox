# C2 Derived Semantic Classifications

```
C2-E — CONSTITUTIONAL ARBITRATION PHASE
DERIVED SEMANTIC SYSTEM CATEGORY DECOMPOSITION
TAXONOMY FOR SEMANTIC-PRODUCING SYSTEMS
```

**Phase:** C2-E  
**Owner:** Terminal 1 (Governance) + Terminal 4 (Provenance)  
**Date:** 2026-05-18  
**Status:** Classification Complete — Awaiting Cross-Terminal Review

---

## 1. Purpose

This document decomposes derived semantic systems into constitutional categories.

This document:
- Defines each core category
- Maps category boundaries
- Documents category evidence
- Establishes category requirements
- Identifies category-specific risks

This document does NOT:
- Close the taxonomy permanently
- Assign implementation ownership
- Mandate specific implementations

---

## 2. Classification Framework

### 2.1 Framework Principle

```
The classification framework is constitutional.
The specific categories are empirical.
```

### 2.2 Category Inclusion Criteria

| Criterion | Requirement |
|-----------|-------------|
| Semantic influence | Must produce semantic output or constrain semantic paths |
| Non-authority | Must NOT inherently possess semantic authority |
| Escalation risk | Must present constitutional escalation risk |
| Evidence | Must have evidence in repository or likely future presence |

### 2.3 Category Evolution

```
Categories may be added as evidence emerges.
Categories may be refined as understanding deepens.
Categories may be split or merged based on operational evidence.
```

---

## 3. Core Categories (6)

### 3.1 Category Summary

| Category | Function | Risk | Provenance |
|----------|----------|------|------------|
| evaluator | assessment | hidden authority | PROV_DERIVATION |
| validator | gating | operational canonization | PROV_DERIVATION |
| analyzer | derivation | truth escalation | PROV_DERIVATION + PROV_EPISTEMIC |
| translator | transformation | semantic mutation | PROV_TRANSFORMATION |
| cache | persistence | hardening | inherited |
| serializer | propagation | amplification | PROV_TRANSFORMATION + PROV_ARCHIVE |

---

## 4. Evaluator Category

### 4.1 Definition

```
An evaluator is a derived semantic system that:
- Assesses semantic quality
- Produces evaluation results
- Reports semantic status

WITHOUT:
- Defining what is semantically correct
- Creating semantic authority
- Establishing semantic truth
```

### 4.2 Characteristics

| Property | Value |
|----------|-------|
| Input | Semantic data |
| Output | Evaluation result (pass/fail/score/classification) |
| Provenance | PROV_DERIVATION |
| Authority-state | derived |
| Non-goal | Semantic definition |

### 4.3 Repository Evidence

| Evidence Source | Evaluator Type |
|-----------------|----------------|
| Continuity evaluators | G0/G1/G2 junction quality assessment |
| Geometry validators | Dimension plausibility checking |
| Export validators | Format compliance checking |

### 4.4 Constitutional Requirements

| Requirement | Purpose |
|-------------|---------|
| Evaluation role explicit | "evaluator" not "definer" |
| Constraint provenance | Where evaluation criteria originated |
| Non-authority marker | Cannot define semantic truth |
| Scope limitation | Evaluation scope documented |
| PROV_DERIVATION | Constitutional provenance compliance |

### 4.5 Escalation Risk

```
RISK: Evaluation results treated as semantic truth
MECHANISM: "Good evaluation" becomes "correct semantics"
EXAMPLE: G2 continuity pass → "valid geometry"
PREVENTION: Explicit non-authority markers, PROV_DERIVATION enforcement
```

### 4.6 Anti-Patterns

```
ANTI-PATTERN: Evaluation defining correctness
ANTI-PATTERN: Evaluation score becoming canonical quality
ANTI-PATTERN: Evaluation frequency implying authority
ANTI-PATTERN: Evaluation criteria becoming semantic law
```

---

## 5. Validator Category

### 5.1 Definition

```
A validator is a derived semantic system that:
- Gates semantic transitions
- Approves or rejects semantic operations
- Enforces semantic constraints

WITHOUT:
- Defining what is semantically valid
- Creating semantic ownership
- Establishing semantic governance
```

### 5.2 Characteristics

| Property | Value |
|----------|-------|
| Input | Semantic operation request |
| Output | Approval/rejection decision |
| Provenance | PROV_DERIVATION + constraint source |
| Authority-state | operational |
| Non-goal | Semantic definition |

### 5.3 Repository Evidence

| Evidence Source | Validator Type |
|-----------------|----------------|
| topology_builder | Surface relationship validation |
| Export validators | Format constraint enforcement |
| Schema validators | Structure compliance checking |

### 5.4 Constitutional Requirements

| Requirement | Purpose |
|-------------|---------|
| Constraint source documented | Where validation rules originated |
| Operational scope | Validation is operational, not canonical |
| Non-authority marker | Gating ≠ ownership |
| Derivation provenance | Validation result is derived |

### 5.5 Escalation Risk

```
RISK: Validation criteria become semantic law
MECHANISM: "Must pass validation" becomes "semantically correct"
EXAMPLE: Manufacturability check → "valid morphology"
PREVENTION: Constraint provenance, operational authority-state
```

### 5.6 Anti-Patterns

```
ANTI-PATTERN: Validator defining semantic validity
ANTI-PATTERN: Validation pass becoming canonical status
ANTI-PATTERN: Validation rules becoming ontology
ANTI-PATTERN: Validator scope expanding to semantic ownership
```

---

## 6. Analyzer Category

### 6.1 Definition

```
An analyzer is a derived semantic system that:
- Derives insights from semantic data
- Produces derived observations
- Creates analytical interpretations

WITHOUT:
- Defining authoritative interpretations
- Creating observational truth
- Establishing analytical governance
```

### 6.2 Characteristics

| Property | Value |
|----------|-------|
| Input | Semantic data |
| Output | Derived insights/observations |
| Provenance | PROV_DERIVATION + PROV_EPISTEMIC |
| Authority-state | derived |
| Non-goal | Authoritative interpretation |

### 6.3 Repository Evidence

| Evidence Source | Analyzer Type |
|-----------------|----------------|
| Geometry analyzers | Derived measurement computation |
| Acoustic analyzers | Frequency/resonance derivation |
| Morphology analyzers | Shape classification |

### 6.4 Constitutional Requirements

| Requirement | Purpose |
|-------------|---------|
| Derivation chain visibility | How analysis was computed |
| Epistemic markers | Confidence/uncertainty explicit |
| Non-authority marker | Analysis ≠ authoritative truth |
| Source traceability | What was analyzed |

### 6.5 Escalation Risk

```
RISK: Derived observations treated as authoritative
MECHANISM: "Analysis shows X" becomes "X is true"
EXAMPLE: Computed zone_radius → "canonical body dimension"
PREVENTION: PROV_EPISTEMIC, derivation chain, non-authority markers
```

### 6.6 Anti-Patterns

```
ANTI-PATTERN: Analysis output becoming canonical
ANTI-PATTERN: Derived value replacing authoritative source
ANTI-PATTERN: Analytical interpretation becoming definition
ANTI-PATTERN: Repeated analysis implying authority
```

---

## 7. Translator Category

### 7.1 Definition

```
A translator is a derived semantic system that:
- Transforms semantic representations
- Converts between semantic formats
- Maps semantic vocabularies

WITHOUT:
- Defining canonical representations
- Creating format authority
- Establishing semantic meaning through format
```

### 7.2 Characteristics

| Property | Value |
|----------|-------|
| Input | Semantic data in source format |
| Output | Semantic data in target format |
| Provenance | PROV_TRANSFORMATION |
| Authority-state | operational |
| Non-goal | Canonical format definition |

### 7.3 Repository Evidence

| Evidence Source | Translator Type |
|-----------------|----------------|
| Export translators | Internal → external format |
| DXF generators | Geometry → DXF format |
| Schema translators | Version migration |

### 7.4 Constitutional Requirements

| Requirement | Purpose |
|-------------|---------|
| Transformation provenance | What transformation occurred |
| Quarantine enforcement | Translator cannot claim authority |
| Format documentation | Input/output formats explicit |
| Non-authority marker | Format ≠ semantic truth |

### 7.5 Escalation Risk

```
RISK: Transformation introduces semantic mutation
MECHANISM: Format conversion changes semantic meaning
EXAMPLE: Export format becomes "official representation"
PREVENTION: PROV_TRANSFORMATION, quarantine, non-authority markers
```

### 7.6 Anti-Patterns

```
ANTI-PATTERN: Translated output becoming canonical
ANTI-PATTERN: Format choice becoming semantic choice
ANTI-PATTERN: Re-import of translated data as authority
ANTI-PATTERN: Translator assumptions becoming ontology
```

---

## 8. Cache Category

### 8.1 Definition

```
A cache is a derived semantic system that:
- Persists semantic state for performance
- Stores and retrieves semantic data
- Maintains copies of semantic values

WITHOUT:
- Creating authoritative versions
- Defining semantic truth through persistence
- Establishing temporal authority
```

### 8.2 Characteristics

| Property | Value |
|----------|-------|
| Input | Semantic data from authoritative source |
| Output | Cached copy of semantic data |
| Provenance | Inherited from source (MUST preserve) |
| Authority-state | Inherited from source (MUST preserve) |
| Non-goal | Authority through persistence |

### 8.3 Repository Evidence

| Evidence Source | Cache Type |
|-----------------|------------|
| Derived geometry cache | Computed geometry persistence |
| Topology cache | Relationship persistence |
| Morphology descriptor cache | Classification persistence |

### 8.4 Constitutional Requirements

| Requirement | Purpose |
|-------------|---------|
| Source provenance preserved | Cache inherits source provenance |
| Authority-state preserved | Cache inherits authority-state |
| Derivation chain maintained | Original source traceable |
| Temporal marker | When cached, not "when true" |

### 8.5 Escalation Risk

```
RISK: Cached values harden into authority
MECHANISM: "Always available" becomes "authoritative"
EXAMPLE: Cached zone_radius → "canonical body dimension"
PREVENTION: Source provenance persistence, authority-state preservation
```

### 8.6 Anti-Patterns

```
ANTI-PATTERN: Cache becoming source of truth
ANTI-PATTERN: Cached value outliving source validity
ANTI-PATTERN: Cache persistence implying authority
ANTI-PATTERN: Cache access frequency implying legitimacy
```

---

## 9. Serializer Category

### 9.1 Definition

```
A serializer is a derived semantic system that:
- Encodes semantics for storage or transmission
- Converts semantic state to persistent form
- Prepares semantics for propagation

WITHOUT:
- Creating authoritative archives
- Defining semantic truth through encoding
- Establishing propagation authority
```

### 9.2 Characteristics

| Property | Value |
|----------|-------|
| Input | Semantic state |
| Output | Serialized/encoded form |
| Provenance | PROV_TRANSFORMATION + PROV_ARCHIVE |
| Authority-state | operational |
| Non-goal | Propagation authority |

### 9.3 Repository Evidence

| Evidence Source | Serializer Type |
|-----------------|-----------------|
| DXF serializers | Geometry → file format |
| JSON serializers | State → storage format |
| Export serializers | Internal → external format |

### 9.4 Constitutional Requirements

| Requirement | Purpose |
|-------------|---------|
| Export quarantine | Serializer cannot claim authority |
| Propagation documentation | What is being propagated |
| Format provenance | Serialization format documented |
| Non-authority marker | Format ≠ semantic truth |

### 9.5 Escalation Risk

```
RISK: Serialization amplifies semantic propagation
MECHANISM: Serialized form spreads beyond original scope
EXAMPLE: DXF export consumed as "official geometry"
PREVENTION: Export quarantine, propagation documentation
```

### 9.6 Anti-Patterns

```
ANTI-PATTERN: Serialized form becoming canonical
ANTI-PATTERN: Export format becoming definition
ANTI-PATTERN: Propagation implying authority
ANTI-PATTERN: Archive becoming source of truth
```

---

## 10. Future Category Candidates

### 10.1 Candidate List

| Candidate | Semantic Function | Constitutional Risk |
|-----------|-------------------|---------------------|
| recommender | semantic suggestion | preference canonization |
| ranker | semantic prioritization | hidden priority authority |
| classifier | semantic categorization | category authority escalation |
| aggregator | semantic combination | semantic flattening |
| observer/monitor | semantic observation | operational legitimacy inference |
| AI inference system | probabilistic semantic production | probabilistic ontology emergence |

### 10.2 Recommender (Candidate)

```
Function: Suggests semantic options based on context
Risk: Suggested options become "correct" options
Evidence needed: Recommendation systems in codebase
```

### 10.3 Ranker (Candidate)

```
Function: Orders semantic options by priority
Risk: Ranking order becomes semantic priority authority
Evidence needed: Ranking/sorting systems with semantic implications
```

### 10.4 Classifier (Candidate)

```
Function: Assigns semantic categories to data
Risk: Classification becomes category definition
Evidence needed: Classification systems (ML or rule-based)
```

### 10.5 Aggregator (Candidate)

```
Function: Combines multiple semantic inputs
Risk: Aggregation flattens semantic distinctions
Evidence needed: Summary/aggregation systems
```

### 10.6 Observer/Monitor (Candidate)

```
Function: Observes and reports semantic state
Risk: Observation becomes legitimacy inference
Evidence needed: Monitoring systems with semantic reporting
```

### 10.7 AI Inference System (Candidate)

```
Function: Produces probabilistic semantic outputs
Risk: Probabilistic outputs become ontological assertions
Evidence needed: ML/AI components producing semantic outputs
```

---

## 11. Category Boundary Analysis

### 11.1 Boundary Overlaps

| Category A | Category B | Overlap Area | Distinction |
|------------|------------|--------------|-------------|
| evaluator | validator | Both assess | Evaluator reports; validator gates |
| analyzer | evaluator | Both derive | Analyzer produces insights; evaluator produces status |
| translator | serializer | Both transform | Translator changes format; serializer encodes for storage |
| cache | serializer | Both persist | Cache optimizes access; serializer enables propagation |

### 11.2 Boundary Rules

```
RULE CB1: Categories may overlap operationally
RULE CB2: Overlap does not collapse categories
RULE CB3: Each category has distinct constitutional risk
RULE CB4: Composite systems carry all relevant category requirements
```

### 11.3 Composite Systems

```
A system may be multiple categories simultaneously.

Example: Export pipeline
  - Translator (format conversion)
  - Serializer (encoding for transmission)
  - Validator (format compliance checking)

Each category's constitutional requirements apply.
```

---

## 12. Classification Checklist

### 12.1 For Any Derived Semantic System

- [ ] Category identified (evaluator/validator/analyzer/translator/cache/serializer)
- [ ] Provenance type assigned
- [ ] Authority-state explicit
- [ ] Non-authority marker present
- [ ] Escalation risk documented
- [ ] Anti-patterns understood

### 12.2 Category-Specific Checklists

#### Evaluator
- [ ] Evaluation role explicit
- [ ] Constraint provenance documented
- [ ] Scope limitation defined

#### Validator
- [ ] Constraint source documented
- [ ] Operational scope explicit
- [ ] Gating ≠ ownership clear

#### Analyzer
- [ ] Derivation chain visible
- [ ] Epistemic markers present
- [ ] Source traceability maintained

#### Translator
- [ ] Transformation provenance documented
- [ ] Quarantine enforcement
- [ ] Format ≠ truth explicit

#### Cache
- [ ] Source provenance preserved
- [ ] Authority-state preserved
- [ ] Temporal marker present

#### Serializer
- [ ] Export quarantine enforced
- [ ] Propagation documented
- [ ] Format ≠ truth explicit

---

## 13. Related Documents

### C2-E Documents

- `C2_DERIVED_SEMANTIC_SYSTEMS.md` — Primary framework
- `C2_DERIVED_SEMANTIC_PROPAGATION.md` — Influence propagation
- `C2_DERIVED_SEMANTIC_RISKS.md` — Escalation surfaces
- `packets/C2_DERIVED_SEMANTIC_ARBITRATION_PACKET_005.md` — Formal packet

### Pattern Documents

- `../patterns/CONSUMER_WITHOUT_AUTHORITY_PATTERN.md` — Behavioral doctrine

---

*C2-E Derived Semantic Classifications — Taxonomy for Semantic-Producing Systems*
