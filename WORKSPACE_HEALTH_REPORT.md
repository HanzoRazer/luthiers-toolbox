# Workspace Health Report

**Date:** December 15, 2025  
**Repository:** `luthiers-toolbox`  
**Status:** ✅ Core Systems Operational

---

## Executive Summary

Post-consolidation health check completed. The backend imports successfully and no duplicate router/CAM/calculator files were found. However, **5 nested Git repositories** were detected, which may cause commit confusion.

---

## 1. Nested Git Repositories

⚠️ **Issue:** Multiple `.git` folders exist within the workspace, which can cause commit discipline problems.

| Status | Repository Path |
|--------|-----------------|
| ✅ Main | `luthiers-toolbox\.git` |
| ⚠️ Nested | `ltb-express\.git` |
| 📦 Legacy | `Guitar Design HTML app\...\Luthiers_Tool_Box_...\.git` |
| 📦 Legacy | `Luthiers Tool Box\Smart Guitar Build\desktop-tutorial\.git` |
| 📦 Legacy | `Luthiers Tool Box\Smart Guitar Build\Rogue-one\.git` |

### Recommendations

**Option A — Remove nested `.git` folders:**
```powershell
# Remove ltb-express nested repo (keeps files, removes git tracking)
Remove-Item "c:\Users\thepr\Downloads\luthiers-toolbox\ltb-express\.git" -Recurse -Force
```

**Option B — Add to `.gitignore`:**
```gitignore
# Nested repos in legacy directories
ltb-express/.git/
Guitar Design HTML app/**/.git/
Luthiers Tool Box/**/.git/
```

---

## 2. Backend Import Check

✅ **Result:** `app.main` imports successfully

### Command Run
```powershell
cd "c:\Users\thepr\Downloads\luthiers-toolbox\services\api"
python -c "from app.main import app; print('✓ All imports OK')"
```

### Output
```
✓ All imports OK
```

### Warnings (Non-Critical)

| Module | Status | Notes |
|--------|--------|-------|
| WeasyPrint | ⚠️ Not installed | PDF export disabled (optional feature) |
| AI-CAM router | ⚠️ Experimental | `app.routers.ai_cam_router` not found |
| JobLog router | ⚠️ Experimental | `app.routers.joblog_router` not found |
| Learn router | ⚠️ Experimental | `cnc_production` module not found |
| Learned overrides | ⚠️ Experimental | `app.cnc_production.feeds_speeds` not found |
| Analytics routers | ⚠️ Experimental | `app.analytics` module not found |
| Dashboard router | ⚠️ Experimental | `cnc_production` module not found |

**Note:** These warnings are expected — experimental features are gracefully disabled via try/except blocks in `main.py`.

### Pydantic Warning
```
Valid config keys have changed in V2: 'schema_extra' has been renamed to 'json_schema_extra'
```
**Action:** Low priority — update Pydantic models when convenient.

---

## 3. Duplicate File Scan

✅ **Result:** No duplicate routers, CAM modules, or calculators found

### Directories Scanned
- `services/api/app/routers/`
- `services/api/app/cam/`
- `services/api/app/calculators/`

### Findings

| Count | Filename | Notes |
|-------|----------|-------|
| 11 | `__init__.py` | Expected — required for Python packages |

**No problematic duplicates detected.**

---

## 4. Recent Commit

**Commit:** `5b34528`  
**Message:** "Add consolidation docs, blade JSON fix, validation script, and workspace config"

### Files Committed
| File | Description |
|------|-------------|
| `CONSOLIDATION_PHASE.md` | Consolidation planning doc |
| `REPO_AUDIT_REPORT.md` | Repository audit findings |
| `SUBSYSTEM_PROMOTION_CHECKLIST.md` | Checklist for subsystem promotion |
| `saw_lab_blades_FIXED.json` | Corrected blade fixture data |
| `validate_blade_json.py` | JSON validation script |
| `Reorganize-LTB-Repos.ps1` | Repo reorganization script |
| `luthiers-toolbox.code-workspace` | VS Code workspace config |

**Status:** Pushed to `origin/main`

---

## 5. Recommended Actions

### Immediate (High Priority)
- [ ] Decide on nested repo handling (Option A or B above)
- [ ] Close `ltb-express\.git\COMMIT_EDITMSG` — you're editing in nested repo

### Short-Term
- [ ] Verify other JSON fixtures in `services/api/app/data/` are valid
- [ ] Run full test suite: `.\test_adaptive_l1.ps1`, `.\test_adaptive_l2.ps1`

### Low Priority
- [ ] Update Pydantic models to use `json_schema_extra` instead of `schema_extra`
- [ ] Install WeasyPrint if PDF export is needed: `pip install weasyprint`

---

## Appendix: Commands Used

```powershell
# Find nested .git folders
Get-ChildItem -Path "c:\Users\thepr\Downloads\luthiers-toolbox" -Recurse -Directory -Filter ".git" -Force | Select-Object FullName

# Backend import check
cd "c:\Users\thepr\Downloads\luthiers-toolbox\services\api"
python -c "from app.main import app; print('✓ All imports OK')"

# Duplicate file scan
cd "c:\Users\thepr\Downloads\luthiers-toolbox\services\api\app"
Get-ChildItem -Path "routers","cam","calculators" -Recurse -Filter "*.py" | Group-Object Name | Where-Object { $_.Count -gt 1 }
```

---

**Report Generated:** December 15, 2025  
**Next Review:** After nested repo resolution
