# Tap-Tone-Pi Sandbox → Evidence Viewer
## Analyzer-Side Pipeline Handoff (Lab-Ready)

> **Doctrine:** The analyzer exports evidence and derivations. It does not export conclusions.
> Any file that can influence a human to remove wood must be treated as advisory (Wave 7) and is out-of-scope.

### Audience
- tap-tone-pi developers
- lab engineers
- signal processing engineers
- acoustic researchers

### Scope
- Analyzer-side pipeline only
- Physical measurement → deterministic evidence pack
- Validation under real lab conditions

### Out of Scope
- UI logic
- Interpretation, scoring, grading, or recommendations
- "Good / bad" judgments
- Design decisions or optimization logic (Wave 7+)

### Reference Documents
- **Normative:** This document defines what MUST/SHOULD/MAY be true
- **Reference:** [contracts/EVIDENCE_PACK_CONTRACT_v1.md](contracts/EVIDENCE_PACK_CONTRACT_v1.md) — full column specs, units, examples

---

## 1. Purpose of the Sandbox

The tap_tone_pi sandbox exists to answer a single, non-negotiable question:

> **Can real physical measurements be exported as stable, explicit, self-describing evidence that downstream tools can visualize without inventing meaning?**

Everything in this sandbox serves that goal.

The sandbox is **not** a product UI, a teaching aid, or a design advisor. It is a **measurement instrument** whose outputs must stand on their own years later, outside the original context, without oral explanation.

The downstream Viewer assumes:
- Measurements are already complete
- Semantics are already explicit
- Nothing downstream corrects, infers, or interprets intent

If the sandbox exports ambiguous, unstable, or under-specified artifacts, the Viewer must not compensate — doing so would violate measurement integrity.

---

## 2. End-to-End Pipeline Overview

The analyzer-side pipeline is responsible for everything up to and including the Evidence ZIP boundary.

```
Physical Excitation (Tap / Shaker / Sweep)
        ↓
Raw Audio Capture
        ↓
Signal Conditioning (windowing, FFT, coherence)
        ↓
Per-Point Artifacts
  - spectrum.csv
  - analysis.json
  - audio.wav
        ↓
Session-Level Artifacts
  - wsi_curve.csv
  - wolf_candidates.json
  - provenance.json
  - session_meta.json
        ↓
Evidence ZIP (viewer_pack_v1)
```

Once the ZIP is produced, the analyzer's responsibility ends.

---

## 3. Evidence Contract (What the Viewer Trusts)

### 3.1 Determinism Is Mandatory

For identical physical inputs:
- same tap location
- same excitation method
- same mic placement
- same capture parameters

The analyzer **must** produce:
- identical column headers
- identical frequency bins
- stable peak detection behavior
- stable admissibility classification

Minor numeric variance due to floating-point precision is acceptable. **Structural variance is not.**

Non-determinism upstream creates false analytical affordances downstream and invalidates comparative workflows.

---

## 4. Per-Point Artifacts (Critical)

### 4.1 `spectra/points/{POINT_ID}/spectrum.csv`

**Role:** Authoritative frequency-domain measurement for a single spatial point.

**Canonical Header:**
```
freq_hz,H_mag,coherence,phase_deg
```

**Invariants (MUST):**
- `freq_hz` MUST be numeric and monotonically increasing
- All points in session MUST share identical frequency bins
- Column order MUST match canonical header exactly
- Missing coherence MUST be explicit (`0` or `NaN`, never omit row)
- No undocumented smoothing or interpolation

> Full column semantics: [EVIDENCE_PACK_CONTRACT_v1.md](contracts/EVIDENCE_PACK_CONTRACT_v1.md#11-spectrapointspoint_idspectrumcsv)

**Viewer Assumption:** Each row is a measurement, not a conclusion.

---

### 4.2 `spectra/points/{POINT_ID}/analysis.json`

**Role:** Per-point annotations derived directly from the spectrum.

**Canonical Structure:**
```json
{
  "peaks": [
    {
      "freq_hz": 187.5,
      "label": "Mode 1"
    }
  ]
}
```

**Invariants (MUST/MUST NOT):**
- Peaks MUST map directly to spectrum bins
- Labels MUST NOT contain ranking ("strongest", "worst", "dominant")
- Labels MUST NOT contain quality language ("good", "bad", "problem")
- Empty `peaks: []` is valid if no peaks detected

**MAY:**
- Include `bin_index` for reproducibility
- Include factual `notes` (no recommendations)

**Viewer Assumption:** Peaks are annotations, not judgments.

---

### 4.3 `audio/points/{POINT_ID}.wav`

**Role:** Provenance, audit trail, and future re-processing.

**Invariants (MUST):**
- MUST correspond exactly to the tap producing the spectrum
- MUST preserve sample rate, bit depth, and channel count
- MUST NOT be trimmed/enhanced/filtered after FFT unless documented in provenance

**Viewer Behavior:** Missing audio triggers warning, not compensation.

---

## 5. Session-Level Artifacts (WSI Pipeline)

### 5.1 `wolf/wsi_curve.csv`

**Role:** Session-level measurement derived from all points.

**Canonical Header (MUST MATCH EXACTLY):**
```
freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible
```

**Column Semantics:**
| Column | Description |
|--------|-------------|
| `freq_hz` | frequency bin (must align with spectra bins) |
| `wsi` | Wolf Stress Index (0–1, normalized upstream) |
| `coh_mean` | mean coherence across all points |
| `phase_disorder` | exported metric, not computed downstream |
| `loc`, `grad` | exporter-defined metrics (units documented) |
| `admissible` | boolean classification computed upstream |

**Rules:**
- `admissible` is the only classification field in Wave 6
- No implicit thresholds (e.g., undocumented "wsi > 0.4")
- All bins must be present even if inadmissible

**Viewer Assumption:** WSI is a measurement surface, not advice.

---

### 5.2 `wolf/wolf_candidates.json`

**Role:** Explicitly surfaced frequencies requiring analyst attention.

**Rules:**
- Must include thresholds explicitly (`wsi_threshold`, `coherence_threshold`)
- Each candidate must list contributing spatial points
- No language implying quality or defect
- Optional notes must be factual, not advisory

> Full schema: [EVIDENCE_PACK_CONTRACT_v1.md](contracts/EVIDENCE_PACK_CONTRACT_v1.md#22-wolfwolf_candidatesjson)

---

## 6. Provenance & Metadata

### 6.1 `provenance.json`

Must answer:
- how the data was captured
- tool versions
- FFT parameters
- windowing choices
- calibration assumptions

This file exists to **prevent post-hoc reinterpretation**.

### 6.2 `session_meta.json`

Should include:
- instrument ID
- operator (if appropriate)
- environment notes
- grid definition

The Viewer displays this verbatim.

---

## 7. Evidence Pack Assembly Rules

When assembling the ZIP:
- **Paths are semantic** — Viewer logic depends on them
- `kind` values in the manifest must match file roles
- Sibling resolution assumes:
  - `spectra/points/{PID}/spectrum.csv`
  - `spectra/points/{PID}/analysis.json`

**No auto-repair downstream.**

Malformed packs surface explicit errors.

---

## 8. Sandbox Validation Checklist (Pre-Lab)

### Determinism
- [ ] Repeated runs produce identical CSV headers
- [ ] Peak frequencies stable within expected variance
- [ ] Admissibility stable for identical inputs

### Alignment
- [ ] All spectra share identical frequency bins
- [ ] WSI bins align exactly with spectra bins

### Completeness
- [ ] Every spectrum has audio
- [ ] Every spectrum has analysis.json (even if empty)
- [ ] Session-level artifacts present when expected

---

## 9. What the Sandbox Must NOT Do (Wave Boundary)

The analyzer **must not**:
- encode "good / bad" language
- rank frequencies or points
- compute "wolf likelihood"
- aggregate peaks into conclusions
- hide thresholds inside undocumented metrics

Those belong exclusively in **Wave 7+ interpretation**.

---

## 10. Definition of "Pipeline Complete"

The analyzer pipeline is complete when:

> A lab operator can produce an evidence ZIP that a downstream analyst can explore, correlate, and question — **without the tool telling them what to think**.

At that point:
- the analyzer has done its job
- the Viewer has done its job
- interpretation remains a human act

---

## 11. Handoff Summary (One Sentence)

> **tap-tone-pi is responsible for producing stable, explicit, self-describing measurements; the Viewer is responsible for showing them faithfully — nothing more, nothing less.**

---

## Appendix: Future Extensions

If needed next:
- lab-operator SOP
- failure-mode appendix
- Wave-7 experiment framing

All without crossing the measurement boundary.
