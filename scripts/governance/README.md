# Governance Scripts

## Unified Governance Runner

**Canonical entry point for CI and local governance checks.**

### Local Usage

```bash
# Run CI-tier checks in blocking mode (default)
python scripts/governance/check_all.py

# Run precommit-tier checks only (fast)
python scripts/governance/check_all.py --tier precommit

# Run with policy file and JSON output
python scripts/governance/check_all.py \
  --tier ci \
  --mode block \
  --policy docs/governance/ontology/ontology_ci_policy.json \
  --json-output reports/governance/check_all_ci.json

# Strict policy enforcement (fail on missing active scripts)
python scripts/governance/check_all.py \
  --tier ci \
  --mode block \
  --policy docs/governance/ontology/ontology_ci_policy.json \
  --strict-policy \
  --fail-on-missing-active-script

# List available checks
python scripts/governance/check_all.py --list
```

### Enforcement Tiers

| Tier | Purpose | Typical Duration |
|------|---------|------------------|
| precommit | Fast checks for pre-commit hooks | <10s |
| ci | Standard CI checks | <60s |
| nightly | Heavy checks requiring full app init | >60s |
| manual | Explicit invocation only | varies |

### Blocking vs Warning

- **Blocking** checks: CI fails if check fails (exit code 1)
- **Warning** checks: CI reports but does not fail (exit code 0)

Governance is CI-enforced only for checks marked blocking.
Runtime governance remains observational unless otherwise documented.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks pass (or warn mode) |
| 1 | Blocking check(s) failed |
| 2 | Policy error (missing active scripts, invalid policy) |

---

## Legacy Endpoint Usage Gate

Script:
- `scripts/governance/check_legacy_endpoint_usage.py`

What it does:
- Reads deprecated endpoints from `services/api/app/data/endpoint_truth.json`
- Scans repo source trees (client/sdk/api) for direct string usages
- Fails if usage exceeds `LEGACY_USAGE_BUDGET` (default 10)

Run locally:

```bash
python scripts/governance/check_legacy_endpoint_usage.py
```

Tune:
- `LEGACY_USAGE_BUDGET=0` to require **zero** legacy usage
- `LEGACY_SCAN_PATHS=packages/client/src,packages/sdk` to narrow scope
- `LEGACY_IGNORE_GLOBS=**/generated/**,**/fixtures/**` to silence known safe areas

---

## Artifact Linkage Invariants Gate (OPERATION lane)

Script:
- `scripts/governance/check_artifact_linkage_invariants.py`

What it does:
- Creates a minimal Saw batch flow via HTTP:
  - spec → plan → approve → toolpaths → job-log
- Queries `/api/rmos/runs?session_id=...&batch_label=...`
- Validates:
  - required `index_meta`: `tool_kind`, `batch_label`, `session_id`
  - parent linkage invariants:
    - plan.parent == spec
    - decision.parent == plan
    - execution.parent == decision

Run locally (API must be running on 127.0.0.1:8000):

```bash
python scripts/governance/check_artifact_linkage_invariants.py
```

---

## RunArtifact Contract Validator

Script:
- `scripts/governance/validate_run_artifact_contract.py`

What it does:
- Fetches artifacts from GET /api/rmos/runs
- Validates required index_meta keys:
  - tool_kind, batch_label, session_id
- Validates parent linkage invariants based on artifact kind:
  - plans link to spec
  - decisions link to plan
  - executions/toolpaths link to decision

Examples:

Validate latest N artifacts:
```bash
CONTRACT_LIMIT=200 python scripts/governance/validate_run_artifact_contract.py
```

Validate a specific session/batch:
```bash
CONTRACT_SESSION_ID=sess123 CONTRACT_BATCH_LABEL=mybatch python scripts/governance/validate_run_artifact_contract.py
```

---

## Semantic sandbox import gate (Phase 0.5)

Script:
- `scripts/governance/check_semantic_sandbox_imports.py`

Blocks production `services/` imports of Tier A cognition/grid modules (`cognitive_extract*`, `extract_body_grid*`) until they are re-homed to [vectorizer-sandbox](https://github.com/HanzoRazer/vectorizer-sandbox). Enforced in **precommit** tier via `check_all.py`.

```bash
python scripts/governance/check_semantic_sandbox_imports.py
```

See `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md` (Phase 0.5).

---

## Vectorizer audit ground-truth

PowerShell (from repo root):

```powershell
.\scripts\governance\verify_vectorizer_audit.ps1
```

Also runs `check_semantic_sandbox_imports.py` as check 2. Results written to `verify_vectorizer_audit_results.txt` when the script completes.

Lifecycle registry: `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md`
