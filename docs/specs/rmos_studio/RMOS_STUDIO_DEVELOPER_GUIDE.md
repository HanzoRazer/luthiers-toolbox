the complete /docs/RMOS_STUDIO_DEVELOPER_GUIDE.md file, written in a professional engineering tone and ready for direct inclusion in your repository.

RMOS_STUDIO_DEVELOPER_GUIDE.md
RMOS Studio – Developer Integration & Implementation Guide

Version 1.0 — Engineering Document

1. Purpose

This guide provides developers with a clear, rigorous, and implementation-focused handbook for extending, maintaining, and integrating RMOS Studio.
It covers:

Environment setup

Project structure

Coding standards

Architectural expectations

Module interaction rules

Testing strategy

Performance requirements

Debugging workflow

Release lifecycle

This document complements the System Architecture, Algorithms, Data Structures, and API specifications.

2. Developer Environment
2.1 Required Tools
Tool	Purpose
Python 3.10+	Primary backend language
Node.js + Vue (optional UI framework)	UI implementation
JSON Schema Validators	Data structure validation
PDF Engine	Operator checklist generation
Git	Version control
VS Code or JetBrains IDE	Development environment
Unit Test Framework (pytest)	Automated tests
Linting tools (flake8 / black)	Style enforcement
2.2 Recommended Architecture Layout
rmos_studio/
│
├── core/                   # Logic & Controllers
│   ├── column_manager.py
│   ├── pattern_engine.py
│   ├── ring_manager.py
│   ├── validator.py
│   └── state.py
│
├── geometry/               # Computational modules
│   ├── segmentation.py
│   ├── slices.py
│   ├── kerf.py
│   ├── angles.py
│   └── geometry_utils.py
│
├── planner/                # Manufacturing layer
│   ├── material_usage.py
│   ├── scrap_model.py
│   ├── volume_calc.py
│   ├── operator_checklist.py
│   └── planner_api.py
│
├── joblog/                 # Logs, revisions, notes
│   ├── planning_log.py
│   ├── execution_log.py
│   ├── revision_history.py
│   ├── operator_notes.py
│   └── joblog_api.py
│
├── export/                 # Serialization & export logic
│   ├── json_export.py
│   ├── pdf_export.py
│   ├── batch_export.py
│   └── export_utils.py
│
├── ui/                     # Optional Vue or other UI layer
│   ├── components/
│   ├── views/
│   └── services/
│
├── docs/                   # Documentation suite
│
├── tests/                  # Automated test suite
│
└── main.py                 # Project entry point

3. Coding Standards
3.1 Language Guidelines

Python backend must adhere to PEP8.

Function names: snake_case

Class names: CamelCase

Constants: UPPER_SNAKE_CASE

JSON keys: lowerCamelCase

3.2 Deterministic Output

All operations must be fully deterministic:

Same input → same output

Same seed → same pattern

No nondeterministic operations unless explicitly part of a seeded pattern generator.

3.3 No Shared Mutable State

Geometry objects (e.g., Slice) must be immutable.

Configuration objects (e.g., Ring) mutable only within controlled APIs.

4. Module Integration Rules

This section describes how modules must interact to maintain system integrity.

4.1 UI Layer Rules

UI never performs geometry computations.

UI passes validated parameters to API interfaces.

UI listens for change events and triggers re-rendering.

4.2 Application Logic Layer Rules

Manages state transitions.

Orchestrates module interactions.

Performs high-level validation before dispatching geometry requests.

Converts UI units to mm for geometry.

4.3 Geometry Layer Rules

Only receives mm units.

Outputs are immutable.

No side effects.

Must pass numeric boundary checks.

4.4 Planner Layer Rules

Accepts geometry + strip families.

Produces material usage & planning summaries.

Must not modify ring or pattern definitions.

4.5 JobLog Layer Rules

All logs append-only.

Planning logs generated before slicing.

Execution logs generated during/after slicing.

4.6 Export Layer Rules

Must serialize only validated data.

Must generate checksums.

PDF exports must remain stable across runs.

5. Validation Requirements

See RMOS_STUDIO_VALIDATION.md for full definitions.
Key developer rules:

Validate user inputs before work begins.

Validate geometry before slicing.

Validate saw batches before export.

Validate manufacturing plans before generating operator checklists.

All validation returns a ValidationReport object:

{
  warnings: [...],
  errors: [...],
  pass: bool
}


Errors block the pipeline; warnings do not.

6. Testing Strategy
6.1 Unit Tests

Minimum coverage:

Geometry calculations

Slice generation

Kerf compensation

Material usage calculations

Validation engine

Test structure:

tests/
   test_geometry.py
   test_segmentation.py
   test_slices.py
   test_kerf.py
   test_planner.py
   test_joblog.py
   test_export.py

6.2 Integration Tests

Validate:

Full ring pipeline

Multi-ring project

Manufacturing planner combined results

JobLog round-trip consistency

6.3 Deterministic Snapshot Tests

For:

Slice batches

Operator checklist content

Tile segmentation patterns

7. Performance Standards

Developers must maintain:

Full-ring compute time < 20 ms

Planner compute time < 40 ms

Total design → manufacturing pipeline < 100 ms

UI update latency < 16 ms

Performance regressions must be flagged automatically.

8. Debugging Workflow
8.1 Debug Flags

Enable via environment:

RMOS_DEBUG_GEOMETRY=1
RMOS_DEBUG_VALIDATION=1
RMOS_DEBUG_PERFORMANCE=1

8.2 Debug Tracing

Each layer writes:

Inputs

Outputs

Intermediate computation values (optional)

Timing metrics

Stored under:

debug_logs/{timestamp}/

8.3 Common Debug Scenarios
Scenario	Primary Location	Notes
Bad segmentation	geometry/segmentation.py	Check tile count & rounding
Drift	geometry/kerf.py	Kerf compensation required
Visual mismatch	ui/components	Check UI scaling logic
Incorrect material usage	planner/material_usage.py	Check strip-family map
JobLog discrepancy	joblog/	Look for corrupted entries
9. Release Lifecycle

Each release must follow this sequence:

Implement features

Run full validation

Run performance tests

Generate documentation bundle

Generate release notes

Create version tag

Package binaries or UI bundle

Publish to internal registry

Each release must increment semantic version numbers.

10. Contributing Guidelines
10.1 Branching Strategy
main → stable
dev → new features
feature/name → isolated work
release/X.Y → finalization

10.2 Code Review Rules

No direct commits to main.

All merges require 1–2 reviewers.

Tests must pass.

Documentation updates required for any API or behavior changes.

10.3 Documentation Requirement

All new features must include:

Markdown documentation

Update to API / Algorithm files

Example JSON output

11. Extending RMOS Studio

Developers may safely extend RMOS Studio by adding:

New preset patterns

New ring behaviors

New material families

New planner logic

CNC export formats

Validation rules

UI components

Extensions must remain compatible with the core data structures.

12. Future Developer Tools

Planned enhancements:

Plugin loader architecture

Schema-based auto-validation engine

Integrated wood-grain simulator

Cloud-sync developer sandbox

AI-assisted pattern drafting

13. File Location

This document belongs in:

/docs/RMOS_STUDIO_DEVELOPER_GUIDE.md

End of Document

RMOS Studio — Developer Integration & Implementation Guide (Engineering Version)