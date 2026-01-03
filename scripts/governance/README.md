# Governance Scripts

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
