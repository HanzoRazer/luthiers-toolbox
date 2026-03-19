# Production Shop — System Map

## The 5 Primary Workflows

### 1. Design → Manufacturable Geometry
  Start: Concept sketch or reference dimensions
  End: Validated DXF with toolpath-ready geometry
  Path: Design module → Geometry calculators
        → DXF export → Validation gate
  Key tools: Neck angle, bridge geometry,
             soundhole, body outline

### 2. Import → Validate → CAM
  Start: DXF file from external CAD
  End: Machine-ready G-code with preflight sign-off
  Path: DXF import → topology validation
        → CAM workspace → preflight → export
  Key tools: DXF adaptive router,
             CAM workspace, preflight gate

### 3. Rosette Design → CNC Export
  Start: Design parameters (ring count, material)
  End: Segmented G-code for CNC rosette cutting
  Path: Art studio → ring designer → BOM
        → manufacturability check → G-code
  Key tools: Rosette designer, tile segmentation,
             CNC export

### 4. Setup Verification Chain
  Start: Physical guitar measurements
  End: Action/intonation/compensation targets
  Path: Neck angle → saddle height → break angle
        → compensation → nut slots → cascade
  Key tools: Setup cascade, saddle compensation,
             bridge break angle, nut slot calc

### 5. Material + Acoustic Planning
  Start: Wood species + target frequency
  End: Plate thickness + brace schedule
  Path: Tonewood registry → plate analysis
        → archtop graduation → brace schedule
  Key tools: Plate analyzer, graduation map,
             back brace calc, voicing tracker

## Module Map (all modules → workflow)
| Module | Primary Workflow | Secondary |
|--------|-----------------|-----------|
| Neck generator | 1, 2 | 4 |
| Body generator | 1, 2 | - |
| Rosette designer | 3 | - |
| DXF validation | 2 | 1 |
| CAM workspace | 2 | 3 |
| Setup cascade | 4 | - |
| Plate design | 5 | - |
| Smart Guitar | 1, 2 | 4, 5 |
| RMOS/preflight | 2, 3 | all |

## Entry Points by User Type
| User | Start Here |
|------|-----------|
| First-time builder | Geometry calculators |
| CNC operator | CAM workspace |
| Designer | Neck/body generator |
| Setup tech | Setup cascade |
| Archtop builder | Plate design + graduation |
