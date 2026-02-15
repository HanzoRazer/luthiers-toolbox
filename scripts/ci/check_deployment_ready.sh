#!/bin/bash
# Quick deployment readiness check
# Run this before deploying to catch common issues
#
# Usage: ./scripts/ci/check_deployment_ready.sh
#
# Exit codes:
#   0 = Ready to deploy
#   1 = Issues found - review output

set -e
cd "$(dirname "$0")/../.."

echo "======================================"
echo "Deployment Readiness Check"
echo "======================================"
echo ""

ERRORS=0

# 1. Check requirements.txt has openai (common miss)
echo "1. Checking critical Python dependencies..."
if ! grep -q "^openai" services/api/requirements.txt; then
    echo "   ✗ ERROR: 'openai' package missing from requirements.txt"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✓ openai package present"
fi

# 2. Check Dockerfile creates all required directories
echo ""
echo "2. Checking Dockerfile directory creation..."
REQUIRED_DIRS=("run_attachments" "runs/rmos" "backups/cam")
for dir in "${REQUIRED_DIRS[@]}"; do
    if ! grep -q "$dir" services/api/Dockerfile; then
        echo "   ✗ ERROR: Dockerfile missing mkdir for $dir"
        ERRORS=$((ERRORS + 1))
    else
        echo "   ✓ $dir directory creation present"
    fi
done

# 3. Check Dockerfile has required ENV vars
echo ""
echo "3. Checking Dockerfile ENV vars..."
REQUIRED_ENVS=("RMOS_RUNS_DIR" "CAM_BACKUP_DIR" "RMOS_RUN_ATTACHMENTS_DIR")
for env in "${REQUIRED_ENVS[@]}"; do
    if ! grep -q "ENV $env" services/api/Dockerfile; then
        echo "   ✗ ERROR: Dockerfile missing ENV $env"
        ERRORS=$((ERRORS + 1))
    else
        echo "   ✓ ENV $env present"
    fi
done

# 4. Check client has VITE_API_BASE in Dockerfile
echo ""
echo "4. Checking client cross-origin configuration..."
if ! grep -q "VITE_API_BASE" packages/client/Dockerfile; then
    echo "   ✗ ERROR: Client Dockerfile missing VITE_API_BASE"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✓ VITE_API_BASE configured"
fi

# 5. Check for resolveAssetUrl in VisionAttachToRunWidget
echo ""
echo "5. Checking asset URL resolution..."
if ! grep -q "resolveAssetUrl" packages/client/src/features/ai_images/VisionAttachToRunWidget.vue 2>/dev/null; then
    echo "   ⚠ WARNING: VisionAttachToRunWidget may need resolveAssetUrl helper"
else
    echo "   ✓ resolveAssetUrl helper present"
fi

# Summary
echo ""
echo "======================================"
if [ $ERRORS -gt 0 ]; then
    echo "FAILED: $ERRORS error(s) found"
    echo "Fix the above issues before deploying"
    exit 1
else
    echo "PASSED: All deployment checks passed"
    echo "Ready to deploy!"
    exit 0
fi
