# Failure Modes — Viewer Pack v1

> **Audience:** Viewer developers, QA engineers, operators diagnosing issues.
> **Doctrine:** If you see these symptoms in the Viewer, the *producer* broke the contract.

This document maps observable Viewer symptoms to their producer-side contract violations.

---

## Symptom → Rule Mapping

| Symptom | Rule ID | Producer Violation | Fix |
|---------|---------|-------------------|-----|
| "Manifest not found" error | M-001 | `viewer_pack.json` missing from ZIP root | Ensure exporter creates manifest at root |
| "Invalid schema version" error | M-002 | `schema_id` ≠ `"viewer_pack_v1"` or `schema_version` ≠ `"v1"` | Fix manifest generation |
| Point missing from list | M-003 | Point ID not in `manifest.points[]` | Add point to manifest before export |
| Empty spectrum display | S-001 | `spectra/points/{PID}/spectrum.csv` missing | Ensure spectrum CSV exported for each point |
| "Peaks not aligned" warning | P-001 | Peak `freq_hz` not in shared frequency grid | Snap peaks to nearest bin or fix detection |
| Inconsistent frequency axis | S-002 | Points have different `freq_hz` arrays | Use identical FFT params for all points |
| WSI curve empty | W-001 | `wolf/wsi_curve.csv` missing required columns | Export all required columns |
| WSI frequencies misaligned | W-002 | WSI `freq_hz` differs from spectrum grid | Ensure WSI uses same frequency bins |
| Audio playback fails | A-001 | `audio/points/{PID}.wav` missing | Export audio or mark as intentionally absent |
| Hash mismatch error | H-001 | File SHA-256 doesn't match manifest | Re-export pack (file corrupted or modified) |
| Bundle hash invalid | H-002 | `bundle_sha256` doesn't match computed | Re-export (manifest modified after hash) |

---

## Rule Severity

| Severity | Viewer Behavior | Producer Action |
|----------|-----------------|-----------------|
| **ERROR** | Viewer refuses to load / displays error | Must fix before export |
| **WARN** | Viewer loads with degraded functionality | Should fix, export allowed |
| **INFO** | Viewer logs note, full functionality | Optional improvement |

---

## Rule Definitions

### Manifest Rules (M-xxx)

#### M-001: Manifest Existence
- **Severity:** ERROR
- **Check:** `viewer_pack.json` exists at ZIP root
- **Symptom:** Viewer shows "Cannot load pack: manifest not found"

#### M-002: Schema Identity
- **Severity:** ERROR
- **Check:** `schema_id == "viewer_pack_v1"` AND `schema_version == "v1"`
- **Symptom:** Viewer shows "Unsupported pack version"

#### M-003: Points List Completeness
- **Severity:** ERROR
- **Check:** Every point with spectrum data is listed in `manifest.points[]`
- **Symptom:** Point selector missing entries

---

### Spectrum Rules (S-xxx)

#### S-001: Spectrum File Existence
- **Severity:** ERROR
- **Check:** For each PID in `points[]`, `spectra/points/{PID}/spectrum.csv` exists
- **Symptom:** Blank spectrum panel, "No data" message

#### S-002: Shared Frequency Grid
- **Severity:** ERROR
- **Check:** All `spectrum.csv` files have identical `freq_hz` arrays
- **Symptom:** Overlay plots misaligned, comparison fails

#### S-003: Frequency Monotonicity
- **Severity:** ERROR
- **Check:** `freq_hz` column is strictly increasing, no duplicates
- **Symptom:** Rendering glitches, incorrect interpolation

#### S-004: Magnitude Validity
- **Severity:** ERROR
- **Check:** `H_mag` values are finite (no NaN, no Inf)
- **Symptom:** Missing data points, rendering errors

---

### Peaks Rules (P-xxx)

#### P-001: Peaks Grid Alignment
- **Severity:** ERROR
- **Check:** Each `peaks[].freq_hz` matches a `freq_hz` bin in spectrum
- **Symptom:** Peak markers at wrong positions

#### P-002: Analysis File Existence
- **Severity:** ERROR
- **Check:** For each PID in `points[]`, `spectra/points/{PID}/analysis.json` exists
- **Symptom:** No peak annotations displayed

---

### WSI Rules (W-xxx)

#### W-001: WSI Column Contract
- **Severity:** ERROR
- **Check:** `wolf/wsi_curve.csv` has exact columns: `freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible`
- **Symptom:** WSI panel fails to render

#### W-002: WSI Frequency Alignment
- **Severity:** ERROR
- **Check:** WSI `freq_hz` array matches spectrum frequency grid
- **Symptom:** WSI overlay misaligned with spectrum

---

### Audio Rules (A-xxx)

#### A-001: Audio File Existence
- **Severity:** WARN (if audio omission allowed) / ERROR (if required)
- **Check:** For each PID in `points[]`, `audio/points/{PID}.wav` exists
- **Symptom:** Audio playback button disabled or "Audio not available"

---

### Hash Rules (H-xxx)

#### H-001: File Hash Integrity
- **Severity:** ERROR
- **Check:** Each `files[].sha256` matches actual file content
- **Symptom:** "Pack integrity check failed"

#### H-002: Bundle Hash Integrity
- **Severity:** ERROR
- **Check:** `bundle_sha256` matches recomputed value from manifest
- **Symptom:** "Manifest integrity check failed"

---

## References

- [EVIDENCE_PACK_CONTRACT_v1.md](contracts/EVIDENCE_PACK_CONTRACT_v1.md) — Full column specifications
- [PRE_EXPORT_VALIDATION.md](PRE_EXPORT_VALIDATION.md) — Validator implementation
- [TAP_TONE_PI_SANDBOX_HANDOFF.md](TAP_TONE_PI_SANDBOX_HANDOFF.md) — Evidence pipeline overview
