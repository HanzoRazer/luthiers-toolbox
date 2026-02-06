# ADR-0002: Multi-Channel Expansion Strategy

**Status:** Accepted  
**Date:** 2025-12-25  
**Context:** Tap-Tone Measurement Node → Multi-Channel Acoustic Testing  
**Decision Drivers:** Phase coherence, repeatability, physical validity, controlled scope expansion

---

## Decision

### 1. Expansion Philosophy

Multi-channel capability SHALL be introduced **incrementally**, with each phase gated by measurable validation criteria.

Multi-channel expansion exists to:

* improve **physical insight**
* enable **phase-aware analysis**
* support **testing and research**

It SHALL NOT be introduced for visualization novelty or premature spatial claims.

---

### 2. Phase 2: Two-Channel (Stereo) Measurement — First Expansion

**Phase 2 (2-channel capture)** is the **mandatory next step** after Phase 1 completion.

#### Phase 2 objectives:

* Establish **phase-coherent capture**
* Measure **time delay**, **phase difference**, and **coherence**
* Validate that multi-channel data adds information beyond single-channel FFT

#### Phase 2 requirements:

* Two microphones captured via a **shared clock**

  * Single multi-input USB audio interface
  * OR a single USB stereo measurement device
* Identical sampling rate, buffer size, and latency path
* Fixed and documented mic geometry

#### Phase 2 analyses SHALL include:

* Cross-correlation (time delay estimation)
* Magnitude-squared coherence vs frequency
* Phase difference vs frequency
* Per-channel FFT + peak sets

#### Phase 2 outputs SHALL include:

* Multi-channel WAV (interleaved or split)
* Channel-indexed FFT data
* Cross-channel metrics (JSON)
* Updated session log entries referencing channel geometry

Phase 2 explicitly **does not** claim spatial reconstruction.

---

### 3. Phase 3: Small Array (4–8 Channels) — Directional Inference

Phase 3 introduces a **small microphone array** to infer **directionality and radiation zones**, not structural vibration.

#### Phase 3 goals:

* Identify frequency-dependent "hot zones"
* Observe how radiation shifts with frequency bands
* Support *relative* spatial inference

#### Phase 3 constraints:

* Array geometry MUST be fixed, measured, and recorded
* Mic spacing MUST be appropriate for target wavelength bands
* Reconstruction MUST be limited to:

  * delay-and-sum beamforming
  * frequency-band-limited maps

Phase 3 SHALL NOT:

* claim true modal shapes
* infer plate deflection
* present results as structural motion

Outputs are **acoustic radiation maps**, not vibration fields.

---

### 4. Phase 4: Near-Field Reconstruction (Advanced / Research)

Phase 4 introduces **near-field acoustic reconstruction** techniques (e.g., NAH / ESM).

This phase is:

* explicitly **experimental**
* for research, not production tooling

Requirements include:

* dense or scanned arrays
* precise geometry registration
* propagation model assumptions
* frequency-band limits

Results MUST be labeled:

> "Near-field acoustic reconstruction (inferred)"

---

### 5. Phase 5: Structural Mode Measurement (Out of Scope for Mic Arrays)

True **structural wave flow and mode shapes** SHALL NOT be claimed from microphones alone.

Phase 5 requires:

* Laser Doppler Vibrometry (LDV), OR
* Accelerometer grids directly mounted to the structure

Microphone arrays may only:

* complement
* correlate
* validate trends

They SHALL NOT replace structural sensing.

---

## Validation Gates

Each phase MUST pass validation before advancing:

### Phase 2 gate:

* Stable phase relationship across repeated taps
* Coherence > threshold in expected bands
* Delay estimates consistent with geometry

### Phase 3 gate:

* Repeatable spatial patterns across sessions
* Frequency-dependent radiation differences observable
* No unexplained phase decorrelation

### Phase 4 gate:

* Reconstructed fields match expected low-order behavior
* Sensitivity to array placement documented

---

## Rationale

1. **Phase coherence is non-negotiable.**
   Without shared clocks and stable geometry, multi-channel data is physically meaningless.

2. **Spatial inference is fragile.**
   Many "acoustic camera" visuals over-promise. Phased gating prevents false confidence.

3. **Radiation ≠ structure.**
   Air pressure fields are not plate motion. Conflating them invalidates results.

4. **Incremental expansion preserves trust.**
   Each phase builds confidence instead of compounding uncertainty.

5. **Testing, not marketing.**
   This system exists to reveal physical behavior, not to produce persuasive images.

---

## Consequences

* Multi-channel development proceeds with scientific discipline
* Claims remain defensible under scrutiny
* Early data remains valid as later sophistication increases
* The system can grow into a true acoustic test platform

---

## Non-Goals (Explicit)

* No "full wave flow" claims from sparse mic arrays
* No structural mode labeling from pressure data alone
* No skipping Phase 2 to reach spatial visualizations
* No optimization or design recommendations at this layer
