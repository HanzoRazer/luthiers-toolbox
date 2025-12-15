# Testing Quick Reference Card
**Phase 1 Repository Transfer - Testing Cheat Sheet**

---

## 🚀 Execution Sequence

```powershell
# 1. Authenticate GitHub CLI (one-time setup)
gh auth login

# 2. Test workflow with dummy repo (20 min)
.\scripts\Create-TestDummy.ps1
# → Validates creation process safely
# → If passes: delete dummy and proceed
# → If fails: debug before production run

# 3. Create all 9 production repositories (30 min)
.\scripts\Create-ProductRepos.ps1
# → Creates minimal skeletons with automated Python setup
# → Installs fastapi, uvicorn, pydantic, python-dotenv
# → Generates requirements.txt for each repo

# 4. Validate all repositories (15 min)
.\scripts\Test-ProductRepos.ps1
# → Tests all 9 repos automatically
# → Checks: venv, dependencies, server, edition flags
# → Expected: 9/9 pass = ready for feature extraction
```

---

## 📋 Test Scripts Reference

### **Create-TestDummy.ps1**
**Purpose:** Pre-production validation  
**Usage:** `.\scripts\Create-TestDummy.ps1`  
**Options:** `-CleanupAfter` (auto-delete after test)  
**Tests:** Single test repo with full workflow  
**Time:** 10 minutes  

### **Create-ProductRepos.ps1**
**Purpose:** Create all 9 production repositories  
**Usage:** `.\scripts\Create-ProductRepos.ps1`  
**Options:** `-DryRun` (preview without creating)  
**Creates:** Minimal skeletons + automated Python setup  
**Time:** 20-30 minutes (script runtime)  

### **Test-ProductRepos.ps1** 🆕
**Purpose:** Validate all repositories post-creation  
**Usage:** `.\scripts\Test-ProductRepos.ps1`  
**Options:**  
- `-Quick` - Fast smoke test (skip dependency checks)
- `-RepoNames @("ltb-express", "ltb-pro")` - Test specific repos

**Tests Per Repo:**
- ✓ Directory exists
- ✓ Python venv created
- ✓ Dependencies installed
- ✓ requirements.txt generated
- ✓ Server starts on unique port
- ✓ HTTP 200 response
- ✓ Edition flag correct

**Time:** 10-15 minutes (full), 3-5 minutes (quick)

---

## 🎯 Success Criteria

### **Pre-Production (Test Dummy)**
✅ ltb-test-dummy repo created  
✅ Server starts on port 8000  
✅ Returns `{"status": "ready", "edition": "TEST_DUMMY"}`  
✅ Dummy deleted after validation  

### **Post-Creation (All 9 Repos)**
✅ All repos created on GitHub  
✅ All repos cloned locally  
✅ Automated validation: 9/9 pass  
✅ Each repo has working minimal server  
✅ Edition flags correct for all  

---

## 🔧 Troubleshooting

### **Test Dummy Fails**
```powershell
# Check GitHub auth
gh auth status

# Try manual creation
gh repo create HanzoRazer/ltb-test-dummy --public
```

### **Automated Validation Fails (Few Repos)**
```powershell
# Test specific failed repo
.\scripts\Test-ProductRepos.ps1 -RepoNames @("ltb-express")

# Manual validation
cd ..\ltb-express\server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
# Visit http://localhost:8000/
```

### **Automated Validation Fails (Many Repos)**
```powershell
# Likely systematic issue - review script
# Delete all and restart
$repos = @("ltb-express", "ltb-pro", "ltb-enterprise", ...)
foreach ($repo in $repos) {
    gh repo delete "HanzoRazer/$repo" --yes
}
```

---

## 📊 Testing Matrix

| Phase | Script | Time | Pass Criteria |
|-------|--------|------|---------------|
| Pre-Production | Create-TestDummy.ps1 | 20 min | Dummy validates |
| Creation | Create-ProductRepos.ps1 | 30 min | 9 repos created |
| Validation | Test-ProductRepos.ps1 | 15 min | 9/9 repos pass |
| Express Features | Manual tests | Week 1 | 3 features work |
| Parametric | Manual tests | Week 2 | Shapes + exports |

---

## 🚨 Critical Rules

1. **DO NOT** skip test dummy validation
2. **DO NOT** proceed to feature extraction until automated tests pass
3. **DO NOT** delete failed repos until you understand the issue
4. **DO** run tests incrementally (test dummy → full validation → features)
5. **DO** review error messages before retrying

---

## 📚 Full Documentation

- **Complete Testing Strategy:** [COMPLETE_TESTING_STRATEGY.md](./COMPLETE_TESTING_STRATEGY.md)
- **Phase 1 Execution Plan:** [PHASE_1_EXECUTION_PLAN.md](./PHASE_1_EXECUTION_PLAN.md)
- **Lean Extraction Strategy:** [LEAN_EXTRACTION_STRATEGY.md](./LEAN_EXTRACTION_STRATEGY.md)

---

## ⚡ Quick Commands

```powershell
# Authenticate GitHub
gh auth login

# Test workflow
.\scripts\Create-TestDummy.ps1

# Create repos
.\scripts\Create-ProductRepos.ps1

# Validate all
.\scripts\Test-ProductRepos.ps1

# Quick smoke test
.\scripts\Test-ProductRepos.ps1 -Quick

# Test specific repos
.\scripts\Test-ProductRepos.ps1 -RepoNames @("ltb-express", "ltb-pro")
```

---

**Status:** ✅ Complete testing infrastructure ready  
**Next Step:** Authenticate GitHub CLI and run test dummy  
**Time to Launch:** ~1 hour (testing) + 4 weeks (Phase 1)
