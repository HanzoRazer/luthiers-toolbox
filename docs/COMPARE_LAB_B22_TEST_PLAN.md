# Compare Lab (B22) – Test & Verification Plan

This checklist validates the new `/api/compare/lab` backend plus the Compare Lab Vue interface.

## Prerequisites

1. Backend: `cd services/api && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000` (ensure `compare_lab_router` loads without warnings).
2. Frontend: `cd client && npm install && npm run dev` (Vite dev server on `http://localhost:5173`).
3. Adaptive Lab snapshot: open `/lab/adaptive`, run a quick plan or load demo loops so the compare storage key (`toolbox.compare.currentGeometry`) is populated.

## API Smoke Script (PowerShell)

```powershell
$geometry = @{ units = "mm"; paths = @(@{ segments = @(@{ type = "line"; x1 = 0; y1 = 0; x2 = 60; y2 = 0 })) } |
            ConvertTo-Json -Depth 8

$baseline = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/compare/lab/baselines" -Body (
  @{ name = "Test Baseline"; description = "B22 smoke"; geometry = (ConvertFrom-Json $geometry) } | ConvertTo-Json -Depth 8
) -ContentType 'application/json'

$baselines = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/compare/lab/baselines"

$diff = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/compare/lab/diff" -ContentType 'application/json' -Body (
  @{ baseline_id = $baseline.id; current_geometry = (ConvertFrom-Json $geometry) } | ConvertTo-Json -Depth 8
)

$export = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/compare/lab/export" -ContentType 'application/json' -Body (
  @{ baseline_id = $baseline.id; current_geometry = (ConvertFrom-Json $geometry); format = 'json' } | ConvertTo-Json -Depth 8
)

# cleanup
Invoke-RestMethod -Method Delete -Uri "http://localhost:8000/api/compare/lab/baselines/$($baseline.id)"
```

**Assertions**
- `POST /baselines` returns `200` with persisted `id` and `geometry` echo.
- `GET /baselines` returns the saved entry.
- `POST /diff` produces segment counts and includes both baseline/current geometries.
- `POST /export` returns the same payload as diff (ready to download).
- `DELETE /baselines/{id}` returns `{ "success": true }`.

## UI Verification Flow

1. **Load Geometry**
   - In Adaptive Lab, import DXF/demos, run plan, ensure loops render. Confirm `localStorage['toolbox.compare.currentGeometry']` is set.
2. **Compare Lab Entry**
   - Click “Open Compare Lab” from Adaptive Lab, or navigate to `/lab/compare`. Page should auto-load stored geometry.
3. **Baseline Capture**
   - Enter a baseline name/notes, save. Sidebar refresh should list the baseline.
4. **Diff Rendering**
   - Select the baseline: middle column should show dual SVGs, right column shows summary cards + segment table.
5. **Diff Update**
   - Return to Adaptive Lab, edit loops (e.g., change width), rerun adaptive to persist new geometry. Go back to Compare Lab; baseline remains selected and diff recomputes automatically.
6. **Export JSON**
   - Click “Export JSON Overlay” and confirm a download containing summary + geometries.

## Regression Notes

- Verify legacy `/api/compare` endpoints still respond (Rosette Compare Mode). Both compare routers can coexist.
- Ensure Compare Lab honors units: create baseline in mm, then attempt to diff with inch payload; API should return `400` “Mixed units not yet supported”.
- Confirm Adaptive Lab still opens PipelineLab and no console errors occur after adding the Compare Lab bridge.

## Documentation Targets

- Reference this plan in future bundle notes (B22) and link from the Compare Lab section in `README.md` when that document is updated.
- Once automated tests exist, convert the PowerShell snippet above into `test_compare_lab.ps1` under the repo root.
