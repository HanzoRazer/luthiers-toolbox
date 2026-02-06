# Evidence Pack Contract v1 — Reference Specification

> **Status:** Normative reference for `viewer_pack_v1` schema.  
> **Audience:** Engineers implementing exporters/validators.  
> **Normative summary:** See [TAP_TONE_PI_SANDBOX_HANDOFF.md](../TAP_TONE_PI_SANDBOX_HANDOFF.md)

---

## 1. Per-Point Artifacts

### 1.1 `spectra/points/{POINT_ID}/spectrum.csv`

**Canonical Header:**
```
freq_hz,H_mag,coherence,phase_deg
```

| Column | Type | Units | Description | Missing Value Policy |
|--------|------|-------|-------------|---------------------|
| `freq_hz` | float | Hz | Frequency bin center. Must be monotonically increasing. | Never missing |
| `H_mag` | float | dimensionless | Transfer function magnitude \|H(f)\| | `NaN` if undefined |
| `coherence` | float | 0–1 | γ²(f), coherence estimate | `0` or `NaN`, never omit row |
| `phase_deg` | float | degrees | ∠H(f), unwrapped preferred | `NaN` if undefined |

**Invariants:**
- All points in a session MUST share identical `freq_hz` bins (same count, same values)
- Bin spacing MUST be constant (FFT-derived)
- Column order MUST match canonical header exactly
- Decimal separator MUST be `.` (not locale `,`)
- Field delimiter MUST be `,`

---

### 1.2 `spectra/points/{POINT_ID}/analysis.json`

**Canonical Structure:**
```json
{
  "schema_version": "analysis_v1",
  "peaks": [
    {
      "freq_hz": 187.5,
      "bin_index": 16,
      "label": null
    }
  ],
  "notes": ""
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | MUST | Version identifier |
| `peaks` | array | MUST | May be empty `[]` |
| `peaks[].freq_hz` | float | MUST | Must match a `freq_hz` value in `spectrum.csv` |
| `peaks[].bin_index` | int | SHOULD | Index into spectrum for reproducibility |
| `peaks[].label` | string\|null | MAY | Operator-assigned label only. No "strongest", "worst", etc. |
| `notes` | string | MAY | Factual only. No recommendations. |

**Forbidden in `label` or `notes`:**
- Ranking words: "strongest", "dominant", "worst", "primary"
- Quality words: "good", "bad", "optimal", "problem"
- Prescriptions: "fix", "thin", "stiffen", "remove"
- Diagnostic claims: "wolf", "dead spot"

---

### 1.3 `audio/points/{POINT_ID}.wav`

| Property | Requirement |
|----------|-------------|
| Format | PCM WAV (int16 or int24) |
| Channels | Must match capture (1 or 2) |
| Sample rate | Must match provenance declaration |
| Correspondence | MUST be the exact recording that produced the spectrum |
| Post-processing | None, unless documented in provenance |

---

## 2. Session-Level Artifacts

### 2.1 `wolf/wsi_curve.csv`

**Canonical Header:**
```
freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible
```

| Column | Type | Units | Description | Missing Value Policy |
|--------|------|-------|-------------|---------------------|
| `freq_hz` | float | Hz | Must align exactly with per-point spectrum bins | Never missing |
| `wsi` | float | 0–1 | Wolf Stress Index, normalized | `NaN` if undefined |
| `loc` | float | exporter-defined | Localization metric | `NaN` if undefined |
| `grad` | float | exporter-defined | Gradient metric | `NaN` if undefined |
| `phase_disorder` | float | exporter-defined | Phase spread metric | `NaN` if undefined |
| `coh_mean` | float | 0–1 | Mean coherence across all points | `NaN` if undefined |
| `admissible` | bool | true/false | Upstream classification only | Never missing |

**Invariants:**
- Row count MUST equal per-point spectrum bin count
- `freq_hz` values MUST be identical to per-point spectra
- `admissible` is the ONLY classification field (Wave 6)

---

### 2.2 `wolf/wolf_candidates.json`

**Canonical Structure:**
```json
{
  "schema_version": "wolf_candidates_v2",
  "thresholds": {
    "wsi_threshold": 0.6,
    "coherence_threshold": 0.7
  },
  "candidates": [
    {
      "freq_hz": 185.5,
      "wsi": 0.82,
      "coh_mean": 0.45,
      "admissible": false,
      "top_points": ["A3", "B2", "C4"],
      "notes": ""
    }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `thresholds.wsi_threshold` | MUST | Explicit numeric threshold used |
| `thresholds.coherence_threshold` | MUST | Explicit numeric threshold used |
| `candidates[].freq_hz` | MUST | Frequency bin |
| `candidates[].top_points` | MUST | Contributing spatial points |
| `candidates[].notes` | MAY | Factual only, no quality language |

**Forbidden language in `notes`:**
- "problem frequency", "wolf tone", "dead spot"
- "likely wolf", "suspected issue"
- "should be addressed", "consider thinning"

---

## 3. Provenance Artifacts

### 3.1 `provenance.json`

```json
{
  "schema_version": "provenance_v1",
  "capture": {
    "device_id": "UMIK-1_SN12345",
    "sample_rate_hz": 48000,
    "channels": 2,
    "timestamp_utc": "2026-01-15T14:30:00Z"
  },
  "algorithm": {
    "algo_id": "phase2_transfer_coherence",
    "algo_version": "1.0.0",
    "numpy_version": "1.24.0",
    "scipy_version": "1.11.0"
  },
  "fft": {
    "nperseg": 4096,
    "window": "hann",
    "noverlap": 2048
  }
}
```

**Invariants:**
- `capture` and `algorithm` MUST be separate objects
- Paths MUST be relative, not OS-specific absolute paths
- Versions MUST be explicit, not "latest"

---

### 3.2 `session_meta.json`

```json
{
  "schema_version": "session_meta_v1",
  "instrument_id": "J45_2024_001",
  "operator": "RKS",
  "environment": {
    "temp_c": 22.0,
    "rh_pct": 45.0
  },
  "grid_id": "guitar_top_35pt",
  "notes": ""
}
```

The Viewer displays this verbatim. No interpretation.

---

## 4. Units Conventions

| Quantity | Unit | Notes |
|----------|------|-------|
| Frequency | Hz | Always Hz, never kHz |
| Phase | degrees | Prefer unwrapped |
| Coherence | 0–1 | Never percentage |
| Temperature | °C | |
| Humidity | % RH | 0–100 |
| Dimensions | mm | Unless explicitly stated |
| Force | N | Unless explicitly stated |

---

## 5. NaN and Zero Policies

| Situation | Value | Notes |
|-----------|-------|-------|
| Coherence undefined (no overlap) | `NaN` | |
| Coherence zero (no correlation) | `0` | Valid measurement |
| Phase undefined | `NaN` | |
| Magnitude undefined | `NaN` | |
| Missing row | **FORBIDDEN** | All bins must be present |

---

## 6. Examples

### Minimal Valid `spectrum.csv`
```csv
freq_hz,H_mag,coherence,phase_deg
30.0,0.0012,0.92,12.3
41.015625,0.0018,0.88,15.7
52.03125,0.0025,0.91,-8.2
```

### Minimal Valid `analysis.json`
```json
{
  "schema_version": "analysis_v1",
  "peaks": [],
  "notes": ""
}
```

### Minimal Valid `wolf_candidates.json`
```json
{
  "schema_version": "wolf_candidates_v2",
  "thresholds": {
    "wsi_threshold": 0.6,
    "coherence_threshold": 0.7
  },
  "candidates": []
}
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2026-01-16 | Initial release |
