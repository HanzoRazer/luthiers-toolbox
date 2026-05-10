#!/bin/bash
# =============================================================================
# Git History Cleanup — Remove Large Files (5.2 GB)
# =============================================================================
#
# Removes test_temp artifacts and CITES reference dumps from git history.
# Run from repository root. Requires git-filter-repo installed.
#
# Install first: pip install git-filter-repo
#
# WARNING: This rewrites history. All commit SHAs will change.
# =============================================================================

set -e  # Exit on error

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
BACKUP_DIR="$(dirname "$REPO_ROOT")/${REPO_NAME}.backup-$(date +%Y%m%d-%H%M%S)"

echo "=== Step 0: Pre-flight checks ==="

# Check filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo "ERROR: git-filter-repo not installed"
    echo ""
    echo "Install with one of:"
    echo "  pip install git-filter-repo"
    echo "  pip install --user git-filter-repo"
    echo "  pip install --break-system-packages git-filter-repo"
    echo ""
    exit 1
fi

git filter-repo --version
echo ""
echo "Repository: $REPO_ROOT"
echo "Current branch: $(git branch --show-current)"
echo ""

echo "=== Step 1: Full directory backup ==="
echo "Copying to: $BACKUP_DIR"
cp -r "$REPO_ROOT" "$BACKUP_DIR"
echo "Backup complete. If anything goes wrong:"
echo "  rm -rf \"$REPO_ROOT\" && mv \"$BACKUP_DIR\" \"$REPO_ROOT\""
echo ""

cd "$REPO_ROOT"

echo "=== Step 2: Pre-cleanup size ==="
echo "Current .git size:"
du -sh .git
echo ""

echo "=== Step 3: Add .gitignore entries BEFORE rewrite ==="
# Add prevention before cleanup so it's in the cleaned history
if ! grep -q "services/api/test_temp/" .gitignore 2>/dev/null; then
    cat >> .gitignore << 'EOF'

# Test artifacts — never commit (added after 5.2 GB cleanup 2026-05-02)
services/api/test_temp/
**/test_outputs/
*.dxf.tmp

# Large reference data — fetch on demand, don't commit
data/reference/cites_*.json
Index_of_CITES_Species_*.json
EOF
    git add .gitignore
    git commit -m "chore: gitignore test artifacts and large reference data

Prevents recurrence of the 5.2 GB test_temp commit that required
git filter-repo cleanup on 2026-05-02. Test outputs from vectorizer
runs and CITES reference dumps stay outside version control."
    echo "Added .gitignore entries"
else
    echo ".gitignore already has test_temp entry"
fi
echo ""

echo "=== Step 4: Show files to be removed ==="
echo "Files >= 50MB in history:"
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '$1 == "blob" && $3 >= 52428800 {printf "%.1f MB  %s\n", $3/1048576, $4}' | \
  sort -rn | head -30
echo ""

echo "=== Step 5: Run filter-repo ==="
echo "Removing large files from history..."
echo ""

# Use glob patterns to handle spaces and variations
git filter-repo \
    --invert-paths \
    --path-glob 'services/api/test_temp/*' \
    --path-glob 'Index_of_CITES_Species_*.json' \
    --force

# Belt-and-suspenders: strip any remaining large blobs
echo ""
echo "Stripping any remaining blobs > 100MB..."
git filter-repo --strip-blobs-bigger-than 100M --force

echo ""
echo "=== Step 6: Aggressive garbage collection ==="
echo "Compacting pack files..."
git gc --prune=now --aggressive
echo ""

echo "=== Step 7: Verify cleanup ==="
echo "Checking for remaining large files..."

REMAINING=$(git rev-list --objects --all 2>/dev/null | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' 2>/dev/null | \
  awk '$1 == "blob" && $3 >= 52428800' | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "SUCCESS: No files >= 50MB remain in history"
else
    echo "WARNING: $REMAINING large files still present:"
    git rev-list --objects --all | \
      git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
      awk '$1 == "blob" && $3 >= 52428800 {printf "%.1f MB  %s\n", $3/1048576, $4}'
fi
echo ""

echo "Post-cleanup .git size:"
du -sh .git
echo ""

echo "Recent commits (verify FRET-CONSOLIDATION-1 survived):"
git log --oneline | head -10
echo ""

echo "=== Step 8: Ready to push ==="
echo ""
echo "History has been rewritten. To push:"
echo ""
echo "  # Re-add remote (filter-repo removes it)"
echo "  git remote add origin https://github.com/HanzoRazer/luthiers-toolbox.git"
echo ""
echo "  # Force push (safe for solo project)"
echo "  git push --force origin --all"
echo "  git push --force origin --tags"
echo ""
echo "Backup preserved at: $BACKUP_DIR"
echo "Delete backup after verifying push succeeded."
echo ""
echo "=== Done ==="
