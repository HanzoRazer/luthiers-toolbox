#!/usr/bin/env bash
set -euo pipefail

# This script assumes you've pasted the files above into a temp folder `wirein/add/`
# If not using that flow, you can skip this script.

if [ ! -d "wirein/add" ]; then
  echo "Error: wirein/add directory not found"
  echo "Usage: Create wirein/add/ with files to copy, then run this script"
  exit 1
fi

echo "Copying files from wirein/add/ to repository root..."
rsync -av wirein/add/ ./

echo "✓ Done. Now run:"
echo "  git add ."
echo "  git commit -m 'feat: wire-in packages/ + services/api'"
