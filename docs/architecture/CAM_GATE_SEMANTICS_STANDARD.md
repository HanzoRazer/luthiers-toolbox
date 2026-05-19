# CAM Gate Semantics Standard

**Date:** 2026-05-09  
**Status:** ACTIVE STANDARD  
**Scope:** GREEN/YELLOW/RED gate evaluation semantics  
**Reference Implementation:** `app/cam/nut_slot_cam.py`

---

## Purpose

This document defines the canonical semantics for CAM safety gates. Gates evaluate whether a preview request is safe to process and visualize.

---

## Important Distinction

```
preview invalid ≠ machine dangerous
```

Machine execution does not exist in governed preview. Gates evaluate **preview safety**, not machine safety.

| Gate | Meaning |
|------|---------|
| GREEN | Preview-safe: parameters are valid and within conservative bounds |
| YELLOW | Preview-safe with caution: parameters are marginal but renderable |
| RED | Preview-invalid: parameters are invalid or would produce unsafe geometry |

---

## Gate Definitions

### GREEN

**Meaning:** All parameters within safe bounds. Preview can proceed without warnings.

**Conditions:**
- All required parameters present
- All values within Pydantic constraints
- No safety threshold violations
- No marginal conditions detected

**User experience:** Preview renders immediately, no warnings shown.

### YELLOW

**Meaning:** Preview-safe but with cautions. Preview can proceed with warnings displayed.

**Conditions:**
- Parameters are valid but marginal
- Conservative thresholds exceeded but not dangerous
- Unusual combinations detected
- Recommend review before any future export

**User experience:** Preview renders with yellow warning indicators.

### RED

**Meaning:** Preview-invalid. Cannot generate meaningful preview.

**Conditions:**
- Required parameters missing or invalid
- Physical impossibility (tool larger than slot)
- Safety limits exceeded (depth > stock thickness)
- Data integrity violation (positions not monotonic)

**User experience:** Preview blocked, error message displayed.

---

## Gate Evaluation Rules

### Rule 1: Gate Escalation

Gates can only escalate, never de-escalate within a single evaluation.

```python
# Correct: escalate from GREEN to YELLOW to RED
gate = CamGate.GREEN
if marginal_condition:
    gate = CamGate.YELLOW
if blocking_condition:
    gate = CamGate.RED

# Incorrect: never de-escalate
if gate == CamGate.RED and some_condition:
    gate = CamGate.YELLOW  # FORBIDDEN
```

### Rule 2: RED Blocks Preview

If gate is RED, the response must still return but `canonical_toolpath` may be empty or partial.

```json
{
  "gate": "red",
  "errors": ["Tool diameter exceeds slot width"],
  "canonical_toolpath": null
}
```

### Rule 3: YELLOW Allows Preview

YELLOW does not block preview. Toolpath generation proceeds, warnings are attached.

### Rule 4: Issues Must Match Gate

If `issues` array contains severity "red" entries, gate must be RED.
If `issues` array contains only severity "yellow" entries, gate must be YELLOW.
If `issues` array is empty, gate should be GREEN.

---

## Reference Gate Conditions (nut_slot_cam.py)

### RED Conditions (Block Preview)

| Condition | Message Pattern |
|-----------|-----------------|
| Depth ≥ stock thickness | "Slot depth ({x}mm) >= stock thickness ({y}mm)" |
| Depth > 80% stock thickness | "Slot depth ({x}mm) > 80% of stock thickness ({y}mm)" |
| Tool > slot width | "Tool diameter ({x}mm) > slot width ({y}mm)" |
| Positions outside bounds | "Position {x}mm outside nut width [0, {y}mm]" |
| Positions not increasing | "String positions must be strictly increasing" |
| Edge offsets consume width | "Edge offsets ({x}mm + {y}mm) >= nut width ({z}mm)" |
| Position count mismatch | "Expected {x} positions, got {y}" |
| Adjacent spacing < 3mm | "Adjacent spacing ({x}mm) < minimum (3.0mm)" |

### YELLOW Conditions (Warnings)

| Condition | Message Pattern |
|-----------|-----------------|
| Depth 60-80% stock thickness | "Slot depth ({x}mm) > 60% of stock thickness" |
| Tool 90-100% slot width | "Tool diameter ({x}mm) is 90-100% of slot width" |
| Edge offset < 2mm | "Edge offset ({x}mm) < 2.0mm may be fragile" |
| Spacing 3-5mm | "Adjacent spacing ({x}mm) between 3-5mm is tight" |
| Stock < 3mm | "Stock thickness ({x}mm) < 3.0mm is thin" |
| Slot width < 0.2mm | "Slot width ({x}mm) < 0.2mm is very narrow" |
| Slot length < 2mm | "Slot length ({x}mm) < 2.0mm is short" |
| Safe Z < 2mm | "Safe Z ({x}mm) < 2.0mm is low" |

---

## Gate Evaluation Pattern

Reference implementation pattern:

```python
class CamGate(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class GateEvaluation:
    gate: CamGate = CamGate.GREEN
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    issues: List[CamIssue] = field(default_factory=list)

    def add_error(self, code: str, msg: str, field_name: Optional[str] = None) -> None:
        """Add RED error with structured issue."""
        self.errors.append(msg)
        self.issues.append(CamIssue(code=code, severity="red", message=msg, field=field_name))
        self.gate = CamGate.RED

    def add_warning(self, code: str, msg: str, field_name: Optional[str] = None) -> None:
        """Add YELLOW warning with structured issue."""
        self.warnings.append(msg)
        self.issues.append(CamIssue(code=code, severity="yellow", message=msg, field=field_name))
        if self.gate != CamGate.RED:
            self.gate = CamGate.YELLOW
```

---

## Operation-Specific Gate Conditions

Different operations have different gate conditions. Document operation-specific conditions in module docstrings.

### General Patterns

| Category | RED Example | YELLOW Example |
|----------|-------------|----------------|
| Depth | depth ≥ stock | depth > 60% stock |
| Tool | tool > feature | tool > 90% feature |
| Spacing | spacing < minimum | spacing < recommended |
| Position | outside bounds | near edge |
| Reach | tool cannot reach | tool at limit |

---

## Frontend Gate Handling

| Gate | UI Treatment |
|------|--------------|
| GREEN | Render preview, show success indicator |
| YELLOW | Render preview, show warnings in yellow banner |
| RED | Show error message, optionally show partial preview |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Response shape |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Export gate requirements |
| `nut_slot_cam.py` | Reference implementation |

---

*Standard established: 2026-05-09*
