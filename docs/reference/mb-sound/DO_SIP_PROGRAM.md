# DO-SIP program — MB Sound empirical tonewood (bounded)

**Intake PR:** https://github.com/HanzoRazer/luthiers-toolbox/pull/244  
**Branch:** `cursor/mb-sound-panel-corpus-83c1`  
**Corpus root:** `services/api/app/data_registry/system/materials/empirical_tonewood/mb_sound/`

This corpus is a **versioned empirical dataset** (~4 species, ~60 specimens). It is **not** a handful of material defaults and must **not** be folded casually into modal interpretation work.

## Sequence (developer-revised)

| DO | Title | Role |
|----|-------|------|
| **DO-SIP-013** | MB Sound Empirical Tonewood Corpus Intake | Import + validate complete corpus from draft PR |
| **DO-SIP-014** | Tonewood Dynamic Consistency and Quality Validation | f, Q, decay, log-dec, E, ρ, radiation, fit |
| **DO-SIP-015** | Empirical Tonewood Cohorts and Distribution Analysis | Species / treatment / batch / distributions |
| **DO-SIP-016** | Alternative Tonewood Behavioral Matching | Specimen vs reference across props (+ later mobility) |
| **DO-SIP-017** | Damping-Aware Plate Response | Bandwidth, decay, phase, impulse, modal mobility |

Modal / Chladni interpretation follows or runs beside these only after specimen evidence classifications are stable.

## What PR #244 is

Controlled **intake boundary** only:

```text
source → draft PR → inventory/validation → specimens → cohorts
        → (future) Empirical Material Registry → adapters
```

Must remain **draft** until corpus-level gates pass. Must **not** change generator defaults, material authorities, plate solvers, or production behavior.

## Layer contracts

See specimen JSON: `source` / `normalized` / `derived` / `validation` / `unresolved` / `artifacts`.
