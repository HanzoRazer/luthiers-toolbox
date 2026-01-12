# Governance Executive Summary: luthiers-toolbox ↔ sg-spec

> **Version**: 1.0.0
> **Created**: 2026-01-12
> **Authors**: Development Team
> **Status**: Active

---

## Table of Contents

1. [Purpose and Rationale](#1-purpose-and-rationale)
2. [Repository Relationship](#2-repository-relationship)
3. [Contract Schema Registry](#3-contract-schema-registry)
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

### 6.2 Contract Fixtures

Test fixtures ensure schema validation catches violations:

```
contracts/fixtures/
├── telemetry_valid_hardware_performance.json    # Should PASS validation
├── telemetry_invalid_pedagogy_leak.json         # Should FAIL (blocked fields)
└── telemetry_invalid_metric_key_smuggle.json    # Should FAIL (invalid keys)
```

### 6.3 Endpoint Truth File

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

---

*This document should be updated whenever governance mechanisms are added or modified.*
