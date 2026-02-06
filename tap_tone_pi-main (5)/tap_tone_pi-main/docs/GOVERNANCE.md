# Governance — Tap Tone Pi

> **This repository builds instruments, not opinions.**

---

## 1. Phase 2 Location & Ownership Doctrine

**Phase 2 Implementation Boundary**

Phase 2 algorithms (ODS, coherence, wolf metrics, and related DSP) SHALL live under `scripts/phase2/` as pipeline-oriented implementations.

The `modes/` namespace is reserved exclusively for *measurement entry points* (capture, excitation, sensing, and raw observation) and MAY NOT contain pipeline orchestration, multi-stage DSP workflows, or cross-point aggregation logic.

`modes/` modules MAY invoke Phase 2 pipelines, but Phase 2 pipelines MUST NOT depend on `modes/` internals. This dependency direction is mandatory to preserve an acyclic architecture.

```
┌─────────────┐      ┌─────────────────┐
│   modes/    │ ───▶ │  scripts/phase2/ │
│  (capture)  │      │   (pipelines)    │
└─────────────┘      └─────────────────┘
       │                     │
       └──────────┬──────────┘
                  ▼
         modes/_shared/wav_io.py
            (canonical I/O)
```

---

## 2. Analyzer → ToolBox / RMOS Contract Doctrine

**Analyzer Authority & Downstream Consumption Contract**

All artifacts emitted by this repository represent **authoritative measurement records**.

Downstream systems (including Luthier's ToolBox, RMOS, or any future orchestration layers) MAY:

- index measurement artifacts
- annotate artifacts with advisory or interpretive metadata
- reference artifacts by content hash or manifest

Downstream systems MUST NOT:

- modify raw measurement artifacts
- recompute derived measurement outputs
- replace analyzer-generated values with inferred or optimized alternatives

Any interpretation, optimization, or design guidance derived from these artifacts MUST be expressed as **separate advisory records**, never as mutations of the original measurement data.

```
┌──────────────────┐
│   Tap Tone Pi    │  ← Authoritative source of truth
│   (Analyzer)     │
└────────┬─────────┘
         │
         │  artifacts (immutable)
         ▼
┌──────────────────┐
│  ToolBox / RMOS  │  ← May index, annotate, reference
│  (Downstream)    │     Must NOT modify, recompute, replace
└──────────────────┘
```

---

## 3. CI Enforcement & Guardrail Doctrine

**CI Enforcement Scope**

The following constraints are enforced via CI and are considered **merge-blocking** for the main branch:

| Violation | Enforcement |
|-----------|-------------|
| Direct WAV I/O (`wavfile.read`, `wavfile.write`, `soundfile.read`) outside `modes/_shared/wav_io.py` | `.github/workflows/wav-io-guard.yml` |
| Artifact output violating declared measurement schema version | Schema validation in bundle checks |
| Code introducing interpretation, ranking, optimization, or design guidance into measurement outputs | PR review + grep guardrails |

Experimental or exploratory code MUST reside under explicitly marked experimental directories and MUST NOT be imported by production pipelines.

Warnings MAY be permitted in feature branches, but all violations MUST be resolved prior to merge into `main`.

---

## Enforcement Summary

```
                    ┌─────────────────────────────────┐
                    │          main branch            │
                    │   (protected, merge-blocking)   │
                    └─────────────────────────────────┘
                                   ▲
                                   │ merge
                    ┌──────────────┴──────────────┐
                    │                             │
              ┌─────┴─────┐               ┌───────┴───────┐
              │ CI passes │               │ CI fails      │
              │ ✅ merge  │               │ ❌ blocked    │
              └───────────┘               └───────────────┘
```

---

---

## 4. Measurement Schema Authority & Versioning Doctrine

All analyzer-emitted artifacts SHALL declare an explicit `schema_version`.

Schemas are authoritative contracts and MUST be treated as immutable once released.

### Required vs Optional Fields

Each schema MUST explicitly define:

- **Required fields**: necessary to interpret the measurement numerically
- **Optional fields**: metadata, diagnostics, or contextual enrichment

Optional fields MAY be omitted without invalidating the artifact.
Required fields MUST be present for the artifact to be considered valid.

### Schema Location & Ownership

Canonical schemas SHALL live under:

```
docs/schemas/       # Core measurement schemas
contracts/          # Cross-repo interface schemas
```

**All validators MUST source schema file locations and versions from `contracts/schema_registry.json` (no hardcoded maps).**

Each schema file MUST include:

- schema name
- schema_version
- required vs optional field list
- unit declarations
- interpretation boundary notes (if applicable)

Schema changes require:

1. Version bump
2. Backward compatibility note OR migration rationale
3. Corresponding test update

---

## 5. Audio Handling & WAV Policy Doctrine

The analyzer defines a single canonical audio policy.

### Canonical Audio Representation

- Internal DSP representation: `float32`, normalized to `[-1.0, +1.0]`
- External storage: PCM WAV

### Mono vs Multi-Channel Policy

- Mono measurements SHALL be represented as single-channel WAV
- Two-channel WAVs SHALL be used only when a reference/roving distinction is required
- Stereo files MUST NOT be implicitly averaged without an explicit policy declaration

### Bit Depth Policy

- Default write format: **16-bit PCM**
- 24-bit PCM MAY be adopted in the future via a schema + governance update
- Bit depth choice MUST be documented in the WAV I/O module and not redefined elsewhere

### Canonical WAV I/O Layer

All WAV read/write operations MUST go through:

```
modes/_shared/wav_io.py
```

Direct use of `wavfile.read`, `wavfile.write`, or `soundfile.read/write`
outside this module is a **CI-blocking violation**.

---

## 6. Imaging & Chladni Measurement Doctrine

Imaging-based measurements (e.g., Chladni patterns) are treated as
measurement artifacts, not interpretations.

### Image Matching Rules

- Image-to-grid mismatch tolerance MUST be explicitly declared
- Multiple images per excitation MAY be supported but MUST be declared in schema
- Environmental conditions (lighting, contrast agents) MUST be logged if required

### Frequency Mismatch Policy

**Mismatch policy:** warn + keep, **fail** if `delta_hz` exceeds `CHLADNI_FREQ_TOLERANCE_HZ` (default 5 Hz).

- Each pattern record includes `nearest_detected_hz` and `delta_hz`
- Warnings are recorded in `_warnings` array
- Exit code 2 if worst delta exceeds tolerance

### Interpretation Boundary

Pattern recognition, modal labeling, or aesthetic scoring MUST NOT occur
inside analyzer outputs.

Any interpretation of imaging artifacts SHALL occur downstream
as advisory records.

---

## 7. Lab-to-Analyzer Promotion Doctrine

Experimental or lab code MAY exist under clearly marked `lab/` or `experimental/`
namespaces.

Promotion into the Analyzer requires completion of the following checklist:

| # | Requirement | Verification |
|---|-------------|--------------|
| 1 | Measurement-only behavior verified | Code review |
| 2 | Schema defined and versioned | `docs/schemas/` or `contracts/` |
| 3 | Deterministic test fixture added | `tests/` |
| 4 | Documentation updated | README or phase doc |
| 5 | CI gates pass | All workflows green |
| 6 | Owner sign-off recorded | CODEOWNERS or ADR |

No feature is considered "Analyzer-grade" without completing this checklist.

### Promotion Flow

```
┌─────────────────┐     checklist      ┌─────────────────┐
│   tap-tone-lab  │ ────────────────▶  │   tap_tone/     │
│  (experimental) │     complete       │   (production)  │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │                                      │
        └──────────────────┬───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  CI + Tests │
                    │  must pass  │
                    └─────────────┘
```

---

## 8. Continuous Integration Minimum Bar Doctrine

The following tests constitute the **non-negotiable CI floor**:

| Test Category | Enforcement | Status |
|---------------|-------------|--------|
| Schema validation | `schemas-validate.yml` | ✅ Active |
| Deterministic DSP regression | `test.yml` | ✅ Active |
| WAV I/O unit tests | `test.yml` | ✅ Active |
| WAV I/O guardrail | `wav-io-guard.yml` | ✅ Active |
| Boundary enforcement | `boundary-guard.yml` | ✅ Active |
| Advisory language guard | `no-logic-creep.yml` | ✅ Active |
| Phase 2 schema validation | `phase2-validate.yml` | ✅ Active |

**Hardware-dependent tests MUST NOT be required for PR merge.**

Additional tests MAY be added, but these minimums SHALL NOT be removed
without governance approval.

### CI Workflow Summary

| Workflow | Purpose | Blocking |
|----------|---------|----------|
| `test.yml` | pytest suite (DSP, WAV I/O, unit tests) | ✅ Yes |
| `wav-io-guard.yml` | Block direct `wavfile` usage | ✅ Yes |
| `schemas-validate.yml` | Validate measurement artifact schemas | ✅ Yes |
| `contracts-validate.yml` | Validate contract schemas (tap_peaks, moe_result, etc.) | ✅ Yes |
| `boundary-guard.yml` | Enforce import boundaries | ✅ Yes |
| `no-logic-creep.yml` | Block advisory language in modes/ | ✅ Yes |
| `phase2-validate.yml` | Validate Phase 2 schemas | ✅ Yes |

---

## Enforcement Summary

```
                    ┌─────────────────────────────────┐
                    │          main branch            │
                    │   (protected, merge-blocking)   │
                    └─────────────────────────────────┘
                                   ▲
                                   │ merge
                    ┌──────────────┴──────────────┐
                    │                             │
              ┌─────┴─────┐               ┌───────┴───────┐
              │ CI passes │               │ CI fails      │
              │ ✅ merge  │               │ ❌ blocked    │
              └───────────┘               └───────────────┘
```

---

## 9. Analysis vs. Interpretation Boundary Doctrine

The Desktop Analyzer and associated instrumentation tools may perform **objective analytical transformations** (e.g., FFTs, transfer functions, coherence, statistical summaries) on captured measurement data in order to produce **verifiable, reproducible descriptors**. These analytical outputs are **measurement facts**, not judgments.

**Interpretation, evaluation, optimization, or prescriptive guidance**—including tonal assessment, structural recommendations, or design decisions—**are explicitly out of scope** for this system and must occur only in downstream tools or human-in-the-loop workflows.

> *Analysis is permitted; interpretation is prohibited.*

---

## 10. Spectral View UX Contract

### Purpose

The Spectral View exists to **visualize measured data and analytical results** so that users can verify signal quality, repeatability, and objective features of the measurement.

It is **not** a tone-grading or decision interface.

---

### What the Spectral View MAY Show (Allowed)

These are **raw facts** or direct mathematical transforms.

#### Time Domain

- Raw waveform (mono or channel-separated)
- Time scale (seconds)
- Amplitude scale (normalized or physical units)
- Clipping indicators

**Label:** *Raw measurement — time domain*

#### Frequency Domain

- Magnitude spectrum (FFT / PSD)
- Frequency axis (Hz)
- Amplitude axis (linear or dB, explicitly labeled)
- Peak markers (frequency + magnitude only)

**Label:** *Measured frequency content (FFT)*

#### Transfer / Coherence (Phase 2)

- |H(f)| magnitude
- Phase (degrees)
- Coherence γ²(f)

**Label:** *Derived analytical quantities (transfer function, coherence)*

#### Spatial / ODS

- Grid heatmaps
- Mode-shape amplitude distributions
- Localization indices

**Label:** *Spatial distribution of measured response*

#### Metadata / Provenance

- Sample rate
- Window type
- FFT size
- Device ID
- Capture timestamp

**Label:** *Measurement configuration*

---

### What the Spectral View MUST NOT Show (Prohibited)

These are interpretive or prescriptive and **must never appear** in this UI:

| Prohibited | Reason |
|------------|--------|
| ❌ "Good / bad" indicators | Value judgment |
| ❌ "Optimal" frequencies | Prescriptive |
| ❌ "Too stiff / too loose" | Design guidance |
| ❌ "This area should be thinned" | Prescriptive |
| ❌ Tone adjectives (warm, bright, dead, etc.) | Subjective interpretation |
| ❌ Scores, rankings, or grades | Value judgment |
| ❌ Automated comparisons to "ideal" guitars | Prescriptive |

If a value can't be defended as a **direct output of math on measured data**, it doesn't belong here.

---

### Mandatory UX Labeling Rules

Every Spectral View must include:

1. **Mode Banner**

   ```
   Measurement View — No Interpretation Applied
   ```

2. **Legend Discipline**

   - Units must be explicit (Hz, dB, seconds, mm)
   - Axes must be labeled
   - No unlabeled color scales

3. **Provenance Footer**

   - Capture timestamp
   - Device/channel info
   - Schema version (if applicable)

---

## Philosophy

This governance exists to **protect innovation**, not constrain it.

- Measurement code stays measurement code
- Advisory code stays in downstream systems
- Artifacts remain forensically defensible
- Dependencies flow in one direction
- Policy is enforced by machines, not memory

---

*Adopted: 2025-12-31*  
*Last Updated: 2025-12-31*  
*Owner: Ross Echols*
