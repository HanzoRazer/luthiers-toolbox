# ADR-0003: Artifact Schema for Multi-Channel Data

**Status:** Accepted  
**Date:** 2025-12-25  
**Context:** Tap-Tone Measurement Node — Single & Multi-Channel Acquisition  
**Decision Drivers:** Reproducibility, forward compatibility, RMOS ingestion, scientific traceability

---

## Decision

### 1. Artifact-First Principle

All measurements SHALL produce **durable, inspectable artifacts** that fully describe:

* what was measured
* how it was measured
* with what geometry
* under what assumptions

Artifacts, not UI state or in-memory objects, are the **primary product** of the system.

---

### 2. Artifact Bundle Structure (Canonical)

Each measurement session SHALL produce a **self-contained artifact bundle**.

#### Session root

```
session_<UTC_TIMESTAMP>/
├── metadata.json
├── session.jsonl
├── captures/
│   ├── capture_<UTC_TIMESTAMP>/
│   │   ├── audio.wav
│   │   ├── analysis.json
│   │   ├── spectrum.csv
│   │   ├── channels.json
│   │   └── geometry.json
│   └── ...
```

This structure applies to:

* single-channel (Phase 1)
* multi-channel (Phase 2+)

Files may be empty or simplified in early phases but **paths SHALL exist**.

---

### 3. Multi-Channel Audio Artifact (`audio.wav`)

* Format: WAV
* Encoding: PCM 16-bit or 24-bit
* Sampling: single shared sample rate across all channels
* Channels:

  * Channel order SHALL be deterministic
  * Channel index SHALL map to geometry metadata

Example:

```
audio.wav
Channels:
  ch0 → mic_0
  ch1 → mic_1
  ch2 → mic_2
```

No resampling, mixing, or phase manipulation SHALL occur at capture time.

---

### 4. Analysis Artifact (`analysis.json`)

`analysis.json` SHALL describe **derived features**, not raw signals.

#### Required (Phase 1+)

```json
{
  "ts_utc": "2025-03-08T19:42:10Z",
  "sample_rate": 48000,
  "channels": 2,
  "dominant_hz": 183.4,
  "rms": [0.021, 0.019],
  "clipped": [false, false],
  "confidence": 0.82
}
```

#### Required (Phase 2+ additions)

```json
{
  "peaks": {
    "ch0": [{"freq_hz": 183.4, "magnitude": 0.91}],
    "ch1": [{"freq_hz": 181.9, "magnitude": 0.88}]
  },
  "cross_channel": {
    "delay_samples": 14,
    "delay_seconds": 0.000291,
    "coherence": [
      {"freq_hz": 180, "value": 0.93},
      {"freq_hz": 220, "value": 0.87}
    ]
  }
}
```

Derived fields SHALL be:

* clearly labeled
* reproducible from `audio.wav`
* versioned if algorithms change

---

### 5. Spectrum Artifact (`spectrum.csv`)

`spectrum.csv` SHALL represent **per-channel spectra**.

Minimum schema:

```csv
freq_hz,ch0_mag,ch1_mag
40.0,0.12,0.10
41.0,0.15,0.13
...
```

* Frequency axis SHALL be shared across channels
* Magnitudes SHALL be normalized per channel
* No smoothing unless explicitly documented

---

### 6. Channel Metadata (`channels.json`)

This file defines **what each channel physically represents**.

```json
{
  "channels": [
    {
      "index": 0,
      "id": "mic_0",
      "type": "microphone",
      "model": "UMIK-1",
      "serial": "A12345",
      "role": "reference"
    },
    {
      "index": 1,
      "id": "mic_1",
      "type": "microphone",
      "model": "ECM8000",
      "role": "secondary"
    }
  ]
}
```

Channel order in this file MUST match WAV channel order.

---

### 7. Geometry Metadata (`geometry.json`)

This file captures **physical placement and orientation**.

```json
{
  "coordinate_system": "instrument_body",
  "units": "mm",
  "origin": "bridge_center",
  "microphones": [
    {
      "id": "mic_0",
      "position": [0, 0, 300],
      "orientation_deg": [0, 0, -1]
    },
    {
      "id": "mic_1",
      "position": [120, 40, 300],
      "orientation_deg": [0, 0, -1]
    }
  ]
}
```

Geometry SHALL be:

* explicit
* numeric
* human-readable

Estimates are acceptable if labeled as such.

---

### 8. Session Log (`session.jsonl`)

`session.jsonl` SHALL be append-only and record **capture events**.

Each entry MUST include:

* capture timestamp
* capture path
* summary metrics
* operator label (if provided)

This file is the **chronological ground truth** for the session.

---

## Rationale

1. **Artifacts outlive code.**
   WAV + JSON + CSV can always be reanalyzed as methods improve.

2. **Multi-channel data is meaningless without geometry.**
   Phase, delay, and spatial inference require explicit placement.

3. **Reproducibility requires separation.**
   Raw signals, derived features, and interpretation must be distinct.

4. **RMOS ingestion should be trivial.**
   This schema aligns with RunArtifact-style attachment models.

5. **Early rigor prevents later data loss.**
   Even Phase 1 data becomes usable for future multi-channel analysis.

---

## Consequences

* All future phases can rely on a stable data contract
* Multi-channel analysis remains physically grounded
* Tooling can evolve without invalidating historical data
* Research-grade claims remain defensible

---

## Non-Goals (Explicit)

* No binary-only artifacts
* No implicit geometry or channel meaning
* No overwriting or mutation of raw data
* No "smart" interpretation embedded in artifact files

---

## Notes

This schema MAY be extended, but fields SHALL NOT be removed or repurposed.
Versioning MUST be additive.
