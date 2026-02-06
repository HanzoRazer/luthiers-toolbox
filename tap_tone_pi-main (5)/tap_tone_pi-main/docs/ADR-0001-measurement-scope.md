# ADR-0001: Measurement Scope, Protocol, and Integration Boundaries

**Status:** Accepted  
**Date:** 2025-12-25  
**Context:** Tap-Tone Measurement Node / Workstation  
**Decision Drivers:** Repeatability, scientific validity, future extensibility, avoidance of premature optimization

---

## Decision

### 1. Measurement Protocol (Phase 1)

A **minimal but explicit v0.1 measurement protocol** SHALL be documented and followed in Phase 1.

The protocol MUST specify:

* **Tap tool:** small rubber or wooden hammer (consistent mass)
* **Tap location(s):** at least one named location (e.g., "bridge area")
* **Microphone type:** USB measurement mic *or* XLR condenser + audio interface
* **Microphone placement:**

  * distance (e.g., ~30 cm from soundboard)
  * approximate angle (0–15° off normal)
* **Environment:** quiet room, consistent support/fixture
* **Gain target:** avoid clipping; RMS in a defined nominal range

The protocol MAY be expanded in later phases, but **Phase 1 SHALL NOT remain "unspecified."**

---

### 2. Multi-Channel Capture Priority

**Phase 1 (single-channel)** is a **hard gate** and MUST be completed before multi-channel development.

Phase 1 is considered complete only when:

* Artifact outputs (WAV, JSON, CSV) are stable
* Repeated taps on the same instrument produce bounded variance
* The v0.1 measurement protocol is written and used

**Phase 2 (2-channel capture)** is the **first expansion**, enabling:

* Time delay estimation
* Cross-correlation
* Magnitude-squared coherence

Multi-channel (>2) and spatial reconstruction are explicitly **out of scope** until Phase 2 is validated.

---

### 3. DSP Techniques and Algorithm Porting

Specific DSP techniques SHALL be named to avoid reinvention and drift.

**Phase 1 DSP scope includes:**

* FFT magnitude spectrum
* Peak detection with frequency bounds and spacing
* RMS and clipping detection

**Explicitly approved future ports (post-Phase-1):**

* **Parabolic peak interpolation** (sub-bin frequency refinement)
* Improved peak prominence/guardrail logic (as isolated, testable functions)

All DSP additions MUST:

* Be implemented as standalone functions
* Include unit tests using fixed WAV fixtures
* Avoid embedding "guitar interpretation" logic at the measurement layer

---

### 4. RMOS / ToolBox Integration Boundary

Direct RMOS integration is **explicitly deferred**.

However, Phase 1 outputs MUST conform to a **minimal, forward-compatible artifact contract**.

Each capture SHALL produce:

* `audio.wav`
* `analysis.json`
* `spectrum.csv`
* `session.jsonl` (append-only log)

`analysis.json` MUST include:

* `ts_utc`
* `label`
* `sample_rate`
* `dominant_hz`
* `peaks[]`
* `rms`
* `clipped`
* `confidence`

Reserved (optional) fields MAY exist for future use:

* `instrument_id`
* `build_stage`
* `tap_point`
* `mic_model`
* `mic_distance_mm`
* `fixture`
* `gain_db`

No design optimization, modal labeling, or structural recommendations SHALL be made at this layer.

---

## Rationale

1. **Repeatability beats cleverness.**
   A loosely defined protocol undermines every downstream result. Minimal specificity now prevents ambiguous data later.

2. **Single-channel truth precedes spatial inference.**
   Multi-channel analysis is meaningless without a trusted single-channel baseline.

3. **Naming algorithms prevents accidental reinvention.**
   Declaring approved DSP techniques keeps agents focused and avoids low-quality substitutes.

4. **Measurement ≠ interpretation.**
   This system measures physical response. Design reasoning belongs in RMOS / ToolBox, not in the capture node.

5. **Artifacts are the product.**
   The long-term value is in durable, inspectable, replayable data—not UI behavior or real-time heuristics.

---

## Consequences

* Phase 1 remains small, testable, and scientifically defensible
* Future agents have clear guardrails and expansion paths
* The system can evolve into multi-mic acoustic testing without invalidating early data
* RMOS integration can occur later without retrofitting artifacts

---

## Non-Goals (Explicit)

* No real-time "tone optimization"
* No automatic monopole classification in Phase 1
* No web-based capture UI
* No embedded design advice or CNC decisions at the measurement layer
