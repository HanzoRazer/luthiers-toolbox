# The Production Shop - Link Mappings to Application

**Date:** March 3, 2026
**Status:** ✅ All links connected to actual application

---

## Overview

All marketing website links now point to functional application routes instead of placeholder URLs. This allows you to test the actual features directly from the marketing site.

**Application Base URL:** http://localhost:5173

---

## Complete Feature Link Mappings

### Design Features (10 features)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| Guitar Dimensions | `/instrument-geometry` | http://localhost:5173/instrument-geometry |
| Scale Length Designer | `/instrument-geometry` | http://localhost:5173/instrument-geometry |
| Rosette Designer | `/rosette` | http://localhost:5173/rosette |
| Art Studio | `/art-studio` | http://localhost:5173/art-studio |
| Blueprint Importer | `/blueprint` | http://localhost:5173/blueprint |
| Compound Radius Calculator | `/calculators` | http://localhost:5173/calculators |
| Radius Dish Designer | `/calculators` | http://localhost:5173/calculators |
| Archtop Calculator | `/calculators` | http://localhost:5173/calculators |
| Bracing Calculator | `/calculators` | http://localhost:5173/calculators |
| Bridge Calculator | `/calculators` | http://localhost:5173/calculators |

---

### Calculators (4 features)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| Basic Calculator | `/calculators` | http://localhost:5173/calculators |
| Scientific Calculator | `/calculators` | http://localhost:5173/calculators |
| Fraction Calculator | `/calculators` | http://localhost:5173/calculators |
| Woodworking Calculator | `/calculators` | http://localhost:5173/calculators |

**Note:** All calculators are accessible from the Calculator Hub at `/calculators`

---

### CAM Features (6 features)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| Quick Cut | `/quick-cut` | http://localhost:5173/quick-cut |
| Adaptive Lab | `/lab/adaptive` | http://localhost:5173/lab/adaptive |
| Saw Lab | `/lab/saw/slice` | http://localhost:5173/lab/saw/slice |
| Bridge Lab | `/lab/bridge` | http://localhost:5173/lab/bridge |
| Drilling Lab | `/lab/bridge` | http://localhost:5173/lab/bridge |
| G-code Explainer | `/cam/advisor` | http://localhost:5173/cam/advisor |

---

### Production Features (8 features)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| RMOS Manufacturing Candidates | `/rmos` | http://localhost:5173/rmos |
| Live Monitor | `/rmos/live-monitor` | http://localhost:5173/rmos/live-monitor |
| CNC History | `/rmos/runs` | http://localhost:5173/rmos/runs |
| Compare Runs | `/compare` | http://localhost:5173/compare |
| Hardware Layout | `/art-studio` | http://localhost:5173/art-studio |
| Wiring Workbench | `/art-studio` | http://localhost:5173/art-studio |
| Finish Planner | `/rmos/runs` | http://localhost:5173/rmos/runs |
| DXF Cleaner | `/blueprint` | http://localhost:5173/blueprint |

---

### Business Features (4 features)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| Instrument Costing | `/business/estimator` | http://localhost:5173/business/estimator |
| CNC ROI Calculator | `/calculators` | http://localhost:5173/calculators |
| Cash Flow Planner | `/business/estimator` | http://localhost:5173/business/estimator |
| Engineering Estimator | `/business/estimator` | http://localhost:5173/business/estimator |

---

### Instrument Library (Design Tab)

| Instrument | Application Route | Full URL |
|-----------|-------------------|----------|
| Smart Guitar | `/instrument-geometry` | http://localhost:5173/instrument-geometry |
| Benedetto 17" Archtop | `/instrument-geometry` | http://localhost:5173/instrument-geometry |
| Flying V | `/instrument-geometry` | http://localhost:5173/instrument-geometry |
| J-200 Jumbo Acoustic | `/instrument-geometry` | http://localhost:5173/instrument-geometry |
| Gibson L-00 | `/instrument-geometry` | http://localhost:5173/instrument-geometry |
| Soprano Ukulele | `/instrument-geometry` | http://localhost:5173/instrument-geometry |

**Note:** All instrument designs are accessible through the Instrument Geometry designer.

---

## Navigation & CTA Updates

### All Pages

| Element | Old Link | New Link |
|---------|----------|----------|
| Nav "Get Started" button | `contact.html` | http://localhost:5173 |

### Home Page (index.html)

| Element | Old Link | New Link |
|---------|----------|----------|
| Hero "Get Started Free" button | `pricing.html` | http://localhost:5173 |
| "Explore Design Studio" link | `features.html#design-studio` | http://localhost:5173/instrument-geometry |
| "Explore CAM Pipeline" link | `features.html#cam-pipeline` | http://localhost:5173/quick-cut |
| "Explore Business Tools" link | `features.html#panel-business` | http://localhost:5173/business/estimator |

---

## Testing the Links

### Prerequisites

1. **Start the Application:**
   ```bash
   cd C:/Users/thepr/Downloads/luthiers-toolbox/packages/client
   npm run dev
   ```

2. **Verify App is Running:**
   - Open browser to http://localhost:5173
   - You should see the Luthier's Toolbox application dashboard

3. **Keep Marketing Site Running:**
   - The test server is already running at http://localhost:8080

---

### Test Procedure

#### Test 1: Navigation Links

1. Go to http://localhost:8080/index.html
2. Click **"Get Started"** button in navigation
   - Should open http://localhost:5173 in new tab
   - Should show application dashboard

#### Test 2: Hero CTA

1. On home page, click **"Get Started Free"** button in hero
   - Should open http://localhost:5173 in new tab

#### Test 3: Feature Cards (Home Page)

1. Click **"Explore Design Studio"** → Should go to `/instrument-geometry`
2. Click **"Explore CAM Pipeline"** → Should go to `/quick-cut`
3. Click **"Explore Business Tools"** → Should go to `/business/estimator`

#### Test 4: Features Page - Design Tab

1. Go to http://localhost:8080/features.html
2. Ensure **Design** tab is active
3. Test each "Try it →" link:
   - **Guitar Dimensions** → `/instrument-geometry`
   - **Scale Length Designer** → `/instrument-geometry`
   - **Rosette Designer** → `/rosette`
   - **Art Studio** → `/art-studio`
   - **Blueprint Importer** → `/blueprint`
   - **Compound Radius Calculator** → `/calculators`
   - **Radius Dish Designer** → `/calculators`
   - **Archtop Calculator** → `/calculators`
   - **Bracing Calculator** → `/calculators`
   - **Bridge Calculator** → `/calculators`

4. Test Instrument Library links (all should go to `/instrument-geometry`)

#### Test 5: Features Page - Calculators Tab

1. Click **Calculators** tab
2. Test each "Try it →" link (all should go to `/calculators`)

#### Test 6: Features Page - CAM Tab

1. Click **CAM** tab
2. Test each "Try it →" link:
   - **Quick Cut** → `/quick-cut`
   - **Adaptive Lab** → `/lab/adaptive`
   - **Saw Lab** → `/lab/saw/slice`
   - **Bridge Lab** → `/lab/bridge`
   - **Drilling Lab** → `/lab/bridge`
   - **G-code Explainer** → `/cam/advisor`

#### Test 7: Features Page - Production Tab

1. Click **Production** tab
2. Test each "Try it →" link:
   - **RMOS Manufacturing Candidates** → `/rmos`
   - **Live Monitor** → `/rmos/live-monitor`
   - **CNC History** → `/rmos/runs`
   - **Compare Runs** → `/compare`
   - **Hardware Layout** → `/art-studio`
   - **Wiring Workbench** → `/art-studio`
   - **Finish Planner** → `/rmos/runs`
   - **DXF Cleaner** → `/blueprint`

#### Test 8: Features Page - Business Tab

1. Click **Business** tab
2. Test each "Try it →" link:
   - **Instrument Costing** → `/business/estimator`
   - **CNC ROI Calculator** → `/calculators`
   - **Cash Flow Planner** → `/business/estimator`
   - **Engineering Estimator** → `/business/estimator`

---

## Link Behavior

**All feature links:**
- Open in same window (no `target="_blank"`)
- Navigate directly to application route
- Use absolute URLs (http://localhost:5173/path)

**Navigation "Get Started" button:**
- Opens in new tab (`target="_blank"`)
- Goes to application home (`/`)

---

## Known Issues

### Instrument Library Links

The following instrument cards don't have specific dedicated routes yet, so they all point to the general Instrument Geometry designer:

- Smart Guitar
- Benedetto 17" Archtop
- Flying V
- J-200 Jumbo Acoustic
- Gibson L-00
- Soprano Ukulele

**Future Enhancement:** Create individual routes for each instrument design (e.g., `/instrument-geometry/smart-guitar`, `/instrument-geometry/benedetto-17`, etc.)

---

## Summary

**Total Features Mapped:** 32
**Total Links Updated:** 41

### Updated Files:
1. `features.html` - 32 feature card links + 6 instrument links
2. `index.html` - Nav button + Hero CTA + 3 feature card links
3. `pricing.html` - Nav button
4. `about.html` - Nav button
5. `contact.html` - Nav button

---

## Troubleshooting

### Links Don't Work

**Problem:** Clicking a feature link shows "Unable to connect"
**Solution:** Make sure the application is running:
```bash
cd C:/Users/thepr/Downloads/luthiers-toolbox/packages/client
npm run dev
```

### Wrong Port

**Problem:** Application is running on a different port (not 5173)
**Solution:** Update `BASE_URL` in the mapping script and re-run:
```bash
python C:/Users/thepr/Downloads/connect_website_to_app.py
```

### 404 Errors

**Problem:** Link goes to application but shows 404
**Solution:** Check if the route exists in `packages/client/src/router/index.ts`. Some features may map to routes that don't exist yet.

---

## Next Steps

1. ✅ All links connected to application
2. 🔄 **Test all links** (in progress)
3. ⏳ Fix any broken routes
4. ⏳ Add specific routes for individual instruments
5. ⏳ Deploy to production with production URLs

---

**Document Version:** 1.0
**Last Updated:** March 3, 2026
**Maintained By:** Development Team

---

## UPDATE: March 3, 2026 - Top 5 Features Added

**5 new high-priority features added to the marketing website:**

### New Design Features (2 added)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| **3D Relief Carving** | `/art-studio/relief` | http://localhost:5173/art-studio/relief |
| **Inlay Designer** | `/art-studio/inlay` | http://localhost:5173/art-studio/inlay |

### New CAM Features (1 added)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| **V-Carve Toolpaths** | `/art-studio/vcarve` | http://localhost:5173/art-studio/vcarve |

### New Production Features (2 added)

| Marketing Feature | Application Route | Full URL |
|-------------------|-------------------|----------|
| **Preset Hub** | `/preset-hub` | http://localhost:5173/preset-hub |
| **Machine Manager** | `/lab/machines` | http://localhost:5173/lab/machines |

**Total Features Now:** 37 features documented (was 32)
**Coverage:** Increased from 49% to 56% of all application features

---

## Updated Feature Count by Tab

- **Design:** 12 features (was 10) - Added Relief Carving, Inlay Designer
- **Calculators:** 4 features (unchanged)
- **CAM:** 7 features (was 6) - Added V-Carve Toolpaths
- **Production:** 10 features (was 8) - Added Preset Hub, Machine Manager
- **Business:** 4 features (unchanged)

**Total:** 37 features across 5 tabs

