# Wave 12 — AI-Driven CAM Advisor UI

This wave exposes the RMOS 2.0 + Calculator Spine + AI-CAM backend through a dedicated front-end UI.

**Status:** ✅ Implemented  
**Date:** December 7, 2025  
**Module:** AI-CAM UI (Wave 12)

---

## Overview

Wave 12 provides Vue 3 components for the AI-CAM backend:

1. **CamAdvisorPanel** — Cut operation analysis with physics advisories
2. **GCodeExplainerPanel** — Line-by-line G-code explanation
3. **PhysicsSummaryBadges** — Compact badge strip for physics results
4. **CamAdvisorView** — Combined view hosting both panels

---

## Components

### CamAdvisorPanel.vue

Accepts tool + cut parameters, calls `/api/ai-cam/analyze-operation`, and displays:
- Advisories (info/warning/error) with severity icons
- Recommended changes (raw JSON)
- Physics summary via `PhysicsSummaryBadges.vue`

**File:** `packages/client/src/components/cam/CamAdvisorPanel.vue`

### PhysicsSummaryBadges.vue

Renders physics results as colored badges:
- **Chipload** — OK (green) / OUT (amber)
- **Heat** — COLD (blue) / WARM (amber) / HOT (red)
- **Deflection** — GREEN / YELLOW / RED
- **Rim Speed** — OK (green) / OUT (amber)
- **Kickback** — LOW (green) / MEDIUM (amber) / HIGH (red)

**File:** `packages/client/src/components/cam/PhysicsSummaryBadges.vue`

### GCodeExplainerPanel.vue

Accepts raw G-code text, calls `/api/ai-cam/explain-gcode`, and displays:
- Line-by-line explanations
- Risk hints per line (color-coded)
- Overall risk assessment

**File:** `packages/client/src/components/cam/GCodeExplainerPanel.vue`

### CamAdvisorView.vue

Combined layout for Advisor + G-code Explainer, mounted under route `/cam/advisor`.

**File:** `packages/client/src/views/cam/CamAdvisorView.vue`

---

## Store

### camAdvisorStore.ts

Pinia store centralizing:
- `analyzeOperation(payload)` — Cut operation analysis
- `explainGcode(gcodeText, safeZ)` — G-code explanation
- `optimizeParameters(payload, searchPct)` — Parameter optimization
- `clearAll()` — Reset all state

Holds:
- Advisories list
- Physics results
- Recommended changes
- G-code explanations
- Optimization candidates

**File:** `packages/client/src/stores/camAdvisorStore.ts`

---

## Route

```typescript
// packages/client/src/router/index.ts
{
  path: '/cam/advisor',
  name: 'CamAdvisor',
  component: () => import('@/views/cam/CamAdvisorView.vue'),
}
```

Navigate to: **http://localhost:5173/cam/advisor**

---

## File Structure

```
packages/client/src/
├── stores/
│   └── camAdvisorStore.ts        # Pinia store
├── components/
│   └── cam/
│       ├── CamAdvisorPanel.vue       # Operation analysis form
│       ├── PhysicsSummaryBadges.vue  # Physics badges
│       └── GCodeExplainerPanel.vue   # G-code explainer
├── views/
│   └── cam/
│       └── CamAdvisorView.vue        # Combined view
└── router/
    └── index.ts                      # Route: /cam/advisor
```

---

## Backend Dependencies

Requires Wave 11 backend:
- `ai_cam/advisor.py`
- `ai_cam/explain_gcode.py`
- `ai_cam/models.py`
- `ai_cam/optimize.py`
- `routers/ai_cam_router.py`

---

## Usage

### 1. Start Backend

```bash
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend

```bash
cd packages/client
npm install
npm run dev
```

### 3. Navigate

Open **http://localhost:5173/cam/advisor**

---

## Screenshots

*(Add screenshots here after testing)*

---

## Status

- ✅ UI compiles with Pinia + Vue 3
- ✅ Store actions wired to backend endpoints
- ✅ Route registered at `/cam/advisor`
- ⏳ Physics + recommendations still stub-level until later waves implement full Calculator Spine models

---

## See Also

- [Wave 11 — AI-CAM Backend](./Wave_11_AI_CAM_Upgrade.md)
- [Calculator Spine](../Calculator_Spine_Overview.md)
- [RMOS 2.0](../../RMOS_2_0_ARCHITECTURE.md)
