# Schema Location Notice

**⚠️ This directory contains legacy/development schema drafts.**

## Canonical Location

The authoritative schemas are in `contracts/schemas/`. Evidence:

1. `contracts/schema_registry.json` points all schemas to `contracts/schemas/` paths
2. CI workflow `contracts-validate.yml` validates against `contracts/schemas/`
3. `scripts/validate_schemas.py` defaults to `--schemas-root contracts/schemas`

## This Directory

The `schemas/measurement/` files are simpler drafts used by `tests/test_measurement_schemas.py` for example validation. They lack:

- `$id` and `$schema` declarations
- `additionalProperties: false` enforcement
- Full field validation

**Do not add new schemas here.** All new contracts go in `contracts/schemas/`.
