#!/usr/bin/env bash
# Package JSONL session fixtures for release attachment
#
# Usage: ./tools/package_sessions.sh <tag> [out_dir] [fixtures_dir]
# Example: ./tools/package_sessions.sh toolbox-v0.35.0 dist services/api/tests/fixtures
#
# Output: dist/agentic-sessions-toolbox-v0.35.0.zip

set -euo pipefail

TAG="${1:-unknown}"
OUT_DIR="${2:-dist}"
FIXTURES_DIR="${3:-services/api/tests/fixtures}"

mkdir -p "$OUT_DIR"

ZIP_NAME="agentic-sessions-${TAG}.zip"
ZIP_PATH="${OUT_DIR}/${ZIP_NAME}"

# Resolve absolute path for zip output (needed when cd'ing into fixtures dir)
ABS_ZIP_PATH="$(cd "$(dirname "$ZIP_PATH")" && pwd)/$(basename "$ZIP_PATH")"

# Verify fixtures exist
JSONL_COUNT=$(find "$FIXTURES_DIR" -maxdepth 1 -name "*.jsonl" | wc -l)
if [ "$JSONL_COUNT" -eq 0 ]; then
    echo "❌ No JSONL fixtures found in $FIXTURES_DIR" >&2
    exit 1
fi

echo "📦 Packaging $JSONL_COUNT session files from $FIXTURES_DIR"

# List files being packaged
find "$FIXTURES_DIR" -maxdepth 1 -name "*.jsonl" -exec basename {} \; | sort

# Create zip (from fixtures dir so paths are clean)
( cd "$FIXTURES_DIR" && zip -r -q "$ABS_ZIP_PATH" ./*.jsonl )

echo "✅ Created: $ZIP_PATH"
echo "zip_path=$ZIP_PATH"
