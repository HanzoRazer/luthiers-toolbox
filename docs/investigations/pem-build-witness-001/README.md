# PEM-BUILD-WITNESS-001

Checked against `origin/main` before this branch. No open pull request already covered a physical build-response witness.

This increment adds the contract and the command-line tools for one working instrument's evidence package. It does not contain a real build. No microphone, photograph, mass, or environment reading was available here, and none was invented.

## What a witness is

A completed instrument is a coupled system: wood, geometry, bracing, joints, finish, strings, bridge, the room, the sensors, and the test method. The witness class is `BUILD_RESPONSE_WITNESS`. A separate controlled plate or coupon would be required before anyone could claim a material property. This package does not make that claim.

`PEM-LITERATURE-MB-RECONCILE-002R` is still blocked before preflight. This capture does not compare a build with the 114-row reference population, does not use R1–R5, and does not promote a literature or MB Sound value above `DECLARED_ONLY`.

## Why this is not the stored-evidence artifact

`LtbStoredEvidenceArtifactV1` remains the record for one proposal quantity. It was not amended. A build-response package is a directory of raw files plus a manifest, and it lives outside Git. The code sits under `app.physical_engineering.build_witness` and is not exported from `app.physical_engineering`, so it adds no route.

## What is in Git

- Schemas under `services/api/app/physical_engineering/build_witness/schemas/`
- The library and the scripts `create_build_witness.py`, `ingest_build_witness.py`, `verify_build_witness.py`, `analyze_build_response.py`, and `render_build_witness_report.py`
- Synthetic tests. Their audio is generated in the test process.

Raw audio, photographs, and the real manifest stay out of Git.

## First real witness

Status: not captured.

`create_build_witness.py` writes a blank package and burns a witness id. The blank is `CAPTURE_INCOMPLETE`. It has no audio, no environment numbers, and no mass. Filling it in is an operator action on a real instrument. Until that package exists and verifies, there is no physical witness id to publish.

## Commands

From the repository root, with the API environment:

```bash
python scripts/create_build_witness.py \
  --output /external/evidence/PEM-BUILD-WITNESS-001 \
  --instrument-type acoustic_guitar

python scripts/ingest_build_witness.py \
  --package /external/evidence/PEM-BUILD-WITNESS-001 \
  --write-manifest

python scripts/verify_build_witness.py \
  --package /external/evidence/PEM-BUILD-WITNESS-001 \
  --json
```

Verifier exits: `0` intact and complete, `1` malformed or incomplete, `2` bytes or digests disagree, `3` the check could not be run, `4` a prohibited authority claim.

`analyze_build_response.py` runs only after exit `0`. It writes descriptive duration, level, spectral-peak, envelope-ratio, and repeatability figures under `derived/`. `--derive moe`, `--infer-species`, and `--compare-reference` exit `4` and write nothing.

## States

A verified synthetic package can carry `INTEGRITY_VERIFIED` together with `BUILD_RESPONSE_OBSERVED`, `CALIBRATION_UNVERIFIED`, `METHOD_REVIEW_PENDING`, `REFERENCE_COMPARISON_BLOCKED`, and `SCIENTIFIC_INTERPRETATION_PENDING`. `INTEGRITY_VERIFIED` is a verifier result. The stored manifest is not allowed to claim it. It is not scientific approval.

## Gates after this increment

| Gate | State |
|---|---|
| Evidence-package tooling | Present, covered by synthetic tests |
| Real build-response witness | Not captured |
| Material-property validation | Pending |
| Literature comparison | Blocked |
| Scientific validation | Pending |
| Production readiness | Closed |
| CAM authority | Closed |
| Machine execution | Closed |
