) Doc stub: Wave_12_AI_CAM_UI.md

File: docs/CAM_Core/Wave_12_AI_CAM_UI.md

# Wave 12 — AI-Driven CAM Advisor UI

This wave exposes the RMOS 2.0 + Calculator Spine + AI-CAM backend
through a dedicated front-end UI.

## Components

- `CamAdvisorPanel.vue`
  - Accepts tool + cut parameters
  - Calls `/api/ai-cam/analyze-operation`
  - Displays:
    - advisories (info/warning/error)
    - recommended_changes (raw)
    - physics summary via `PhysicsSummaryBadges.vue`

- `PhysicsSummaryBadges.vue`
  - Renders chipload/heat/deflection/rim-speed/kickback as status badges.

- `GCodeExplainerPanel.vue`
  - Accepts raw G-code text
  - Calls `/api/ai-cam/explain-gcode`
  - Displays line-by-line explanations + risk hints.

- `CamAdvisorView.vue`
  - Combined layout for Advisor + G-code Explainer
  - Mounted under route `/cam/advisor`.

## Store

- `camAdvisorStore.ts`
  - Centralizes:
    - `analyzeOperation(payload)`
    - `explainGcode(gcodeText)`
  - Holds advisories, physics results, and G-code explanations.

## Backend Dependencies

Requires Wave 11 backend:

- `ai_cam/advisor.py`
- `ai_cam/explain_gcode.py`
- `ai_cam/models.py`
- `routers/ai_cam_router.py`

## Status

- UI verified to compile with Pinia + Vue 3.
- Physics + recommendations still stub-level until later waves implement full models.


At this point, Wave 12 gives you:

A visible CAM Advisor operators can play with today.

A G-code Explainer harness ready to plug into more advanced physics later.

A clean route (/cam/advisor) you can demo as “smart CAM.”