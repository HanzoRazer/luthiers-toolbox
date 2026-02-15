# Deployment Validation Harness

This document describes the deployment validation system that catches common deployment issues before they reach production.

## Overview

The validation harness systematically checks for five categories of deployment issues:

| Category | What it checks | Example issue |
|----------|----------------|---------------|
| **Dependencies** | Python imports vs requirements.txt | `openai` package imported but not in requirements |
| **Docker directories** | ENV vars have corresponding mkdir | `RMOS_RUN_ATTACHMENTS_DIR` set but directory not created |
| **Docker env vars** | Required ENV vars present | Missing `RMOS_RUNS_DIR` definition |
| **Cross-origin URLs** | Frontend URL resolution | Relative URL `/api/...` used without `VITE_API_BASE` prefix |
| **Field mapping** | API response field names | Backend returns `configured`, frontend expects `available` |

## Quick Start

### Shell Script (Fast)
```bash
./scripts/ci/check_deployment_ready.sh
```

### Python Script (Comprehensive)
```bash
python scripts/ci/validate_deployment.py --verbose
```

### CI Integration
The `deployment_validation.yml` workflow runs automatically on:
- Push to main (deployment-related files)
- Pull requests to main
- Manual trigger via workflow_dispatch

## Common Issues and Fixes

### 1. Missing Python Dependency

**Error:**
```
✗ [dependencies] Package 'openai' is imported but not in requirements.txt
  Location: app/vision/router.py:15
```

**Fix:**
```bash
echo "openai>=1.0.0" >> services/api/requirements.txt
```

### 2. Missing Docker Directory

**Error:**
```
✗ [docker] ENV RMOS_RUN_ATTACHMENTS_DIR=/app/data/attachments but directory not created by mkdir
```

**Fix in Dockerfile:**
```dockerfile
RUN mkdir -p /app/data/attachments && chown -R app:app /app/data
ENV RMOS_RUN_ATTACHMENTS_DIR=/app/data/attachments
```

### 3. Cross-Origin URL Issue

**Error:**
```
⚠ [cross-origin] Possible relative URL in :src binding
  Location: VisionAttachToRunWidget.vue:438
```

**Fix:**
```vue
<script setup>
const API_BASE = (import.meta as any).env?.VITE_API_BASE || '';

function resolveAssetUrl(url: string): string {
  if (!url) return '/placeholder.svg';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return `${API_BASE}${url}`;
}
</script>

<template>
  <img :src="resolveAssetUrl(asset.url)" />
</template>
```

### 4. Field Mapping Mismatch

**Error:**
```
⚠ [field-mapping] Potential field mapping issue: 'configured' used without fallback
  Location: api.ts:238
```

**Fix:**
```typescript
// Before (broken when API field name differs)
available: p.available,

// After (with fallback)
available: p.available ?? p.configured ?? false,
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | Warnings found (non-blocking) |
| 2 | Errors found (blocking) |

## Architecture

```
scripts/ci/
├── validate_deployment.py   # Comprehensive Python checker
├── check_deployment_ready.sh  # Quick shell script
└── ...

.github/workflows/
└── deployment_validation.yml  # CI integration
```

## Adding New Checks

### Python Checker
Add a new function in `validate_deployment.py`:

```python
def check_my_new_thing(report: ValidationReport, verbose: bool = False):
    """Check for my new issue type."""
    # ... implementation ...
    report.add(ValidationResult(
        category="my-category",
        severity="error",  # or "warning"
        message="Description of the issue",
        file_path=str(file_path),
        fix_hint="How to fix it",
    ))
```

### Shell Checker
Add to `check_deployment_ready.sh`:

```bash
echo "N. Checking my new thing..."
if ! grep -q "expected_pattern" some/file.txt; then
    echo "   ✗ ERROR: Description"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✓ Check passed"
fi
```

## Historical Issues Caught

This harness was created after encountering these deployment issues:

1. **OpenAI provider not in dropdown** - Field mapping: `configured` vs `available`
2. **"openai package not installed"** - Missing pip dependency in requirements.txt
3. **Permission denied: /app/data/run_attachments** - Missing mkdir in Dockerfile
4. **Images not displaying** - Relative URL without API_BASE prefix

Each of these is now automatically detected.
