#!/usr/bin/env bash
# scripts/tag_preview.sh
# Create a preview tag for mesh-pipeline release.
#
# Usage:
#   ./scripts/tag_preview.sh v0.1.0
#   ./scripts/tag_preview.sh v0.1.0-rc1
#
# Creates tag: toolbox-mesh-pipeline-v0.1.0 (or -rc1)

set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <version>"
  echo "  e.g., $0 v0.1.0"
  exit 1
fi

TAG_NAME="toolbox-mesh-pipeline-${VERSION}"

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "❌ Uncommitted changes detected. Commit or stash first."
  exit 1
fi

# Check if tag already exists
if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
  echo "❌ Tag $TAG_NAME already exists."
  exit 1
fi

# Get current commit info
COMMIT_SHA=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --pretty=%s)

echo "Creating tag: $TAG_NAME"
echo "  Commit: $COMMIT_SHA"
echo "  Message: $COMMIT_MSG"
echo ""

read -rp "Proceed? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

git tag -a "$TAG_NAME" -m "Mesh pipeline preview release $VERSION

Commit: $COMMIT_SHA
Message: $COMMIT_MSG

Components:
- services/api/app/mesh/
- services/api/app/retopo/
- services/api/app/fields/
- presets/retopo/
- examples/retopo/
"

echo "✅ Tag created: $TAG_NAME"
echo ""
echo "To push: git push origin $TAG_NAME"
