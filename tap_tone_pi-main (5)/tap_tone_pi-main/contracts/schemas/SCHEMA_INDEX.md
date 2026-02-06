# Schema Index — Tap Tone Pi Contracts

> **Governance Reference:** See [GOVERNANCE.md §4](../../docs/GOVERNANCE.md) for schema authority doctrine.

---

## Schema Registry

| Schema ID | Version | File | Artifact Type | Purpose |
|-----------|---------|------|---------------|---------|
| `tap_peaks` | 1.0 | `tap_peaks.schema.json` | `chladni_peaks` | FFT peak detection results |
| `moe_result` | 1.0 | `moe_result.schema.json` | `bending_moe` | Static bending MOE calculation |
| `measurement_manifest` | 1.0 | `manifest.schema.json` | `measurement_manifest` | Run manifest with artifact hashes |
| `chladni_run` | 1.0 | `chladni_run.schema.json` | `chladni_run` | Chladni pattern run index |

---

## Version Policy

- Schema versions follow `MAJOR.MINOR` format (e.g., `1.0`, `1.1`, `2.0`)
- **MAJOR** bump: breaking changes (field removal, type change, new required field)
- **MINOR** bump: backward-compatible additions (new optional fields)

All emitters MUST include both `schema_id` and `schema_version` fields.

---

## Required vs Optional Fields

Each schema defines required fields explicitly. See individual schema files for:

- `required` array — fields that MUST be present
- All other properties — optional (omission is valid)

---

## Field Conventions

### Timestamps

- Field: `created_utc`
- Format: ISO 8601 with timezone (`2025-12-31T15:00:00Z`)

### Hashes

- Algorithm: SHA-256
- Format: lowercase hex, 64 characters
- Pattern: `^[a-f0-9]{64}$`

### Paths

- Relative to artifact root or absolute
- Forward slashes preferred for cross-platform compatibility

### Units

| Field Pattern | Unit |
|---------------|------|
| `*_hz` | Hertz |
| `*_mm` | Millimeters |
| `*_GPa` | Gigapascals |
| `*_Nmm2` | Newton-millimeters² |
| `*_C` | Celsius |
| `*_pct` | Percent (0–100) |

---

## Validation

Run the validator against output artifacts:

```bash
python scripts/validate_schemas.py --out-root out --schemas-root contracts/schemas
```

Or via Makefile:

```bash
make validate-schemas
```

---

## Adding New Schemas

1. Create `contracts/schemas/<name>.schema.json`
2. Add entry to `SCHEMA_MAP` in `scripts/validate_schemas.py`
3. Update this index
4. Add example artifact to `examples/measurement/`
5. Update CI if needed

---

*Last Updated: 2025-12-31*
