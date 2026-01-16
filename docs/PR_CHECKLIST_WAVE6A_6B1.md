# PR Checklist — Wave 6A + 6B.1 (Linked Cursor + WSI)

## Selection & Cursor

- [ ] Selection persists across file switches until user clears it
- [ ] Clearing cursor removes highlight **without deleting selection context**
- [ ] `selected-freq-hz` passed as `null` when cleared (NaN-safe)

## Spectrum Behavior

- [ ] Clicking a spectrum peak sets `{ pointId, freqHz }`
- [ ] Spectrum renders vertical cursor at `freqHz`
- [ ] Selection Details shows spectrum relpath + analysis relpath

## Audio Jump

- [ ] "Open point audio" navigates to `audio/points/{PID}.wav`
- [ ] Missing audio shows warning, does not navigate

## WSI Renderer

- [ ] `wolf/wsi_curve.csv` renders as a chart (not table)
- [ ] X = `freq_hz`, Y = `wsi` (0–1)
- [ ] Secondary traces: `coh_mean`, `phase_disorder`
- [ ] Admissible zones shaded using exporter `admissible` field only

## WSI Selection

- [ ] Clicking WSI sets `freqHz` **only** (`pointId` remains null)
- [ ] Selection Details shows WSI row fields:
  `wsi`, `coh_mean`, `phase_disorder`, `loc`, `grad`, `admissible`
- [ ] Raw selection JSON equals exporter row (no derived fields)

## Governance Guardrails

- [ ] No scoring, ranking, filtering, or "risk" computation
- [ ] Selection object contains no derived metrics
