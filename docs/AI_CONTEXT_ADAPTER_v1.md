# AI Context Adapter Interface v1 - Implementation Summary

**Implemented:** 2026-01-14  
**Contract:** `contracts/AI_CONTEXT_ADAPTER_INTERFACE_v1.json`

## Overview

The AI Context Adapter provides a **read-only, redaction-first** interface for external AI systems to consume ToolBox context without direct code coupling.

### Design Goals
- **Read-only**: No mutation, no "actions" - GET endpoints only
- **Deterministic**: Same inputs → same snapshot structure
- **Redaction-first**: Secrets and user-private data stripped by default
- **Composable**: Multiple context sources merged into single envelope

## File Structure

```
services/api/app/ai_context/
├── __init__.py              # Package exports
├── schemas.py               # Core data structures & protocols
├── routes.py                # FastAPI read-only endpoints
├── validator.py             # CLI validator + pytest gate
├── redactor/
│   ├── __init__.py
│   └── strict.py            # Strict redaction enforcement
├── providers/
│   ├── __init__.py
│   ├── run_summary.py       # RMOS run summary (no toolpaths)
│   ├── design_intent.py     # Pattern/design intent (no manufacturing)
│   ├── governance_notes.py  # Blocker explanations
│   ├── docs_excerpt.py      # Documentation snippets
│   └── ui_state_hint.py     # UI context hints
└── assembler/
    ├── __init__.py
    └── default.py           # Orchestrates providers + redaction

contracts/
└── AI_CONTEXT_ADAPTER_INTERFACE_v1.json  # JSON Schema

tests/
└── test_ai_context_adapter.py            # Pytest test suite
```

## API Endpoints

All endpoints are **read-only** (GET only).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/context/health` | Health check, lists available providers |
| GET | `/api/ai/context/envelope` | Full context envelope for AI consumption |
| GET | `/api/ai/context/run_summary` | Run summary (status, blockers, counts) |
| GET | `/api/ai/context/design_intent` | Pattern/design intent |
| GET | `/api/ai/context/governance_notes` | Why something is blocked |
| GET | `/api/ai/context/docs_excerpt` | Relevant documentation snippets |

## Context Source Kinds (v1 Vocabulary)

| Kind | Description | Status |
|------|-------------|--------|
| `run_summary` | Run status, candidate counts, blockers | Required |
| `design_intent` | Pattern parameters, visual metadata | Required |
| `governance_notes` | Blocker explanations, suggested actions | Required |
| `docs_excerpt` | Documentation snippets | Required |
| `ui_state_hint` | Current UI context | Required |
| `telemetry_summary` | Manufacturing telemetry summaries | Optional |
| `calc_status` | Calculator completeness flags | Optional |

## Forbidden Categories (Strict Redaction)

The following are **always redacted** in strict mode:

| Category | Description |
|----------|-------------|
| `toolpaths` | Toolpath data, path_data, trajectory |
| `gcode` | G-code, NC code |
| `machine_secrets` | API keys, tokens, credentials |
| `credential_material` | Passwords, private keys |
| `player_pedagogy` | Smart Guitar player/lesson data |
| `personal_data` | Email, phone, SSN, etc. |
| `proprietary_algorithms` | Proprietary algorithm details |
| `raw_telemetry` | Raw telemetry samples |

## Usage Examples

### Get Full Context Envelope

```bash
curl "http://localhost:8000/api/ai/context/envelope?intent=Explain%20why%20export%20is%20blocked&run_id=run_123"
```

### Response Structure

```json
{
  "envelope": {
    "schema_id": "toolbox_ai_context_envelope",
    "schema_version": "v1",
    "created_at_utc": "2026-01-14T10:30:00Z",
    "request": {
      "request_id": "ctxreq_abc123",
      "actor": {"kind": "human", "role": "builder", "auth_context": "toolbox_session"},
      "intent": "Explain why export is blocked",
      "scope": {"run_id": "run_123"}
    },
    "policy": {
      "mode": "read_only",
      "redaction_level": "strict",
      "forbidden_categories": ["toolpaths", "gcode", "machine_secrets", ...]
    },
    "context": {
      "sources": [
        {"source_id": "run_summary_run_123", "kind": "run_summary", ...},
        {"source_id": "governance_export_blocked", "kind": "governance_notes", ...}
      ],
      "attachments": []
    },
    "integrity": {
      "bundle_sha256": "abc123..."
    }
  },
  "warnings": []
}
```

## CLI Validator

```bash
# Validate envelope against schema
python -m app.ai_context.validator --envelope path/to/envelope.json

# Run redaction pipeline tests
python -m app.ai_context.validator --test-redaction

# Schema-only validation
python -m app.ai_context.validator --envelope envelope.json --schema-only
```

## Running Tests

```bash
cd services/api
pytest tests/test_ai_context_adapter.py -v

# With markers
pytest tests/test_ai_context_adapter.py -v -m ai_context
```

## Boundary Compliance

This adapter respects ToolBox architectural boundaries:

1. **External Boundary**: Does not import `tap_tone.*` or `modes.*`
2. **Read-Only**: No mutation endpoints, no artifact creation
3. **Redaction-First**: All forbidden categories stripped before output
4. **Action Filtering**: POST/PUT/DELETE instructions removed from text

## Integration with toolbox-ai

External AI systems consume the envelope without direct imports:

```python
# In toolbox-ai
response = requests.get(
    "http://toolbox/api/ai/context/envelope",
    params={"intent": "...", "run_id": "..."}
)
envelope = response.json()["envelope"]

# AI can now explain blockers without accessing ToolBox internals
```

## See Also

- [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) - Architectural boundaries
- [BOUNDARY_RULES.md](../docs/BOUNDARY_RULES.md) - Import rules
- [contracts/AI_CONTEXT_ADAPTER_INTERFACE_v1.json](../contracts/AI_CONTEXT_ADAPTER_INTERFACE_v1.json) - JSON Schema
