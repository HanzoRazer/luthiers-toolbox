# Review Packet Format

## Overview

A review packet is a human-readable Markdown document generated from a validated strategy package. It summarizes all relevant information for operator review before any downstream CAM or machining work.

Review packets are **advisory only**. They do not:
- Generate G-code
- Authorize machine execution
- Replace operator judgment
- Produce toolpaths

## Generation

```bash
python scripts/generate_review_packet.py <strategy_json>
python scripts/generate_review_packet.py examples/valid/fret_slot_strategy.json
python scripts/generate_review_packet.py examples/valid/fret_slot_strategy.json --out /tmp/review.md
```

## Required Sections

Every review packet includes:

| Section | Purpose |
|---------|---------|
| 1. Non-Execution Notice | Explicit statement that this is advisory only |
| 2. Strategy Identity | Package ID, version, provenance |
| 3. Instrument Context | Source specification reference |
| 4. Material Context | Wood species, hardness, grain |
| 5. Operation Intent | What the operation aims to accomplish |
| 6. Coordinate Frame | How geometry is oriented |
| 7. Fret Slot Summary | Key positions and parameters |
| 8. Tool Assumptions | Expected tooling |
| 9. Workholding Assumptions | Clamping requirements |
| 10. Safety Boundary | Non-execution declarations |
| 11. Human Review Requirements | Checklist of items to verify |
| 12. Warnings and Failure Modes | Known risks |
| 13. Operator Sign-Off | Signature section for accountability |

## Non-Execution Notice

Every review packet begins with this notice:

> **NON-EXECUTION NOTICE**
>
> This review packet is advisory only.
> It does not authorize machine execution.
> It does not generate G-code.
> It does not replace operator judgment.
> Human review and downstream CAM verification are required before machining.

## Validation Requirements

The generator will **refuse** to produce a review packet if:

- The strategy JSON fails A2 validation
- `operation_intent.non_execution_declaration` is not `true`
- `safety_boundary.non_execution_declaration` is not `true`
- `safety_boundary.execution_authority_claim` is `true`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Review packet generated successfully |
| 1 | Strategy validation failed |
| 2 | File/read/write error |

## Operator Sign-Off

The sign-off section requires:

- Confirmation that parameters match specification
- Acknowledgment that the packet is advisory only
- Commitment to independent verification
- Acceptance of responsibility for execution decisions

## Future Extensions

Planned additions:
- PDF export option
- Interactive HTML version
- Diff comparison between strategy versions
- Integration with approval workflow system
