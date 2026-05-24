# Sprint Architecture Handoff

**Sprint:** Constitutional Stabilization (Dev Orders 77–82)  
**Date Range:** 2026-05-23 to 2026-05-24  
**Repository:** tap-tone-pi  
**Cross-Repo:** luthiers-toolbox (downstream consumer)

---

## 1. Executive Summary

### Sprint Objectives

Transform tap-tone-pi from **governed instrumentation** into **constitutionally stabilized experimental epistemics** without changing the repository's core operational mission.

### Major Systems Worked On

| System | Scope |
|--------|-------|
| Governance Framework | Constitutional doctrine for measurement authority |
| Advisory Boundary | Runtime and semantic separation of advisory systems |
| Epistemic Classification | Formal taxonomy of data authority states |
| Presentation Semantics | Visual/semantic authority leakage prevention |
| AGE (Analyzer Guidance Engine) | Operational containment and presentation rules |

### Key Outcomes

1. **ADR-0009** (pre-existing) — Runtime boundary between MEASUREMENT and DECISION SUPPORT
2. **ADR-0010** — Advisory authority constitutional boundary with orthogonal authority domains
3. **ADR-0011** — Measurement authority constitutional definition (measurement ≠ truth)
4. **ADR-0012** — Epistemic status taxonomy (seven primary categories)
5. **AGE_CONTRACT.md** — Operational advisory containment rules
6. **ADVISORY_PRESENTATION_BOUNDARY.md** — Visual/semantic presentation rules
7. **CONSTITUTIONAL_CONTINUATION_NOTICE.md** — Mode transition to conditional stabilization

### Unresolved Blockers

None. Constitutional baseline is sufficient for operational development to resume.

### Architectural Direction

The ecosystem now operates in **conditional constitutional stabilization mode**:
- Operational development is primary
- Constitutional escalation activates only when implementation exposes contradictions
- Constitution emerges through implementation cycles, not abstract expansion

### Why This Sprint Matters

This sprint established the **epistemic foundation** for all future measurement, advisory, and historical learning systems. Without this foundation:
- Authority would emerge implicitly through repetition
- Advisory outputs could silently become canonical
- Operator sovereignty could be bypassed by accumulated system confidence
- Measurement legitimacy would remain undefined

The constitutional baseline prevents **authority laundering** — the most dangerous architectural risk identified during the sprint.

---

## 2. Sprint Timeline & Milestones

### Chronological Reconstruction

| Dev Order | Date | Milestone | Significance |
|-----------|------|-----------|--------------|
| 77 | 2026-05-23 | Governance Consolidation Audit | Discovered tap-tone-pi already had mature CI-enforced governance |
| 78 | 2026-05-23 | AGE Constitutional Contract | Created ADR-0010 + AGE_CONTRACT.md |
| 79 | 2026-05-23 | Advisory Presentation Boundary | Created presentation rules + codebase audit |
| 80 | 2026-05-24 | Advisory Presentation Patch Pass | Applied four wording patches to remediate leakage |
| 81 | 2026-05-24 | Measurement Authority & Epistemic Status | Created ADR-0011, ADR-0012, schema implications review |
| 82 | 2026-05-24 | Constitutional Mode Transition | Stabilized baseline, defined escalation triggers |

### Major Pivots

1. **Dev Order 77 Reframe**: Originally scoped as "governance creation" — reframed to "consolidation audit" after discovering existing governance structure
2. **Dev Order 81 Sequencing**: Constitutional review crossed into partial stabilization before roadmap restructuring — validated the principle that constitution emerges through implementation
3. **Dev Order 82 Mode Transition**: Recognized that continuing abstract constitutional expansion would be counterproductive

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Multiple tightly-scoped ADRs | Different stability profiles and amendment likelihoods |
| Schema implications as analysis memo (not doctrine) | Preserve implementation flexibility |
| Epistemic taxonomy baseline (not expansion) | Stabilize distinctions before optimization |
| Constitutional escalation triggers | Prevent speculative governance expansion |

---

## 3. Commit-Level Analysis

### Dev Order 77 — Governance Consolidation Audit

**Purpose:** Audit existing tap-tone-pi governance structure

**Files Created:**
- `docs/handoffs/TAP_TONE_PI_GOVERNANCE_CONSOLIDATION_AUDIT.md` (in luthiers-toolbox)

**Systems Impacted:** Documentation, cross-repo governance alignment

**Significance:** Discovered that tap-tone-pi uses **structural governance** (CI guards, instrument classes) while luthiers-toolbox uses **lexical governance** (forbidden vocabulary). Combined, they form constitutional semantics + runtime-enforced authority boundaries.

---

### Dev Order 78 — AGE Constitutional Contract

**Purpose:** Create constitutional doctrine for all DECISION SUPPORT systems

**Files Created:**
- `docs/ADR-0010-advisory-authority-constitutional-boundary.md`
- `docs/AGE_CONTRACT.md`

**Systems Impacted:** AGE, WolfAdvisor, all future advisory systems

**Significance:** Established orthogonal authority domains (Measurement, Advisory, Interpretive, Operator). Defined operator sovereignty as constitutionally supreme.

**Key Sections:**
- Orthogonal authority domains
- Advisory authority boundaries (may do / may NOT do)
- Forbidden vocabulary
- Semantic authority leakage prevention

---

### Dev Order 79 — Advisory Presentation Boundary

**Purpose:** Harden against presentation-layer authority leakage

**Files Created:**
- `docs/ADVISORY_PRESENTATION_BOUNDARY.md`
- `docs/ADVISORY_PRESENTATION_AUDIT.md`

**Files Modified:**
- `docs/AGE_CONTRACT.md` (added Section 7: Presentation Boundary)
- `docs/ADR-0010-advisory-authority-constitutional-boundary.md` (added Section 7: Presentation-Layer Authority Leakage)

**Systems Impacted:** HTML reports, AGE output, guidance panel

**Significance:** Recognized that authority can leak visually even when runtime boundaries are correct. UI design participates in authority governance.

**Audit Findings:**
- Strong structural compliance (INSTRUMENT CLASS banners)
- Presentation gaps: bare "Confidence" percentages, "Quality Grade" without heuristic marker
- Four patches recommended

---

### Dev Order 80 — Advisory Presentation Patch Pass

**Purpose:** Apply narrow, low-risk presentation wording patches

**Files Modified:**
- `analyzer/reports/html_report.py` (lines 353, 426, 430)
- `analyzer/guidance/engine.py` (line 168)
- `docs/ADVISORY_PRESENTATION_AUDIT.md` (marked remediated)

**Patches Applied:**

| File | Line | Change |
|------|------|--------|
| html_report.py | 353 | `Quality Grade` → `Quality Grade (heuristic)` |
| html_report.py | 426 | `Quality Grade` → `Quality Grade (heuristic)` |
| html_report.py | 430 | `Confidence` → `Advisory Confidence` |
| engine.py | 168 | `Confidence:` → `Advisory confidence:` |

**Path Correction:** Handoff referenced `tap_tone_pi/*` paths; actual repository locations are `analyzer/*` paths.

---

### Dev Order 81 — Measurement Authority & Epistemic Status

**Purpose:** Constitutional review of measurement authority and epistemic classification

**Files Created:**
- `docs/ADR-0011-measurement-authority-constitutional-definition.md`
- `docs/ADR-0012-epistemic-status-taxonomy.md`
- `docs/EPISTEMIC_STATUS_SCHEMA_IMPLICATIONS_REVIEW.md`

**Systems Impacted:** All measurement artifacts, provenance chains, downstream consumers

**Significance:** Resolved the deepest unresolved issue: **measurement authority ≠ truth authority**. Defined authority laundering chain with constitutional interruption points.

**Key Principles:**
- Measurement legitimacy is context-dependent
- Authority does not transfer to derived artifacts
- Epistemic status cannot be silently elevated
- Operator sovereignty is final

---

### Dev Order 82 — Constitutional Mode Transition

**Purpose:** Transition from constitutional excavation to operational development

**Files Created:**
- `docs/CONSTITUTIONAL_CONTINUATION_NOTICE.md`

**Systems Impacted:** Development process model

**Significance:** Formalized the discovery that constitution emerges through implementation cycles, not abstract expansion. Defined escalation triggers for future constitutional work.

---

## 4. Repository & File-Level Mapping

### Constitutional Documents

| File | Purpose | System Role |
|------|---------|-------------|
| `docs/GOVERNANCE.md` | Master governance (10 doctrines) | Top-level governance reference |
| `docs/BOUNDARY_RULES.md` | Hard boundary: no ToolBox imports | CI enforcement reference |
| `docs/ADR-0009-advisory-boundary.md` | MEASUREMENT vs DECISION SUPPORT | Runtime classification |
| `docs/ADR-0010-advisory-authority-constitutional-boundary.md` | Advisory authority semantics | Authority domain separation |
| `docs/ADR-0011-measurement-authority-constitutional-definition.md` | Measurement ≠ truth | Authority definition |
| `docs/ADR-0012-epistemic-status-taxonomy.md` | Seven epistemic categories | Classification system |
| `docs/AGE_CONTRACT.md` | AGE operational rules | Subsystem containment |
| `docs/ADVISORY_PRESENTATION_BOUNDARY.md` | Visual/semantic rules | Presentation governance |
| `docs/ADVISORY_PRESENTATION_AUDIT.md` | Codebase audit results | Compliance verification |
| `docs/EPISTEMIC_STATUS_SCHEMA_IMPLICATIONS_REVIEW.md` | Future implementation analysis | Planning reference |
| `docs/CONSTITUTIONAL_CONTINUATION_NOTICE.md` | Mode transition notice | Process governance |

### Implementation Files Modified

| File | Purpose | Sprint Changes |
|------|---------|----------------|
| `analyzer/reports/html_report.py` | HTML report generation | Presentation wording patches |
| `analyzer/guidance/engine.py` | AGE implementation | Confidence label patch |

### CI Enforcement

| File | Purpose | Status |
|------|---------|--------|
| `ci/check_advisory_boundary.py` | INSTRUMENT CLASS enforcement | Pre-existing, not modified |
| `ci/check_boundary_imports.py` | Import boundary enforcement | Pre-existing, not modified |
| `.github/workflows/advisory_boundary_guard.yml` | CI workflow | Pre-existing, not modified |

---

## 5. Schema & Data Model Documentation

### Epistemic Status Taxonomy (Constitutional, Not Schema)

| Status | Definition | Authority Level |
|--------|------------|-----------------|
| OBSERVED | Directly captured from physical sensor | Measurement-authoritative |
| DERIVED | Mathematical transform of observed data | Computationally authoritative |
| ESTIMATED | Inferential approximation | Approximation only |
| PREDICTED | Model-generated future/inferred state | Model-dependent |
| HEURISTIC | Advisory/non-authoritative guidance | No authority |
| OPERATOR-ANNOTATED | Human judgment or annotation | Operator authority only |
| EXTERNALLY-SOURCED | Imported from outside the system | External authority |

### Schema Implications (Theoretical, Not Committed)

Potential future fields (from `EPISTEMIC_STATUS_SCHEMA_IMPLICATIONS_REVIEW.md`):

```
epistemicStatus: string
epistemicStatusReason: string
epistemicStatusTimestamp: ISO8601
provenanceChain: [{ step, operation, inputStatus, outputStatus, timestamp }]
```

**Important:** These are analysis, NOT implementation doctrine.

### Existing Schema Boundaries

- `viewer_pack_v1` may only contain MEASUREMENT-class data
- Advisory fields forbidden in viewer_pack_v1 exports
- HEURISTIC data must be excluded from provenance chains

---

## 6. Build & Development Environment

### Repository Structure

```
tap_tone_pi-main/
├── analyzer/           # Desktop analyzer application
│   ├── analysis/       # Wood properties, coherence (DECISION SUPPORT)
│   ├── guidance/       # AGE implementation (DECISION SUPPORT)
│   ├── reports/        # HTML/JSON report generation
│   └── ...
├── tap_tone_pi/        # Core library
│   ├── wolf/           # Wolf tone detection + WolfAdvisor (DECISION SUPPORT)
│   ├── agentic/        # Agentic spine contracts
│   └── ...
├── ci/                 # CI enforcement scripts
├── docs/               # Governance and constitutional documents
└── ...
```

### Key Commands

```bash
# Run boundary enforcement
python ci/check_advisory_boundary.py

# Run import boundary check
python ci/check_boundary_imports.py --preset analyzer

# Run tests
pytest tests/
```

### CI Workflows

| Workflow | Purpose | Blocking |
|----------|---------|----------|
| `advisory_boundary_guard.yml` | INSTRUMENT CLASS enforcement | Yes |
| `boundary-guard.yml` | Import boundary enforcement | Yes |
| `no-logic-creep.yml` | Advisory language guard | Yes |

---

## 7. Scripts, Utilities, and Automation

### Governance Enforcement Scripts

| Script | Purpose | Risk |
|--------|---------|------|
| `ci/check_advisory_boundary.py` | Enforce INSTRUMENT CLASS declarations | Low (read-only) |
| `ci/check_boundary_imports.py` | Block forbidden imports | Low (read-only) |
| `ci/boundary_spec.py` | BoundarySpec class for validation | Low (library) |

### Future Recommendations

| Script | Purpose | Status |
|--------|---------|--------|
| `ci/check_advisory_presentation_language.py` | Vocabulary guard for DECISION SUPPORT modules | Recommended, not implemented |

---

## 8. Architectural Changes During the Sprint

### Systems Added

| System | Purpose | Location |
|--------|---------|----------|
| Measurement Authority Doctrine | Define what makes measurements authoritative | ADR-0011 |
| Epistemic Status Taxonomy | Classify all artifacts by authority level | ADR-0012 |
| Advisory Presentation Rules | Prevent visual authority leakage | ADVISORY_PRESENTATION_BOUNDARY.md |
| Constitutional Mode Transition | Process governance | CONSTITUTIONAL_CONTINUATION_NOTICE.md |

### Systems Refined

| System | Changes |
|--------|---------|
| ADR-0010 | Added Section 7 (Presentation-Layer Authority Leakage) |
| AGE_CONTRACT.md | Added Section 7 (Presentation Boundary) |
| HTML Reports | Patched confidence/grade labels |
| AGE Output | Patched confidence label |

### Abstractions Evolved

| Before | After |
|--------|-------|
| MEASUREMENT vs DECISION SUPPORT (binary) | Four orthogonal authority domains |
| Implicit measurement authority | Constitutional measurement definition |
| No epistemic classification | Seven-category taxonomy |
| Runtime governance only | Runtime + presentation governance |

### Technical Debt

| Item | Severity | Notes |
|------|----------|-------|
| Legacy "Quality Grade" in some contexts | Low | May need additional patches |
| Epistemic status not tracked in schemas | Medium | Deferred to future Dev Orders |
| Historical learning governance | Low | Deferred until needed |

---

## 9. Testing & Validation

### Validation Methods

| Method | Scope | Status |
|--------|-------|--------|
| Grep search for forbidden vocabulary | Codebase-wide | Complete |
| CI boundary guards | Runtime | Pre-existing, passing |
| Manual audit | Advisory presentation surfaces | Complete |

### Audit Results

- **Structural compliance:** All advisory modules have INSTRUMENT CLASS banners
- **Presentation compliance:** Four patches applied, verified clean
- **Vocabulary compliance:** No forbidden terms in advisory UI contexts

### Test Gaps

| Gap | Risk | Recommendation |
|-----|------|----------------|
| No automated vocabulary guard | Medium | Add CI workflow in future |
| No epistemic status validation | Low | Implement when schema work begins |

---

## 10. Risks, Fragility, and Technical Debt

### Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Authority laundering through historical accumulation | High | ADR-0011 defines interruption points |
| Presentation-layer authority leakage | Medium | ADVISORY_PRESENTATION_BOUNDARY.md + patches |
| Epistemic status drift | Medium | ADR-0012 taxonomy |
| Operator sovereignty bypass | High | Constitutional protection in ADR-0010, ADR-0011 |

### Fragile Systems

| System | Fragility | Notes |
|--------|-----------|-------|
| AGE Claude API integration | Medium | Silent fallback implemented |
| HTML report formatting | Low | Presentation patches applied |

### Technical Debt

| Item | Priority | Notes |
|------|----------|-------|
| Epistemic status schema implementation | Deferred | Constitutional foundation complete |
| Lexical CI guard for advisory vocabulary | Recommended | Not implemented per scope |
| Provenance chain status tracking | Deferred | Analysis complete in schema review |

---

## 11. Knowledge Preservation Notes

### Critical Assumptions

1. **Constitution emerges through implementation** — Governance cannot be completed in abstraction
2. **Measurement ≠ truth** — Captured data is authoritative as record, not as acoustic reality
3. **Authority laundering is the primary risk** — Cumulative confidence can create implicit canonization
4. **Operator sovereignty is constitutionally supreme** — No system may override human judgment

### Inferred Architecture

- tap-tone-pi uses **structural governance** (CI guards, instrument classes)
- luthiers-toolbox uses **lexical governance** (forbidden vocabulary)
- Combined: constitutional semantics + runtime-enforced authority boundaries

### Non-Obvious Decisions

| Decision | Rationale |
|----------|-----------|
| Separate ADRs for measurement authority vs epistemic taxonomy | Different stability profiles and amendment likelihoods |
| Schema implications as memo, not doctrine | Preserve implementation flexibility |
| Constitutional escalation triggers | Prevent speculative governance expansion |
| Epistemic taxonomy baseline (not expansion) | Stabilize distinctions before optimizing |

### Developer Heuristics

- Check INSTRUMENT CLASS banner before adding advisory logic
- Use allowed vocabulary in advisory contexts
- Never display bare "Confidence" percentages without domain qualifier
- Epistemic status cannot be elevated, only lowered through combination

---

## 12. Reconstruction Readiness Assessment

### Reconstructability Score: **High**

| Aspect | Status | Notes |
|--------|--------|-------|
| Constitutional doctrine | Complete | Six stable documents |
| Authority boundaries | Defined | ADR-0009, ADR-0010, ADR-0011 |
| Epistemic classification | Defined | ADR-0012 |
| Presentation rules | Defined | ADVISORY_PRESENTATION_BOUNDARY.md |
| Process governance | Defined | CONSTITUTIONAL_CONTINUATION_NOTICE.md |
| Implementation gaps | Documented | Schema implications review |

### Missing Documentation

| Item | Impact | Priority |
|------|--------|----------|
| Epistemic status schema specification | Medium | Future Dev Order |
| Lexical CI guard implementation | Low | Future Dev Order |
| Historical learning governance | Low | Deferred until needed |

### Recommended Reconstruction Sequence

1. Read CONSTITUTIONAL_CONTINUATION_NOTICE.md (process context)
2. Read ADR-0009 (runtime boundary)
3. Read ADR-0010 (advisory authority)
4. Read ADR-0011 (measurement authority)
5. Read ADR-0012 (epistemic taxonomy)
6. Read AGE_CONTRACT.md (operational rules)
7. Read ADVISORY_PRESENTATION_BOUNDARY.md (presentation rules)
8. Read EPISTEMIC_STATUS_SCHEMA_IMPLICATIONS_REVIEW.md (future planning)

---

## 13. Recommended Next Sprint Actions

### Immediate (Resume Operational Development)

| Action | Priority | Notes |
|--------|----------|-------|
| Return to luthiers-toolbox | High | Measurement Lab maturity |
| Topology experimentation | High | Core acoustic mission |
| Archive interoperability | Medium | Instrumentation continuity |

### Cleanup Priorities

| Action | Priority | Notes |
|--------|----------|-------|
| Additional presentation patches if found | Low | Audit marked complete |
| Update cross-references in GOVERNANCE.md | Low | Optional consolidation |

### Architecture Hardening

| Action | Trigger |
|--------|---------|
| Add lexical CI guard | When advisory vocabulary violations found |
| Implement epistemic status schema | When implementation pressure emerges |
| Define historical learning governance | When historical systems are built |

### Constitutional Escalation

Re-enter constitutional mode **only when**:
- Authority semantics become ambiguous
- Epistemic status assignment conflicts arise
- Advisory/measurement boundary violations are discovered
- Provenance legitimacy questions emerge
- Operator sovereignty is bypassed
- Authority laundering is detected

---

## Terminal Summary

```
SPRINT ARCHITECTURE HANDOFF — Constitutional Stabilization (Dev Orders 77–82)

Commits Analyzed:        6 Dev Orders (77–82)
Files Inspected:         15+ constitutional documents, 4 implementation files
Schemas Identified:      Epistemic status taxonomy (7 categories), not yet implemented
Major Systems:           Governance, Advisory Boundary, Epistemic Classification, AGE

Technical Debt Hotspots:
  - Epistemic status schema implementation (deferred)
  - Lexical CI guard (recommended, not implemented)
  - Historical learning governance (deferred)

Reconstruction Readiness: HIGH
  - Constitutional baseline complete and stable
  - Authority boundaries defined
  - Escalation triggers documented
  - Process governance formalized

Generated Handoff: docs/SPRINT_ARCHITECTURE_HANDOFF.md

Key Architectural Discovery:
  Governance is part of the runtime architecture,
  not external oversight or documentation overhead.
  Constitution emerges through implementation cycles.
```

---

**Handoff Version:** 1.0.0  
**Last Updated:** 2026-05-24  
**Owner:** tap-tone-pi governance  
**Next Mode:** Operational development (luthiers-toolbox Measurement Lab)
