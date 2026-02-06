# ADR-0005: Repeatability, Variance, and Confidence Metrics

**Status:** Accepted  
**Date:** 2025-12-25  
**Context:** Tap-Tone Measurement Node (Phase 1+)  
**Decision Drivers:** Measurement reliability, comparability across time, scientific defensibility

---

## Decision

### 1) Repeatability is a first-class requirement

The system SHALL include repeatability tooling and metrics before advancing beyond Phase 1.

A "capture" is not a single tap; it is a **set of takes** when repeatability is required.

---

### 2) Canonical repeatability procedure (v0.1)

For a given configuration (instrument + protocol + mic geometry):

* Record **N takes** (default N=10) at the same tap point
* Compute metrics per take
* Report summary statistics across takes

All repeatability runs MUST reference:

* protocol identifiers (tap tool, mic distance, fixture)
* capture config (sample rate, seconds, gain info if available)

---

### 3) Metrics computed per take (minimum)

Each take SHALL compute:

* `dominant_hz`
* `peaks[]` (top K)
* `rms`
* `clipped`
* (Phase 2+) coherence and delay metrics

---

### 4) Aggregate repeatability metrics (minimum)

Across N takes, compute:

* Mean and standard deviation of `dominant_hz`
* Median absolute deviation (MAD) for robustness
* Peak stability: for each of top K peaks, frequency clustering across takes
* Outlier detection: identify takes outside tolerance

Store aggregates in `takes.json` (or in `analysis.json` under a `repeatability` block).

---

### 5) Confidence metric definition (v0.1)

`confidence` SHALL be a conservative 0..1 score derived from:

* non-clipped audio (penalize clipping strongly)
* sufficient RMS above noise floor
* peak presence above prominence threshold
* (Phase 2+) coherence in band of interest

Confidence SHALL NOT encode "tone quality" or "good/bad" judgments.

---

### 6) Acceptance gates (starter targets)

Targets are configurable per instrument class, but defaults:

* Clipping rate: **0%** (any clipped take requires re-run)
* Dominant peak stability: `std(dominant_hz)` ≤ **2.0 Hz** over N=10 (starter gate)
* Peak cluster stability: top 3 peaks appear in ≥ **70%** of takes

These gates are documentation defaults and SHALL be refined with empirical data.

---

## Rationale

* Single-shot taps are too noisy for credible conclusions.
* Repeatability metrics provide a sanity check for both hardware and protocol.
* Confidence must reflect measurement validity, not musical opinion.

---

## Consequences

* Phase 1 requires multi-take support and summary artifacts.
* Multi-channel work becomes far easier to debug with repeatability baselines.
* Longitudinal tracking is enabled through stable stats.

---

## Non-Goals

* No "quality score" or "tone rating"
* No direct mapping from confidence to build recommendations
