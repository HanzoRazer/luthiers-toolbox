# Build Chronicle: VCarve/Fusion 360 Style UI Redesign

**Date Started**: March 9, 2026
**Status**: In Progress
**Goal**: Transform luthiers-toolbox into a professional CAD/CAM application with dark theme, 3-panel layout, and checkbox-based feature toggles.

---

## Background

The Production Shop (luthiers-toolbox) is a comprehensive CAM application for luthiers. The user requested a UI overhaul to match the professional look and feel of industry-standard tools like **VCarve** and **Fusion 360**.

### Key Design Requirements
- Dark charcoal/slate theme (default)
- Left sidebar: Tool browser / navigation
- Center: Large canvas/viewport
- Right sidebar: Properties / parameters panel
- Checkbox-based feature toggles in panels
- Consistent panel-based console layout

---

## Pre-Work Completed (Same Session)

### Supabase Authentication
Before the UI redesign, we completed Supabase authentication:

1. **Database Migration** - Created SQLite-compatible auth tables:
   - `user_profiles` - User tier, preferences
   - `projects` - User-owned projects
   - `feature_flags` - Tier-based feature gating (7 flags seeded)

2. **GitHub OAuth Setup**:
   - Created GitHub OAuth App
   - Configured Supabase provider
   - Added redirect URL: `http://localhost:5181/auth/callback`
   - **Login tested successfully**

3. **Edition Integration** - Updated `useEdition.ts` to check:
   - Server feature flags first
   - Auth tier second
   - Local edition fallback

---

## Exploration Findings

### Current Architecture
| Component | Location | Status |
|-----------|----------|--------|
| App.vue | `/packages/client/src/App.vue` | Vertical flex, no sidebar |
| AppNav.vue | `/packages/client/src/components/AppNav.vue` | Horizontal nav (commented out) |
| Design Tokens | `/packages/client/src/styles/design-tokens.css` | Has dark mode support |
| Layout Proto | `/packages/client/src/views/dev/LayoutProto.vue` | 3 layout templates exist |
| Nav Proto | `/packages/client/src/views/dev/NavProto.vue` | Sidebar variant exists |

### Existing Strengths
- Design tokens already defined with dark mode CSS variables
- Layout prototypes show 3-panel design pattern
- Navigation domains identified: Design, CAM, Production, Analytics, Business
- Modular component system in place

### Gaps Identified
- No unified layout wrapper
- Navigation is horizontal, not sidebar
- No standardized properties panel system
- No feature toggle UI with checkboxes
- Dark theme not applied consistently

---

## Implementation Plan

### Phase 1: Global Layout Shell
| File | Action | Purpose |
|------|--------|---------|
| `src/layouts/CadLayout.vue` | Create | Master 3-panel layout |
| `src/components/layout/CadSidebar.vue` | Create | Navigation sidebar |
| `src/components/layout/CadHeaderBar.vue` | Create | Top header bar |
| `src/components/layout/CadStatusBar.vue` | Create | Bottom status bar |

### Phase 2: Dark Theme
| File | Action | Purpose |
|------|--------|---------|
| `src/styles/design-tokens.css` | Modify | Dark theme as default |
| `src/styles/cad-theme.css` | Create | CAD-specific panel styles |

### Phase 3: Panel Components
| File | Action | Purpose |
|------|--------|---------|
| `src/components/layout/CadPanel.vue` | Create | Collapsible panel |
| `src/components/layout/CadPropertyGroup.vue` | Create | Property grouping |
| `src/components/layout/CadFeatureToggles.vue` | Create | Checkbox toggles |
| `src/components/ui/CadCheckbox.vue` | Create | Styled checkbox |
| `src/components/ui/CadInput.vue` | Create | Styled input |
| `src/components/ui/CadSelect.vue` | Create | Styled dropdown |

### Phase 4: Feature Toggles
| File | Action | Purpose |
|------|--------|---------|
| `src/composables/useFeatureToggles.ts` | Create | Toggle state management |

### Phase 5: View Migration
Priority order:
1. DxfToGcodeView (primary CAM workflow)
2. AdaptiveLabView
3. PipelineLabView
4. BlueprintLabView
5. ArtStudioView

---

## Progress Log

### March 9, 2026

#### 14:00 - Supabase Auth Completed
- Migration ran successfully
- GitHub OAuth configured and tested
- User can log in with GitHub

#### 15:30 - UI Redesign Planning
- Explored codebase architecture
- Identified existing layout prototypes
- Created implementation plan

#### 15:45 - Phase 1 Started
- Created `/layouts/` directory
- Created `/components/layout/` directory
- **Created `CadLayout.vue`** - Master 3-panel layout with:
  - Header slot
  - Left panel slot (240px default)
  - Center canvas slot (flex: 1)
  - Right panel slot (320px default)
  - Status bar slot
  - Dark theme CSS variables
  - Custom scrollbar styling

#### 16:00 - Phase 1 Completed
- **Created `CadSidebar.vue`** - Collapsible navigation sidebar:
  - 6 domain groups: Design, CAM, Production, Analytics, AI Tools, Business
  - Auto-expands domain containing current route
  - Active route highlighting with accent color
  - SVG icons for each domain header

- **Created `CadHeaderBar.vue`** - Top header bar:
  - Auto-generated breadcrumb from route path
  - User menu integration (auth store)
  - Sign In/Logout buttons
  - Settings icon button

- **Created `CadStatusBar.vue`** - Bottom status bar:
  - X, Y, Z coordinate display
  - Zoom percentage
  - Units display (mm/in)
  - Optional memory usage display
  - Monospace font for coordinates

#### 16:15 - Phase 2 Completed (Theme)
- **Updated `design-tokens.css`**:
  - Dark theme as default (not media query dependent)
  - Added CAD-specific variables: --color-bg-app, --color-bg-panel, etc.
  - Light mode now opt-in via `.allow-light-mode` class

- **Created `cad-theme.css`**:
  - Panel styles with gradient headers
  - Property group styling
  - Form controls: inputs, selects, checkboxes, sliders
  - Buttons: primary, secondary, ghost, danger
  - Tabs, dividers, badges, tooltips
  - Global scrollbar styling

#### 16:30 - Phase 3 Completed (Components)
- **Created `CadPanel.vue`** - Collapsible property panel:
  - Click-to-collapse header
  - Optional icon
  - Header actions slot
  - Nested panel support

- **Created `CadCheckbox.vue`** - Styled checkbox:
  - Label + description support
  - Disabled and indeterminate states
  - Focus ring styling

- **Created `CadInput.vue`** - Styled input:
  - Label, prefix, suffix support
  - Number input without spinners
  - Focus state with accent border

- **Created `CadFeatureToggles.vue`** - Toggle panel:
  - Array of checkbox toggles
  - Hover highlight
  - Compact mode option

- **Created `useFeatureToggles.ts`** - Composable:
  - Reactive toggle state
  - localStorage persistence option
  - isEnabled, toggle, setToggle, reset helpers
  - toggleList computed for rendering

#### 16:45 - App.vue Updated
- Imported `cad-theme.css`
- Set `color-scheme: dark` on html
- Updated body to use dark theme variables
- Added global scrollbar styling for dark theme
- Updated link colors to use accent

#### 17:00 - Demo Page Created
- **Created `CadLayoutDemo.vue`** - Full working demonstration:

#### 17:00 - DxfToGcodeView Migration Complete
- **Migrated `DxfToGcodeView.vue`** to use CadLayout:
  - Left panel: CadSidebar navigation
  - Center: Upload zone + generate button + results
  - Right panel: CAM parameters organized into CadPanel components:
    - Tool Settings (diameter, stepover, stepdown)
    - Depths (target depth, safe Z)
    - Feed Rates (XY, Z)
    - Options (layer name, climb milling checkbox)
    - Display (feature toggles for grid, toolpath preview, auto-generate)
  - Status bar: Dynamic status message + file name + units
  - OverrideModal moved to Teleport for proper z-index stacking
  - All existing functionality preserved (risk badges, warnings, downloads, compare)

---

#### Earlier - Demo Page Created
- **Created `CadLayoutDemo.vue`** - Full working demonstration:
  - CadLayout with all three panels
  - CadSidebar navigation (functional)
  - CadPanel with Tool Settings, Cut Settings, Display Options, Preferences
  - CadInput fields with labels and suffixes
  - CadFeatureToggles with live toggle state display
  - CadCheckbox with descriptions
  - Live mouse coordinate tracking in status bar
  - Grid background in canvas area
  - Route added at `/dev/cad-layout-demo`

---

## Design Specifications

### Color Palette (Dark Theme)
```css
--color-bg-app: #1a1a1a;
--color-bg-panel: #242424;
--color-bg-panel-elevated: #2d2d2d;
--color-bg-canvas: #1e1e1e;
--color-bg-input: #333333;

--color-text-primary: #e0e0e0;
--color-text-secondary: #a0a0a0;
--color-text-muted: #707070;

--color-border-panel: #3a3a3a;
--color-border-input: #4a4a4a;

--color-accent: #4a9eff;
--color-accent-hover: #6ab0ff;

--color-success: #4ade80;
--color-warning: #fbbf24;
--color-danger: #f87171;
```

### Layout Structure
```
┌──────────────────────────────────────────────────────────────┐
│  HeaderBar (48px)                                            │
├────────────┬────────────────────────────┬────────────────────┤
│            │                            │                    │
│  LeftPanel │      CenterCanvas          │    RightPanel      │
│  (240px)   │      (flex: 1)             │    (320px)         │
│            │                            │                    │
├────────────┴────────────────────────────┴────────────────────┤
│  StatusBar (24px)                                            │
└──────────────────────────────────────────────────────────────┘
```

### Navigation Domains
1. **Design** - Guitar geometry, rosette, art studio, blueprint import
2. **CAM** - Toolpath generation, adaptive, drilling, bridge, saw labs
3. **Production** - Manufacturing candidates, live monitor, CNC history
4. **Analytics** - Risk dashboards, CAM dashboard, AI logs, acoustics
5. **Business** - Costing, ROI, cash flow, estimators

---

## Files Created/Modified

### Created
- [x] `packages/client/src/layouts/CadLayout.vue` - Master 3-panel layout wrapper
- [x] `packages/client/src/components/layout/CadSidebar.vue` - Navigation sidebar with domain groups
- [x] `packages/client/src/components/layout/CadHeaderBar.vue` - Top header with breadcrumb
- [x] `packages/client/src/components/layout/CadStatusBar.vue` - Bottom status bar with coordinates
- [x] `packages/client/src/components/layout/CadPanel.vue` - Collapsible property panel
- [x] `packages/client/src/components/layout/CadFeatureToggles.vue` - Checkbox toggle panel
- [x] `packages/client/src/components/ui/CadCheckbox.vue` - Styled checkbox component
- [x] `packages/client/src/components/ui/CadInput.vue` - Styled input with label/suffix
- [x] `packages/client/src/styles/cad-theme.css` - CAD-specific panel and control styles
- [x] `packages/client/src/composables/useFeatureToggles.ts` - Feature toggle state management

### Modified
- [x] `packages/client/src/styles/design-tokens.css` - Dark theme as default
- [x] `packages/client/src/App.vue` - Import cad-theme.css, dark scrollbars
- [x] `packages/client/src/router/index.ts` - Added /dev/cad-layout-demo route
- [x] `packages/client/src/views/DxfToGcodeView.vue` - Migrated to CadLayout (March 9, 2026)

### Demo
- [x] `packages/client/src/views/dev/CadLayoutDemo.vue` - Full working demo at /dev/cad-layout-demo

---

## Success Criteria

- [x] Dark theme applied globally
- [x] 3-panel layout working (left nav, center canvas, right properties)
- [x] Collapsible panels with checkboxes
- [x] Navigation sidebar with domain groups
- [x] Demo page created (`/dev/cad-layout-demo`)
- [x] DxfToGcodeView fully migrated (see Migration Guide below)
- [x] All existing functionality preserved

#### 17:30 - Animated Toolpath Visualizer Integration
- **Integrated ToolpathPlayer into DxfToGcodeView**:
  - Added `ToolpathPlayer` import from `@/components/cam/ToolpathPlayer.vue`
  - Toolpath player appears in center canvas after G-code generation
  - Controlled by Display panel toggles:
    - "Show Toolpath Preview" - enables/disables the visualizer
    - "Animate Toolpath" - enables auto-play animation
  - Shows animated/static badge to indicate current mode
  - Full playback controls: play/pause, scrub, speed, step forward/back
  - HUD shows: G-code line, Z position, feed rate, M-code states, time estimates
  - Memory warning for large files with resolution slider

---

## Demo Page

A fully working demo is available at `/dev/cad-layout-demo` showing:
- 3-panel layout with navigation sidebar
- Collapsible property panels
- Feature toggles with checkboxes
- Input fields with labels and suffixes
- Live coordinate display in status bar
- Grid background in canvas area

---

## Migration Guide for Existing Views

To migrate a view to use CadLayout:

```vue
<template>
  <CadLayout title="View Title">
    <!-- Left: Navigation (optional - CadSidebar is default) -->
    <template #left>
      <CadSidebar />
    </template>

    <!-- Center: Main content -->
    <template #default>
      <!-- Your existing view content -->
    </template>

    <!-- Right: Properties panels -->
    <template #right>
      <div class="properties-scroll">
        <CadPanel title="Parameters">
          <CadInput v-model="value" label="Label" suffix="mm" />
        </CadPanel>

        <CadPanel title="Display Options">
          <CadFeatureToggles :features="toggles" @toggle="handleToggle" />
        </CadPanel>
      </div>
    </template>

    <!-- Status: Coordinates / status message -->
    <template #status>
      <CadStatusBar :x="cursorX" :y="cursorY" message="Ready" />
    </template>
  </CadLayout>
</template>

<script setup lang="ts">
import CadLayout from "@/layouts/CadLayout.vue";
import CadSidebar from "@/components/layout/CadSidebar.vue";
import CadPanel from "@/components/layout/CadPanel.vue";
import CadFeatureToggles from "@/components/layout/CadFeatureToggles.vue";
import CadInput from "@/components/ui/CadInput.vue";
import CadStatusBar from "@/components/layout/CadStatusBar.vue";
</script>
```

### Views to Migrate (Priority Order)
1. **DxfToGcodeView** - Primary CAM workflow
2. **AdaptiveLabView** - Adaptive pocketing
3. **PipelineLabView** - Pipeline runner
4. **BlueprintLabView** - Blueprint import
5. **ArtStudioView** - Art design tools

---

## Notes

- Existing `LayoutProto.vue` and `NavProto.vue` in `/views/dev/` provide reference implementations
- Design tokens already support dark mode via `@media (prefers-color-scheme: dark)`
- Will make dark theme the default regardless of system preference
- Auth system (Supabase + GitHub OAuth) is fully operational

---

## References

- VCarve Pro: https://www.vectric.com/products/vcarve-pro
- Fusion 360: https://www.autodesk.com/products/fusion-360
- Existing prototypes: `/packages/client/src/views/dev/LayoutProto.vue`

---

## Post-Session Assessment (2026-03-10)

**Status:** Incomplete. Component library and theme are solid. View migration stopped at 1 of 5.

Work was interrupted after the environment reset. The commit survived but the effort was not resumed.

### What Was Completed

Phases 1–4 are fully delivered:

- **9 Cad* components** created and functional (CadLayout, CadSidebar, CadHeaderBar, CadStatusBar, CadPanel, CadFeatureToggles, CadCheckbox, CadInput)
- **cad-theme.css** — full dark CAD theme (535+ lines)
- **design-tokens.css** — modified for dark-by-default
- **App.vue** — imports the theme globally
- **useFeatureToggles.ts** — composable with localStorage persistence
- **Demo page** at `/dev/cad-layout-demo` — fully functional showcase
- **DxfToGcodeView** — first view migration complete with toolpath visualizer integration

### What's Not Done

#### Phase 5 — View Migration (1 of 5 complete)

| View | Status |
|------|--------|
| DxfToGcodeView | ✅ Migrated |
| AdaptiveLabView | ❌ Not migrated |
| PipelineLabView | ❌ Not migrated |
| BlueprintLabView | ❌ Not migrated |
| ArtStudioView | ❌ Not migrated |

#### Phase 3 — Planned but never created

| Component | Status |
|-----------|--------|
| `CadSelect.vue` (styled dropdown) | ❌ Not created |
| `CadPropertyGroup.vue` (property grouping) | ❌ Not created |

#### Broader migration

The remaining ~70 views in the app still use the old layout (no sidebar, no dark CAD panels).

### Supersession Notice

Some of the unmigrated views may be superseded by future architecture changes, product segmentation (Express/Pro/Enterprise tiers), or route consolidation (the app currently has ~262 routes, targeted to drop below 300 per the remediation plan). Views that are candidates for removal or merger should not be migrated — only views that survive consolidation should adopt CadLayout.

### Recommendation

Before resuming view migration, determine which views are staying. Cross-reference with:
- `docs/UNFINISHED_REMEDIATION_EFFORTS.md` — lists route consolidation status
- `docs/PHASE_2_3_IMPLEMENTATION_PLAN.md` — SaaS tier plan determines which views exist per tier
- `ROUTER_MAP.md` — router organization by deployment wave
