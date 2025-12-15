# Final Integration Test Checklist - Unified Preset System

**Test Date:** ______________  
**Tester:** ______________  
**Environment:** ______________  
**Status:** 🎯 Ready for Testing

---

## 🎯 Pre-Test Setup

- [ ] Backend API running: `uvicorn app.main:app --reload --port 8000`
- [ ] Frontend dev server running: `npm run dev` (port 5173)
- [ ] Browser DevTools open (F12)
- [ ] Clear localStorage: `localStorage.clear()` in console
- [ ] Create test presets using `test_b19_clone.ps1`

---

## ✅ Test Suite 1: Core Preset System (Phase 1)

### **1.1 Preset Hub Navigation**
- [ ] Navigate to Preset Hub (verify URL)
- [ ] All 5 tabs visible: All, CAM, Export, Neck, Combo
- [ ] Tabs switch correctly
- [ ] No console errors

### **1.2 Preset Creation**
- [ ] Click "New Preset" button
- [ ] Fill form: name, description, kind, tags
- [ ] Submit form
- [ ] Verify preset appears in correct tab
- [ ] Check localStorage for persistence

### **1.3 Preset Editing**
- [ ] Click "Edit" on existing preset
- [ ] Modify name and tags
- [ ] Save changes
- [ ] Verify updates reflected immediately
- [ ] Refresh page, verify persistence

### **1.4 Preset Deletion**
- [ ] Click "Delete" on test preset
- [ ] Confirm deletion dialog
- [ ] Verify preset removed from list
- [ ] Check localStorage cleaned up

### **1.5 Search & Filters**
- [ ] Search by preset name (verify results)
- [ ] Filter by tag (verify results)
- [ ] Clear search (all presets return)
- [ ] Test empty search results message

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 2: Export Integration

### **2.1 Template Engine**
- [ ] Open CompareLabView export dialog
- [ ] Enter template: `{preset}__{date}`
- [ ] Select export format: SVG
- [ ] Verify filename preview updates
- [ ] Change format to PNG, verify preview changes

### **2.2 Preset Selector**
- [ ] Export preset dropdown loads
- [ ] Select export preset
- [ ] Verify template populates from preset
- [ ] Test "Use custom template" option

### **2.3 Neck Context Detection**
- [ ] Navigate from NeckLab with profile context
- [ ] Open export dialog
- [ ] Verify blue badge: "Neck context detected"
- [ ] Check tokens {neck_profile} and {neck_section} work
- [ ] Navigate without context, verify amber warning

### **2.4 Template Validation**
- [ ] Enter invalid template: `{invalid_token}`
- [ ] Verify red error message appears
- [ ] Enter valid template
- [ ] Verify green "✓ Valid template" message

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 3: B19 Clone as Preset

### **3.1 Clone from JobLog**
- [ ] Run CAM job in JobInt
- [ ] Open JobLog view
- [ ] Click "Clone as Preset" button
- [ ] Verify modal opens with pre-filled data
- [ ] Submit form
- [ ] Verify preset created with `job_source_id`

### **3.2 Job Lineage**
- [ ] Find cloned preset in Preset Hub
- [ ] Verify job source badge visible
- [ ] Click job source link
- [ ] Verify navigates to JobInt detail
- [ ] Check preset includes job metrics

### **3.3 Performance Metrics**
- [ ] Cloned preset shows sim_time_s
- [ ] Cloned preset shows energy_j
- [ ] Cloned preset shows move_count
- [ ] Metrics match source job exactly

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 4: B20 Enhanced Tooltips

### **4.1 Preset Card Tooltips**
- [ ] Hover over preset card
- [ ] Tooltip shows job metrics (if lineage exists)
- [ ] Tooltip shows preset description
- [ ] Tooltip shows creation date
- [ ] Tooltip disappears on mouse leave

### **4.2 Smart Suggestions**
- [ ] Find preset with job lineage
- [ ] Verify "🏆 From successful job" badge
- [ ] Find preset without lineage
- [ ] Verify different styling (no badge)

### **4.3 Context Badges**
- [ ] Preset with CAM params shows "CAM" badge
- [ ] Preset with neck params shows "Neck" badge
- [ ] Preset with both shows "Combo" badge
- [ ] Badge colors correct (green/blue/purple)

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 5: NeckLab Preset Loading

### **5.1 Preset Selector**
- [ ] Open NeckLab view
- [ ] Preset dropdown loads neck presets
- [ ] Select preset
- [ ] Verify profile_id loads
- [ ] Verify scale_length_mm loads
- [ ] Verify section_defaults load

### **5.2 Quick Action**
- [ ] Go to Preset Hub
- [ ] Find neck preset
- [ ] Click "Use in NeckLab" button
- [ ] Verify navigates to NeckLab
- [ ] Verify preset auto-loads
- [ ] Verify parameters applied

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 6: CompareLab Preset Integration

### **6.1 Baseline/Candidate Selection**
- [ ] Open CompareLab
- [ ] Baseline preset dropdown loads
- [ ] Select baseline preset
- [ ] Candidate preset dropdown loads
- [ ] Select candidate preset
- [ ] Run comparison

### **6.2 Save Comparison as Preset**
- [ ] After comparison, click "Save as Preset"
- [ ] Modal opens with diff results
- [ ] Enter preset name
- [ ] Select kind: "combo"
- [ ] Submit form
- [ ] Verify preset created with diff data

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 7: B21 Multi-Run Comparison

### **7.1 Route Navigation**
- [ ] Navigate to `/lab/compare-runs`
- [ ] Component loads without 404
- [ ] Page title: "Multi-Run Comparison"
- [ ] No console errors

### **7.2 Preset Selection**
- [ ] Only presets with job lineage show
- [ ] Select 1 preset → button disabled
- [ ] Select 2 presets → button enabled
- [ ] Counter shows "2 presets selected"
- [ ] Clear selection button works

### **7.3 Run Comparison**
- [ ] Select 3 presets
- [ ] Click "Compare Runs" button
- [ ] Loading spinner appears
- [ ] Results display:
  - [ ] 4 summary cards (Runs, Avg Time, Avg Energy, Avg Moves)
  - [ ] Trend badges (green/red/gray)
  - [ ] Recommendations panel
  - [ ] Comparison table (8 columns)
  - [ ] Best run highlighted green 🏆
  - [ ] Worst run highlighted red ⚠️

### **7.4 Chart.js Bar Chart**
- [ ] Chart renders below table
- [ ] Y-axis: "Time (seconds)"
- [ ] 3 bars visible (one per preset)
- [ ] Best run: green bar
- [ ] Worst run: red bar
- [ ] Others: blue bars
- [ ] Hover shows tooltip with value
- [ ] Chart responsive to window resize

### **7.5 Efficiency Scores**
- [ ] Each row has progress bar (0-100)
- [ ] Color coding:
  - [ ] Green: ≥70
  - [ ] Yellow: 40-69
  - [ ] Red: <40
- [ ] Score text displays (e.g., "85/100")

### **7.6 CSV Export**
- [ ] Click "📥 Export as CSV" button
- [ ] File downloads (timestamp name)
- [ ] Open CSV in Excel
- [ ] Headers correct (8 columns)
- [ ] 3 data rows (one per preset)
- [ ] Values match table display

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 8: State Persistence (localStorage)

### **8.1 MultiRunComparisonView Persistence**
- [ ] Select 2 presets
- [ ] Run comparison
- [ ] Open DevTools → Application → Local Storage
- [ ] Verify keys exist:
  - [ ] `multirun.selectedPresets` (array of IDs)
  - [ ] `multirun.lastComparison` (full result object)
  - [ ] `multirun.lastUpdated` (Unix timestamp)
- [ ] Refresh page (F5)
- [ ] Verify checkboxes re-checked
- [ ] Verify comparison table/chart restored
- [ ] Verify NO API call made (cached)

### **8.2 MultiRunComparisonView Reset**
- [ ] Click "🔄 New Comparison" button
- [ ] Verify results cleared
- [ ] Verify checkboxes unchecked
- [ ] Check localStorage keys removed (all 3)
- [ ] No errors in console

### **8.3 PresetHubView Persistence**
- [ ] Change active tab to "CAM"
- [ ] Enter search query: "test"
- [ ] Select tag filter: "production"
- [ ] Refresh page (F5)
- [ ] Verify tab restored: "CAM"
- [ ] Verify search restored: "test"
- [ ] Verify tag restored: "production"
- [ ] Check localStorage keys:
  - [ ] `presethub.activeTab` = "cam"
  - [ ] `presethub.searchQuery` = "test"
  - [ ] `presethub.selectedTag` = "production"

### **8.4 CompareLabView Persistence**
- [ ] Open export dialog
- [ ] Select export preset
- [ ] Enter filename template: `custom_{date}`
- [ ] Select format: PNG
- [ ] Refresh page (F5)
- [ ] Open export dialog again
- [ ] Verify preset restored
- [ ] Verify template restored: `custom_{date}`
- [ ] Verify format restored: PNG
- [ ] Check localStorage keys:
  - [ ] `comparelab.selectedPresetId` (preset ID)
  - [ ] `comparelab.filenameTemplate` ("custom_{date}")
  - [ ] `comparelab.exportFormat` ("png")

### **8.5 Edge Case: Corrupted JSON**
- [ ] Open DevTools → Console
- [ ] Run: `localStorage.setItem('multirun.lastComparison', 'invalid json')`
- [ ] Refresh page
- [ ] Verify NO crash (graceful error handling)
- [ ] Verify corrupted key cleared automatically
- [ ] Check console for error message (not user-facing)

### **8.6 Edge Case: Stale Data (24h TTL)**
- [ ] Open DevTools → Console
- [ ] Run: `localStorage.setItem('multirun.lastUpdated', Date.now() - 25*60*60*1000)` (25 hours ago)
- [ ] Refresh page
- [ ] Verify stale data NOT loaded
- [ ] Verify keys cleared automatically
- [ ] No errors in console

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 9: Extension Validation

### **9.1 Scenario: SVG Template, PNG Format**
- [ ] Open CompareLabView export dialog
- [ ] Set template: `{preset}__{date}.svg`
- [ ] Select format: PNG
- [ ] Verify ⚠️ warning appears:
  - [ ] Amber background, orange border
  - [ ] Message: "Template has .svg extension but export format is PNG"
  - [ ] Two buttons visible
- [ ] Click "Fix Template → .png"
- [ ] Verify template changes to: `{preset}__{date}.png`
- [ ] Verify warning disappears

### **9.2 Scenario: PNG Template, SVG Format**
- [ ] Set template: `comparison_{timestamp}.png`
- [ ] Select format: SVG
- [ ] Verify ⚠️ warning appears
- [ ] Click "Fix Format → PNG"
- [ ] Verify format changes to: PNG
- [ ] Verify warning disappears

### **9.3 Scenario: CSV Template, SVG Format**
- [ ] Set template: `metrics_{date}.csv`
- [ ] Select format: SVG
- [ ] Verify ⚠️ warning appears
- [ ] Test "Fix Template" button → template becomes `.svg`
- [ ] Reset template to `.csv`
- [ ] Test "Fix Format" button → format becomes CSV
- [ ] Verify both fixes work

### **9.4 Scenario: No Extension (Valid)**
- [ ] Set template: `{preset}_comparison` (no extension)
- [ ] Select format: PNG
- [ ] Verify NO warning (no extension = OK)
- [ ] Check filename preview: should show `.png` appended

### **9.5 Scenario: Matching Extension (Valid)**
- [ ] Set template: `output.svg`
- [ ] Select format: SVG
- [ ] Verify NO warning (match = OK)

### **9.6 Scenario: Unsupported Extension**
- [ ] Set template: `file.dxf`
- [ ] Select format: SVG
- [ ] Verify ⚠️ warning appears (.dxf != svg)
- [ ] Click "Fix Template → .svg"
- [ ] Verify template changes to: `file.svg`
- [ ] Verify warning disappears

### **9.7 Edge Case: Multiple Dots**
- [ ] Set template: `my.file.name.svg`
- [ ] Select format: PNG
- [ ] Verify warning detects `.svg` (last extension wins)
- [ ] Fix and verify

### **9.8 Edge Case: Extension in Token**
- [ ] Set template: `{preset.svg}__{date}` (extension inside braces)
- [ ] Select format: PNG
- [ ] Verify NO warning (token ignored)
- [ ] Filename preview should show `.png` appended

### **9.9 Edge Case: Case Insensitivity**
- [ ] Set template: `output.SVG` (uppercase)
- [ ] Select format: svg (lowercase)
- [ ] Verify NO warning (case insensitive match)

### **9.10 localStorage Persistence**
- [ ] Set template: `test.svg` with format PNG (mismatch)
- [ ] Click "Fix Template → .png"
- [ ] Refresh page (F5)
- [ ] Verify template restored: `test.png`
- [ ] Verify format restored: PNG
- [ ] Verify NO warning (fix persisted)

### **9.11 Filename Preview Correctness**
- [ ] Set template: `test_{date}` (no extension)
- [ ] Select format: SVG
- [ ] Preview should show: `test_2025-11-28.svg`
- [ ] Change format to PNG
- [ ] Preview should show: `test_2025-11-28.png`
- [ ] Verify extension ALWAYS matches selected format

### **9.12 Actual Export**
- [ ] Set template with mismatch: `output.svg`
- [ ] Select format: PNG
- [ ] Fix warning (either button)
- [ ] Run comparison
- [ ] Click "Export" button
- [ ] Verify downloaded file has `.png` extension
- [ ] Open file, verify it's valid PNG

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## ✅ Test Suite 10: Unit Conversion & Validation

### **10.1 Template Validation API**
- [ ] Open DevTools → Network tab
- [ ] Enter template in CompareLabView
- [ ] Verify POST to `/api/presets/validate-template`
- [ ] Check response: `{valid: true}` or `{valid: false, warnings: [...]}`

### **10.2 Filename Resolution API**
- [ ] Export a file
- [ ] Check Network tab for POST to `/api/presets/resolve-filename`
- [ ] Verify request includes context (preset, date, etc.)
- [ ] Verify response contains resolved filename

### **10.3 Unit Conversion**
- [ ] Create preset with mm values
- [ ] Export using inch template
- [ ] Verify conversion applied correctly
- [ ] (This may be edge case, verify if implemented)

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________________

---

## 📊 Final Test Summary

| Test Suite | Status | Pass/Fail | Notes |
|------------|--------|-----------|-------|
| 1. Core Preset System | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 2. Export Integration | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 3. B19 Clone as Preset | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 4. B20 Enhanced Tooltips | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 5. NeckLab Preset Loading | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 6. CompareLab Integration | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 7. B21 Multi-Run Comparison | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 8. State Persistence | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 9. Extension Validation | ⬜ Pass / ⬜ Fail | __/__ | __________ |
| 10. Unit Conversion | ⬜ Pass / ⬜ Fail | __/__ | __________ |

**Overall Result:** ⬜ ALL PASS / ⬜ SOME FAILURES  
**Production Ready:** ⬜ YES / ⬜ NO (see issues below)

---

## 🐛 Issues Found

| Issue # | Description | Severity | Suite | Reproduction Steps |
|---------|-------------|----------|-------|-------------------|
| 1 | | ⬜ Critical / ⬜ Major / ⬜ Minor | __ | _______________ |
| 2 | | ⬜ Critical / ⬜ Major / ⬜ Minor | __ | _______________ |
| 3 | | ⬜ Critical / ⬜ Major / ⬜ Minor | __ | _______________ |

---

## ✅ Sign-Off

**Tester Signature:** _____________________  
**Date:** _____________________  
**Status:** ⬜ APPROVED FOR PRODUCTION / ⬜ REQUIRES FIXES

**Notes:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

---

## 📚 Reference Documentation

- [UNIFIED_PRESET_INTEGRATION_STATUS.md](./UNIFIED_PRESET_INTEGRATION_STATUS.md) - Overall status
- [PROJECT_COMPLETE_SUMMARY.md](./PROJECT_COMPLETE_SUMMARY.md) - Completion summary
- [B21_INTEGRATION_TEST_GUIDE.md](./B21_INTEGRATION_TEST_GUIDE.md) - B21 specific tests
- [STATE_PERSISTENCE_QUICKREF.md](./STATE_PERSISTENCE_QUICKREF.md) - localStorage docs
- [EXTENSION_VALIDATION_QUICKREF.md](./EXTENSION_VALIDATION_QUICKREF.md) - Extension validation docs

---

**Total Test Items:** 120+  
**Estimated Testing Time:** 4-6 hours  
**Last Updated:** November 28, 2025
