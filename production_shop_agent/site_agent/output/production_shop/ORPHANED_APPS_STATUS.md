# Orphaned Apps Status

**Last Updated:** March 3, 2026 (Session 3)

## Status Clarification

These apps are "orphaned" from the **marketing website** - they have Vue views and API connections but are not featured on the marketing site.

## Session 3: API Connections Verified

All 5 views connected this session have full API integration:

| Feature | Route | API Endpoints | Commit |
|---------|-------|---------------|--------|
| **Relief Carving** | `/art-studio/relief` | `/api/cam/relief/*` | `9d1b7925` |
| **Inlay Designer** | `/art-studio/inlay` | `/api/art-studio/inlay/*` | `90250d97` |
| **V-Carve Toolpaths** | `/art-studio/vcarve` | `/api/art-studio/vcarve/*`, `/api/cam/toolpath/vcarve/*` | `b8f9bfcb` |
| **Machine Manager** | `/lab/machines` | `/api/machines/*`, `/api/posts/*` | `f9e02bd0` |
| **Preset Hub** | `/preset-hub` | `/api/presets/*` | Already working |

## Already Connected (Not on Marketing Site)

These features have Vue views AND working API connections, just not on marketing site:

| Feature | Route | API Connection | Status |
|---------|-------|----------------|--------|
| **Material Analytics** | `/rmos/material-analytics` | `useRmosAnalyticsStore` → `/api/rmos/analytics/*` | Connected (stubs) |
| **AI Visual Analyzer** | `/ai-images` | `useAiImageStore` → `/api/ai/*` | Connected |
| **DXF to G-code** | `/cam/dxf-to-gcode` | `useDxfToGcode` → `/api/cam/adaptive/*` | Connected |
| **Risk Timeline Lab** | `/lab/risk-timeline` | `camRisk` → `/api/cam/risk/*` | Connected |
| **CNC Production** | `/cnc` | Connected | Connected |
| **Run Comparison** | `/rmos/runs/diff` | Connected | Connected |
| **Variant Analysis** | `/rmos/runs/:run_id/variants` | Connected | Connected |
| **Saw Lab Batch Mode** | `/lab/saw/batch` | SawLabView props mode | Connected |
| **Saw Lab Contour Mode** | `/lab/saw/contour` | SawLabView props mode | Connected |
| **Pipeline Lab** | `/lab/pipeline` | Connected | Connected |
| **Strip Optimization** | `/rmos/strip-family-lab` | Connected | Connected |
| **Acoustic Analyzer** | `/tools/audio-analyzer` | Connected | Connected |
| **CAM Settings** | `/settings/cam` | Connected | Connected |

## Next Steps

These features need to be **added to the marketing website**, not connected to APIs:

1. Create feature cards for marketing site
2. Add screenshots/demos
3. Update pricing tiers to include premium features

## Progress

- **API Connections:** All features are connected
- **Marketing Coverage:** ~56% of features documented
- **Remaining Work:** Marketing content, not code
