# CAM Assist Blueprint

## Project Identity

CAM Assist is a **strategy export assistant** for lutherie manufacturing. It translates instrument design intent into reviewable, portable strategy packages (DXF + JSON + checklist).

## What This Is

- Human-guided manufacturing intelligence
- Strategy documentation system
- Portable output format generator

## What This Is Not

- G-code generator
- Machine controller
- Autonomous CAM AI
- Generic CAM replacement

## Core Principle

**Human authority over manufacturing decisions is non-negotiable.**

Every strategy package requires explicit human approval.

## First Implementation Slice

**Fret Slot Strategy Export** — produces DXF geometry + strategy JSON + review checklist for fret slot operations.

## Repository Structure

```
docs/           # Product and workflow documentation
schemas/        # JSON Schema definitions
samples/        # Reference strategy packages
```

## Development Guidelines

1. Do not generate G-code or machine control signals
2. All outputs require human review workflow
3. DXF is the primary geometry interchange format
4. Strategy JSON carries parameters, not toolpaths
5. Every operation needs a review checklist

## Key Documents

- `docs/CAM_ASSIST_SYSTEM_DEFINITION.md` — Product boundaries
- `docs/HUMAN_AUTHORITY_MODEL.md` — Approval workflow
- `docs/CAM_ASSIST_OPERATION_TAXONOMY.md` — Supported operations
