# SHOP-OP-RECORD-HARDEN-002

Date: 2026-10-27. Draft only. PR #464 (`cc8e13ae`) remains the canonical first slice.

## Versioning decision

Phase 0 found no minor-version mechanism on `ltb_shop_operation_record`. The merged contract pins `schema_version` to the exact string `1.0`. Other domain records in this tree, including physical-engineering evidence, do the same. The written minor-version note in `docs/specs/FRETBOARD_ECOSPHERE_SCHEMA.md` is for that DXF schema, not a shared record library.

This package can represent an additive minor version without changing v1.0 digest semantics:

- `schema_version` is already inside the canonical payload.
- A schema 1.0 file that still has the merged keys produces the merged bytes and the merged SHA-256.
- A schema 1.1 file is a new file. Its digest covers `1.1` and the provenance fields.
- The reader accepts only `1.0` and `1.1`. `1.2`, `2.0`, and any other value fail closed with `UNKNOWN_SCHEMA_VERSION`.
- New writes use `1.1`. A new schema 1.0 file is refused with `NEW_WRITE_REQUIRES_SCHEMA_1_1`.
- No reader rewrites or upgrades a 1.0 file.

Golden bytes were generated from unmodified `origin/main` (`cc8e13ae`) before this version bump was applied to the writer. Digests:

| Fixture | Digest |
|---|---|
| `pre_harden_002_started.json` | `0502de2eb983486d7fdf336989d5de1febe60a97c6546c71fdd68bd907a08c18` |
| `pre_harden_002_completed.json` | `6de312e9279943d8ecfd113b93ec831226ecabe825465d440e448cfb6db3bf6f` |
| `pre_harden_002_aborted.json` | `1bebcdecf9fa8b005267a7e69d0e203ce7026882867c0925726a92d404e0e5be` |
| `pre_harden_002_completed_supersession.json` | `092938283f071f241d3f9facf66bd6551bb6b5764247a6eb782f801002ed48ba` |

## Unit audit

No authoritative quantity vocabulary was adopted. None of the candidates is a shop-actual contract, and they disagree with each other.

| Candidate | Finding |
|---|---|
| CAM translator `supported_units` (`mm`, `inch`) | Toolpath units. This package must not import `app.cam`. |
| BOM `Material.unit` | Free string. The field description lists examples (`bd_ft`, `piece`, `oz`). Not a closed list. |
| Mesh `normalize_unit` | Stiffness and density units that convert to Pa and kg/m³. That is a conversion policy. |
| Physical-engineering `EvidenceProvenance` | Evidence-artifact provenance (`source_type`, `source_id`, `operator_or_process`), not a material-consumption measurement. Importing it would cross a domain boundary and would not match the measurement-source enum. |

The merged token rule remains: `^[a-z][a-z0-9_]*$`, stored as written. Different tokens are not converted, summed, or treated as comparable because their numbers match.

## What changed

1. Default record ids are `sop_{UTC milliseconds}_{uuid4 hex}`, the MAINT-DEFER-019 shape (lane prefix, underscore, full 32-hex suffix). `make_operation_record(..., id_factory=)` injects the factory. An explicit `record_id` is stored unchanged and the factory is not called.
2. New records are schema `1.1`. A material line requires `measurement_source`, `recorded_by`, `observed_at`, and `source_ref` when the source is `IMPORTED_MEASUREMENT`.
3. Allowed sources: `MANUAL_MEASUREMENT`, `SCALE_READING`, `COUNTED`, `IMPORTED_MEASUREMENT`. Prohibited sources raise `PROHIBITED_MEASUREMENT_SOURCE`.
4. Schema 1.0 material lines stay three fields. `material_provenance_disposition` returns `LEGACY_PROVENANCE_UNAVAILABLE`. That string is not stored.
5. `AUTHORITY_BOUNDARY.md` states what the record cannot decide.
6. Structural tests refuse imports outside the standard library and this package, including CAM, readiness, G-code, routers, and estimate or BOM packages.

## Limitations

- One writer per directory. The sequence check reads, then writes. `os.link` publishes a temp file in the same directory and then removes it. This is not a multi-writer store.
- Job verification remains `UNVERIFIED_EXTERNAL_REFERENCE` only.
- Duration remains decimal minutes with basis `MEASURED`.
- No route, UI, cost calculation, design revision, or manufacturing authority.

## Runtime

Python 3.12.3 (`services/api/.venv`). Branch prefix `cursor/`, suffix `-b509`.

## Results

`pytest tests/shop_operations tests/physical_engineering/test_evidence_artifact_v1.py tests/test_openapi.py -q --no-cov`: 45 passed (32 shop-operation, 12 evidence-artifact, 1 OpenAPI). Complexity, file size, bare except, fence checker (2 passed), duplication (0 clone groups, threshold 100), execution-class, and manufacturing inventory `--check` (239 candidates, 143 routers, live=1157) passed. No baseline was raised.

## Rerun

```bash
cd services/api
python -m pytest tests/shop_operations -q --no-cov
python -m app.ci.check_complexity --baseline app/ci/complexity_baseline.json
python -m app.ci.check_file_sizes --baseline app/ci/file_sizes_baseline.json
python -m app.ci.check_bare_except
python -m app.ci.fence_checker_v2
python -m app.ci.check_duplication --threshold 100
python -m app.ci.manufacturing_output_inventory --inventory governance/manufacturing_output_inventory.json --check
python -m app.ci.check_execution_class_compliance
```

From the repo root:

```bash
python scripts/ci/check_cbsp21_gate.py --changed-files $(git diff --name-only origin/main...HEAD)
python scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
git diff --check
```
