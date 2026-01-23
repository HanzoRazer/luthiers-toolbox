# Mock RMOS Server (FastAPI)

This is a **frontend-only development server** that simulates RMOS behavior for AI advisories,
without requiring the lab, SQLite ledger, or ai-integrator.

Use this to:
- Develop ToolBox AI UI flows
- Test AIContextPacket generation
- Validate error handling and headers

## What it does
- Accepts POST /ai/advisories/request
- Validates minimal shape of AIContextPacket
- Returns a deterministic mock AdvisoryArtifact
- Emits X-Request-Id header
- Supports forced error modes via request flags

## Run
```bash
pip install fastapi uvicorn
uvicorn mock_rmos.main:app --reload
```

Server runs on http://localhost:8000

## Error simulation
Add to request.request.debug:

```json
{ "force_error": "GOVERNANCE" }
```

Options:
- SCHEMA
- GOVERNANCE
- UNSUPPORTED
- RUNTIME
