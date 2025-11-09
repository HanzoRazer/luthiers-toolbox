
# README_Community_Patch — Apply Guide

## What this adds
- A celebratory **Milestones & Community** section to your main `README.md` calling out your **first star** and inviting contributors.
- `CONTRIBUTORS.md` starter
- `docs/PR_GUIDE.md` short playbook
- GitHub issue templates (bug + feature)

## Apply options
**Option A — git apply (preferred):**
```bash
git apply --reject --whitespace=fix patches/readme_community.diff
```

**Option B — append (Windows PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File patches\Append-Community.ps1 -ReadmePath README.md
```

Then add files and commit:
```bash
git add -A
git commit -m "docs: milestones/community section + templates"
git push
```
