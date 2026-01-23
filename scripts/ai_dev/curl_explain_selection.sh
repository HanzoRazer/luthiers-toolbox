#!/usr/bin/env bash

curl -X POST http://localhost:8000/ai/advisories/request \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: dev-test-001" \
  -d @scripts/ai_dev/sample_context.json | jq .
