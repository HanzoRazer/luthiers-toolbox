# Advisory Presentation Audit

**Dev Order:** 79  
**Date:** 2026-05-23  
**Scope:** UI/source audit for advisory presentation boundary compliance  
**Status:** Complete

---

## Audit Summary

This audit searched the tap-tone-pi codebase for advisory presentation terms and assessed compliance with ADR-0010 and `ADVISORY_PRESENTATION_BOUNDARY.md`.

**Overall Assessment:** The codebase has strong structural governance (INSTRUMENT CLASS declarations, ADR-0009 CI gates). Presentation-layer compliance is partial — several areas would benefit from additional qualification markers.

---

## Findings by Area

### 1. AGE (AnalyzerGuidanceEngine)

**Location:** `analyzer/guidance/engine.py`, `analyzer/guidance/panel.py`

**Status:** Compliant with structural governance; presentation improvements recommended

**Findings:**

| Line | Current | Assessment | Recommendation |
|------|---------|------------|----------------|
| engine.py:168 | `f"Confidence: {props.get('confidence', 0):.0%}"` | Bare confidence percentage | Add "Advisory" qualifier |
| panel.py:67-72 | Action color mapping (blue/amber/red) | Compliant | None |
| panel.py:74-79 | Action labels (INFO/REVIEW/DECIDE/URGENT) | Compliant | None |

**Compliant Elements:**
- INSTRUMENT CLASS: DECISION SUPPORT banner present
- Clear constraints documented in docstring
- No green/approval colors in action mapping
- "Act" button is navigation-only, not validation

**Recommended Changes (deferred to owner):**
- engine.py:168: Change to `f"Advisory confidence: {props.get('confidence', 0):.0%} (heuristic)"`

---

### 2. WolfAdvisor

**Location:** `tap_tone_pi/wolf/wolf_advisor.py`

**Status:** Compliant with structural governance; presentation well-documented

**Findings:**

| Line | Current | Assessment |
|------|---------|------------|
| Line 7-8 | "does NOT make decisions" | Excellent boundary language |
| Line 25-30 | INSTRUMENT CLASS: DECISION SUPPORT | Compliant |
| Line 65-71 | ConfidenceLevel enum | Compliant (internal classification) |
| Line 84 | `predicted_severity` | Internal field, not presentation |

**Compliant Elements:**
- Explicit docstring stating recommendations require "operator validation and laboratory proficiency"
- ConfidenceLevel is internal classification, not UI-facing validation claim
- All recommendations marked as "physics-grounded" not "validated"

**No Changes Recommended**

---

### 3. Wood Properties

**Location:** `analyzer/analysis/wood_properties.py`

**Status:** Compliant with explicit heuristic annotation

**Findings:**

| Line | Current | Assessment |
|------|---------|------------|
| Line 53 | `quality_grade: str  # A/B/C/D — HEURISTIC ONLY, not a calibrated measurement` | Excellent annotation |
| Line 55 | `confidence: float  # 0-1, how confident we are in estimates` | Internal field |

**Compliant Elements:**
- INSTRUMENT CLASS: DECISION SUPPORT banner present
- quality_grade explicitly annotated as "HEURISTIC ONLY"
- Excluded from viewer_pack_v1 per annotation

**No Changes Recommended**

---

### 4. HTML Reports

**Location:** `analyzer/reports/html_report.py`

**Status:** Partial compliance; presentation improvements recommended

**Findings:**

| Line | Current | Assessment | Recommendation |
|------|---------|------------|----------------|
| 426-427 | `<label>Quality Grade</label>` | Missing heuristic marker | Add "(heuristic)" |
| 430-431 | `<label>Confidence</label>` with bare percentage | Missing domain qualifier | Add "Advisory confidence" |
| 353 | `<div class="label">Quality Grade</div>` | Missing heuristic marker | Add "(heuristic)" |

**Recommended Changes (deferred to owner):**
- Line 426: Change to `<label>Quality Grade (heuristic)</label>`
- Line 430: Change to `<label>Advisory Confidence</label>`
- Line 353: Change to `<div class="label">Quality Grade (heuristic)</div>`

---

### 5. Guidance Panel Widget

**Location:** `analyzer/guidance/panel.py`

**Status:** Compliant

**Findings:**

| Line | Current | Assessment |
|------|---------|------------|
| 213-217 | Urgency → border color mapping | Compliant (intensity, not approval) |
| 67-72 | Action → color mapping | Compliant (no green) |

**Compliant Elements:**
- Amber for attention, not green for approval
- Urgency uses intensity gradient, not pass/fail semantics
- "Dismiss" is neutral, not error-styled

**No Changes Recommended**

---

### 6. WSI Curve Loader

**Location:** `analyzer/loaders/wsi_curve.py`

**Status:** Compliant (measurement domain)

**Findings:**

| Line | Current | Assessment |
|------|---------|------------|
| 56-57 | `severity = "high" if wsi > 0.85 else "medium"` | Measurement classification |

**Assessment:** This is in the measurement domain (WSI is a computed metric), not advisory. "Severity" here refers to wolf tone severity based on measured WSI values, not advisory confidence.

**No Changes Recommended**

---

### 7. Documentation

**Locations:** Various docs files

**Status:** Mostly compliant; some historical usage of "canonical" and "recommended"

**Findings:**

| File | Term | Assessment |
|------|------|------------|
| engineer_handoff.md | "Recommended path" | Engineer-facing documentation, not advisory UI |
| CHANGELOG.md | "canonical module" | Technical term for file location, not authority claim |
| GOLD_STANDARD_EXAMPLE_RUN.md | "Recommended Specimen" | User guide, not advisory output |
| theory/*.md | "Best for:" | Educational content, not advisory output |

**Assessment:** These usages are in documentation contexts, not advisory UI output. They do not violate the advisory presentation boundary.

**No Changes Recommended**

---

## Vocabulary Audit

### Forbidden Terms Found

| Term | Location | Context | Assessment |
|------|----------|---------|------------|
| `verified` | three_topics_elaboration.md:28 | "(verified: 0.000 Hz difference on synthetic signals)" | Technical verification note, not advisory |
| `verified` | ADR-0008:230 | "declarations verified" | Technical checklist, not advisory |
| `validated` | phase2_validate.yml:55 | "Validated {len(schemas)} Phase 2 schemas" | CI log output, not advisory |
| `optimal` | ACOUSTIC_TESTING_METHODS_ANALYSIS.md:219 | "optimal tap points" | Research documentation, not advisory |
| `recommended` | engineer_handoff.md | Multiple "Recommended path:" | Engineer-facing, not advisory |
| `canonical` | wav-io-guard.yml | "canonical module" | Technical term, not authority claim |

**Assessment:** No forbidden terms found in advisory UI output contexts. Terms appear in technical documentation, CI logs, and engineer-facing content where they are appropriate.

---

### Allowed Terms Verification

| Term | Found In | Context |
|------|----------|---------|
| `flagged` | wolf_advisor.py, guidance/engine.py | Advisory output |
| `suggested` | guidance/engine.py | Advisory output |
| `possible` | guidance/engine.py | Advisory output |
| `potential` | guidance/engine.py | Advisory output |
| `heuristic` | wood_properties.py | Field annotation |

**Assessment:** Allowed advisory vocabulary is correctly used in advisory contexts.

---

## Patch Decisions

### Applied Patches (Dev Order 80)

**Status:** Remediated  
**Date:** 2026-05-24

Dev Order 80 applied low-risk advisory presentation wording patches. No runtime, scoring, confidence, or advisory behavior changed.

**Path correction from handoff:** Actual repository locations are:
- `analyzer/reports/html_report.py` (not `tap_tone_pi/reports/html_report.py`)
- `analyzer/guidance/engine.py` (not `tap_tone_pi/analyzer_guidance_engine/engine.py`)

| File | Line | Change | Status |
|------|------|--------|--------|
| analyzer/reports/html_report.py | 353 | `Quality Grade` → `Quality Grade (heuristic)` | **Remediated** |
| analyzer/reports/html_report.py | 426 | `Quality Grade` → `Quality Grade (heuristic)` | **Remediated** |
| analyzer/reports/html_report.py | 430 | `Confidence` → `Advisory Confidence` | **Remediated** |
| analyzer/guidance/engine.py | 168 | `Confidence:` → `Advisory confidence:` | **Remediated** |

**Verification:** Grep search confirms no remaining unqualified `Quality Grade` or `Confidence:` labels in audited presentation surfaces.

---

## CI Recommendations

### Future Lexical Guard (Not Implemented)

A future Dev Order may add `ci/check_advisory_presentation_language.py` that:

1. Scans DECISION SUPPORT modules for forbidden vocabulary in string literals
2. Validates that confidence displays include domain qualifier
3. Checks for bare "Quality Grade" labels without heuristic marker
4. Fails CI on violations in advisory/interpretive contexts

**Not implemented in Dev Order 79** — documented as future hardening recommendation per scope.

---

## Conclusion

The tap-tone-pi codebase has strong structural governance for the measurement/advisory boundary. Presentation-layer compliance is now complete after Dev Order 80 remediation.

**Strengths:**
- All advisory modules have INSTRUMENT CLASS: DECISION SUPPORT banners
- WolfAdvisor has excellent boundary language in docstrings
- wood_properties.py has explicit heuristic annotation
- Guidance panel uses non-approval colors and styling
- HTML reports now display qualified "Quality Grade (heuristic)" labels
- HTML reports now display "Advisory Confidence" instead of bare "Confidence"
- AGE prompt now uses "Advisory confidence:" instead of bare "Confidence:"

**Gaps:** None remaining in audited presentation surfaces.

---

**Audit completed by:** Dev Order 79  
**Patches applied by:** Dev Order 80 (2026-05-24)  
**Status:** Complete
