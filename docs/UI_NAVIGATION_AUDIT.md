# Option B: UI Polish & Navigation - Action Plan

**Start Date:** November 26, 2025  
**Duration:** 3-5 days  
**Goal:** Make all features discoverable, improve navigation flow, add tooltips, fix any UI bugs

---

## 🎯 Current State Analysis

### **Navigation Structure (App.vue)**
**Current:** 5 main buttons only
1. 🎸 Guitar Design Tools
2. 🎨 Art Studio (routes to `/art-studio-dashboard`)
3. ⚙️ CAM Tools (routes to `/cam-dashboard`)
4. 🧮 Calculators
5. 💼 CNC Business

### **Router Has 50+ Routes But Many Are Hidden!**

**Problem:** Users can't discover features because:
1. Main nav only shows 5 buttons
2. Dashboards exist (`/cam-dashboard`, `/art-studio-dashboard`) but users may not find them
3. Many powerful features are buried:
   - Blueprint Lab (`/blueprint-lab`)
   - Adaptive Pocketing Labs (`/lab/adaptive-kernel`)
   - CAM Essentials (`/lab/cam-essentials`)
   - Helical Ramping (`/lab/helical`)
   - Drilling Lab (`/lab/drilling`)
   - Polygon Offset Lab (`/lab/polygon-offset`)
   - And 40+ more routes!

---

## 📊 Feature Inventory (From Router)

### **CAM Production Tools** (13 routes)
- ✅ `/cam` - CAM Production View
- ✅ `/cam-dashboard` - CAM Dashboard (NEW - Re-Forestation Plan)
- `/cam/risk-timeline` - Risk Timeline
- `/cam/risk-timeline-relief` - Risk Timeline Relief
- `/cam/risk-preset-compare` - Risk Preset Side-by-Side
- `/lab/helical` - Helical Ramp Lab
- `/lab/adaptive-kernel` - Adaptive Kernel Lab
- `/lab/adaptive-benchmark` - Adaptive Benchmark Lab
- `/lab/cam-essentials` - CAM Essentials Lab
- `/lab/drilling` - Drilling Lab
- `/lab/polygon-offset` - Polygon Offset Lab
- `/settings/machines` - Machine Manager
- `/settings/posts` - Post Manager

### **Art Studio Tools** (10 routes)
- ✅ `/art-studio-dashboard` - Art Studio Dashboard (NEW - Re-Forestation Plan)
- `/art-studio` - Art Studio Unified
- `/art-studio/cam` - Art Studio CAM Toolbox (N15-N18)
- `/art/headstock` - Headstock Logo Lane
- `/art/relief` - Relief Carving Lane
- `/blueprint-lab` - Blueprint Lab (AI Analysis)
- `/lab/relief` - Relief Kernel Lab
- `/art-studio/rosette` - Rosette MVP
- `/art-studio/rosette-compare` - Rosette Compare
- `/lab/offset` - Offset Lab (Pyclipper Visualizer)

### **Guitar Design Tools** (currently in GuitarDesignHub component)
- Body Outline Generator
- Bracing Calculator
- Archtop Calculator
- Neck Gen
- Scale Length Calculator
- Radius Dish Calculator
- Enhanced Dish Calculator
- Compound Radius Calculator
- Bridge Calculator (`/tools/bridge`)
- Hardware Layout
- Wiring Workbench (`/tools/wiring`)
- Rosette Designer
- Finish Planner (`/tools/finish`)
- Finishing Guide

### **Labs & Utilities** (7 routes)
- `/lab/compare` - Compare Lab
- `/lab/pipeline` - Pipeline Lab
- `/settings/cam` - CAM Settings Hub
- `/guitar-dimensions` - Guitar Parametric Designer
- `/pipeline/preset-runner` - Pipeline Preset Runner
- `/cam/risk-dashboard` - Risk Dashboard Cross-Lab
- DXF Cleaner (component, no route)
- DXF Preflight (component, no route)
- Export Queue (component, no route)

### **Calculators** (in CalculatorHub component)
- Fraction Calculator
- Scientific Calculator
- CNC ROI Calculator
- Business Calculator

### **Business Tools** (in CNCBusinessFinancial component)
- Business Planning
- Pricing Strategy
- Financial Projections

---

## 🚨 Critical Issues Found

### **Issue 1: Discoverability Crisis**
**Problem:** 50+ features, only 5 visible in nav
**Impact:** Users have no idea these features exist
**Solution:** Add secondary navigation or feature discovery panel

### **Issue 2: Dashboard Awareness**
**Problem:** Dashboards exist but aren't prominently advertised
**Impact:** Users may never find `/cam-dashboard` or `/art-studio-dashboard`
**Solution:** Make dashboards the PRIMARY landing for CAM/Art Studio

### **Issue 3: Labs Are Hidden**
**Problem:** 10+ lab routes (`/lab/*`) have no discovery mechanism
**Impact:** Advanced features like Adaptive Kernel, Helical Ramp invisible
**Solution:** Add "Labs" submenu or labs listing page

### **Issue 4: No Tooltips**
**Problem:** No hover hints explaining what features do
**Impact:** Users don't know what "Polygon Offset Lab" or "Risk Timeline Relief" means
**Solution:** Add tooltips to all nav buttons

### **Issue 5: No Breadcrumbs**
**Problem:** Users can't tell where they are in the app
**Impact:** Confusing navigation, can't backtrack easily
**Solution:** Add breadcrumb trail at top of content area

### **Issue 6: Inconsistent Routing**
**Problem:** Some tools use router, some use local state (activeView)
**Impact:** Confusing code, can't bookmark/share URLs for many features
**Solution:** Convert all tools to use router

---

## ✅ Action Items (Priority Order)

### **Day 1: Navigation Enhancement (4-6 hours)**

#### **Task 1.1: Add Secondary Navigation Bar**
**File:** `client/src/App.vue`
**Goal:** Show category submenus when main nav clicked

**Implementation:**
```vue
<nav class="secondary-nav" v-if="activeCategory">
  <button v-for="item in categoryItems" @click="navigate(item)">
    {{ item.label }}
  </button>
</nav>
```

**Items to show:**
- CAM Tools → Show 13 CAM routes
- Art Studio → Show 10 Art Studio routes
- Guitar Design → Show 14 design tools
- Labs → Show 10 lab routes

---

#### **Task 1.2: Add Tooltips to All Buttons**
**File:** `client/src/App.vue`
**Goal:** Explain what each feature does

**Implementation:**
```vue
<button
  v-for="view in views"
  :title="view.description"
  @click="handleNavClick(view)"
>
  {{ view.label }}
</button>
```

**Tooltip Text Examples:**
- "🎸 Guitar Design Tools" → "14 tools across 6 build phases: body, neck, bridge, hardware, rosettes, finishing"
- "⚙️ CAM Tools" → "CNC toolpath generation, helical ramping, adaptive pocketing, drilling, and risk analysis"
- "🎨 Art Studio" → "Blueprint analysis, SVG editing, relief mapping, rosette design, and DXF export"

---

#### **Task 1.3: Add Breadcrumbs**
**File:** `client/src/App.vue`
**Goal:** Show current location

**Implementation:**
```vue
<div class="breadcrumbs">
  <span v-for="(crumb, i) in breadcrumbs" :key="i">
    <router-link v-if="crumb.to" :to="crumb.to">{{ crumb.label }}</router-link>
    <span v-else>{{ crumb.label }}</span>
    <span v-if="i < breadcrumbs.length - 1"> / </span>
  </span>
</div>
```

---

### **Day 2: Dashboard Improvements (3-4 hours)**

#### **Task 2.1: Make Dashboards Primary Landing**
**Files:** 
- `client/src/App.vue` (change routes)
- `client/src/views/CAMDashboard.vue` (enhance)
- `client/src/views/ArtStudioDashboard.vue` (enhance)

**Changes:**
1. Change nav buttons to route directly to dashboards:
   - "⚙️ CAM Tools" → `/cam-dashboard` (not `/cam`)
   - "🎨 Art Studio" → `/art-studio-dashboard` (already correct!)

2. Add "Quick Actions" section to each dashboard
3. Add "Recently Used" tools tracking
4. Add search/filter for tools

---

#### **Task 2.2: Add Feature Discovery Panel**
**File:** `client/src/components/FeatureDiscoveryPanel.vue` (NEW)
**Goal:** Show "Did you know?" hints about hidden features

**Implementation:**
```vue
<template>
  <div class="discovery-panel">
    <h4>💡 Did You Know?</h4>
    <p>{{ currentTip.text }}</p>
    <button @click="navigate(currentTip.route)">Try it now →</button>
  </div>
</template>
```

**Tips to rotate:**
- "Blueprint Lab can analyze guitar photos and generate DXF files automatically!"
- "Adaptive Kernel Lab lets you test pocketing algorithms with real-time visualization"
- "Helical Ramp Lab generates smooth Z-axis ramping for hardwood machining"
- "Compare Lab lets you A/B test different CAM strategies side-by-side"

---

### **Day 3: Labs Discovery (3-4 hours)**

#### **Task 3.1: Create Labs Listing Page**
**File:** `client/src/views/LabsIndex.vue` (NEW)
**Route:** `/labs`

**Content:**
- Grid of all 10 lab tools with descriptions
- Screenshots/previews
- Tags: "Beginner", "Advanced", "Experimental"
- Search/filter

---

#### **Task 3.2: Add "Labs" to Main Nav**
**File:** `client/src/App.vue`

**Add 6th button:**
```typescript
const views = [
  // ... existing 5 buttons
  { id: 'labs', label: '🧪 Labs', category: 'advanced', route: '/labs' }
]
```

---

### **Day 4: Route Consolidation (4-5 hours)**

#### **Task 4.1: Convert All Tools to Router**
**Goal:** Every feature should have a bookmarkable URL

**Files to update:**
- `client/src/components/toolbox/GuitarDesignHub.vue`
- `client/src/components/toolbox/CalculatorHub.vue`
- `client/src/components/toolbox/CNCBusinessFinancial.vue`
- `client/src/components/toolbox/DXFCleaner.vue`
- `client/src/components/toolbox/DxfPreflightValidator.vue`
- `client/src/components/toolbox/ExportQueue.vue`

**New Routes to Add:**
```typescript
// Guitar Design Tools
{ path: '/design/body-outline', component: BodyOutlineGenerator },
{ path: '/design/bracing', component: BracingCalculator },
{ path: '/design/neck-gen', component: NeckGen },
// ... etc for all 14 tools

// Utilities
{ path: '/tools/dxf-cleaner', component: DXFCleaner },
{ path: '/tools/dxf-preflight', component: DxfPreflightValidator },
{ path: '/tools/export-queue', component: ExportQueue },

// Calculators
{ path: '/calc/fraction', component: FractionCalculator },
{ path: '/calc/scientific', component: ScientificCalculator },
{ path: '/calc/roi', component: ROICalculator },
{ path: '/calc/business', component: BusinessCalculator },
```

---

### **Day 5: Polish & Testing (3-4 hours)**

#### **Task 5.1: Add Loading States**
**Goal:** Show spinners/skeletons while components load

**Files:** All view components
**Implementation:** Add `<Suspense>` wrapper with fallback

---

#### **Task 5.2: Add Empty States**
**Goal:** Guide users when no data exists

**Example:** In CAM Production view, if no jobs exist:
```vue
<div class="empty-state">
  <h3>No jobs yet</h3>
  <p>Get started by importing a blueprint or designing a component</p>
  <button @click="$router.push('/blueprint-lab')">Import Blueprint →</button>
  <button @click="$router.push('/design')">Design Tool →</button>
</div>
```

---

#### **Task 5.3: Add Keyboard Shortcuts**
**Goal:** Power users can navigate faster

**Implementation:**
```typescript
// Add to App.vue
onMounted(() => {
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault()
      showCommandPalette.value = true
    }
  })
})
```

**Shortcuts:**
- `Ctrl+K` → Command palette (search all features)
- `Ctrl+1-5` → Main nav buttons
- `Escape` → Close dialogs/panels

---

#### **Task 5.4: Add Quick Search**
**File:** `client/src/components/QuickSearch.vue` (NEW)
**Goal:** Fuzzy search all features (like VS Code Command Palette)

**Features:**
- Search by name: "helical" → Helical Ramp Lab
- Search by category: "lab" → All 10 labs
- Search by keyword: "drilling" → Drilling Lab, CAM Essentials
- Recent items at top
- Keyboard navigation (arrow keys, Enter)

---

#### **Task 5.5: Manual UI Testing Checklist**

**Test Each Route:**
- [ ] All 50+ routes load without errors
- [ ] No console errors
- [ ] Breadcrumbs show correct path
- [ ] Secondary nav highlights active item
- [ ] Tooltips appear on hover
- [ ] Mobile responsive (nav collapses to hamburger menu)
- [ ] Dark mode works (if supported)
- [ ] Browser back button works
- [ ] Bookmarked URLs load correctly
- [ ] Search finds all features

**Test User Flows:**
- [ ] New user can find Blueprint Lab in < 3 clicks
- [ ] User can navigate: Dashboard → Lab → Back to Dashboard
- [ ] User can find any feature using Quick Search in < 5 seconds
- [ ] User understands what each tool does from tooltips
- [ ] User can access 10+ labs without searching documentation

---

## 📊 Success Metrics

**Before:**
- 5 visible features in main nav
- ~50+ features hidden
- 0 tooltips
- No breadcrumbs
- No search
- Mixed routing (some tools not bookmarkable)

**After:**
- 6 main nav buttons (added "Labs")
- All 50+ features discoverable via:
  - Secondary nav menus
  - Dashboards with tool grids
  - Labs index page
  - Quick search/command palette
- Tooltips on all buttons (50+ tooltips)
- Breadcrumbs on every page
- Keyboard shortcuts (Ctrl+K command palette)
- 100% router-based navigation (all bookmarkable)

**Key Success Criteria:**
1. ✅ New user can find ANY feature in < 30 seconds
2. ✅ All features have clear descriptions (tooltips)
3. ✅ Navigation is intuitive (breadcrumbs, secondary menus)
4. ✅ Power users can use keyboard shortcuts
5. ✅ Every feature has a bookmarkable URL

---

## 🎯 MVP for Day 1 (Quick Wins)

**If you only have 4 hours today, prioritize these:**

1. **Add Tooltips** (1 hour)
   - Add `title` attribute to all nav buttons
   - Quick win, immediate value

2. **Make Dashboards Primary** (1 hour)
   - Change CAM button to route to `/cam-dashboard`
   - Enhance dashboards with tool grids

3. **Add Breadcrumbs** (1 hour)
   - Simple `<Breadcrumbs />` component
   - Shows current location

4. **Add Labs Button** (1 hour)
   - 6th main nav button
   - Routes to new `/labs` listing page

**Total:** 4 hours, big impact on discoverability

---

## 📝 File Changes Summary

### **New Files to Create:**
1. `client/src/components/Breadcrumbs.vue`
2. `client/src/components/FeatureDiscoveryPanel.vue`
3. `client/src/components/QuickSearch.vue`
4. `client/src/views/LabsIndex.vue`

### **Files to Modify:**
1. `client/src/App.vue` (nav enhancements, tooltips, Labs button)
2. `client/src/router/index.ts` (add ~15 new routes for design tools/utils)
3. `client/src/views/CAMDashboard.vue` (enhance with tool grid)
4. `client/src/views/ArtStudioDashboard.vue` (enhance with tool grid)
5. `client/src/components/toolbox/GuitarDesignHub.vue` (convert to router)
6. `client/src/components/toolbox/CalculatorHub.vue` (convert to router)

### **Estimated Lines Changed:**
- **New code:** ~800 lines
- **Modified code:** ~300 lines
- **Total:** ~1100 lines

---

## 🚀 Let's Start!

**Ready to begin with Day 1 MVP (4 hours)?**

**Next steps:**
1. Add tooltips to main nav (15 min)
2. Add Labs button (30 min)
3. Create Breadcrumbs component (45 min)
4. Create LabsIndex page (90 min)
5. Manual test (30 min)

**Which task should we tackle first?**
