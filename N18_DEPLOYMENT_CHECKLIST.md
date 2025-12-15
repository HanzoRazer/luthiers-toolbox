# N18 Spiral PolyCut - Deployment Checklist

**Status:** Ready for Production Deployment  
**Date:** November 5, 2025

---

## ✅ Pre-Deployment Validation

### **1. Run All Tests (5 minutes)**

```powershell
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api"

# Activate environment
.\.venv\Scripts\Activate.ps1

# Ensure dependencies installed
pip install pyclipper==1.3.0.post5

# Test 1: Validation suite
python scripts/validate_n18_baseline.py
# Expected: "All Validations PASSED"

# Test 2: Performance benchmarks
python scripts/benchmark_n18_spiral_poly.py
# Expected: Timing data for 3 geometries

# Test 3: Pytest suite
pytest tests/test_n18_spiral_gcode.py -v
# Expected: 5 passed
```

**Pass Criteria:**
- [ ] Validation script exits with code 0
- [ ] Benchmark shows avg times < 5ms per geometry
- [ ] All 5 pytest tests pass

---

## 🚀 Deployment Steps

### **2. Start Server & Test Endpoint (2 minutes)**

```powershell
# Terminal 1: Start server
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Test endpoint
curl -X POST http://localhost:8000/cam/adaptive3/offset_spiral.nc `
  -H 'Content-Type: application/json' `
  -d '{
    "geometry": {
      "units": "mm",
      "paths": [
        {"type": "closed", "points": [[0,0], [100,0], [100,60], [0,60]]}
      ]
    },
    "tool_d": 6.0,
    "stepover": 0.45,
    "margin": 0.5,
    "corner_radius_min": 1.0,
    "corner_tol_mm": 0.3,
    "climb": true,
    "feed_xy": 1200,
    "safe_z": 5.0,
    "z_rough": -1.5
  }' `
  -o test_spiral.nc

# Verify output
type test_spiral.nc
```

**Pass Criteria:**
- [ ] Server starts without errors
- [ ] Endpoint returns 200 OK
- [ ] G-code file created (> 0 bytes)
- [ ] G-code contains `G21`, `G90`, spiral moves

---

### **3. Create Git Tag & Release (3 minutes)**

```powershell
cd "c:\Users\thepr\Downloads\Luthiers ToolBox"

# Review changes
git status

# Commit if needed
git add .
git commit -m "N18: Complete Phase 4 validation suite and documentation"

# Create release tag
.\scripts\release_n18_tag_and_notes.ps1

# Review tag
git tag -l "v0.18.0*"
git show v0.18.0-n18_spiral_poly

# Push tag to remote
.\scripts\release_n18_tag_and_notes.ps1 -Push
```

**Pass Criteria:**
- [ ] Working tree clean (no uncommitted changes)
- [ ] Tag created successfully
- [ ] Tag contains release notes
- [ ] Tag pushed to origin

---

### **4. Create GitHub Release (2 minutes)**

1. Go to: `https://github.com/YOUR_USERNAME/luthiers-toolbox/releases`
2. Click **"Draft a new release"**
3. **Choose tag:** `v0.18.0-n18_spiral_poly`
4. **Release title:** `N.18 – Spiral PolyCut`
5. **Description:** Copy from `docs/releases/N18_SPIRAL_POLYCUT_RELEASE_NOTES.md`
6. Click **"Publish release"**

**Pass Criteria:**
- [ ] Release visible on GitHub
- [ ] Release notes formatted correctly
- [ ] Tag shows in releases list

---

## 📋 Post-Deployment Verification

### **5. Smoke Test Real Geometry (5 minutes)**

Test with actual guitar part geometry:

```powershell
# Create test geometry (bridge slot)
$bridgeSlot = @"
{
  "units": "mm",
  "paths": [
    {
      "type": "closed",
      "points": [
        [0, 0], [140, 0], [140, 18], [0, 18]
      ]
    }
  ]
}
"@

$bridgeSlot | Out-File bridge_slot.json

# Generate G-code
curl -X POST http://localhost:8000/cam/adaptive3/offset_spiral.nc `
  -H 'Content-Type: application/json' `
  -d "@bridge_slot.json" `
  -d '{"tool_d":3.175,"stepover":0.4,"margin":0.3,"corner_radius_min":0.8,"climb":true,"feed_xy":800}' `
  -o bridge_slot.nc

# Verify output
type bridge_slot.nc
```

**Pass Criteria:**
- [ ] G-code generated without errors
- [ ] Toolpath fits within 140×18mm boundary
- [ ] Feed rates correct (800 mm/min)
- [ ] Safe Z movements present

---

### **6. CNC Air Cut Test (Optional - 10 minutes)**

If CNC machine available:

1. **Load G-code:** Import `bridge_slot.nc` into CNC controller
2. **Set work zero:** Position tool at X0 Y0 Z0
3. **Run air cut:** Execute program with Z +10mm above work
4. **Observe:**
   - Tool follows spiral path
   - No unexpected rapids
   - Feed rates consistent

**Pass Criteria:**
- [ ] Program runs without errors
- [ ] Toolpath matches expected spiral
- [ ] No collisions or unexpected moves

---

## 📊 Success Metrics

### **Performance Targets**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Small Rect (100×60mm) | < 5ms | ____ ms | ⏳ |
| Bridge Slot (140×18mm) | < 4ms | ____ ms | ⏳ |
| Thin Strip (200×12mm) | < 3ms | ____ ms | ⏳ |
| Validation Pass Rate | 100% | ____ % | ⏳ |
| Pytest Pass Rate | 100% | ____ % | ⏳ |

### **Quality Gates**

- [ ] All validation tests pass
- [ ] All pytest tests pass
- [ ] Benchmark times within targets
- [ ] Endpoint returns valid G-code
- [ ] Git tag created and pushed
- [ ] GitHub release published
- [ ] Documentation complete and accessible

---

## 🎯 Rollback Plan

If deployment fails:

```powershell
# Remove tag locally
git tag -d v0.18.0-n18_spiral_poly

# Remove tag from remote
git push origin :refs/tags/v0.18.0-n18_spiral_poly

# Revert commits if needed
git revert HEAD~1

# Delete GitHub release
# (Manually via GitHub UI)
```

---

## 📞 Support Contacts

**Issues Found?**
1. Check `docs/releases/N18_SPIRAL_POLYCUT_RELEASE_NOTES.md` Section 8 (Troubleshooting)
2. Review `N18_SPIRAL_POLYCUT_QUICKREF.md` for configuration guidance
3. Run validation scripts to isolate issue

**Common Issues:**
- **Import Error:** `pip install pyclipper==1.3.0.post5`
- **Validation Fails:** Check baseline file paths exist
- **Endpoint 500:** Check server logs for Python traceback

---

## ✅ Final Sign-Off

**Deployment completed by:** ________________  
**Date:** ________________  
**Time:** ________________

**Validation Results:**
- Tests passed: ____ / 5
- Benchmarks: ✅ / ❌
- Endpoint: ✅ / ❌
- Git tag: ✅ / ❌
- GitHub release: ✅ / ❌

**Production Status:** ✅ APPROVED / ❌ NEEDS REVIEW

**Notes:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

---

**Next Steps:**
- [ ] Integrate N18 into AdaptiveKernelLab.vue UI
- [ ] Test with real guitar body DXF files
- [ ] Add G2/G3 arc emission (Phase 5)
- [ ] Multi-pass depth support (Phase 6)
- [ ] Real-time canvas preview (Phase 7)

---

**Deployment Checklist Version:** 1.0  
**Last Updated:** November 5, 2025
