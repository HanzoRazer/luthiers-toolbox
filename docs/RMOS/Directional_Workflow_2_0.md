# Directional Workflow 2.0 — Art Studio / RMOS Integration

**Status:** ✅ Implemented  
**Module:** RMOS 2.0  
**Date:** January 2025

---

## Overview

Directional Workflow 2.0 provides three distinct workflow modes for rosette and pattern design in Art Studio. Each mode offers a different balance between artistic freedom and manufacturing constraints.

---

## Workflow Modes

### 1. Design First (`design_first`)

**Philosophy:** Full artistic freedom, then machine constraints

- **No hard limits enforced upfront**
- User designs freely without interruption
- Feasibility warnings appear after parameter changes
- Best for experienced designers who know machine limits

**Use Cases:**
- Experimental or artistic projects
- Quick prototyping without constraint overhead
- Users who prefer "design then validate" workflow

**API Behavior:**
- Full feasibility scoring applied
- All warnings returned for review
- No parameters rejected upfront

### 2. Constraint First (`constraint_first`)

**Philosophy:** Start with machine limits, then design within bounds

- **Hard limits enforced upfront**
- Parameters outside limits immediately rejected (score=0, RED risk)
- Green indicators show optimal ranges
- Best for production-focused workflows

**Hard Limits (defaults):**
| Parameter | Limit |
|-----------|-------|
| Max RPM | 18,000 |
| Max Feed | 3,000 mm/min |
| Max Depth | 15 mm |
| Min Tool Ø | 3.0 mm |

**Use Cases:**
- Mission-critical production parts
- Beginners learning safe parameters
- Zero tolerance for out-of-spec operations

**API Behavior:**
- Hard limit check before scoring
- Immediate rejection if limits exceeded
- Clear violation messages returned

### 3. AI Assisted (`ai_assisted`)

**Philosophy:** AI-driven suggestions based on your goals

- **Goal sliders control optimization direction**
- Balance speed, quality, and tool life priorities
- AI generates parameter recommendations
- Best for learning or multi-objective optimization

**Goal Weights:**
- `goal_speed` (0.0-1.0): Prioritize cycle time
- `goal_quality` (0.0-1.0): Prioritize surface finish
- `goal_tool_life` (0.0-1.0): Prioritize tool longevity

**Use Cases:**
- Learning optimal parameters for new materials
- Complex multi-objective optimization
- Getting recommendations without manual research

**API Behavior:**
- Recommendations generated based on goal weights
- Feasibility score reflects goal balance
- Suggestions include tool/material-specific advice

---

## API Endpoints

### GET `/api/rmos/workflow/modes`

List all available workflow modes with descriptions.

**Response:**
```json
{
  "modes": [
    {
      "id": "design_first",
      "name": "Design First",
      "description": "Full artistic freedom, then machine constraints...",
      "best_for": ["Experienced designers", "Experimental projects", ...]
    },
    ...
  ],
  "default_mode": "design_first"
}
```

### POST `/api/rmos/workflow/mode/preview`

Get constraints and feasibility preview for a mode.

**Request:**
```json
{
  "mode": "constraint_first",
  "tool_id": "router:6_2_6.35",
  "material_id": "mahogany",
  "machine_profile": "shapeoko_4",
  "goal_speed": 0.7,
  "goal_quality": 0.5,
  "goal_tool_life": 0.3
}
```

**Response:**
```json
{
  "mode": "constraint_first",
  "constraints": {
    "mode": "constraint_first",
    "hard_limits": {
      "max_rpm": 18000,
      "max_feed_mm_min": 3000,
      "max_depth_mm": 15,
      "min_tool_diameter_mm": 3.0
    },
    "soft_limits": {
      "recommended_rpm": 12000,
      "recommended_feed_mm_min": 1500,
      "recommended_stepover_pct": 40
    },
    "suggestions": [
      "Parameters are clamped to safe machine limits",
      "Green indicators show optimal ranges",
      "Router mode: Standard milling constraints active"
    ]
  },
  "feasibility_score": 85.0,
  "risk_level": "GREEN",
  "warnings": [],
  "recommendations": ["Operating within safe limits"]
}
```

### GET `/api/rmos/workflow/mode/{mode_id}/constraints`

Get constraints for a specific mode without context.

**Response:**
```json
{
  "mode": "ai_assisted",
  "hard_limits": {"max_rpm": 24000, "max_feed_mm_min": 5000},
  "soft_limits": {},
  "suggestions": [
    "Adjust goal sliders to prioritize speed, quality, or tool life",
    "AI will suggest optimal parameters based on your priorities"
  ]
}
```

---

## Integration with Feasibility Scorer

The `score_design_feasibility()` function in `rmos/feasibility_scorer.py` now accepts an optional `workflow_mode` parameter:

```python
from app.rmos.feasibility_scorer import score_design_feasibility

# Design-first mode (default behavior)
result = score_design_feasibility(design, ctx, workflow_mode="design_first")

# Constraint-first mode (hard limits enforced)
result = score_design_feasibility(design, ctx, workflow_mode="constraint_first")

# AI-assisted mode (enhanced recommendations)
result = score_design_feasibility(design, ctx, workflow_mode="ai_assisted")
```

---

## Architecture

```
services/api/app/
├── workflow/
│   ├── __init__.py                 # Public API exports
│   ├── directional_workflow.py     # Core logic + models
│   └── mode_preview_routes.py      # FastAPI endpoints
└── rmos/
    └── feasibility_scorer.py       # Updated with workflow_mode support
```

---

## Testing

### Smoke Test Script

```powershell
# Test mode listing
Invoke-RestMethod -Uri "http://localhost:8010/api/rmos/workflow/modes" -Method GET

# Test mode preview
$body = @{
    mode = "ai_assisted"
    goal_speed = 0.8
    goal_quality = 0.4
    goal_tool_life = 0.3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8010/api/rmos/workflow/mode/preview" `
    -Method POST -Body $body -ContentType "application/json"

# Test constraint lookup
Invoke-RestMethod -Uri "http://localhost:8010/api/rmos/workflow/mode/constraint_first/constraints" -Method GET
```

---

## Future Enhancements

1. **Machine Profile Integration (M.4):** Load hard limits from machine profile JSON
2. **Material Library Integration:** Adjust limits based on material hardness
3. **Learning System:** Track user preferences and adjust AI suggestions
4. **Mode Persistence:** Remember user's preferred mode across sessions

---

## See Also

- [RMOS 2.0 Architecture](../RMOS_N8_N10_ARCHITECTURE.md)
- [Saw Lab 2.0 Quickref](../../SAW_LAB_2_0_QUICKREF.md)
- [Art Studio Integration](../../ART_STUDIO_INTEGRATION_V13.md)
