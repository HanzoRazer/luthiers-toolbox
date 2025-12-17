# DIRECTIONAL_WORKFLOW_2_0_QUICKREF.md

**Module:** Directional Workflow 2.0  
**Status:** ✅ Complete  
**Server:** RMOS 2.0 (port 8010)

---

## Quick API Reference

### List Modes
```http
GET /api/rmos/workflow/modes
```
Returns: All 3 workflow modes with descriptions and best-use cases.

### Preview Mode
```http
POST /api/rmos/workflow/mode/preview
Content-Type: application/json

{
  "mode": "ai_assisted",
  "tool_id": "router:6_2_6.35",
  "goal_speed": 0.8,
  "goal_quality": 0.4,
  "goal_tool_life": 0.3
}
```
Returns: Constraints, feasibility score, risk level, recommendations.

### Get Constraints
```http
GET /api/rmos/workflow/mode/{mode_id}/constraints
```
Returns: Hard limits, soft limits, suggestions for specified mode.

---

## Workflow Modes

| Mode | Hard Limits | Scoring | Best For |
|------|-------------|---------|----------|
| `design_first` | None | Post-change | Experienced designers |
| `constraint_first` | Enforced | Upfront | Production workflows |
| `ai_assisted` | Flexible | Goal-based | Learning / optimization |

---

## Constraint-First Hard Limits

| Parameter | Default Limit |
|-----------|---------------|
| Max RPM | 18,000 |
| Max Feed | 3,000 mm/min |
| Max Depth | 15 mm |
| Min Tool Ø | 3.0 mm |

**Saw Tools:** Max RPM capped at 6,000, Max Feed at 2,000 mm/min.

---

## AI-Assisted Goals

| Goal | Effect |
|------|--------|
| `goal_speed` | Higher feeds, larger stepovers |
| `goal_quality` | Lower feeds, finer stepovers |
| `goal_tool_life` | Conservative RPM, light passes |

---

## Files Created

```
services/api/app/workflow/
├── __init__.py                  # Public API
├── directional_workflow.py      # Core logic (320 LOC)
└── mode_preview_routes.py       # FastAPI endpoints (115 LOC)

services/api/app/rmos/
└── feasibility_scorer.py        # Modified: +workflow_mode param

docs/RMOS/
└── Directional_Workflow_2_0.md  # Full documentation

scripts/
└── Test-DirectionalWorkflow.ps1 # Integration tests (7 tests)
```

---

## Test Commands

```powershell
# Run all workflow tests
.\scripts\Test-DirectionalWorkflow.ps1

# Quick mode list check
Invoke-RestMethod http://localhost:8010/api/rmos/workflow/modes
```

---

## Integration with Feasibility Scorer

```python
from app.rmos.feasibility_scorer import score_design_feasibility

# With workflow mode
result = score_design_feasibility(
    design, 
    ctx, 
    workflow_mode="constraint_first"  # Optional
)
```

---

## See Also

- [Full Documentation](docs/RMOS/Directional_Workflow_2_0.md)
- [Saw Lab 2.0 Quickref](SAW_LAB_2_0_QUICKREF.md)
- [RMOS 2.0 Architecture](docs/RMOS_N8_N10_ARCHITECTURE.md)
