# Git History Cleanup Procedure

## Problem

Push blocked by GitHub 100MB file limit. Large files in commit history:
- `Index_of_CITES_Species_2026-04-30 09_16.json` — 148.73 MB
- `services/api/test_temp/vectorizer_test_april21/*.dxf` — up to 1.1 GB each

## Option 1: BFG Repo Cleaner

```bash
# 1. Make a fresh mirror clone (BFG works on bare repos)
cd /tmp
git clone --mirror https://github.com/HanzoRazer/luthiers-toolbox.git
cd luthiers-toolbox.git

# 2. Run BFG to remove files matching patterns
java -jar bfg.jar --strip-blobs-bigger-than 100M
# Or by name:
java -jar bfg.jar --delete-files "Index_of_CITES_Species_*.json"
java -jar bfg.jar --delete-folders "vectorizer_test_april21"

# 3. Clean up the now-orphaned references
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. Push the cleaned history
git push
```

The `--mirror` clone is important. BFG operates on a bare repo.

## Option 2: git-filter-repo (Preferred)

```bash
# 1. Install git-filter-repo if not already installed
pip install git-filter-repo --break-system-packages
# (or via apt/brew/choco depending on your platform)

# 2. Identify all oversized blobs in history
cd /path/to/luthiers-toolbox
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1 == "blob" && $3 >= 52428800' \
  | sort -k3 -n -r \
  > /tmp/large_files.txt

# Review the list — make sure you're removing what you intend to remove
cat /tmp/large_files.txt

# 3. Make a backup (filter-repo will refuse to run on a non-fresh clone by default)
cd ..
cp -r luthiers-toolbox luthiers-toolbox.backup

# 4. Run the cleanup — multiple options:

# Option A: Strip everything over 100MB (catches both CITES JSON and DXFs)
cd luthiers-toolbox
git filter-repo --strip-blobs-bigger-than 100M

# Option B: Remove specific paths (more surgical)
git filter-repo --invert-paths \
  --path-glob 'services/api/test_temp/vectorizer_test_april21' \
  --path-glob 'Index_of_CITES_Species_*.json'

# Option C: Combine both — strip large blobs AND remove specific paths
git filter-repo --strip-blobs-bigger-than 100M \
  --path-glob 'services/api/test_temp/vectorizer_test_april21' --invert-paths
```

**Recommended**: Option A — catches anything over 100MB regardless of path, matches GitHub's hard limit.

## Post-Cleanup Steps

```bash
# filter-repo removes remote config by design — re-add it
git remote add origin https://github.com/HanzoRazer/luthiers-toolbox.git

# Confirm large files are gone
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1 == "blob" && $3 >= 52428800'
# Should output nothing

# Check repo size before/after
du -sh .git
# Should be substantially smaller than the backup

# Force push all branches and tags
git push --force --all origin
git push --force --tags origin
```

## Re-clone Requirement

After force push, anyone with the repo locally needs to discard their clone and re-clone fresh:

```bash
cd /path/to/old/luthiers-toolbox
git stash push -u -m "Save before re-clone"
cd ..
mv luthiers-toolbox luthiers-toolbox.old
git clone https://github.com/HanzoRazer/luthiers-toolbox.git
# Move uncommitted work back if needed
```

## Prevention (.gitignore additions)

```gitignore
# Test artifacts — never commit
services/api/test_temp/

# Large reference data — use external data sources
Index_of_CITES_Species*.json
```

## Pre-commit Hook (Optional)

```bash
# .git/hooks/pre-commit (make executable)
#!/bin/bash
LIMIT_MB=50
LIMIT_BYTES=$((LIMIT_MB * 1024 * 1024))

for file in $(git diff --cached --name-only); do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        if [ "$size" -gt "$LIMIT_BYTES" ]; then
            echo "ERROR: $file is ${size} bytes (limit ${LIMIT_BYTES})"
            echo "Add to .gitignore or use Git LFS for binary assets."
            exit 1
        fi
    fi
done
```

## Current State (2026-05-02)

- **Tier 2 species audit**: 7 commits, local only, NOT pushed
- **Blocking commits**: khaya audit commit accidentally included CITES JSON + test artifacts
- **Action required**: Run filter-repo Option A, force push, re-clone working directory
