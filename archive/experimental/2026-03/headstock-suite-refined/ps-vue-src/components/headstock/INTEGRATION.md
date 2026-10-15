# Headstock Suite — Vue 3 Integration Guide

## File inventory

```
src/
├── types/headstock.ts              ← All TypeScript interfaces
├── stores/headstock.ts             ← Pinia store (replaces PS{} object)
├── styles/ps-tokens.css            ← CSS custom properties
├── composables/
│   ├── useKonvaCanvas.ts           ← Konva lifecycle + resize
│   ├── useHeadstockPath.ts         ← Parametric bezier builder
│   ├── useDxfImport.ts             ← SVG/DXF parse + normalize
│   └── useScoring.ts               ← Novelty + gates
└── components/headstock/
    ├── constants.ts                ← HS_MODELS, PARAM_DEFS
    ├── HeadstockSuite.vue          ← Shell + tab routing
    ├── workspace/
    │   ├── WorkspacePanel.vue      ← Layout wrapper (stub: wire to canvas)
    │   ├── WorkspaceCanvas.vue     ← Full Konva inlay canvas ✓
    │   ├── ModelSelector.vue       ← (stub)
    │   ├── InlayLibrary.vue        ← (stub)
    │   ├── LayerList.vue           ← (stub)
    │   └── ElementProps.vue        ← (stub)
    ├── import/
    │   ├── ImportPanel.vue         ← (stub)
    │   ├── ImportCanvas.vue        ← (stub)
    │   ├── NormalizeControls.vue   ← (stub)
    │   └── PathList.vue            ← (stub)
    └── parametric/
        ├── ParametricPanel.vue     ← (stub)
        ├── ParametricCanvas.vue    ← Full reactive canvas ✓
        ├── ParameterSliders.vue    ← (stub)
        └── ScorePanel.vue          ← Full novelty + gates ✓
```

## Install dependencies

```bash
npm install konva pinia
npm install -D @types/konva
# DXF parser (UMD, load in index.html)
# <script src="https://cdn.jsdelivr.net/npm/dxf-parser@1.1.2/dist/dxf-parser.js"></script>
```

## Wire into main.ts

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import '@/styles/ps-tokens.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

## Add to router (if using vue-router)

```typescript
// router/index.ts
import HeadstockSuite from '@/components/headstock/HeadstockSuite.vue'

{
  path: '/headstock',
  component: HeadstockSuite,
  meta: { requiresAuth: true }   // pro gate: check subscription tier
}
```

## Pro tier gate

The parametric tab is flagged with `pro: true` in HeadstockSuite.vue.
Wire into your existing auth/subscription store:

```typescript
// In HeadstockSuite.vue, replace the tab click handler:
function switchTab(id: ActiveTab) {
  const tab = TABS.find(t => t.id === id)
  if (tab?.pro && !authStore.hasProAccess) {
    router.push('/upgrade')
    return
  }
  store.setTab(id)
}
```

## FastAPI backend handoff

The `useDxfImport` composable calls `POST /api/dxf/spline/evaluate`
for NURBS splines. Wire the backend from `dxf_service.py`:

```python
# main.py
from app.routers.dxf_service import router as dxf_router
app.include_router(dxf_router, prefix='/api/dxf')
```

## Data flow

```
Parametric tab
  store.params (HeadstockParams)
    → buildHeadstockPath() [composable]
      → ParametricCanvas (Konva, reactive watcher)
      → ScorePanel (computed, via useScoring)
  store.sendParametricToWorkspace(path)
    → store.customShape = { path, source:'parametric' }
    → store.activeTab = 'workspace'
    → WorkspaceCanvas picks up via watch(store.customShape)

Import tab
  useDxfImport.parseFile(file)
    → store.setRawPaths(...)
    → ImportCanvas renders split view
  useDxfImport.applyNormalize(...)
    → store.setNormPaths(...)
  store.sendImportToWorkspace()
    → store.customShape = { path, source:'svg-import'|'dxf-import' }
    → store.activeTab = 'workspace'

Workspace tab
  watch(store.currentModel) → WorkspaceCanvas.drawHS()
  watch(store.customShape)  → WorkspaceCanvas.drawHS() (custom template)
  WorkspaceCanvas.placeInlay(type) → store.addInlay(layer)
  WorkspaceCanvas.exportSVG() → returns SVG string
```

## Undo stack

The undo stack currently lives in WorkspaceCanvas (Konva node snapshots).
For full undo across all three tabs, move it to Pinia:

```typescript
// stores/headstock.ts — add to workspace section:
const snapshots = ref<Array<typeof inlays.value>>([])
const snapIdx   = ref(-1)

function snapshot() {
  snapshots.value = snapshots.value.slice(0, snapIdx.value + 1)
  snapshots.value.push(JSON.parse(JSON.stringify(inlays.value)))
  snapIdx.value = snapshots.value.length - 1
}

function undo() {
  if (snapIdx.value <= 0) return
  snapIdx.value--
  inlays.value = JSON.parse(JSON.stringify(snapshots.value[snapIdx.value]))
}
```

## Unit tests (Vitest)

```typescript
// composables/useHeadstockPath.test.ts
import { describe, it, expect } from 'vitest'
import { buildHeadstockPath } from './useHeadstockPath'
import { CORPUS } from '@/stores/headstock'

describe('buildHeadstockPath', () => {
  it('returns a closed SVG path', () => {
    const d = buildHeadstockPath(CORPUS['Les Paul'], 0)
    expect(d).toMatch(/^M /)
    expect(d).toMatch(/Z$/)
  })

  it('asymmetry shifts tip off-centre', () => {
    const sym   = buildHeadstockPath({ ...CORPUS['Les Paul'], asymmetry: 0  }, 0)
    const asym  = buildHeadstockPath({ ...CORPUS['Les Paul'], asymmetry: 10 }, 0)
    expect(sym).not.toBe(asym)
  })
})
```
