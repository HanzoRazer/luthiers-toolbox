# VEC-ARCHAEO-001 Stage 1 inventory

## Context

VEC-ARCHAEO-001 reconstructs the January–March 2026 build history of the
`luthiers-toolbox` parent repo so later archaeology stages can work from a
frozen, downloadable scan instead of re-walking git. Stage 1 is inventory
only: it lists commits, files, and author-date sessions in the window
`2026-01-01` → `2026-04-01` (exclusive). It does not assign dispositions
and it does not implement or evaluate AGE, IBG, or three-loop architecture.

This packet is **not** the IBG/AGE precursor forensic report
([PR #332](https://github.com/HanzoRazer/luthiers-toolbox/pull/332)).
That report lives under `docs/forensics/` and answers a different question
(lineage and terminology). This inventory is the Stage 1 input for
vectorizer-era build-history work.

## Contents

- Human deliverable: `TIMELINE.md`
- Stage 2 inputs: `commits.jsonl`, `files.jsonl`, `sessions.json`
- Field names and types for those inputs: `SCHEMA.md`
- Evidence: `raw/`

Produced from an isolated `luthiers-toolbox` mirror. Scope is that parent repo only. `vectorizer-sandbox` is not part of this inventory.

Do not copy-paste from the PR. The files are too large.

**After merge, use this download link** (follows `main` and survives branch deletion):

https://github.com/HanzoRazer/luthiers-toolbox/raw/main/reports/archaeology/vec_archaeo_001.zip

**Before merge**, that URL 404s. Use the review-only branch link:

https://github.com/HanzoRazer/luthiers-toolbox/raw/cursor/vec-archaeo-001-inventory-5bd1/reports/archaeology/vec_archaeo_001.zip

Then right-click → Extract All. See `../HOW_TO_DOWNLOAD.md`.
