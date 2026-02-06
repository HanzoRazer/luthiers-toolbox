# JSON Schema Reference

This directory contains formal JSON Schema definitions for all artifact files produced by the Tap Tone measurement system.

## Schema Files

- **[analysis.schema.json](analysis.schema.json)** - Analysis results (`analysis.json`)
- **[channels.schema.json](channels.schema.json)** - Channel metadata (`channels.json`)
- **[geometry.schema.json](geometry.schema.json)** - Microphone geometry (`geometry.json`)
- **[metadata.schema.json](metadata.schema.json)** - Session metadata (`metadata.json`)

## Usage

These schemas enforce the artifact contract defined in [ADR-0003](../ADR-0003-artifact-schema-multichannel.md).

### Validation (Python)

```python
import json
import jsonschema

# Load schema
with open('docs/schemas/analysis.schema.json') as f:
    schema = json.load(f)

# Load artifact
with open('capture_20250325T120000Z/analysis.json') as f:
    data = json.load(f)

# Validate
jsonschema.validate(instance=data, schema=schema)
```

### Validation (Command Line)

Using `ajv-cli`:

```bash
npm install -g ajv-cli
ajv validate -s docs/schemas/analysis.schema.json -d capture_*/analysis.json
```

## Dynamic Constraints

Some constraints cannot be fully expressed in JSON Schema:

- `rms` array length must equal `channels` value
- `clipped` array length must equal `channels` value
- Channel indices in `channels.json` must match WAV file channel order
- Microphone IDs in `geometry.json` must match IDs in `channels.json`

These constraints are enforced by the storage layer and can be validated with custom Python validators if needed.

## Schema Versioning

- Schema version is tracked in `metadata.json` via the `schema_version` field
- Changes to schemas MUST be additive (no field removal or repurposing)
- Breaking changes require a new major version
- Current version: **0.1.0**
