#!/bin/bash
# wait_for_server.sh
# Waits for FastAPI dev server to become responsive

MAX_ATTEMPTS=30
ATTEMPT=0
URL="${1:-http://127.0.0.1:8000/exports/dxf/health}"

echo "Waiting for server at $URL..."

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f "$URL" > /dev/null 2>&1; then
        echo "✓ Server is ready!"
        exit 0
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    sleep 1
done

echo "✗ Server failed to respond after $MAX_ATTEMPTS seconds"
exit 1
