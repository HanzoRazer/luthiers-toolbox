# Headstock Suite — luthiers-toolbox-main Integration

## 1. File placement

Drop the `ps-vue/src/` subtree into your existing codebase:

```
luthiers-toolbox-main/
└── src/
    ├── modules/
    │   └── cam/                        ← existing CAM domain
    │       └── headstock/              ← NEW: add entire headstock/ folder here
    │           ├── views/
    │           │   ├── WorkspaceView.vue
    │           │   ├── ImportView.vue
    │           │   └── ParametricView.vue
    │           ├── composables/
    │           │   ├── useKonvaCanvas.ts
    │           │   ├── useHeadstock.ts
    │           │   ├── useParametric.ts
    │           │   ├── useDxfImport.ts
    │           │   └── useExportDxf.ts
    │           ├── components/
    │           │   └── AppShell.vue    ← rename: HeadstockShell.vue inside the module
    │           └── HeadstockIndex.vue  ← thin wrapper (see below)
    ├── assets/
    │   └── data/
    │       └── headstockData.ts        ← merge with existing data layer
    ├── stores/
    │   └── headstock.ts                ← register in your Pinia root
    └── types/
        └── headstock.ts                ← merge with existing types
```

## 2. Router registration

In your existing `src/router/index.ts` (canonical URL patterns from your
six-domain reorganization spec):

```typescript
// CAM domain routes
{
  path: '/cam/headstock',
  component: () => import('@/modules/cam/headstock/HeadstockIndex.vue'),
  meta: { domain: 'cam', tier: 'free' },
  children: [
    { path: '',           redirect: 'workspace' },
    { path: 'workspace',  component: () => import('@/modules/cam/headstock/views/WorkspaceView.vue'),  meta: { tier: 'free' } },
    { path: 'import',     component: () => import('@/modules/cam/headstock/views/ImportView.vue'),      meta: { tier: 'free' } },
    { path: 'parametric', component: () => import('@/modules/cam/headstock/views/ParametricView.vue'), meta: { tier: 'paid' } },
  ],
},
```

## 3. HeadstockIndex.vue (thin router-view wrapper)

```vue
<script setup lang="ts">
// Replaces AppShell.vue nav — inherits Production Shop's main nav.
// HeadstockShell just provides the sub-tab bar and router-view.
import { useRoute, useRouter } from 'vue-router'
const route  = useRoute()
const router = useRouter()
const tabs = [
  { key: 'workspace',  label: 'Workspace', tier: 'free' },
  { key: 'import',     label: 'Import',    tier: 'free' },
  { key: 'parametric', label: 'Parametric',tier: 'paid' },
]
</script>

<template>
  <div class="headstock-module">
    <!-- Sub-tab bar — sits below the Production Shop main nav -->
    <div class="sub-nav">
      <button
        v-for="t in tabs" :key="t.key"
        class="sub-tab"
        :class="{ on: route.path.endsWith(t.key) }"
        @click="router.push(`/cam/headstock/${t.key}`)"
      >
        {{ t.label }}
        <span v-if="t.tier === 'paid'" class="pro-badge">Pro</span>
      </button>
    </div>
    <div class="headstock-body">
      <router-view />
    </div>
  </div>
</template>
```

## 4. Pinia store registration

Your root `stores/index.ts` or `main.ts`:

```typescript
import { useHeadstockStore } from '@/modules/cam/headstock/stores/headstock'
// No manual registration needed with Pinia — stores are lazy.
// Just ensure createPinia() is called before mount (already done).
```

If you have a root store that tracks active module state, add:
```typescript
// In your root store or app-level composable:
const hs = useHeadstockStore()
// Headstock store persists inlays/customShape across route changes
// within the /cam/headstock/* subtree automatically.
```

## 5. Tier gating

Your existing RMOS tier check pattern:

```typescript
// In router/guards.ts (or your existing auth guard):
router.beforeEach((to) => {
  if (to.meta.tier === 'paid' && !userHasPaidTier()) {
    return { path: '/cam/headstock/workspace', query: { upgrade: '1' } }
  }
})
```

The `ParametricView` emits `navigate` and `toast` events upward.
In `HeadstockIndex.vue`, handle these:
```vue
<router-view @navigate="router.push(`/cam/headstock/${$event}`)" @toast="showToast" />
```

## 6. FastAPI backend — add routers

In your existing `main.py`:

```python
from modules.cam.headstock.dxf_service import router as dxf_router
from modules.cam.headstock.dxf_export  import router as export_router

app.include_router(dxf_router,    prefix="/api/dxf",    tags=["dxf"])
app.include_router(export_router, prefix="/api/export", tags=["export"])
```

Move `dxf_service.py` and `dxf_export.py` to:
```
luthiers-toolbox-main/
└── backend/
    └── modules/
        └── cam/
            └── headstock/
                ├── dxf_service.py
                └── dxf_export.py
```

## 7. CSS tokens

The headstock suite uses `--w0` through `--w4`, `--br`, `--br2` etc.
These match Production Shop's existing token set.

If your app uses different token names, either:
- Add the headstock tokens as aliases in your root CSS:
  ```css
  :root {
    --w0: var(--ps-bg-0);   /* map to your existing tokens */
    --w1: var(--ps-bg-1);
    /* ... */
  }
  ```
- Or run a find/replace across the headstock Vue files:
  `--w0` → your dark bg token, `--br2` → your accent token, etc.

## 8. dxf-parser UMD script tag

The `useDxfImport` composable checks `(window as any).DxfParser`.
Add to `index.html` (or your module's lazy-loaded entry HTML):

```html
<script src="https://cdn.jsdelivr.net/npm/dxf-parser@1.1.2/dist/dxf-parser.js"></script>
```

Alternatively, replace the window check with a proper ESM import:
```typescript
// In useDxfImport.ts, replace the window check with:
import DxfParser from 'dxf-parser'
// and remove the (window as any).DxfParser reference.
// npm install dxf-parser must be in package.json.
```

## 9. Vite proxy (dev only)

If you already have a dev proxy for your FastAPI backend, add:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api/dxf':    { target: 'http://localhost:8000', changeOrigin: true },
    '/api/export': { target: 'http://localhost:8000', changeOrigin: true },
  }
}
```

## 10. What does NOT need to change

- `useKonvaCanvas.ts` — fully self-contained, no Production Shop dependencies
- `useParametric.ts` — pure TypeScript, no Vue/Konva coupling, testable standalone
- `useDxfImport.ts`  — same
- `dxf_export.py`    — standalone FastAPI router, no app-level state
- `dxf_service.py`   — same

## Summary checklist

- [ ] Copy `src/modules/cam/headstock/` tree
- [ ] Register `/cam/headstock/*` routes with tier metadata
- [ ] Create `HeadstockIndex.vue` sub-tab shell
- [ ] Add `dxf_service.py` + `dxf_export.py` to backend, include routers in `main.py`
- [ ] Add `dxf-parser` script tag to `index.html` (or ESM import)
- [ ] Map CSS tokens if your app uses different variable names
- [ ] Add Vite proxy entries for `/api/dxf` and `/api/export`
