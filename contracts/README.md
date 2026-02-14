# API Contracts

Single source of truth for frontend-backend API integration.

## Purpose

Prevents deployment issues caused by:
- Frontend calling endpoints that don't exist
- Frontend using wrong endpoint paths
- Backend removing endpoints still used by frontend
- Router registration gaps (endpoint code exists but not loaded)

## Files

- `api_endpoints.json` - List of all API endpoints and their metadata
- `README.md` - This file

## Scripts

### Validate Contracts
```bash
python scripts/validate_api_contracts.py
```

Scans frontend for `fetch('/api/...')` calls and checks each one exists in the contract.

### Generate Contract (from backend)
```bash
cd services/api
python ../../scripts/generate_api_contract.py
```

Extracts all registered endpoints from FastAPI and generates `api_endpoints.json`.

## CI Integration

The `api_contract_check.yml` workflow runs on:
- Pull requests touching frontend or backend code
- Pushes to main

It fails if frontend calls endpoints not defined in the contract.

## Adding New Endpoints

1. Create the endpoint in backend
2. Register in `router_registry/manifest.py`
3. Add to `contracts/api_endpoints.json`
4. Use in frontend

## Fixing Contract Violations

When CI fails with "No matching endpoint for X":

1. **Endpoint exists but not in contract** → Add it to `api_endpoints.json`
2. **Endpoint doesn't exist** → Create it in backend OR fix frontend path
3. **Wrong path** → Fix frontend to use correct path (check `/docs` for actual paths)
