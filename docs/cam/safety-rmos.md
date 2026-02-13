# Safety & RMOS

Manufacturing decision intelligence for safe CNC operations.

---

## What is RMOS?

RMOS (Run Management & Operations System) is a safety layer that evaluates every manufacturing job before execution. It uses rule-based analysis to catch potentially dangerous configurations.

---

## How It Works

### 1. Input Analysis

When you request a toolpath, RMOS analyzes:

- Geometry dimensions
- Material properties
- Tool specifications
- CAM parameters
- Machine capabilities

### 2. Rule Evaluation

30+ rules evaluate the job:

- Tool compatibility
- Feed/speed limits
- Depth safety
- Structural integrity
- Thermal risks

### 3. Decision

Every job receives a verdict:

| Decision | Meaning |
|----------|---------|
| **GREEN** | Safe to proceed |
| **YELLOW** | Warnings - operator review required |
| **RED** | Blocked - unsafe configuration |

---

## Decision Levels

### GREEN - Safe

The job passes all safety checks. You can proceed with confidence.

```json
{
  "decision": "GREEN",
  "risk_level": "safe",
  "rules_triggered": [],
  "export_allowed": true
}
```

### YELLOW - Review Required

One or more warnings were triggered. Review the warnings and decide whether to proceed.

```json
{
  "decision": "YELLOW",
  "risk_level": "review",
  "rules_triggered": [
    {
      "id": "F010",
      "level": "YELLOW",
      "message": "High stepover percentage (60%) may leave tool marks"
    }
  ],
  "export_allowed": true
}
```

### RED - Blocked

The job has critical safety issues and cannot be exported without override.

```json
{
  "decision": "RED",
  "risk_level": "blocked",
  "rules_triggered": [
    {
      "id": "F020",
      "level": "RED",
      "message": "Excessive depth-of-cut in hardwood (8mm > 1.5x tool diameter)"
    }
  ],
  "export_allowed": false
}
```

---

## Safety Rules

### Core Rules (F001-F007)

| Rule | Description |
|------|-------------|
| F001 | Missing required geometry data |
| F002 | Stepover exceeds 100% of tool diameter |
| F003 | Stepdown exceeds safe limits for material |
| F004 | Feed rate exceeds machine limits |
| F005 | Spindle speed out of range |
| F006 | Tool diameter larger than pocket |
| F007 | Depth exceeds Z travel |

### Warning Rules (F010-F013)

| Rule | Description |
|------|-------------|
| F010 | High stepover may affect finish |
| F011 | Conservative feed rate suggestion |
| F012 | Recommend finishing pass |
| F013 | Consider climb vs conventional |

### Adversarial Rules (F020-F029)

| Rule | Description |
|------|-------------|
| F020 | Excessive DOC in hardwood |
| F021 | Tool breakage risk (DOC:diameter ratio) |
| F022 | Depth exceeds material thickness |
| F023 | Zero/negative geometry dimensions |
| F024 | Missing material specification |
| F025 | Tool larger than pocket width |
| F026 | Chatter/deflection risk |
| F027 | Thermal risk (resinous + small tool) |
| F028 | Structural wall failure |
| F029 | Combined adversarial factors |

### Edge Cases (F030-F040)

| Rule | Description |
|------|-------------|
| F030 | Thin wall warning |
| F031 | Deep pocket aspect ratio |
| F032 | High RPM for large tool |
| F033 | Low feed rate may cause burning |
| F034 | Island stability concern |

---

## Override System

### YELLOW Override

Operators can acknowledge YELLOW warnings and proceed:

```python
response = requests.post(
    "http://localhost:8000/api/rmos/runs_v2/runs/{run_id}/override",
    json={
        "reason": "Tested with scrap, parameters acceptable",
        "risk_acknowledged": True
    }
)
```

### RED Override

RED decisions require explicit authorization:

1. Environment variable: `RMOS_ALLOW_RED_OVERRIDE=1`
2. Override request with justification
3. Audit trail recorded

!!! danger "RED Override Warning"
    RED decisions indicate genuinely dangerous configurations.
    Override only when you fully understand and accept the risks.

---

## Audit Trail

All decisions and overrides are logged:

```json
{
  "run_id": "abc123",
  "timestamp": "2025-01-15T14:30:00Z",
  "decision": "YELLOW",
  "rules_triggered": ["F010", "F011"],
  "override": {
    "applied": true,
    "reason": "Acceptable for prototype",
    "user": "operator@shop.com"
  }
}
```

---

## WhyPanel

The UI includes a "Why?" panel that explains decisions:

- Shows all triggered rules
- Explains each rule's purpose
- Suggests fixes
- Displays override status

---

## Validation Protocol

Before RMOS releases, a 30-scenario validation protocol ensures:

### Tier 1: Baseline (10 scenarios)

Standard production jobs must all pass GREEN.

### Tier 2: Edge Pressure (10 scenarios)

Boundary conditions must produce appropriate YELLOW warnings.

### Tier 3: Adversarial (10 scenarios)

Intentionally unsafe configurations must be blocked RED.

**Pass Criteria:**

- Zero RED→GREEN leaks
- Zero false blocks on baseline
- Accurate explanations

---

## API Usage

### Check Feasibility

```python
import requests

response = requests.post(
    "http://localhost:8000/api/rmos/feasibility/check",
    json={
        "geometry": {...},
        "tool": {...},
        "material": {...},
        "params": {...}
    }
)

result = response.json()
if result["decision"] == "GREEN":
    print("Safe to proceed")
elif result["decision"] == "YELLOW":
    print(f"Warnings: {result['rules_triggered']}")
else:
    print(f"BLOCKED: {result['rules_triggered']}")
```

### Get Run Decision

```python
response = requests.get(
    "http://localhost:8000/api/rmos/runs_v2/runs/{run_id}"
)

run = response.json()
print(f"Decision: {run['decision']}")
print(f"Export allowed: {run['export_allowed']}")
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RMOS_STRICT_STARTUP` | Fail if safety modules missing | `1` |
| `RMOS_ALLOW_RED_OVERRIDE` | Allow RED overrides | `0` |
| `RMOS_RUNS_DIR` | Storage for run data | `./data/runs` |

### Rule Customization

Rules can be tuned for your specific environment:

```yaml
# rules_config.yaml
F020:
  doc_multiplier: 2.0  # Allow 2x tool diameter (default: 1.5x)
F010:
  stepover_threshold: 70  # Warn at 70% (default: 55%)
```

---

## Related

- [Toolpath Generation](../features/toolpaths.md) - Creating toolpaths
- [Machine Profiles](machine-profiles.md) - Configure limits
- [RMOS Rules Reference](../../docs/RMOS_FEASIBILITY_RULES_v1.md) - Full rule documentation
