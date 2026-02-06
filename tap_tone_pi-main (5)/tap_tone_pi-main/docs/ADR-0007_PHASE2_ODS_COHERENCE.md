# ADR-0007: Phase 2 ODS + Coherence Pipeline (Measurement-Only)

## Status
Accepted

## Context
Phase 1 provides single-point tap-tone peaks. To understand spatial behavior and correlate with
wolf phenomena, we need repeatable measurements across a guitar plate/top.

The measurement design must:
- preserve raw evidence (WAV)
- support deterministic re-processing
- minimize added mass and coupling bias
- remain measurement-only (no prescriptions)

## Decision
Implement Phase 2 as a **roving grid measurement** using 2-channel capture:
- channel 0: fixed reference sensor/mic
- channel 1: roving sensor/mic moved point-to-point

Core derived computations:
1) ODS snapshot via transfer function:
   - H(f) = FFT(roving) / FFT(reference)
   - magnitude + phase tracked per point for selected frequencies
2) Coherence γ²(f) computed per point/frequency as a **quality gate**
3) WSI (wolf suspicion index) computed as a conservative heuristic score combining:
   - spatial gradient energy (localization sharpness)
   - phase entropy (instability/disorder indicator)
   - localization metrics
   - coherence influence (admissibility)

Outputs are stored in a run directory (CAPDIR):
- evidence per point: audio.wav + capture_meta.json (+ optional analysis/spectrum summaries)
- derived: ods_snapshot.json, wolf_candidates.json, wsi_curve.csv
- plots: png diagnostics for rapid inspection

## Rationale
- **Roving measurement** avoids adding mass at many points simultaneously (a known bias source).
- **Reference channel** provides a stable normalization and helps detect global drive inconsistencies.
- **Coherence** is the standard engineering method to detect contamination and nonlinearity.
- Derived artifacts remain traceable to evidence; reprocessing does not require re-measurement.

## Consequences
- The system requires consistent channel-role conventions.
- Low coherence data must be treated as low-quality and must not drive conclusions.
- This ADR does not define interpretive claims; Phase 2 remains measurement-only.

## Non-goals
- Automatic mode labeling as ground truth (A0, T(0,0), etc.)
- Prescriptive structural recommendations
- Tight coupling to ToolBox/RMOS
- Real-time UI requirements
