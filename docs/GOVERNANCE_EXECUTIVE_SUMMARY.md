# Governance Executive Summary: luthiers-toolbox ↔ sg-spec

> **Version**: 1.2.0
> **Created**: 2026-01-12
> **Authors**: Development Team
> **Status**: Active

---

## Table of Contents

1. [Purpose and Rationale](#1-purpose-and-rationale)
2. [Repository Relationship](#2-repository-relationship)
3. [Contract Schema Registry](#3-contract-schema-registry)
   - 3.1 [Public Contracts](#31-public-contracts-cross-repo)
   - 3.2 [Internal Contracts](#32-internal-contracts-luthiers-toolbox-only)
   - 3.3 [Contract Files Structure](#33-contract-files-structure)
   - 3.4 [Telemetry Schema Field Reference](#34-telemetry-schema-field-reference)
   - 3.5 [Safe Export Schema Field Reference](#35-safe-export-schema-field-reference)
4. [Governance Mechanisms](#4-governance-mechanisms)
5. [CI/CD Gates and Workflows](#5-cicd-gates-and-workflows)
6. [Key Code References](#6-key-code-references)
7. [Immutability and Versioning Rules](#7-immutability-and-versioning-rules)
8. [Future Development Guidance](#8-future-development-guidance)

---

## 1. Purpose and Rationale

### Why Governance?

The governance effort between `luthiers-toolbox` and `sg-spec` exists to solve several critical challenges:

#### 1.1 Separation of Concerns

**Problem**: The Luthier's ToolBox is a comprehensive manufacturing and CAM system. The Smart Guitar is a connected instrument product. Without clear boundaries, manufacturing secrets (G-code, toolpaths, RMOS decisions) could leak into consumer-facing products.

**Solution**: Explicit contract schemas define what data CAN and CANNOT cross repository boundaries.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        luthiers-toolbox                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ CAM Engine   │  │ RMOS (Runs)  │  │ Manufacturing│   PROTECTED  │
│  │ G-code       │  │ Decisions    │  │ Toolpaths    │   BOUNDARY   │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                            │                                        │
│                    ┌───────▼───────┐                               │
│                    │   Contracts   │◄─── SHA256 checksums          │
│                    │   (schemas)   │◄─── Immutability gates        │
│                    └───────┬───────┘                               │
└────────────────────────────┼────────────────────────────────────────┘
                             │
            ════════════════════════════════ GOVERNANCE BOUNDARY
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                    ┌───────▼───────┐                               │
│                    │   Contracts   │◄─── Mirrored schemas          │
│                    │   (schemas)   │◄─── SHA256 parity checks      │
│                    └───────┬───────┘                               │
│                            │                        sg-spec        │
│  ┌──────────────┐  ┌───────▼──────┐  ┌──────────────┐              │
│  │ Smart Guitar │  │ Safe Exports │  │ Telemetry    │   CONSUMER   │
│  │ Spec         │  │ (education)  │  │ (hardware)   │   SAFE       │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

#### 1.2 Data Privacy and Security

The telemetry contract (`smart_guitar_toolbox_telemetry_v1`) explicitly **BLOCKS** user/pedagogy fields from crossing the boundary:

```json
// From: contracts/smart_guitar_toolbox_telemetry_v1.schema.json (lines 162-180)
"allOf": [
  {
    "$comment": "Hard-block forbidden user/pedagogy fields if they appear at top-level.",
    "not": {
      "anyOf": [
        { "required": ["player_id"] },
        { "required": ["account_id"] },
        { "required": ["lesson_id"] },
        { "required": ["curriculum_id"] },
        { "required": ["practice_session_id"] },
        { "required": ["skill_level"] },
        { "required": ["accuracy"] },
        { "required": ["timing"] },
        { "required": ["midi"] },
        { "required": ["audio"] },
        { "required": ["recording_url"] },
        { "required": ["coach_feedback"] },
        { "required": ["prompt_trace"] }
      ]
    }
  }
]
```

This ensures manufacturing telemetry (hardware performance, utilization) flows back WITHOUT user practice data.

#### 1.3 Manufacturing IP Protection

The safe export contract (`toolbox_smart_guitar_safe_export_v1`) enforces content policies:

```json
// From: contracts/toolbox_smart_guitar_safe_export_v1.schema.json (lines 51-62)
"content_policy": {
  "type": "object",
  "additionalProperties": false,
  "required": ["no_manufacturing", "no_toolpaths", "no_rmos_authority", "no_secrets"],
  "properties": {
    "no_manufacturing": { "type": "boolean", "const": true },
    "no_toolpaths": { "type": "boolean", "const": true },
    "no_rmos_authority": { "type": "boolean", "const": true },
    "no_secrets": { "type": "boolean", "const": true },
    "notes": { "type": "string" }
  }
}
```

These `const: true` constraints mean exports MUST assert they contain no protected content.

---

## 2. Repository Relationship

### 2.1 Ownership Boundaries

| Domain | Owner | Description |
|--------|-------|-------------|
| **Interface Contracts** | `sg-spec` | Defines data structures, capability flags |
| **Manufacturing Logic** | `luthiers-toolbox` | CAM, G-code, RMOS, toolpaths |
| **Interpretation Logic** | `luthiers-toolbox` | Field coupling, policy generation |
| **Runtime/Firmware** | Downstream (Smart Guitar) | Consumer device implementation |

### 2.2 Dependency Direction

```
sg-spec (pip installable)
    │
    └──► luthiers-toolbox (depends on sg-spec)
              │
              └──► Configured via SG_SPEC_TOKEN secret
```

The `luthiers-toolbox` repository installs `sg-spec` as a Python dependency. This is configured in 21 CI workflows via:

```yaml
# From: .github/workflows/*.yml
- name: Configure git for private repos
  run: |
    git config --global url."https://${{ secrets.SG_SPEC_TOKEN }}@github.com/".insteadOf "https://github.com/"
```

### 2.3 ADR-001: Fields and Policy Ownership

The architectural decision record (`docs/adr/ADR-001-fields-and-policy-ownership.md`) establishes:

> **ToolBox owns all interpretation, coupling, and policy generation.**

Key ownership:
- **Field Modules** (`services/api/app/fields/`) - grain_field, brace_graph, thickness_map
- **CAM Policy** (`services/api/app/cam/policy/`) - per-region constraints
- **QA Core** (`contracts/qa_core.schema.json`) - mesh healing, compliance scores
- **Coupling Logic** - the novel combination of grain + brace + thickness → policy caps

---

## 3. Contract Schema Registry

### 3.1 Public Contracts (Cross-Repo)

| Contract | Purpose | Location |
|----------|---------|----------|
| `smart_guitar_toolbox_telemetry_v1` | Hardware telemetry from Smart Guitar → ToolBox | Both repos |
| `toolbox_smart_guitar_safe_export_v1` | Safe educational exports ToolBox → Smart Guitar | Both repos |
| `viewer_pack_v1` | Measurement-only viewer bundles (from tap_tone_pi) | Both repos |

### 3.2 Internal Contracts (luthiers-toolbox only)

| Contract | Purpose |
|----------|---------|
| `cam_policy` | CAM manufacturing constraints (non-versioned) |
| `qa_core` | Quality assessment coupling fields |

### 3.3 Contract Files Structure

```
luthiers-toolbox/contracts/
├── CONTRACTS_VERSION.json          # Governance sentinel
├── CHANGELOG.md                    # Required change documentation
├── smart_guitar_toolbox_telemetry_v1.schema.json
├── smart_guitar_toolbox_telemetry_v1.schema.sha256
├── toolbox_smart_guitar_safe_export_v1.schema.json
├── toolbox_smart_guitar_safe_export_v1.schema.sha256
├── viewer_pack_v1.schema.json
├── viewer_pack_v1.schema.sha256
├── cam_policy.schema.json
├── cam_policy.schema.sha256
├── qa_core.schema.json
├── qa_core.schema.sha256
└── fixtures/                       # Test fixtures for validation
    ├── telemetry_valid_hardware_performance.json
    ├── telemetry_invalid_pedagogy_leak.json
    └── telemetry_invalid_metric_key_smuggle.json
```

```
sg-spec/contracts/
├── CONTRACTS_VERSION.json          # Mirror of governance sentinel
├── CHANGELOG.md                    # Mirror of changelog
├── schemas/                        # Pydantic models
│   ├── __init__.py
│   ├── smart_guitar.py
│   └── sandbox_schemas.py
├── typescript/                     # Generated TypeScript types
│   └── smartGuitar.ts
├── smart_guitar_toolbox_telemetry_v1.schema.json
├── smart_guitar_toolbox_telemetry_v1.schema.sha256
├── toolbox_smart_guitar_safe_export_v1.schema.json
├── toolbox_smart_guitar_safe_export_v1.schema.sha256
├── viewer_pack_v1.schema.json
├── viewer_pack_v1.schema.sha256
├── cam_policy.schema.json
├── cam_policy.schema.sha256
├── qa_core.schema.json
└── qa_core.schema.sha256
```

### 3.4 Telemetry Schema Field Reference

**Schema**: `smart_guitar_toolbox_telemetry_v1.schema.json`

#### Required Fields (7)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `schema_id` | string | `const: "smart_guitar_toolbox_telemetry"` | Fixed identifier |
| `schema_version` | string | `const: "v1"` | Fixed version |
| `emitted_at_utc` | string | `format: date-time` | UTC timestamp when payload was emitted |
| `instrument_id` | string | 6-128 chars, pattern: `^[A-Za-z0-9][A-Za-z0-9._:-]{4,126}[A-Za-z0-9]$` | Smart Guitar physical unit identifier (non-player) |
| `manufacturing_batch_id` | string | 4-128 chars, pattern: `^[A-Za-z0-9][A-Za-z0-9._:-]{2,126}[A-Za-z0-9]$` | ToolBox manufacturing batch/build identifier |
| `telemetry_category` | string | enum: `utilization`, `hardware_performance`, `environment`, `lifecycle` | High-level category for manufacturing intelligence |
| `metrics` | object | min 1 property, pattern keys: `^[a-z][a-z0-9_]{1,63}$` | Map of metric_name → metric data |

#### Optional Fields (3)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `design_revision_id` | string | 1-128 chars | Design revision identifier (manufacturing correlation only) |
| `hardware_sku` | string | 1-128 chars | Hardware SKU (manufacturing correlation only) |
| `component_lot_id` | string | 1-128 chars | Component lot identifier (manufacturing correlation only) |

#### Metrics Object Structure

Each metric key must match pattern `^[a-z][a-z0-9_]{1,63}$` and contains:

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `value` | number | **Yes** | Range: ±1.0e308 |
| `unit` | string | **Yes** | enum: `count`, `hours`, `seconds`, `milliseconds`, `ratio`, `percent`, `celsius`, `fahrenheit`, `volts`, `amps`, `ohms`, `db`, `hz`, `bytes` |
| `aggregation` | string | **Yes** | enum: `sum`, `avg`, `max`, `min`, `bucket` |
| `bucket_label` | string | Only if `aggregation=bucket` | 1-64 chars, human-readable bucket name |

#### Blocked Fields (13) - Privacy Boundary

These fields are **explicitly forbidden** at the top level to protect user privacy:

| Blocked Field | Category | Reason |
|---------------|----------|--------|
| `player_id` | Identity | User identity |
| `account_id` | Identity | User identity |
| `lesson_id` | Pedagogy | Learning content |
| `curriculum_id` | Pedagogy | Learning content |
| `practice_session_id` | Pedagogy | Learning content |
| `skill_level` | Performance | User performance |
| `accuracy` | Performance | User performance |
| `timing` | Performance | User performance |
| `midi` | Content | User content |
| `audio` | Content | User content |
| `recording_url` | Content | User content |
| `coach_feedback` | AI | AI/coaching data |
| `prompt_trace` | AI | AI/coaching data |

#### Example Valid Telemetry Payload

```json
{
  "schema_id": "smart_guitar_toolbox_telemetry",
  "schema_version": "v1",
  "emitted_at_utc": "2026-01-12T23:45:00Z",
  "instrument_id": "SG-2026-001234",
  "manufacturing_batch_id": "BATCH-2026-Q1-042",
  "telemetry_category": "hardware_performance",
  "metrics": {
    "battery_voltage": { "value": 3.72, "unit": "volts", "aggregation": "avg" },
    "cpu_temp": { "value": 42.5, "unit": "celsius", "aggregation": "max" },
    "uptime_hours": { "value": 156.3, "unit": "hours", "aggregation": "sum" }
  }
}
```

### 3.5 Safe Export Schema Field Reference

**Schema**: `toolbox_smart_guitar_safe_export_v1.schema.json`

#### Top-Level Required Fields (9)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `schema_id` | string | `const: "toolbox_smart_guitar_safe_export"` | Fixed identifier |
| `schema_version` | string | `const: "v1"` | Fixed version |
| `created_at_utc` | string | - | UTC timestamp |
| `export_id` | string | - | Stable id (uuid or content-derived) |
| `producer` | object | see below | Origin system info |
| `scope` | object | see below | Usage domain and consumers |
| `content_policy` | object | see below | **Manufacturing boundary assertions** |
| `files` | array | see below | File manifest |
| `bundle_sha256` | string | - | SHA256 of manifest (before this field added) |

#### `producer` Object

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `system` | string | **Yes** | `const: "luthiers-toolbox"` |
| `repo` | string | **Yes** | Repository URL |
| `commit` | string | **Yes** | Git commit SHA |
| `build_id` | string | No | CI build identifier |

#### `scope` Object

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `domain` | string | **Yes** | enum: `education`, `practice`, `coaching`, `reference` |
| `safe_for` | string | **Yes** | `const: "smart_guitar"` |
| `intended_consumers` | array | No | enum items: `smart_guitar_app`, `smart_guitar_coach`, `smart_guitar_firmware_tools` |

#### `content_policy` Object - **THE GOVERNANCE BOUNDARY**

| Field | Type | Required | Constraints | Purpose |
|-------|------|----------|-------------|---------|
| `no_manufacturing` | boolean | **Yes** | `const: true` | **Blocks G-code, CAM data** |
| `no_toolpaths` | boolean | **Yes** | `const: true` | **Blocks DXF, toolpath files** |
| `no_rmos_authority` | boolean | **Yes** | `const: true` | **Blocks run IDs, decisions** |
| `no_secrets` | boolean | **Yes** | `const: true` | **Blocks API keys, tokens** |
| `notes` | string | No | - | Optional explanation |

> **Key Insight**: All four policy fields are `const: true` - the schema REJECTS any export that doesn't explicitly assert these boundaries.

#### `index` Object (Optional)

| Field | Type | Default |
|-------|------|---------|
| `topics_relpath` | string | `"index/topics.json"` |
| `lessons_relpath` | string | `"index/lessons.json"` |
| `drills_relpath` | string | `"index/drills.json"` |

#### `files` Array Items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `relpath` | string | **Yes** | Relative path inside bundle |
| `sha256` | string | **Yes** | File content hash |
| `bytes` | integer | **Yes** | File size |
| `mime` | string | **Yes** | MIME type |
| `kind` | string | **Yes** | enum: `manifest`, `topic_index`, `lesson_index`, `drill_index`, `lesson_md`, `lesson_json`, `reference_md`, `reference_json`, `audio_wav`, `audio_flac`, `image_png`, `image_jpg`, `chart_csv`, `provenance`, `unknown` |

#### Governance Comparison: What CAN vs CANNOT Cross

| ✅ **Allowed in Safe Export** | ❌ **Blocked by content_policy** |
|------------------------------|----------------------------------|
| Lesson markdown | G-code files |
| Reference JSON | DXF toolpaths |
| Audio samples (WAV/FLAC) | RMOS run artifacts |
| Images (PNG/JPG) | Decision records |
| Chart data (CSV) | API keys/tokens |
| Topic/drill indexes | Manufacturing parameters |
| Provenance metadata | CAM policy constraints |

#### Example Valid Safe Export Manifest

```json
{
  "schema_id": "toolbox_smart_guitar_safe_export",
  "schema_version": "v1",
  "created_at_utc": "2026-01-12T23:50:00Z",
  "export_id": "export-2026-01-12-abc123",
  "producer": {
    "system": "luthiers-toolbox",
    "repo": "https://github.com/HanzoRazer/luthiers-toolbox",
    "commit": "c36c852",
    "build_id": "ci-build-4521"
  },
  "scope": {
    "domain": "education",
    "safe_for": "smart_guitar",
    "intended_consumers": ["smart_guitar_app", "smart_guitar_coach"]
  },
  "content_policy": {
    "no_manufacturing": true,
    "no_toolpaths": true,
    "no_rmos_authority": true,
    "no_secrets": true,
    "notes": "Educational content only - fretboard theory lessons"
  },
  "files": [
    { "relpath": "index/topics.json", "sha256": "a1b2c3...", "bytes": 1024, "mime": "application/json", "kind": "topic_index" },
    { "relpath": "lessons/scales-101.md", "sha256": "f6e5d4...", "bytes": 4096, "mime": "text/markdown", "kind": "lesson_md" }
  ],
  "bundle_sha256": "9f8e7d6c5b4a3210..."
}
```

---

## 4. Governance Mechanisms

### 4.1 SHA256 Checksum Verification

Every schema has a corresponding `.sha256` file containing 64 lowercase hex characters:

```
# Example: contracts/smart_guitar_toolbox_telemetry_v1.schema.sha256
a1b2c3d4e5f6...  (64 hex chars)
```

CI gates verify: `sha256sum schema.json == schema.sha256`

### 4.2 CONTRACTS_VERSION.json Sentinel

```json
// From: contracts/CONTRACTS_VERSION.json
{
  "public_released": false,
  "tag": ""
}
```

**When `public_released: true`:**
- All `*_v1.schema.json` files become **IMMUTABLE**
- All `*_v1.schema.sha256` files become **IMMUTABLE**
- Breaking changes require new `*_v2` versions

### 4.3 CHANGELOG.md Requirement

From `contracts/CHANGELOG.md`:

> **Changelog requirement**: Any schema or hash change requires updating this CHANGELOG.md with a mention of the contract stem.

---

## 5. CI/CD Gates and Workflows

### 5.1 Governance-Specific Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| **Smart Guitar Export Gate** | `smart_guitar_export_gate.yml` | Validates export boundary (no manufacturing, no toolpaths) |
| **Run Artifact Contract Gate** | `run_artifact_contract_gate.yml` | Validates RMOS artifact linkage invariants |
| **Artifact Linkage Gate** | `artifact_linkage_gate.yml` | Validates parent/child relationships in runs |
| **Routing Truth Gate** | `routing_truth.yml` | Validates endpoint documentation accuracy |
| **Legacy Endpoint Usage Gate** | `legacy_endpoint_usage_gate.yml` | Tracks deprecated endpoint usage |

### 5.2 Smart Guitar Export Gate Details

```yaml
# From: .github/workflows/smart_guitar_export_gate.yml (lines 40-56)
- name: Validate JSON Schema is valid
  run: |
    python -c "
    import json
    with open('contracts/toolbox_smart_guitar_safe_export_v1.schema.json') as f:
        schema = json.load(f)
    assert schema.get('\$schema'), 'Missing \$schema'
    assert schema.get('title'), 'Missing title'
    print('✓ Schema is valid JSON')
    "

- name: Run export gate tests
  working-directory: services/api
  env:
    PYTHONPATH: .
  run: |
    python -m pytest tests/test_smart_guitar_export_gate.py -v --tb=short
```

### 5.3 Artifact Linkage Invariants

The governance script validates parent linkage:

```python
# From: scripts/governance/check_artifact_linkage_invariants.py (conceptual)
# Validates:
#   - plan.parent == spec
#   - decision.parent == plan
#   - execution.parent == decision
```

### 5.4 Workflows Using SG_SPEC_TOKEN

21 workflows require the `SG_SPEC_TOKEN` secret for private repo access:

1. `adaptive_pocket.yml`
2. `api_dxf_tests.yml`
3. `api_health_and_smoke.yml`
4. `api_health_check.yml`
5. `api_tests.yml`
6. `artifact_linkage_gate.yml`
7. `blueprint_phase3.yml`
8. `cam_essentials.yml`
9. `comparelab-golden.yml`
10. `containers.yml`
11. `core_ci.yml`
12. `geometry_parity.yml`
13. `helical_badges.yml`
14. `proxy_adaptive.yml`
15. `proxy_parity.yml`
16. `rmos_ci.yml`
17. `rmos_migration.yml`
18. `routing_truth.yml`
19. `run_artifact_contract_gate.yml`
20. `sdk_codegen.yml`
21. `server-env-check.yml`

---

## 6. Key Code References

### 6.1 Governance Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `check_legacy_endpoint_usage.py` | `scripts/governance/` | Scans for deprecated endpoint usage |
| `check_artifact_linkage_invariants.py` | `scripts/governance/` | Validates RMOS run linkage |
| `validate_run_artifact_contract.py` | `scripts/governance/` | Validates artifact metadata |
| `check_routing_truth.py` | `scripts/governance/` | Validates endpoint documentation |

### 6.2 CI Gate Scripts (`scripts/ci/`)

| Script | Purpose |
|--------|---------|
| `check_art_studio_scope.py` | Art Studio boundary enforcement |
| `check_cbsp21_gate.py` | CBSP21 gate checks |
| `check_cbsp21_patch_input.py` | CBSP21 patch validation |
| `check_contracts_governance.py` | **Contracts governance gate (Scenario B)** |
| `check_workflow_api_base.py` | Workflow API base URL checks |
| `check_workflow_api_paths.py` | Workflow API path validation |

### 6.3 Contracts Governance Gate Entrypoints

The `check_contracts_governance.py` script enforces three invariants:

```python
# Main gate checks (3 functions):
check_sha256_format(repo_root)                          # SHA256 = 64 lowercase hex
check_changelog_required(repo_root, changed, base_ref)  # Require CHANGELOG update
check_v1_immutability(repo_root, changed)               # Block v1 schema edits if public_released=true
```

**CLI Usage:**
```bash
python scripts/ci/check_contracts_governance.py --repo-root . --base-ref origin/main
```

**Exit codes:** `0` pass, `1` violations, `2` execution error

### 6.4 Governance Gate Workflow Locations

Both repositories run the contracts governance gate:

| Repo | Workflow | Job | Gate Name |
|------|----------|-----|-----------|
| `luthiers-toolbox` | `.github/workflows/core_ci.yml` | `api-tests` | `CONTRACTS_GOVERNANCE_SCENARIO_B_GATE` |
| `sg-spec` | `.github/workflows/ci.yml` | `contracts-governance` | `CONTRACTS_GOVERNANCE_SCENARIO_B_GATE` |

**luthiers-toolbox** (`core_ci.yml` lines 35-37):
```yaml
- name: CONTRACTS_GOVERNANCE_SCENARIO_B_GATE
  run: |
    python scripts/ci/check_contracts_governance.py --base-ref origin/main
```

**sg-spec** (`ci.yml` lines 19-21):
```yaml
- name: CONTRACTS_GOVERNANCE_SCENARIO_B_GATE
  run: |
    python scripts/ci/check_contracts_governance.py --repo-root . --base-ref origin/main
```

### 6.5 Contract Fixtures

Test fixtures ensure schema validation catches violations:

```
contracts/fixtures/
├── telemetry_valid_hardware_performance.json    # Should PASS validation
├── telemetry_invalid_pedagogy_leak.json         # Should FAIL (blocked fields)
└── telemetry_invalid_metric_key_smuggle.json    # Should FAIL (invalid keys)
```

### 6.6 Endpoint Truth File

```
services/api/app/data/endpoint_truth.json
```

This file defines the canonical state of all API endpoints for routing truth validation.

---

## 7. Immutability and Versioning Rules

### 7.1 Pre-Release (Current State)

```json
{ "public_released": false, "tag": "" }
```

- Schemas CAN be modified
- SHA256 hashes MUST be updated when schemas change
- CHANGELOG.md MUST be updated

### 7.2 Post-Release (Future State)

```json
{ "public_released": true, "tag": "v1.0.0" }
```

- `*_v1.schema.json` files are **FROZEN**
- `*_v1.schema.sha256` files are **FROZEN**
- New features require `*_v2` schemas
- Additive changes (new optional fields) MAY be allowed with governance approval

### 7.3 SHA256 Format Requirements

From `contracts/CHANGELOG.md`:

> **SHA256 format**: All `.schema.sha256` files must contain exactly one line of 64 lowercase hex characters.

---

## 8. Future Development Guidance

### 8.1 Adding a New Contract

1. Create `contracts/new_contract_v1.schema.json` with:
   - `$schema` pointing to JSON Schema draft
   - `$id` with canonical URL
   - `title` with descriptive name

2. Generate SHA256 hash:
   ```bash
   sha256sum contracts/new_contract_v1.schema.json | cut -d' ' -f1 > contracts/new_contract_v1.schema.sha256
   ```

3. Update `contracts/CHANGELOG.md` with new contract entry

4. Mirror to `sg-spec/contracts/` if cross-repo

5. Add CI gate workflow if boundary enforcement needed

### 8.2 Modifying an Existing Contract

**Pre-Release:**
1. Edit the schema
2. Regenerate SHA256 hash
3. Update CHANGELOG.md
4. Mirror changes to sg-spec

**Post-Release:**
1. Create new `*_v2` version
2. Deprecate but preserve `*_v1`
3. Update consumers with migration path

### 8.3 Adding a New Governance Gate

1. Create workflow in `.github/workflows/`
2. Add script in `scripts/governance/`
3. Document in `scripts/governance/README.md`
4. Ensure `SG_SPEC_TOKEN` access if needed

### 8.4 Debugging Governance Failures

```bash
# Run locally with verbose output
CONTRACT_VERBOSE=true python scripts/governance/validate_run_artifact_contract.py

# Check specific session
CONTRACT_SESSION_ID=sess123 python scripts/governance/check_artifact_linkage_invariants.py

# Legacy endpoint check with zero budget
LEGACY_USAGE_BUDGET=0 python scripts/governance/check_legacy_endpoint_usage.py
```

---

## Appendix A: Quick Reference

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CONTRACT_API_URL` | `http://127.0.0.1:8000` | API endpoint for live validation |
| `CONTRACT_LIMIT` | `200` | Max artifacts to validate |
| `CONTRACT_FAIL_FAST` | `false` | Stop on first failure |
| `CONTRACT_VERBOSE` | `false` | Enable verbose output |
| `LEGACY_USAGE_BUDGET` | `10` | Allowed deprecated endpoint usages |

### Key Files Checklist

- [ ] `contracts/CONTRACTS_VERSION.json` - Governance sentinel
- [ ] `contracts/CHANGELOG.md` - Change documentation
- [ ] `contracts/*.schema.json` - Schema definitions
- [ ] `contracts/*.schema.sha256` - Checksum files
- [ ] `scripts/governance/README.md` - Gate documentation
- [ ] `.github/workflows/*_gate.yml` - CI enforcement

---

## Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-12 | 1.0.0 | Development Team | Initial creation |
| 2026-01-12 | 1.1.0 | Development Team | Added detailed schema field tables (sections 3.4, 3.5) |
| 2026-01-13 | 1.2.0 | Development Team | Added CI gate scripts, governance entrypoints, workflow locations (sections 6.2-6.4) |

---

*This document should be updated whenever governance mechanisms are added or modified.*
