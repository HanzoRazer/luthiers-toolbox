# Human Authority Model

## Core Principle

**Human authority over manufacturing decisions is non-negotiable.**

CAM Assist operates as an assistant, not an autonomous agent. Every strategy package requires explicit human approval before it can be considered complete.

## Authority Boundaries

### CAM Assist May

| Action | Scope | Constraint |
|--------|-------|------------|
| Calculate | Fret positions, dimensions | Based on human-provided specs |
| Generate | DXF geometry | From approved calculations |
| Suggest | Parameters, tool selections | Human must confirm |
| Document | Strategy packages | Human must review |
| Validate | Input consistency | Report issues, don't auto-fix |

### CAM Assist May Not

| Prohibited Action | Reason |
|-------------------|--------|
| Generate G-code | Machine commands require human-CAM-machine chain |
| Execute operations | No direct machine control |
| Auto-approve strategies | Human judgment required |
| Modify input specs | Only human can change design intent |
| Override warnings | Warnings require human acknowledgment |

## Approval Workflow

### Stage 1: Input Verification

```
Human provides specification
    ↓
CAM Assist validates input consistency
    ↓
CAM Assist reports any warnings
    ↓
Human acknowledges warnings or corrects input
```

**Human checkpoint:** Confirm specification is correct before proceeding.

### Stage 2: Strategy Generation

```
CAM Assist generates strategy package
    ↓
CAM Assist produces review checklist
    ↓
Human reviews checklist items
    ↓
Human marks each item verified
```

**Human checkpoint:** Every checklist item requires explicit verification.

### Stage 3: Approval

```
All checklist items verified
    ↓
Human provides approval
    ↓
Approval recorded with timestamp and identity
    ↓
Strategy package marked as approved
```

**Human checkpoint:** Final approval is explicit, recorded, and attributed.

## Review Checklist Structure

Every strategy package includes a review checklist. Checklists are operation-specific but follow a common structure:

### Section A: Input Verification

- [ ] Instrument specification matches design intent
- [ ] Scale length is correct
- [ ] Material specification is correct
- [ ] Tool selections are appropriate for material

### Section B: Geometry Verification

- [ ] DXF opens correctly in verification software
- [ ] Geometry dimensions match specification
- [ ] Geometry is positioned correctly relative to datum
- [ ] No unexpected geometry artifacts

### Section C: Parameter Verification

- [ ] Depths are appropriate for operation
- [ ] Speeds/feeds are appropriate for material
- [ ] Tool selection matches available tooling
- [ ] Sequence is correct

### Section D: Safety Verification

- [ ] Workholding is adequate for operation
- [ ] Tool reach is sufficient
- [ ] No collision risks identified
- [ ] Dust extraction is appropriate

## Approval Record Format

```json
{
  "approval_version": "1.0",
  "strategy_id": "fret-slots-2024-01-15-001",
  "approval_state": "approved",
  
  "approver": {
    "name": "Luthier Name",
    "identifier": "email or ID"
  },
  
  "timestamp": "2024-01-15T14:30:00Z",
  
  "checklist_completion": {
    "input_verification": ["A1", "A2", "A3", "A4"],
    "geometry_verification": ["B1", "B2", "B3", "B4"],
    "parameter_verification": ["C1", "C2", "C3", "C4"],
    "safety_verification": ["D1", "D2", "D3", "D4"]
  },
  
  "notes": "Optional approver notes",
  
  "acknowledged_warnings": [
    {
      "warning_id": "W001",
      "warning_text": "Slot depth exceeds typical range",
      "acknowledgment": "Intentional for jumbo frets"
    }
  ]
}
```

## Warning System

### Warning Severity Levels

| Level | Meaning | Workflow Impact |
|-------|---------|-----------------|
| **INFO** | Notable but expected | Logged, no acknowledgment required |
| **CAUTION** | Unusual but valid | Displayed, acknowledgment optional |
| **WARNING** | Potentially problematic | Displayed, acknowledgment required |
| **BLOCK** | Invalid or unsafe | Blocks strategy generation |

### Warning Categories

**Specification Warnings**
- Scale length outside typical range
- Fret count unusual for instrument type
- Dimensions inconsistent with instrument type

**Geometry Warnings**
- Geometry extends beyond material bounds
- Geometry intersects other features
- Geometry tolerance may cause issues

**Parameter Warnings**
- Depth exceeds typical range
- Speed/feed outside material recommendations
- Tool selection may not be optimal

**Safety Warnings**
- Operation may exceed machine capacity
- Workholding concerns
- Collision risk detected

## Authority Escalation

### When CAM Assist Cannot Proceed

If CAM Assist encounters a BLOCK-level issue:

1. Generation stops
2. Issue is reported with full context
3. Human must resolve the issue
4. Human must restart generation

CAM Assist does not:
- Attempt to work around blocks
- Suggest "close enough" alternatives
- Proceed with known-bad state

### Human Override Capabilities

Humans may override CAUTION and WARNING levels by:

1. Acknowledging the warning
2. Providing rationale
3. Accepting responsibility

Humans may NOT override BLOCK levels without:

1. Correcting the underlying issue
2. Providing documentation for why the issue is not actually a block
3. Explicitly marking the strategy as non-standard

## Traceability

Every strategy package maintains full traceability:

```
Instrument Spec (version, source)
    ↓
CAM Assist (version, timestamp)
    ↓
Strategy Package (version, contents hash)
    ↓
Review Checklist (completion state)
    ↓
Approval Record (who, when, what)
```

This chain allows any manufactured part to be traced back to:
- Original design intent
- Processing decisions
- Human approvals
- Acknowledged warnings
