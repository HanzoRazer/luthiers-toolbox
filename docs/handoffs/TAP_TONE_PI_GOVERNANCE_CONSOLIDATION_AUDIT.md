# Tap-Tone-Pi Governance Consolidation Audit

**Dev Order:** 77  
**Date:** 2026-05-23  
**Status:** COMPLETE  
**Scope:** Audit of existing governance structure, not creation of new governance

---

## Executive Summary

tap-tone-pi has a **mature, CI-enforced governance structure** built across multiple documents. This audit identifies consolidation opportunities and gaps in cross-document consistency, without adding new governance requirements.

**Key Finding:** The repo has strong measurement-vs-advisory separation via ADR-0009 and CI enforcement. The main consolidation opportunity is better linking between the GOVERNANCE.md overview and the specialized ADRs/contracts that implement specific boundaries.

---

## 1. Current Governance Inventory

### Tier 1 — Core Governance Documents

| Document | Purpose | Status |
|----------|---------|--------|
| `docs/GOVERNANCE.md` | Master governance (10 doctrines) | Active, well-maintained |
| `docs/BOUNDARY_RULES.md` | Hard boundary: no ToolBox imports | Active, CI-enforced |
| `docs/MEASUREMENT_BOUNDARY.md` | Measurement-only scope definition | Active |
| `docs/architecture/BoundarySpec.md` | ToolBox ↔ Analyzer boundary ADR | Accepted |

### Tier 2 — Architectural Decision Records

| ADR | Decision | CI Enforced |
|-----|----------|-------------|
| `ADR-0004` | Acoustic vs structural interpretation boundary | Partial (review-enforced) |
| `ADR-0009` | Advisory boundary — MEASUREMENT vs DECISION SUPPORT | **Yes** (`check_advisory_boundary.py`) |

### Tier 3 — Agentic Spine Specifications

| Document | Purpose |
|----------|---------|
| `AGENTIC_SPINE_ARCHITECTURE_ONEPAGER.md` | System diagram + control surfaces |
| `AGENT_DECISION_POLICY_V1.md` | Operating modes (M0/M1/M2) + decision pipeline |
| `AGENTIC_CONTRACTS_ENGINEER_HANDOFF.md` | Contract specifications |
| `EVENT_MOMENTS_CATALOG_V1.md` | Moment patterns + priority rules |
| `UWSM_UPDATE_RULES_V1.md` | User working-set model updates |

### Tier 4 — CI Enforcement

| Workflow | Guard Script | Blocking |
|----------|--------------|----------|
| `advisory_boundary_guard.yml` | `ci/check_advisory_boundary.py` | Yes |
| `boundary-guard.yml` | `ci/check_boundary_imports.py` | Yes |
| `no-logic-creep.yml` | (grep guardrails) | Yes |
| `wav-io-guard.yml` | WAV I/O centralization | Yes |

---

## 2. Audit Questions & Findings

### Q1: Are "measurement," "decision support," "advisory," and "downstream interpretation" consistently defined?

**Finding: PARTIAL CONSISTENCY**

| Term | Definition Location | Consistency |
|------|---------------------|-------------|
| MEASUREMENT | ADR-0009 (instrument class) | Strong |
| DECISION SUPPORT | ADR-0009 (instrument class) | Strong |
| Advisory | Multiple docs with slight variation | Needs alignment |
| Downstream interpretation | GOVERNANCE.md §2, §9 | Implicit, not enumerated |

**Gap:** "Advisory" is used in three overlapping ways:
1. ADR-0009: DECISION SUPPORT modules (code-level classification)
2. GOVERNANCE.md §2: "advisory records" as a category of downstream output
3. AGENT_DECISION_POLICY_V1.md: "Advisory Mode" (M1 operating mode)

**Recommendation:** Add a terminology glossary section to GOVERNANCE.md that cross-references all three usages and clarifies their relationship.

---

### Q2: Does GOVERNANCE.md overstate analyzer authority?

**Finding: SLIGHT OVERSTATEMENT**

GOVERNANCE.md §2 states:
> "All artifacts emitted by this repository represent **authoritative measurement records**."

This is true for viewer_pack_v1 exports but not universally true, since:
- `AnalyzerGuidanceEngine` (DECISION SUPPORT) lives in this repo
- `WolfAdvisor` (DECISION SUPPORT) lives in this repo
- Agentic Spine emits `AttentionDirectiveV1` which are guidance, not measurements

**The nuance is present** in ADR-0009, which correctly identifies these as DECISION SUPPORT. But GOVERNANCE.md §2 reads as if the entire repo is measurement-only.

**Recommendation:** Amend GOVERNANCE.md §2 to clarify:
> "All artifacts emitted to viewer_pack_v1 represent authoritative measurement records. DECISION SUPPORT modules (see ADR-0009) emit guidance to display layers only, never to viewer_pack_v1."

---

### Q3: Are AGE boundaries fully documented?

**Finding: DOCUMENTED BUT FRAGMENTED**

The AGE boundary is defined across multiple documents:

1. **`analyzer/guidance/engine.py`** — correct INSTRUMENT CLASS banner
2. **ADR-0009** — mentions AGE as DECISION SUPPORT
3. **AGENT_DECISION_POLICY_V1.md** — defines operating modes
4. **AGENTIC_SPINE_ARCHITECTURE_ONEPAGER.md** — system diagram

**Gap:** No single document enumerates:
- What the AGE may read (finished measurement data)
- What the AGE may emit (AttentionDirectiveV1 to display layer)
- What the AGE may NOT do (modify measurements, write to viewer_pack_v1)

The engine.py docstring contains these rules, but they're not in a governance doc.

**Recommendation:** Add "AGE Contract Summary" section to GOVERNANCE.md or create `docs/AGE_CONTRACT.md` that consolidates these rules.

---

### Q4: Is provenance decomposition explicit enough?

**Finding: STRONG BUT IMPLICIT**

Provenance tracking exists:
- viewer_pack_v1 requires SHA256 integrity hashes
- Manifest schemas declare provenance fields
- CI gates block advisory fields in viewer_pack_v1

**Gap:** The provenance chain is not documented as a flow diagram:

```
Raw capture → Analytical transform → Export (viewer_pack_v1)
                                         ↑
                                    MEASUREMENT only
                                    
             → AGE interpretation → Display layer
                                         ↑
                                    DECISION SUPPORT only
```

**Recommendation:** Add a "Provenance Flow" diagram to GOVERNANCE.md §4 or §9 showing where measurement/advisory branches diverge.

---

### Q5: Are forbidden semantics consistently enforced?

**Finding: STRONG ENFORCEMENT, LIMITED VOCABULARY**

**What's enforced:**
- viewer_pack_v1 purity gate blocks these fields:
  - `mitigation_type`, `recommendations`, `wolf_directive`
  - `severity_label`, `action_required`, `operator_guidance`
  - `confidence_label`, `urgency`, `next_steps`

**What's NOT codified:**
Unlike luthiers-toolbox (which explicitly forbids: approved, validated, canonical, certified, optimized, recommended), tap-tone-pi does not have an explicit forbidden vocabulary list.

The semantic boundary is enforced structurally (INSTRUMENT CLASS declarations) rather than lexically (forbidden word lists).

**Assessment:** This is adequate given the CI enforcement of instrument class boundaries. Lexical enforcement would be belt-and-suspenders.

**Recommendation (optional):** Consider adding a `FORBIDDEN_ADVISORY_VOCABULARY` constant to `check_advisory_boundary.py` for grep-based secondary enforcement in MEASUREMENT modules.

---

## 3. Cross-Document Consistency Issues

### Issue A: GOVERNANCE.md Section Numbering Gap

GOVERNANCE.md has sections 1-10 but refers to "Section 9" (Analysis vs Interpretation) in ways that could conflict with ADR-0004's acoustic-vs-structural boundary.

**Resolution:** Add cross-reference note to §9:
> "For sensor-specific claim boundaries, see ADR-0004."

### Issue B: Lab-to-Analyzer Promotion vs DECISION SUPPORT

GOVERNANCE.md §7 defines promotion from lab code to analyzer. The checklist does not mention INSTRUMENT CLASS declaration.

**Resolution:** Add to promotion checklist:
> "6b. INSTRUMENT CLASS declared (MEASUREMENT or DECISION SUPPORT)"

### Issue C: Duplicate Enforcement Summary

GOVERNANCE.md contains two identical "Enforcement Summary" diagrams (after §3 and after §8). One should be removed to avoid drift.

---

## 4. Consolidation Opportunities

### Opportunity 1: Index Document

Create `docs/GOVERNANCE_INDEX.md` that maps governance concerns to their source documents:

| Concern | Primary Source | Secondary Sources |
|---------|----------------|-------------------|
| Measurement vs advisory | ADR-0009 | GOVERNANCE.md §9 |
| Repo boundary | BoundarySpec.md | BOUNDARY_RULES.md |
| Sensor claim limits | ADR-0004 | — |
| AGE operating modes | AGENT_DECISION_POLICY_V1.md | AGENTIC_SPINE_ARCHITECTURE |
| CI gates | GOVERNANCE.md §8 | Individual workflow files |

### Opportunity 2: Terminology Glossary

Add to GOVERNANCE.md:

```markdown
## Appendix: Terminology

| Term | Definition |
|------|------------|
| MEASUREMENT | Instrument class that may appear in viewer_pack_v1 |
| DECISION SUPPORT | Instrument class that emits to display layer only |
| Advisory record | Downstream interpretation attached to measurement |
| Advisory Mode (M1) | AGE operating mode that suggests actions |
```

### Opportunity 3: AGE Contract Consolidation

Extract AGE rules from engine.py docstring into `docs/AGE_CONTRACT.md`:

```markdown
# AGE Contract

## May read
- Finished measurement data
- Session state
- UWSM preferences

## May emit
- AttentionDirectiveV1 to GuidancePanelWidget

## May NOT
- Modify measurements
- Write to viewer_pack_v1
- Block measurement pipelines
- Call external APIs synchronously on main thread
```

---

## 5. Alignment with Luthiers-Toolbox Governance

tap-tone-pi governance is compatible with luthiers-toolbox governance:

| LTB Concept | tap-tone-pi Equivalent |
|-------------|------------------------|
| Forbidden language (approved, validated, canonical) | INSTRUMENT CLASS: DECISION SUPPORT gate |
| Observational-only semantics | viewer_pack_v1 purity gate |
| Append-only evidence | SHA256 manifest integrity |
| Advisory vs measurement | ADR-0009 boundary |

**Key difference:** tap-tone-pi uses structural enforcement (class declarations + CI) rather than lexical enforcement (forbidden word lists). Both approaches are valid; tap-tone-pi's is arguably more robust since it gates at the module level rather than scanning strings.

---

## 6. Recommendations Summary

| Priority | Action | Target |
|----------|--------|--------|
| High | Add cross-reference to ADR-0004 in GOVERNANCE.md §9 | GOVERNANCE.md |
| High | Add INSTRUMENT CLASS to promotion checklist (§7) | GOVERNANCE.md |
| Medium | Create GOVERNANCE_INDEX.md | New document |
| Medium | Consolidate AGE contract into standalone doc | AGE_CONTRACT.md |
| Low | Remove duplicate enforcement diagram | GOVERNANCE.md |
| Low | Add terminology glossary | GOVERNANCE.md |

---

## 7. Conclusion

tap-tone-pi has a well-structured governance system with strong CI enforcement. The main opportunities are:

1. **Better cross-referencing** between GOVERNANCE.md and specialized ADRs
2. **Explicit AGE contract** extracted from engine.py docstring
3. **Terminology alignment** to prevent drift between "advisory" usages

No new governance requirements are needed. The existing structure is sound; it needs consolidation, not expansion.

---

**Audit completed by:** Dev Order 77  
**Next action:** Owner review of recommendations for prioritization
