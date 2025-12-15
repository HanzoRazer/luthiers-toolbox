# Revised Phase 1 Strategy: Lean Extraction vs. Template Copying

**Date:** December 3, 2025  
**Context:** Phase 1 execution planning refinement

---

## 🎯 Key Insight

**Original Plan:** Copy full template stubs into every repo  
**Revised Plan:** Create minimal repos, extract features from golden master as needed

---

## ❌ What We're NOT Doing

### Avoid Template Bloat:
- ❌ Copying 8 stub view files to every repo
- ❌ Installing full canonical `main.py` with all routers
- ❌ Pre-creating empty components that might not be used
- ❌ Duplicating boilerplate across 9 repositories

### Why This Was Wrong:
1. **Wasted disk space** - Stub files in repos that never use them
2. **Confusing structure** - Empty views make it unclear what's implemented
3. **Update nightmare** - Changing a pattern means updating 9 repos
4. **Drift risk** - Each repo diverges from stubs independently

---

## ✅ What We're Actually Doing

### Lean Repo Creation:

**Step 1: Minimal Skeleton Only**
```
ltb-express/
├── client/           # Empty - will populate during extraction
├── server/           # Empty - will populate during extraction
├── docs/             # Empty
├── README.md         # Setup instructions
└── .gitignore        # Python + Node patterns
```

**Step 2: Extract Features from Golden Master**

When implementing Rosette Designer for Express:
```powershell
# Copy ONLY what's needed from golden master
cd luthiers-toolbox/packages/client/src/components/rosette/
# Identify: RosetteDesigner.vue, RingControl.vue, rosetteGeometry.ts

cd ltb-express/client/src/components/
# Copy the 3 files, strip Pro features, done
```

**Step 3: Build Incrementally**

Each feature extraction is isolated:
- ✅ Copy specific component from golden master
- ✅ Remove Pro/Enterprise features
- ✅ Add to router
- ✅ Test
- ✅ Commit

---

## 📊 Comparison

| Aspect | Template Approach | Lean Extraction |
|--------|-------------------|-----------------|
| **Initial Setup** | Copy 50+ stub files | Create 5 directories |
| **Repo Size** | ~2MB of unused code | ~100KB (README + config) |
| **Clarity** | "Is this implemented?" confusion | Empty = not implemented |
| **Updates** | Change 9 repos | Change golden master only |
| **Extraction Work** | Pre-done (but maybe wrong) | Done as needed (always right) |
| **Feature Isolation** | All or nothing | Pick exactly what you need |

---

## 🔧 Updated Workflow

### Phase 1 Week 1 (Revised):

**Day 1: Repo Creation (2-3 hours)**
```powershell
# Authenticate GitHub
gh auth login

# Create 9 minimal repos (just structure, no code)
.\scripts\Create-ProductRepos.ps1

# Result: 9 empty repos with README and .gitignore
```

**Day 2-3: Express Rosette Extraction (8-12 hours)**
```powershell
cd ltb-express

# 1. Setup minimal FastAPI
echo "from fastapi import FastAPI; app = FastAPI()" > server/app/main.py

# 2. Setup minimal Vue
npm create vite@latest client -- --template vue-ts
cd client && npm install vue-router pinia

# 3. Identify rosette files in golden master
cd ../../luthiers-toolbox/packages/client/src
ls components/rosette/  # See what exists

# 4. Copy specific files
cp components/rosette/RosetteDesigner.vue ../../../ltb-express/client/src/components/
cp utils/rosetteGeometry.ts ../../../ltb-express/client/src/utils/

# 5. Strip Pro features (CAM export, machine profiles)
# 6. Add to Express router
# 7. Test and commit
```

**Result:** Rosette Designer working in Express, no unused code

---

## 💡 Benefits of Lean Approach

### For Development:
1. **Faster repo creation** - No copying overhead
2. **Clearer feature status** - If it exists, it's implemented
3. **Easier debugging** - Less code to search through
4. **Natural documentation** - git history shows feature additions

### For Maintenance:
1. **Single source of truth** - Golden master is authoritative
2. **Easy updates** - Fix bug in golden master, re-extract to products
3. **No drift** - Each extraction is intentional, not leftover stub
4. **Simpler CI/CD** - Only test what's actually there

### For Users:
1. **Smaller downloads** - No bloated repos
2. **Clearer feature sets** - README lists actual features, not plans
3. **Faster installs** - Fewer dependencies
4. **Better performance** - Less code to load

---

## 🎯 Revised Timeline Impact

**Original Estimate (Template Approach):**
- Step 1.1 (Repo creation): 8-12 hours ← **Copying stubs**
- Step 1.2 (Setup skeleton): 4-6 hours ← **Configuring stubs**

**Revised Estimate (Lean Approach):**
- Step 1.1 (Repo creation): **2-3 hours** ← Just structure
- Step 1.2 (Setup skeleton): **2-3 hours** ← Minimal main.py + App.vue

**Time Saved:** ~8-12 hours in Week 1  
**Benefit:** Can start feature extraction earlier

---

## 📝 Updated Create-ProductRepos.ps1

The script should create:
- ✅ Directory structure
- ✅ README.md with setup commands
- ✅ .gitignore (Python + Node patterns)
- ❌ NO template copying
- ❌ NO stub views
- ❌ NO boilerplate code

**Minimal README.md Template:**
```markdown
# [Product Name]

## Status
🚧 Under Development

## Setup

### Server
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install fastapi uvicorn
uvicorn app.main:app --reload
```

### Client
```bash
cd client
npm create vite@latest . -- --template vue-ts
npm install vue-router pinia
npm run dev
```

## Features
- TBD (extract from golden master as implemented)

## Documentation
See [PRODUCT_REPO_SETUP.md](https://github.com/HanzoRazer/luthiers-toolbox/blob/main/PRODUCT_REPO_SETUP.md)
```

---

## 🚀 Next Actions

1. ✅ Update PHASE_1_EXECUTION_PLAN.md with lean strategy (DONE)
2. ⏳ Simplify Create-ProductRepos.ps1 to skip template copying
3. ⏳ Authenticate GitHub CLI: `gh auth login`
4. ⏳ Run simplified repo creation script
5. ⏳ Begin feature extraction from golden master

---

**Status:** ✅ Strategy Revised - Lean Extraction Approach  
**Impact:** ~8-12 hours saved in Week 1  
**Next:** Authenticate GitHub CLI and create minimal repos
