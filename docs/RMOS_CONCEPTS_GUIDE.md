# RMOS Concepts Guide

**For Operators and Users**

This guide explains the key concepts in RMOS (Run Manufacturing Operations System) - the safety layer that protects your CNC operations.

---

## Risk Levels

Every operation is assigned a risk level based on automated feasibility checks:

### GREEN - Safe to Run

**What it means:** All checks pass. Your parameters are within safe operating ranges.

**What you can do:** Export G-code and proceed to manufacturing.

**Visual:** Green badge with ✓ checkmark

### YELLOW - Review Required

**What it means:** One or more warnings detected. The operation may succeed but carries additional risk.

**What you can do:**
1. Review each warning
2. Understand the implications
3. Provide an override reason
4. Proceed with caution

**Visual:** Yellow badge with ⚠ warning icon

### RED - Blocked

**What it means:** Safety violation detected. The operation could damage tools, material, or machine.

**What you can do:**
1. Review the blocking rules
2. Fix the parameters
3. Re-run feasibility check

**Visual:** Red badge with ⛔ blocked icon

---

## Key Terms

### Feasibility Check

Automated validation of your CAM parameters against 22 safety rules (F001-F029). Runs before any G-code is generated.

**Rules check:**
- Tool geometry (diameter, stepover, stepdown)
- Feed rates (XY and Z)
- Cutting depths
- Material constraints

### Override

When YELLOW warnings are present, an operator must acknowledge them before proceeding. This creates an audit record with:
- Who approved it
- When it was approved
- Why it was approved (required text)

**Important:** Overrides are logged but do not bypass safety checks. RED operations cannot be overridden.

### Audit Trail

Immutable record of every decision. Cannot be modified after creation. Includes:
- Timestamp
- Parameters used
- Rules triggered
- Override reasons (if any)
- G-code hash

### Operator Pack

ZIP bundle containing everything needed for the CNC job:
- `output.nc` - G-code file
- `input.dxf` - Original design
- `manifest.json` - Run metadata
- `feasibility.json` - Safety check results

### Run ID

Unique identifier for each manufacturing run. Format: `run_{timestamp}_{hash}`

Example: `run_20260218T143022_abc123`

### Content-Addressed Storage

Artifacts (G-code, DXF) are stored by their SHA256 hash. This ensures:
- Same file = same hash (integrity)
- No duplicate storage
- Tamper detection

---

## Common Warnings

| Rule | Level | What It Means |
|------|-------|---------------|
| F010 | YELLOW | Tool may be too large for smallest feature |
| F011 | YELLOW | Plunge feed exceeds cutting feed |
| F012 | YELLOW | Stepdown exceeds 50% of tool diameter |
| F013 | YELLOW | Many loops may slow processing |

## Common Blocks

| Rule | Level | What It Means |
|------|-------|---------------|
| F001 | RED | Tool diameter invalid (<0.5mm or >50mm) |
| F002 | RED | Stepover out of range |
| F006 | RED | No closed geometry found |
| F020 | RED | Excessive depth of cut in hardwood |

---

## Best Practices

1. **Read warnings carefully** - They exist to protect your equipment and material
2. **Provide meaningful override reasons** - Future you will thank past you
3. **Test on scrap first** - Especially after YELLOW overrides
4. **Review operator packs** - Check the feasibility.json before running
5. **Trust RED blocks** - They prevent real damage

---

## Getting Help

- **Feasibility rules:** See `docs/RMOS_FEASIBILITY_RULES_v1.md`
- **API reference:** See `docs/DXF_TO_GCODE_WORKFLOW.md`
- **Architecture:** See `docs/canonical/ARCHITECTURE.md`

---

*This guide is part of Luthier's ToolBox documentation.*
