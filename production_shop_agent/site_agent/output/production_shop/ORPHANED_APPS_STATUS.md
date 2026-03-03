# Orphaned Apps Status

**Last Updated:** March 3, 2026 (Session 3)

## Connected Features (5/18)

| Feature | Route | API Endpoints | Commit |
|---------|-------|---------------|--------|
| **Relief Carving** | `/art-studio/relief` | `/api/cam/relief/*` | `9d1b7925` |
| **Inlay Designer** | `/art-studio/inlay` | `/api/art-studio/inlay/*` | `90250d97` |
| **V-Carve Toolpaths** | `/art-studio/vcarve` | `/api/art-studio/vcarve/*`, `/api/cam/toolpath/vcarve/*` | `b8f9bfcb` |
| **Machine Manager** | `/lab/machines` | `/api/machines/*`, `/api/posts/*` | `f9e02bd0` |
| **Preset Hub** | `/preset-hub` | `/api/presets/*` | Already working |

## Remaining Orphaned Apps (13)

| Feature | Route | Category | Priority |
|---------|-------|----------|----------|
| **AI Visual Analyzer** | `/ai-images` | AI/Tools | HIGH |
| **Material Analytics** | `/rmos/material-analytics` | Production | HIGH |
| **Strip Optimization** | `/rmos/strip-family-lab` | Production | HIGH |
| **Acoustic Analyzer** | `/tools/audio-analyzer` | Quality/Tools | MEDIUM |
| **CNC Production** | `/cnc` | Production | MEDIUM |
| **DXF to G-code** | `/cam/dxf-to-gcode` | CAM | MEDIUM |
| **Run Comparison** | `/rmos/runs/diff` | Production | MEDIUM |
| **Variant Analysis** | `/rmos/runs/:run_id/variants` | Production | MEDIUM |
| **Saw Lab Batch Mode** | `/lab/saw/batch` | CAM | MEDIUM |
| **Saw Lab Contour Mode** | `/lab/saw/contour` | CAM | MEDIUM |
| **Risk Timeline Lab** | `/lab/risk-timeline` | CAM | MEDIUM |
| **Pipeline Lab** | `/lab/pipeline` | CAM | MEDIUM |
| **CAM Settings** | `/settings/cam` | Configuration | LOW |

## Progress

- **Session 3:** Connected 5 features to their APIs
- **Remaining:** 13 orphaned features need Vue views and API connections
- **Coverage:** 28% of orphaned features now connected
