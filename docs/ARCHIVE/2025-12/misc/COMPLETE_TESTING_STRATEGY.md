# Complete Testing Strategy for Repository Transfer
**Phase 1 Execution - Testing & Validation**

---

## 🎯 Testing Philosophy

**Principle:** Test incrementally at each step. Don't proceed to next phase until current phase validates.

**Three-Tier Strategy:**
1. **Pre-Production Test** - Validate workflow with dummy repo
2. **Post-Creation Validation** - Automated testing of all 9 repos
3. **Feature Integration Tests** - Validate extracted features work in new repos

---

## 📋 Tier 1: Pre-Production Testing (Before Creating Real Repos)

### **Step 1A: Create Test Dummy** (10 minutes)

**Purpose:** Validate the entire creation workflow without risk

```powershell
# Create single test repository
.\scripts\Create-TestDummy.ps1

# Expected: ltb-test-dummy repo created with:
# ✓ Minimal server (FastAPI skeleton)
# ✓ Python venv + dependencies installed
# ✓ requirements.txt generated
# ✓ Server starts on port 8000
# ✓ Returns {"status": "ready", "edition": "TEST_DUMMY"}
```

### **Step 1B: Manual Validation** (5 minutes)

```powershell
cd ..\ltb-test-dummy\server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# In browser: http://localhost:8000/
# Expected: JSON response with correct edition flag
```

### **Step 1C: Cleanup Test Dummy** (2 minutes)

```powershell
# If validation passed, delete test dummy
gh repo delete HanzoRazer/ltb-test-dummy --yes
Remove-Item "..\ltb-test-dummy" -Recurse -Force

# If validation FAILED, debug issues before proceeding
```

**🚨 DO NOT PROCEED TO PRODUCTION REPOS UNTIL TEST DUMMY PASSES**

---

## 📋 Tier 2: Post-Creation Validation (After Creating All 9 Repos)

### **Step 2A: Automated Full Validation** (10-15 minutes)

**Script:** `Test-ProductRepos.ps1` - Comprehensive automated testing

```powershell
# Full validation suite
.\scripts\Test-ProductRepos.ps1

# Tests for each of 9 repos:
# ✓ Directory exists
# ✓ Python venv created
# ✓ Dependencies installed (fastapi, uvicorn, pydantic, python-dotenv)
# ✓ requirements.txt generated
# ✓ Server starts on unique port (8000-8008)
# ✓ Server responds with HTTP 200
# ✓ Edition flag matches expected value
```

**Expected Output:**
```
╔═══════════════════════════════════════╗
║  Test Summary                         ║
╚═══════════════════════════════════════╝

Repositories Tested: 9
Passed (Server + Edition): 9
Failed: 0

✅ ALL REPOSITORIES PASSED VALIDATION
Ready to proceed with feature extraction
```

### **Step 2B: Quick Smoke Test** (3-5 minutes)

**Use Case:** Fast validation without dependency checks

```powershell
# Skip dependency validation, just test server startup
.\scripts\Test-ProductRepos.ps1 -Quick
```

### **Step 2C: Selective Testing** (Variable)

**Use Case:** Test specific repos after fixes

```powershell
# Test only Express and Pro
.\scripts\Test-ProductRepos.ps1 -RepoNames @("ltb-express", "ltb-pro")

# Test only Parametric products
.\scripts\Test-ProductRepos.ps1 -RepoNames @("ltb-parametric-guitar", "ltb-neck-designer")
```

### **Step 2D: Manual Validation** (Optional, 10 minutes per repo)

If automated tests fail, manually validate:

```powershell
# For each failed repo:
cd ..\<repo-name>\server

# Check venv
Test-Path ".venv\Scripts\Activate.ps1"  # Should be True

# Activate and check dependencies
.\.venv\Scripts\Activate.ps1
pip list  # Should show fastapi, uvicorn, pydantic, python-dotenv

# Test server
uvicorn app.main:app --reload
# Visit http://localhost:8000/
# Expected: {"status": "ready", "edition": "<EDITION>"}
```

**🚨 DO NOT PROCEED TO FEATURE EXTRACTION UNTIL ALL REPOS VALIDATE**

---

## 📋 Tier 3: Feature Integration Testing (After Extracting Features)

### **Week 1: Express Edition Feature Tests**

After extracting Rosette Designer Lite (Step 1.4):

```powershell
cd ..\ltb-express\server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Test 1: Rosette endpoint exists
curl http://localhost:8000/api/rosette/plan `
  -Method POST `
  -Body '{"rings": [{"inner": 10, "outer": 15}]}' `
  -ContentType "application/json"

# Expected: 200 OK + toolpath JSON

# Test 2: DXF export works
curl http://localhost:8000/api/export/dxf `
  -Method POST `
  -Body '{"geometry": {...}}' `
  -ContentType "application/json" `
  -OutFile "test_rosette.dxf"

# Expected: Valid DXF file (open in CAD to verify)
```

After extracting Curve Lab Mini (Step 1.5):

```powershell
# Test curve endpoint
curl http://localhost:8000/api/curves/bezier `
  -Method POST `
  -Body '{"points": [[0,0], [10,20], [30,10]]}' `
  -ContentType "application/json"

# Expected: 200 OK + curve geometry
```

After extracting Fretboard Designer (Step 1.6):

```powershell
# Test fretboard calculation
curl http://localhost:8000/api/fretboard/calculate `
  -Method POST `
  -Body '{"scale": 25.5, "frets": 24}' `
  -ContentType "application/json"

# Expected: 200 OK + fret positions
```

### **Frontend Integration Tests** (After Each Feature)

```powershell
cd ..\ltb-express\client
npm run build

# Expected: No TypeScript errors
# Expected: Build completes successfully
# Expected: dist/ folder generated

npm run dev
# Visit http://localhost:5173
# Manually test:
# ✓ Feature renders
# ✓ Parameters adjust geometry
# ✓ Export button works
# ✓ Downloaded file is valid
```

---

## 📊 Testing Matrix (Phase 1 Week 1-2)

### **Week 1 Tests**

| Test | When | Expected Result | Pass Criteria |
|------|------|-----------------|---------------|
| Test Dummy Creation | Before production repos | ltb-test-dummy works | Server responds, edition correct |
| Full Repo Validation | After creating 9 repos | All pass automated tests | 9/9 repos pass |
| Express Server Basic | After Step 1.3 setup | Health endpoint works | 200 OK with edition flag |
| Rosette API | After Step 1.4 extraction | Toolpath generated | Valid JSON + export works |
| Curve API | After Step 1.5 extraction | Bezier curves work | Valid geometry returned |
| Fretboard API | After Step 1.6 extraction | Fret positions calculated | Accurate measurements |
| Express Client Build | After UI integration | No build errors | dist/ folder created |

### **Week 2 Tests (Parametric Guitar)**

| Test | When | Expected Result | Pass Criteria |
|------|------|-----------------|---------------|
| Body Params API | After backend extraction | Shape parameters adjust | Valid geometry returned |
| Bridge Placement | After bridge math | Coordinates calculated | Accurate position |
| Neck Pocket | After neck geometry | Pocket dimensions correct | Valid measurements |
| DXF Export | After export integration | Valid DXF file | Opens in CAD software |
| SVG Export | After export integration | Valid SVG file | Renders in browser |
| PDF Export | After export integration | Valid PDF file | Opens in PDF viewer |
| Client Build | After UI completion | No errors | Vite builds successfully |

---

## 🔧 Test Scripts Reference

### **Created Scripts**

1. **`Create-TestDummy.ps1`** ✅
   - Purpose: Pre-production validation
   - Creates single test repo
   - Validates workflow
   - Cleanup option: `-CleanupAfter`

2. **`Test-ProductRepos.ps1`** ✅
   - Purpose: Post-creation validation
   - Tests all 9 repos
   - Checks: venv, dependencies, server, edition
   - Options: `-Quick`, `-RepoNames`

3. **`Test-B22-Export-P0.1.ps1`** ✅ (Already exists)
   - Purpose: Validate P0.1 blocking task
   - Tests B22.12 diff export
   - Required before repo creation

### **To Be Created (Week 1-2)**

4. **`Test-ExpressFeatures.ps1`**
   - Tests Rosette, Curve, Fretboard APIs
   - Validates DXF/SVG exports
   - Frontend build test

5. **`Test-ParametricGuitar.ps1`**
   - Tests body shape generation
   - Validates all export formats
   - Client build + preview

---

## 🚨 Failure Recovery Procedures

### **If Test Dummy Fails**
1. Review error messages
2. Check GitHub CLI auth: `gh auth status`
3. Manually create repo to isolate issue
4. Fix `Create-ProductRepos.ps1` script
5. Delete test dummy and retry

### **If Automated Validation Fails (< 3 repos)**
1. Review specific error messages in test output
2. Manually validate failed repos
3. Re-run creation for those specific repos:
   ```powershell
   gh repo delete HanzoRazer/<repo-name> --yes
   # Then re-run full script (skips existing repos)
   .\scripts\Create-ProductRepos.ps1
   ```

### **If Automated Validation Fails (> 3 repos)**
1. Likely systematic issue (not individual repo problem)
2. Review script logic in `Create-ProductRepos.ps1`
3. Delete ALL repos and restart:
   ```powershell
   # Nuclear option - use with caution
   $repos = @("ltb-express", "ltb-pro", "ltb-enterprise", ...)
   foreach ($repo in $repos) {
       gh repo delete "HanzoRazer/$repo" --yes
   }
   ```
4. Fix script, then re-run

### **If Feature Tests Fail**
1. Verify feature exists in golden master
2. Check extraction copied all dependencies
3. Validate imports/paths are correct
4. Test same feature in golden master first
5. Compare golden master vs extracted code

---

## ✅ Phase 1 Testing Checklist

### **Pre-Execution (Before Creating Repos)**
- [ ] P0.1 validated (B22.12 export works)
- [ ] GitHub CLI authenticated (`gh auth login`)
- [ ] Test dummy created and validated
- [ ] Test dummy deleted after validation
- [ ] `Create-ProductRepos.ps1` script reviewed
- [ ] `Test-ProductRepos.ps1` script ready

### **Post-Creation (After Creating 9 Repos)**
- [ ] All 9 repos created on GitHub
- [ ] All 9 repos cloned locally
- [ ] Automated validation passed (9/9 repos)
- [ ] Manual spot-check of 2-3 repos
- [ ] Ready to proceed with feature extraction

### **Week 1 (Express Edition)**
- [ ] Express server health endpoint works
- [ ] Rosette Designer API tested
- [ ] Curve Lab API tested
- [ ] Fretboard Designer API tested
- [ ] All DXF exports work
- [ ] All SVG exports work
- [ ] Frontend builds without errors
- [ ] Manual UI testing complete

### **Week 2 (Parametric Guitar)**
- [ ] Body shape generation tested
- [ ] Bridge placement math validated
- [ ] Neck pocket geometry correct
- [ ] All export formats work (DXF, SVG, PDF)
- [ ] Frontend builds and renders
- [ ] Manual parameter testing complete

### **Week 3 (Packaging)**
- [ ] Electron builds for Windows
- [ ] Electron builds for macOS
- [ ] Desktop apps launch successfully
- [ ] All features work in packaged app

---

## 🎯 Success Criteria

**Phase 1 testing is complete when:**

✅ Test dummy validates workflow  
✅ All 9 repos pass automated validation  
✅ Express Edition 3 features extracted and tested  
✅ Parametric Guitar generates and exports successfully  
✅ Frontend builds without errors  
✅ Desktop apps package successfully  
✅ Manual testing confirms all features work  

**Timeline:**
- Pre-production testing: 20 minutes
- Post-creation validation: 15 minutes
- Feature integration tests: 2-4 hours/week (ongoing)

**Total Testing Overhead:** ~10-15% of development time (well worth it!)
