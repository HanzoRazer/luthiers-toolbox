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

`analyze_build_response.py` runs only after exit `0`. It writes descriptive duration, level, spectral-peak, envelope-ratio, and repeatability figures to `derived/observations.json`. `--derive moe`, `--infer-species`, and `--compare-reference` exit `4` and write nothing. Neither analysis nor the report rewrites the evidence seal.

`create_build_witness.py`, `ingest_build_witness.py` and `verify_build_witness.py` use the ledger `pem-witness-ledger` beside the package unless `--registry` names another. Keep the ledger with the evidence and protect it like the evidence: it records which witness ids are used and the first seal of each.

## Creating a package

`create` takes exclusive ownership of the destination before writing anything. It creates a reservation directory, `.<name>.reservation`, beside the destination, writes the blank package into a uniquely named staging directory, and publishes it with a single rename. It removes the staging and reservation directories afterwards, whether it succeeded or failed. An existing destination is never written into or replaced, even if it is empty.

If a creator is killed, its reservation stays behind, and the next `create` for that destination fails with the reservation's path. Recovery: make sure no `create` is running and that the destination does not exist, remove the reservation directory, and run `create` again. The ids the interrupted run burned stay burned.

## Package layout and the seal

The evidence is the root records (`BUILD-RECORD.json`, `TEST-PROTOCOL.json`, `EQUIPMENT.json`, `ENVIRONMENT.csv`, `MEASUREMENTS.csv`, `READ-ME-FIRST.txt`) and everything under `raw/`. Recordings must be WAV files under `raw/audio/`, photographs PNG files under `raw/images/`, and every other evidence reference (`raw_evidence_ref`, a material `evidence_ref`) must point under `raw/`. Every referenced file must appear in the sealed manifest with the same length and digest.

Ingest seals the evidence once. Before writing the manifest it records the manifest's SHA-256 in the ledger. A witness is never resealed with different bytes: deleting the manifest and ingesting again, or ingesting with `--replace-manifest` after anything sealed has changed, is refused. Re-running ingest on unchanged evidence is allowed and writes the same bytes. A correction is a new witness that supersedes the old one. When the ledger is present, verify also requires the manifest to be the one the ledger anchored. Without a ledger, verify reports a `ledger_unavailable` warning.

Two generated products may sit outside the seal: `derived/observations.json` and `reports/WITNESS-REPORT.md`. Any other file, under `derived/`, `reports/`, or anywhere else, is refused (exit `2`).

## Derived observations

`derived/observations.json` is written after the seal, so the seal cannot vouch for it. The verifier and the report trust it only if:

- the evidence itself verifies;
- it is UTF-8 JSON that satisfies `pem_derived_observations_v1`;
- it names this witness, this session, and the digest of the current `WITNESS-MANIFEST.json`;
- its inputs are exactly the protocol's recordings, each with its sealed length and digest;
- every observation cites only those inputs;
- recomputing it from the sealed audio gives an identical document.

The last check shows the numbers were not edited. Any failure is exit `2`, and the report is not written. A valid derived document is reported as "recomputed from the sealed audio". The report itself is output, not evidence: it is regenerated from the verified records and is never read back as input.

## What the verifier enforces

Prohibited claims. Every JSON document, every CSV row, every JSON or CSV file under `raw/`, and the derived observations are scanned for prohibited authority claims, both as keys and as whole values, regardless of case or separators: `intrinsic_moe`, `Intrinsic-MOE` and `INTRINSIC MOE` are one claim. A sentence that mentions the words is not a claim. A prohibited claim is exit `4` and never comes with `INTEGRITY_VERIFIED`. Ingest refuses to seal it.

Identity. `BUILD-RECORD.json` holds the witness and session ids. The verifier requires the same ids in:

- `WITNESS-MANIFEST.json` `witness_id`
- `TEST-PROTOCOL.json` `session_id`
- every `MEASUREMENTS.csv` row, `witness_id` and `session_id`, nonblank

`EQUIPMENT.json` and `ENVIRONMENT.csv` carry no ids in schema version 1. They are tied to the witness only by being listed and digested in its manifest.

CSV records. `ENVIRONMENT.csv` and `MEASUREMENTS.csv` must be UTF-8 with strict quoting. The header must match the template's columns exactly, in order. Every data row must be as wide as the header. Any deviation rejects the whole file. The verifier does not repair a row and then check the repaired copy.

Schemas. The verifier applies the published schemas to `BUILD-RECORD.json` (`pem_build_record_v1`), `TEST-PROTOCOL.json` (`pem_test_protocol_v1`), every `MEASUREMENTS.csv` row (`pem_measurement_observation_v1`), and `WITNESS-MANIFEST.json` (`pem_build_witness_v1`). Each schema is closed: an unknown field, a missing field, or a value of the wrong type is a finding that names the document and the location, for example `TEST-PROTOCOL.json /trials/0`. Record and row violations are malformed (exit `1`). Manifest violations are integrity failures (exit `2`). Ingest refuses to write a manifest that would break its own schema. A blank template satisfies the schemas: fields not yet captured are `null`, and completeness is checked separately. `derived/observations.json` has its own schema, `pem_derived_observations_v1`; see "Derived observations".

Configuration. One protocol is one configuration. Every trial must repeat the protocol's excitation method and position, microphone position, support condition, and string state. A change of configuration is a new protocol and session, not a second group inside one.

Scale length. A decimal `scale_length_mm` is accepted. A `null` value with a nonblank `scale_length_unknown_reason` is accepted as recorded uncertainty: the verifier emits a `warning` finding, `scale_length_unknown`, which does not change the exit code and is listed in the report under "Recorded uncertainty". A `null` value with no reason is malformed. At least one directly measured dimension in `MEASUREMENTS.csv` is still required either way.

Photographs. Each required photograph must be a different file, by name regardless of case and by content, that decodes as a complete PNG: valid chunk checksums from `IHDR` through `IEND`, and all pixel data present. This shows the file is an image. It does not show what the image depicts.

Audio. The verifier accepts the protocol's declared rate, channel count, and 8/16/24/32-bit PCM. The data must be exactly as long as the header declares; a truncated recording is malformed. Analysis decodes each width at its own full scale and refuses multichannel captures.

Manifest. Each path may appear once. A duplicate entry, even with a different spelling of case, is an integrity failure.

Report. The report lists only rows the verifier accepted. If `MEASUREMENTS.csv` is rejected, the report says so and shows none of its rows.

Not covered: a Windows directory junction inside the package is not detected as a link on Python 3.11. Do not place junctions in a package.

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
