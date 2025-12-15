# CNC Saw Lab - What's Missing (Simple Visual Guide)

**Date:** November 28, 2025

---

## 🎯 The Big Picture

The documentation describes **8 complete systems**.  
The code has **3 partial systems**.

**Reality Check:** Only 30-40% of what's documented actually exists in the repository.

---

## 📦 What You HAVE vs What's MISSING

### **System 1: Feeds & Speeds Learning** 
**Status: 40% Complete** 🟨

```
✅ YOU HAVE:
   - Basic feeds/speeds API
   - Configuration files
   - Generic resolver

❌ YOU'RE MISSING:
   - learned_overrides.py (stores what the system learned)
   - preset_promotion.py (promotes successful runs)
   - overlay_store.py (applies learned adjustments)
   - promotion_audit.py (tracks changes over time)
   - Machine-specific lane tracking
```

**What This Means:**  
Your system can calculate speeds/feeds, but it **cannot learn** from successful runs or remember machine-specific adjustments.

---

### **System 2: Saw Operations (Cut Types)**
**Status: 60% Complete** 🟨

```
✅ YOU HAVE:
   - Generic operations.py
   - Basic G-code generator
   - SawLabView (main UI)
   - Queue panel
   - Diff panel

❌ YOU'RE MISSING:
   - SawSlicePanel.vue (straight cuts)
   - SawBatchPanel.vue (multiple cuts at once)
   - SawContourPanel.vue (curved cuts for rosettes)
   - Geometry engines (curve_engine.py, offset_engine.py)
   - G-code preview with visual overlay
   - "Send to JobLog" button
```

**What This Means:**  
You have a shell UI, but **no specialized panels** for different cut types. Users can't create slice, batch, or contour operations.

---

### **System 3: Machine Profiles**
**Status: 50% Complete** 🟨

```
✅ YOU HAVE:
   - Generic machine profile system
   - Profile store in TypeScript

❌ YOU'RE MISSING:
   - Saw-specific machine profiles:
     • bcam_router_2030
     • syil_x7
     • manual_saw_rig
   - Per-machine lane learning
   - Badge generation (promoted presets)
```

**What This Means:**  
You have a generic machine system, but **no saw-specific machines** configured. Can't track which machine performed which cut.

---

### **System 4: Vendor Tool Data**
**Status: 0% Complete** 🟥

```
❌ COMPLETELY MISSING:
   - vendor_tools/ directory (manufacturer data)
   - SpeedsFeedsDashboard.vue (comparison widget)
   - Vendor dataset loader
   - Chipload calculations
   - Safety range warnings
```

**What This Means:**  
You **cannot compare** your settings with manufacturer recommendations. No warnings if speeds/feeds are unsafe.

---

### **System 5: Saw Blade Registry**
**Status: 20% Complete** 🟥

```
✅ YOU HAVE:
   - pdf_saw_blade_importer.py (PDF reader - COMPLETE!)
   - CP-S63 documentation

❌ YOU'RE MISSING:
   - saw_blade_registry.py (database of blades)
   - saw_blade_validator.py (safety checks)
   - blade_browser.vue (UI to pick blades)
   - saw_blades.json (stored blade data)
```

**What This Means:**  
You have a **perfect PDF importer** but nowhere to save the data! The importer has a TODO comment: `# TODO: Integrate with CP-S50 saw_blade_registry.py` — that file doesn't exist.

**This is the BIGGEST gap:** A complete feature that's orphaned.

---

### **System 6: JobLog + Telemetry**
**Status: 15% Complete** 🟥

```
✅ YOU HAVE:
   - Generic joblog structure

❌ YOU'RE MISSING:
   - saw_joblog_models.py (saw-specific job data)
   - saw_telemetry_router.py (data collector)
   - Telemetry fields:
     • saw_rpm (actual spindle speed)
     • feed_ipm (actual feed rate)
     • spindle_load_pct (motor load)
     • vibration_rms (blade vibration)
     • sound_db (noise level)
   - Live learn ingestor (analyzes telemetry)
```

**What This Means:**  
You **cannot track** what actually happened during a cut. No way to know if the blade vibrated, if the motor struggled, or if the cut was smooth.

---

### **System 7: Live Learn Dashboard**
**Status: 25% Complete** 🟥

```
✅ YOU HAVE:
   - saw_live_learn_dashboard.py (file exists)

❌ YOU'RE MISSING:
   - risk_buckets.py (classifies risk: green/yellow/orange/red)
   - Dashboard router (API endpoints)
   - SawLiveLearnDashboard.vue (UI)
   - Risk Actions panel (fix problems button)
   - Recent runs table
   - Lane scale history
```

**What This Means:**  
A file exists but it's unclear what it does. Even if it works, there's **no UI** to see it and **no data** to display (because telemetry is missing).

---

### **System 8: PDF OCR Importer**
**Status: 70% Complete** 🟨

```
✅ YOU HAVE:
   - pdf_saw_blade_importer.py (COMPLETE - 451 lines!)
   - Full documentation
   - Command-line usage

❌ YOU'RE MISSING:
   - UI "Import Blade PDF" button
   - Integration with registry (marked TODO in code)
   - Helper script in scripts/ folder
```

**What This Means:**  
The **importer works perfectly** via command line, but there's no UI button and nowhere to save the results.

---

## 🚨 The Critical Problems

### **Problem #1: The Orphaned PDF Importer**
```
Status: COMPLETE CODE, NO INTEGRATION

File: services/api/app/cam_core/saw_lab/importers/pdf_saw_blade_importer.py
Lines: 451 (fully functional)
Issue: Line 383 has comment "# TODO: Integrate with CP-S50 saw_blade_registry.py"
Reality: saw_blade_registry.py DOES NOT EXIST

Impact: You can import blade specs from PDFs but nowhere to store them.
```

### **Problem #2: The Disconnected Telemetry**
```
Status: NO DATA PIPELINE

Have: Generic joblog
Missing: Saw-specific telemetry collection
Missing: Live learn analysis
Missing: Dashboard to view results

Impact: System cannot learn from production runs.
```

### **Problem #3: The Missing Operation Panels**
```
Status: SHELL ONLY, NO CONTENT

Have: SawLabView.vue (main container)
Have: SawLabShell.vue (UI skeleton)
Missing: SawSlicePanel (straight cuts)
Missing: SawBatchPanel (batch cuts)
Missing: SawContourPanel (curved cuts)

Impact: Users see empty panels, cannot create operations.
```

### **Problem #4: The Broken Learning Loop**
```
Status: CANNOT LEARN

Missing: learned_overrides storage
Missing: Lane-specific tracking  
Missing: Promotion system
Missing: Telemetry to analyze

Impact: System makes same mistakes repeatedly, cannot improve.
```

---

## 📊 Visual File Count

**Documentation Says You Should Have:**
```
Backend Python Files:  ~35 files
Frontend Vue Files:    ~15 files
Data Files:            ~10 files
Total:                 ~60 files
```

**You Actually Have:**
```
Backend Python Files:  ~12 files (34% of expected)
Frontend Vue Files:    ~5 files (33% of expected)
Data Files:            ~0 files (0% of expected)
Total:                 ~17 files (28% of expected)
```

**Missing:** ~43 files (72% of documented system)

---

## 🎯 What Should Exist vs What Actually Exists

### **Critical Files That Should Exist:**

| File Path | Status | Priority |
|-----------|--------|----------|
| `saw_blade_registry.py` | ❌ MISSING | 🔴 CRITICAL |
| `saw_blade_validator.py` | ❌ MISSING | 🔴 CRITICAL |
| `learned_overrides.py` | ❌ MISSING | 🔴 CRITICAL |
| `saw_joblog_models.py` | ❌ MISSING | 🔴 CRITICAL |
| `saw_telemetry_router.py` | ❌ MISSING | 🔴 CRITICAL |
| `SawSlicePanel.vue` | ❌ MISSING | 🟠 HIGH |
| `SawBatchPanel.vue` | ❌ MISSING | 🟠 HIGH |
| `SawContourPanel.vue` | ❌ MISSING | 🟠 HIGH |
| `risk_buckets.py` | ❌ MISSING | 🟠 HIGH |
| `curve_engine.py` | ❌ MISSING | 🟠 HIGH |
| `offset_engine.py` | ❌ MISSING | 🟠 HIGH |

### **Files That Actually Exist:**

| File Path | Status | Notes |
|-----------|--------|-------|
| `pdf_saw_blade_importer.py` | ✅ EXISTS | Complete but orphaned |
| `saw_gcode_generator.py` | ✅ EXISTS | Basic functionality |
| `operations.py` | ✅ EXISTS | Generic only |
| `SawLabView.vue` | ✅ EXISTS | Shell UI |
| `SawLabShell.vue` | ✅ EXISTS | Container |
| `SawLabQueuePanel.vue` | ✅ EXISTS | Queue display |
| `SawLabDiffPanel.vue` | ✅ EXISTS | Diff display |
| `saw_live_learn_dashboard.py` | ✅ EXISTS | Unknown functionality |

---

## 💡 Simple Explanation

**Imagine building a car:**

Your **documentation** describes:
- Engine ✅ (exists but basic)
- Transmission ❌ (missing)
- Wheels ✅ (exists but no steering)
- Steering wheel ❌ (missing)
- Dashboard ❌ (partially exists)
- Seats ✅ (exists)
- GPS system ✅ (complete but not connected)
- Airbags ❌ (missing)

**Result:** You have a car frame with seats and a GPS sitting in the trunk. The GPS works perfectly but it's not installed in the dashboard. The engine runs but there's no transmission to make the wheels turn. You can sit in it, but you can't drive it.

**That's your CNC Saw Lab.**

---

## 🔧 What Needs to Happen

### **Step 1: Wire the GPS (Blade Importer)**
Create `saw_blade_registry.py` so the PDF importer has somewhere to save data.

### **Step 2: Install the Transmission (Telemetry Pipeline)**
Create saw-specific telemetry so the system can track what happens during cuts.

### **Step 3: Add Steering Wheel (Operation Panels)**
Create SawSlicePanel, SawBatchPanel, SawContourPanel so users can actually make cuts.

### **Step 4: Install Dashboard (Live Learn UI)**
Wire up the dashboard so users can see learned data and risk analysis.

### **Step 5: Add Airbags (Validators)**
Create blade validator to prevent unsafe operations.

---

## 📈 Progress to Production

```
Current State:     [████░░░░░░░░░░░░░░░░] 30%
Minimal Viable:    [████████░░░░░░░░░░░░] 60% needed
Production Ready:  [████████████████████] 100% target
```

**To reach Minimal Viable (60%), you need:**
1. ✅ Blade registry + validator (System 5)
2. ✅ Saw operation panels (System 2)
3. ✅ Basic telemetry collection (System 6)

**To reach Production Ready (100%), you need:**
4. ✅ Full learning pipeline (System 1)
5. ✅ Risk management dashboard (System 7)
6. ✅ Vendor data integration (System 4)
7. ✅ Machine-specific tracking (System 3)

---

## 🎯 Bottom Line

**You have:**
- A beautiful foundation (30% complete)
- One perfect feature that's disconnected (PDF importer)
- Several partial systems

**You're missing:**
- 70% of documented functionality
- Critical integration points
- Most specialized components

**The gap is large but the path is clear.**

---

**Next Question:** Do you want to:
1. **Update documentation** to match current code (delete 70% of docs)
2. **Build missing components** to match documentation (add 70% of features)
3. **Hybrid approach** (keep some docs, remove unrealistic ones, implement critical gaps)

I recommend **option 3**: Focus on the 5 critical files first, then reassess.
