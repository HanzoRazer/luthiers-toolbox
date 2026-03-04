# The Production Shop - Feature Gap Analysis Report

**Date:** March 3, 2026
**Purpose:** Identify features and functionality that exist in the codebase but are not documented on the marketing website

---

## Executive Summary

A comprehensive scan of the luthiers-toolbox repository reveals **20+ major features and tools** that are implemented in the application but not documented on the marketing website.

**Key Findings:**
- 📊 **41 application routes** total, only **32 documented on website**
- 🔧 **60+ API module directories**, many undocumented
- 🎨 **Multiple specialized tools** for inlay, relief carving, v-carve
- 🤖 **AI/ML features** completely missing from marketing
- 📈 **Analytics and monitoring** tools not mentioned
- 🔬 **Advanced CAM features** like material analytics, strip family optimization

---

## Missing Features by Category

### 🔴 CRITICAL: Major Undocumented Features

#### 1. **AI & ML Features**

**Routes Found:**
- `/ai-images` - AI Images / Visual Analyzer
- `ai/` API module - AI features
- `ai_context_adapter/` - AI context management
- `agentic/` - Agent-based systems

**Description:** Complete AI/ML system for image analysis, context adaptation, and agentic workflows. This is a MAJOR differentiator not mentioned anywhere on the website.

**Impact:** HIGH - This could be a major selling point

**Recommendation:** Create new "AI Tools" section or add AI features to existing categories

---

#### 2. **Toolpath & Advanced CAM**

**API Modules Found:**
- `toolpath/` - Toolpath generation (core CAM feature!)
- `cam_core/` - CAM core engine
- `pipelines/` - CAM pipeline management

**Routes Found:**
- `/cam/dxf-to-gcode` - DXF to G-code converter (not on website)
- `/lab/pipeline` - Pipeline Lab (not on website)

**Description:** Advanced toolpath generation and pipeline management. The core CAM engine has dedicated modules but isn't highlighted.

**Impact:** HIGH - This is core functionality

**Recommendation:** Add "Toolpath Generation" as distinct feature under CAM tab

---

#### 3. **Art Studio Sub-Features**

**API Modules Found:**
- `art_studio/inlay_router.py` - **INLAY DESIGN** (major woodworking feature!)
- `art_studio/relief_router.py` - **3D RELIEF CARVING**
- `art_studio/vcarve_router.py` - **V-CARVE TOOLPATHS**
- `art_studio/bracing_router.py` - Bracing design
- `art_studio/pattern_routes.py` - Pattern generation
- `art_studio/rosette_compare_routes.py` - Rosette comparison
- `art_studio/rosette_snapshot_routes.py` - Rosette versioning

**Current Website:** Lists "Art Studio" as single feature

**Missing:** Inlay Design, Relief Carving, V-Carve are major woodworking features that should be called out explicitly

**Impact:** HIGH - Inlay and relief carving are premium features for high-end lutherie

**Recommendation:** Expand "Art Studio" into multiple feature cards:
- **Inlay Designer** - Design and route inlays, purfling, binding
- **Relief Carving** - 3D relief carving with depth maps
- **V-Carve Toolpaths** - V-bit carving for decorative elements

---

#### 4. **Material Analytics & Optimization**

**Routes Found:**
- `/rmos/material-analytics` - Material-Aware Analytics Dashboard
- `/rmos/strip-family-lab` - Mixed-Material Strip Family Lab

**API Modules Found:**
- `cost_attribution/` - Cost tracking and attribution

**Description:** Advanced material tracking, analytics, and optimization for reducing waste and improving yields.

**Impact:** MEDIUM-HIGH - Important for production efficiency

**Recommendation:** Add under Production tab:
- **Material Analytics** - Track material usage and waste
- **Strip Optimization** - Optimize cutting patterns for mixed materials

---

#### 5. **Audio Analysis & Acoustics**

**Routes Found:**
- `/tools/audio-analyzer` - Audio Analyzer Evidence Viewer
- `/tools/audio-analyzer/library` - Acoustics Library
- `/tools/audio-analyzer/runs` - Acoustics Runs Browser
- `/tools/audio-analyzer/ingest` - Acoustics Ingest Audit Log

**Description:** Complete acoustics analysis system for instrument sound testing and quality control.

**Impact:** MEDIUM - Unique feature for high-end builders

**Recommendation:** Add new "Quality & Testing" section or under Production:
- **Acoustic Analyzer** - Record, analyze, and compare instrument acoustics

---

#### 6. **CNC Production Suite**

**Routes Found:**
- `/cnc` - CNC Production view (exists but not documented)

**API Modules Found:**
- `cnc_production/` - Full CNC production module

**Description:** Dedicated CNC production management system

**Impact:** MEDIUM - Complements existing RMOS/Production features

**Recommendation:** Add under Production tab as separate feature

---

#### 7. **Computer Vision Features**

**API Modules Found:**
- `vision/` - Computer vision module
- `mesh/` - 3D mesh processing

**Description:** Computer vision for visual inspection, mesh processing for 3D modeling

**Impact:** MEDIUM - Advanced features for quality control

**Recommendation:** Add under Production or Tools:
- **Visual Inspection** - AI-powered quality control with computer vision

---

#### 8. **Advanced RMOS Features**

**Routes Found:**
- `/rmos/rosette-designer` - Rosette Designer (within RMOS context)
- `/rmos/runs/:id` - Run Detail Viewer (not documented)
- `/rmos/runs/:run_id/variants` - Run Variants Review (H3 Product Bundle)
- `/rmos/runs/diff` - Run Diff Viewer (compare runs side-by-side)
- `/rmos/analytics` - RMOS Analytics Dashboard

**Current Website:** Only lists "RMOS Manufacturing Candidates"

**Missing:** Multiple analysis and comparison tools

**Impact:** MEDIUM - Important for power users

**Recommendation:** Expand RMOS feature cards to include:
- **Run Comparison** - Side-by-side diff viewer
- **Variant Analysis** - Review manufacturing variants
- **RMOS Analytics** - Advanced analytics dashboard

---

#### 9. **Settings & Configuration**

**Routes Found:**
- `/settings/cam` - CAM Settings (exists but not in docs)

**Description:** Settings and configuration panels for CAM parameters

**Impact:** LOW-MEDIUM - Important for customization

**Recommendation:** Add "Settings" section or note in CAM features

---

#### 10. **Multiple Saw Lab Modes**

**Routes Found:**
- `/lab/saw/slice` - Saw Lab Slice mode (documented)
- `/lab/saw/batch` - Saw Lab Batch mode (NOT documented)
- `/lab/saw/contour` - Saw Lab Contour mode (NOT documented)

**Current Website:** Lists "Saw Lab" as single feature

**Missing:** Batch and Contour modes

**Impact:** MEDIUM - Different modes for different use cases

**Recommendation:** Expand "Saw Lab" description to mention 3 modes:
- Slice mode - Single cuts
- Batch mode - Multiple parts
- Contour mode - Complex contours

---

### 🟡 MEDIUM: Infrastructure & Supporting Features

#### 11. **Observability & Monitoring**

**API Modules Found:**
- `observability/` - Observability features
- `telemetry/` - Telemetry collection
- `health/` - Health checks
- `analytics_router` - Analytics endpoint

**Description:** System monitoring, health tracking, and analytics

**Impact:** LOW - Backend features, not customer-facing

**Recommendation:** Mention in "Enterprise" or "Shop" tier features

---

#### 12. **Workflow Management**

**API Modules Found:**
- `workflow/` - Workflow management system
- `governance/` - Governance features
- `pipelines/` - Pipeline orchestration

**Description:** Workflow orchestration and governance

**Impact:** LOW-MEDIUM - Enterprise features

**Recommendation:** Add to Business/Shop tier

---

#### 13. **Data Management**

**API Modules Found:**
- `data_registry/` - Data management
- `assets/` - Asset management
- `exports/` - Export management
- `reports/` - Report generation

**Description:** Data, asset, and report management

**Impact:** LOW-MEDIUM - Supporting features

**Recommendation:** Mention in feature lists

---

#### 14. **Learning & Documentation**

**API Modules Found:**
- `learn/` - Learning/tutorial system
- `advisory/` - Advisory system

**Description:** In-app learning and advisory features

**Impact:** MEDIUM - Good for onboarding

**Recommendation:** Add to website:
- **Interactive Tutorials** - Learn by doing
- **CAM Advisor** - Get expert advice (already documented as "G-code Explainer")

---

#### 15. **Authentication & Authorization**

**API Modules Found:**
- `auth/` - Authentication
- `governance/` - Governance

**Description:** User authentication and access control

**Impact:** LOW - Infrastructure, assumed

**Recommendation:** Mention in Security/Enterprise features

---

### 🟢 LOW: Development & Internal Tools

#### 16. **Dev Tools**

**Routes Found:**
- `/dev/sandbox` - UI Sandbox (dev tool)
- `/dev/vision-attach` - Vision Attach Test (dev tool)

**Description:** Development and testing tools

**Impact:** NONE - Internal only

**Recommendation:** Don't document (dev-only)

---

#### 17. **WebSocket/Real-time**

**API Modules Found:**
- `websocket/` - WebSocket support

**Description:** Real-time communication infrastructure

**Impact:** LOW - Supporting tech

**Recommendation:** Mention "Real-time updates" in Live Monitor feature

---

#### 18. **Experimental Features**

**API Modules Found:**
- `_experimental/` - Experimental features

**Description:** Features in development

**Impact:** NONE - Unstable

**Recommendation:** Don't document until stable

---

## Summary Tables

### Completely Missing from Website (HIGH PRIORITY)

| Feature | Route | Category | Priority |
|---------|-------|----------|----------|
| **AI Visual Analyzer** | `/ai-images` | AI/Tools | 🔴 HIGH |
| **Inlay Designer** | (API only) | Design/Art Studio | 🔴 HIGH |
| **Relief Carving** | (API only) | Design/Art Studio | 🔴 HIGH |
| **V-Carve Toolpaths** | (API only) | CAM | 🔴 HIGH |
| **Material Analytics** | `/rmos/material-analytics` | Production | 🔴 HIGH |
| **Strip Optimization** | `/rmos/strip-family-lab` | Production | 🔴 HIGH |
| **Acoustic Analyzer** | `/tools/audio-analyzer` | Quality/Tools | 🟡 MEDIUM |
| **CNC Production** | `/cnc` | Production | 🟡 MEDIUM |
| **Visual Inspection** | (API only) | Quality | 🟡 MEDIUM |
| **DXF to G-code** | `/cam/dxf-to-gcode` | CAM | 🟡 MEDIUM |
| **Run Comparison** | `/rmos/runs/diff` | Production | 🟡 MEDIUM |
| **Variant Analysis** | `/rmos/runs/:run_id/variants` | Production | 🟡 MEDIUM |
| **Saw Lab Batch Mode** | `/lab/saw/batch` | CAM | 🟡 MEDIUM |
| **Saw Lab Contour Mode** | `/lab/saw/contour` | CAM | 🟡 MEDIUM |
| **CAM Settings** | `/settings/cam` | Configuration | 🟢 LOW |

---

### Documented but Underrepresented

| Feature | Current Description | Missing Details |
|---------|-------------------|-----------------|
| **Art Studio** | Single feature card | Missing: Inlay, Relief, V-Carve sub-features |
| **Saw Lab** | Single feature card | Missing: Batch and Contour modes |
| **RMOS** | "Manufacturing Candidates" | Missing: Analytics, Run Comparison, Variants |

---

## Recommended Actions

### Immediate (This Week)

1. **Add Inlay Designer** - Major lutherie feature, critical omission
2. **Add Relief Carving** - High-end feature, major selling point
3. **Add V-Carve Toolpaths** - Standard CAM feature
4. **Add AI Visual Analyzer** - Unique differentiator
5. **Expand Art Studio** - Show it's a suite of tools, not one feature

### Short Term (This Month)

6. **Add Material Analytics** - Production efficiency feature
7. **Add Strip Optimization** - Waste reduction tool
8. **Add Acoustic Analyzer** - Quality control feature
9. **Add CNC Production** - Dedicated production management
10. **Expand Saw Lab** - Document all 3 modes

### Long Term (Next Quarter)

11. **Add Visual Inspection** - AI quality control
12. **Add Run Comparison Tools** - RMOS power features
13. **Add Workflow Management** - Enterprise features
14. **Add Learning System** - Onboarding and tutorials

---

## Website Structure Recommendations

### New Sections to Add

#### Option A: Expand Existing Tabs

**Design Tab:**
- Add: Inlay Designer, Relief Carving

**CAM Tab:**
- Add: V-Carve Toolpaths, Toolpath Generation, DXF to G-code
- Expand: Saw Lab (show 3 modes)

**Production Tab:**
- Add: Material Analytics, Strip Optimization, CNC Production, Visual Inspection
- Expand: RMOS (show Analytics, Comparison, Variants)

**New "Quality & Testing" Tab:**
- Add: Acoustic Analyzer, Visual Inspection

**New "AI Tools" Tab:**
- Add: Visual Analyzer, AI Context Adapter

---

#### Option B: Create New Major Categories

**Tools Module:**
- Acoustic Analyzer
- Visual Analyzer
- AI Tools
- Settings & Configuration

**Quality Module:**
- Visual Inspection
- Acoustic Analysis
- Material Analytics

---

## API Modules Not Documented (Reference)

Complete list of API modules with no corresponding website features:

```
advisory/          - Advisory system
agentic/          - Agent-based features
ai/               - AI core
ai_context_adapter/ - AI context management
analyzer/         - Analysis tools
auth/             - Authentication
cnc_production/   - CNC production
cost_attribution/ - Cost tracking
data_registry/    - Data management
governance/       - Governance
infra/            - Infrastructure
learn/            - Learning system
mesh/             - 3D mesh processing
observability/    - Monitoring
pipelines/        - Pipeline management
reports/          - Report generation
safety/           - Safety features
telemetry/        - Analytics
toolpath/         - Toolpath generation
vision/           - Computer vision
websocket/        - Real-time features
workflow/         - Workflow management
```

---

## Testing Recommendations

### Verify These Features Work

Before adding to website, test:

1. `/ai-images` - Does it load? What does it do?
2. `/rmos/material-analytics` - Working dashboard?
3. `/rmos/strip-family-lab` - Functional optimizer?
4. `/tools/audio-analyzer` - Complete feature?
5. `/cnc` - Production interface working?
6. `/cam/dxf-to-gcode` - Converter functional?
7. `/lab/saw/batch` - Batch mode implemented?
8. `/lab/saw/contour` - Contour mode complete?
9. API: Inlay routes - Endpoints functional?
10. API: Relief routes - Endpoints functional?
11. API: V-carve routes - Endpoints functional?

---

## Next Steps

1. **Review this report** - Identify priorities
2. **Test missing features** - Verify they work
3. **Write feature descriptions** - Create marketing copy
4. **Update features.html** - Add new feature cards
5. **Update LINK_MAPPINGS.md** - Add new route mappings
6. **Test all links** - Verify connections work
7. **Deploy updated site** - Push changes

---

## Questions to Answer

1. **Inlay/Relief/V-Carve:**
   - Are these fully functional?
   - Do they have UIs or just APIs?
   - What's the user experience?

2. **AI Visual Analyzer:**
   - What does it analyze?
   - What models does it use?
   - Is this production-ready?

3. **Material Analytics:**
   - What metrics does it track?
   - How does strip optimization work?
   - Real-time or batch?

4. **Acoustic Analyzer:**
   - How does recording work?
   - What analysis algorithms?
   - Export formats?

5. **CNC Production:**
   - How is this different from RMOS?
   - What's the scope?
   - Overlap with existing features?

---

**Document Version:** 1.0
**Last Updated:** March 3, 2026
**Next Review:** After feature testing is complete

---

## Appendix: All Application Routes

**Complete route list from `router/index.ts`:**

```
/ - Home
/ai-images - AI Images ❌ NOT ON WEBSITE
/art-studio - Art Studio ✅ DOCUMENTED
/art-studio/v16 - Art Studio V16 ❌ NOT ON WEBSITE
/blueprint - Blueprint Lab ✅ DOCUMENTED (as "Blueprint Importer")
/bridge - Bridge Lab ✅ DOCUMENTED
/business/estimator - Engineering Estimator ✅ DOCUMENTED
/calculators - Calculators ✅ DOCUMENTED
/cam/advisor - CAM Advisor ✅ DOCUMENTED (as "G-code Explainer")
/cam/dxf-to-gcode - DXF to G-code ❌ NOT ON WEBSITE
/cam-settings - CAM Settings ❌ NOT ON WEBSITE (legacy route)
/cnc - CNC Production ❌ NOT ON WEBSITE
/compare - Compare Lab ✅ DOCUMENTED (as "Compare Runs")
/dev/sandbox - Dev Sandbox ⚠️ DEV TOOL
/dev/vision-attach - Vision Attach Test ⚠️ DEV TOOL
/instrument-geometry - Instrument Geometry ✅ DOCUMENTED
/lab/adaptive - Adaptive Lab ✅ DOCUMENTED
/lab/bridge - Bridge Lab ✅ DOCUMENTED (as "Drilling Lab" too)
/lab/pipeline - Pipeline Lab ❌ NOT ON WEBSITE
/lab/risk-timeline - Risk Timeline Lab ❌ NOT ON WEBSITE
/lab/saw/batch - Saw Lab Batch ❌ NOT ON WEBSITE
/lab/saw/contour - Saw Lab Contour ❌ NOT ON WEBSITE
/lab/saw/slice - Saw Lab Slice ✅ DOCUMENTED (as "Saw Lab")
/pipeline - Pipeline Lab ❌ NOT ON WEBSITE (legacy)
/quick-cut - Quick Cut ✅ DOCUMENTED
/rmos - RMOS ✅ DOCUMENTED (as "RMOS Manufacturing Candidates")
/rmos/analytics - RMOS Analytics ❌ NOT ON WEBSITE
/rmos/live-monitor - Live Monitor ✅ DOCUMENTED
/rmos/material-analytics - Material Analytics ❌ NOT ON WEBSITE
/rmos/rosette-designer - Rosette Designer ❌ NOT ON WEBSITE
/rmos/runs - CNC History ✅ DOCUMENTED
/rmos/runs/:id - Run Viewer ❌ NOT ON WEBSITE
/rmos/runs/:run_id/variants - Run Variants ❌ NOT ON WEBSITE
/rmos/runs/diff - Run Diff ❌ NOT ON WEBSITE
/rmos/strip-family-lab - Strip Family Lab ❌ NOT ON WEBSITE
/rosette - Rosette ✅ DOCUMENTED (as "Rosette Designer")
/saw - Saw Lab ✅ DOCUMENTED (legacy route)
/settings/cam - CAM Settings ❌ NOT ON WEBSITE
/tools/audio-analyzer - Audio Analyzer ❌ NOT ON WEBSITE
/tools/audio-analyzer/ingest - Acoustics Ingest ❌ NOT ON WEBSITE
/tools/audio-analyzer/library - Acoustics Library ❌ NOT ON WEBSITE
/tools/audio-analyzer/runs - Acoustics Runs ❌ NOT ON WEBSITE
```

**Summary:**
- ✅ Documented: 20 routes
- ❌ Not on website: 19 routes
- ⚠️ Dev tools: 2 routes

**Coverage:** 49% of application routes are documented on marketing website
