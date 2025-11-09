#!/usr/bin/env bash
set -euo pipefail

SERVER_PORT=${SERVER_PORT:-8000}

echo "Generating TypeScript SDK from OpenAPI..."
curl -sSf "http://localhost:${SERVER_PORT}/openapi.json" -o /tmp/openapi.json

npx openapi-typescript /tmp/openapi.json -o packages/shared/index.d.ts

echo "✓ Generated packages/shared/index.d.ts"
