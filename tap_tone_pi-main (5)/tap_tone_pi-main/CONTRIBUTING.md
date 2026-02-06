# Contributing to tap_tone_pi

This repo is an **instrumentation toolchain**. The primary success criteria are:
- measurement defensibility (evidence preserved)
- deterministic derived results (same input → same output)
- clear boundaries (no interpretive claims baked into the tool)

Please read:
- `docs/MEASUREMENT_BOUNDARY.md`
- `docs/ADR-0001-measurement-scope.md` … ADRs relevant to your area

---

## Branching

Suggested branches:
- `feature/<topic>-<short-desc>`
- `fix/<topic>-<short-desc>`
- `docs/<topic>-<short-desc>`

---

## Pull requests

PRs should include:
- purpose + scope
- test/validation steps run
- any output shape changes called out explicitly

### Required checks (project intent)
If you change Phase 2 code (`scripts/phase2*`):
- update docs if behavior/CLI/output changed
- update schemas under `contracts/` if JSON output shapes changed

If you add new outputs:
- add a schema (or extend existing)
- add a validation step (script or CI gate)

---

## "Measurement-only" rule

This repo must not:
- assert tone quality labels
- suggest structural modifications
- embed prescriptive advice

It may:
- compute objective features (peaks, coherence, transfer functions)
- compute conservative heuristics (WSI)
- attach quality/confidence metadata

Anything interpretive belongs to a separate advisory layer (Phase 3), and must be
explicitly marked as advisory with provenance and uncertainty.

---

## How to validate locally

Minimum expectations before PR:
1) CLI help runs:
```bash
python scripts/phase2_slice.py --help
```

2) A Phase 2 analyze pass on an existing CAPDIR (if available):

```bash
python scripts/phase2_slice.py analyze --capdir <CAPDIR> --freqs 100,150,185,220,280
```

3) Schema validation (when schemas exist):

* validate `grid.json`, `metadata.json`, `capture_meta.json`, `derived/*.json`

(If a validation script exists, use it. Otherwise, ensure outputs match the contracts.)

---

## Code style

Keep it simple:

* prefer explicit dataclasses/models for run artifacts
* keep "evidence writing" separate from "derived writing"
* avoid hidden state, avoid silent fallbacks
* deterministic processing: document any randomness (and seed it)
