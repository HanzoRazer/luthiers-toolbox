# GEN-5-A — Instrument Library Source Census + Canonical Schema Proposal

**Status:** Dev-ready handoff (implemented — see confirmation note)
**Created:** 2026-07-06
**Baseline:** origin/main at `acadef99` (#201 merged)
**Recommended branch:** `docs/gen5-instrument-library-source-census`
**Owner lane:** SPRINTS.md backlog / instrument-library data consolidation

## Purpose

Turn GEN-5 from a broad "five conflicting registries" backlog item into a bounded,
witnessable first slice. GEN-5's long-term target is a canonical
`instrument_library.json` organized as `family -> model -> variant`. **This first
slice does not create that runtime authority yet.** It builds the source census and
schema proposal needed before any registry is rewritten or retired.

## Grounding Evidence

SPRINTS.md records GEN-5 as queued and high priority because instrument library work
lacks a single home. The five sources:

- `services/api/app/instrument_geometry/guitars/__init__.py` — `MODEL_SPECS`
- `services/api/app/instrument_geometry/instrument_model_registry.json`
- `services/photo-vectorizer/body_dimension_reference.json`
- `services/api/app/data_registry/system/instruments/body_templates.json`
- `services/api/app/instrument_geometry/body/catalog.json`

Fresh grounding on `origin/main` (the stale SPRINTS.md counts had drifted):

| Source | Current observed shape |
|---|---|
| `MODEL_SPECS` | 19 runtime spec factories |
| `instrument_model_registry.json` | 25 top-level model keys under `models` |
| `body_dimension_reference.json` | 15 non-comment dimension-prior entries |
| `body_templates.json` | 7 body template entries under `bodies` |
| `body/catalog.json` | 23 body catalog entries under `bodies` |

The sources are **not all duplicates**. They serve different roles: metadata, runtime
spec factories, vectorizer scale priors, body templates, body catalog/outline metadata,
assets, status, and CAM capability flags.

> **Implementation grounding confirmation (2026-07-06, `acadef99`).** The GEN-5-A census
> utility reproduced these exact counts (19 / 25 / 15 / 7 / 23) — **no material drift**,
> grounding stands. Census result: **35 distinct normalized models**, **10 cross-source
> conflicts** on same-semantic dimension fields (`scale_length_mm`, `body_length_mm`).
> Largest: `gibson_sg` body length 444 vs 394 mm (Δ50). All reported, none resolved.
> Authoritative live counts now live in `services/api/metrics/gen5_instrument_library_census.json`.

## Scope

Create a deterministic census of instrument-library source coverage and a canonical
schema proposal. It answers: which model IDs exist in each source; which are aliases /
naming variants; which source owns each field category today; where dimensions conflict;
which entries are missing from one source but present in another; which values are safe
to copy later vs require human/data review. **Output is evidence and a schema proposal,
not a runtime switch.**

## Non-Goals

- Do not create production `instrument_library.json` in this slice.
- Do not delete, rewrite, or mark generated any of the five legacy sources.
- Do not change public API responses.
- Do not migrate routers or services to a new loader.
- Do not resolve dimension conflicts by picking winners.
- Do not move Sprint 8 model JSON specs yet.
- Do not decide geometry authority or body-outline authority.
- Do not update endpoint counts, router baselines, or branch-protection settings.

## Decisions

1. **GEN-5-A is a census, not a consolidation.** Record current source coverage; propose
   the shape of the future canonical library.
2. **Current source roles are preserved.** A model appearing in multiple files is not
   automatically a duplicate. The census classifies each file's role: metadata, dimensions,
   template data, catalog/outline data, assets, CAM flags, or runtime spec factories.
3. **Conflicts are findings, not fixes.** Disagreements (scale length, lower bout width,
   body length, status, asset references) are reported with both values and source paths.
   No winner is chosen.
4. **Normalize IDs only for comparison.** Compare normalized IDs (hyphen/underscore
   variants, known aliases) but keep original source IDs visible.
5. **Provenance is required for later migration.** The schema proposal includes a
   `source_provenance` strategy so any future canonical record can say where each field
   came from.
6. **Legacy consumers stay on legacy sources.** `registry_router.py`, `registry_cam_router.py`,
   `assets_router.py`, `layer_builder.py`, the data registry, and `guitars/__init__.py`
   keep reading exactly what they read today.
7. **The future canonical library is field-role based** — not one undifferentiated blob.

## File-by-File Plan (as implemented)

- **`services/api/scripts/build_instrument_library_census.py`** — new stdlib-only utility
  (`json/ast/argparse/os/sys/datetime/pathlib`). Loads the four JSON sources and AST-parses
  `guitars/__init__.py` + `models.py` (enum member→value) for `MODEL_SPECS`/`MODEL_INFOS`
  keys **without importing `app.*`**. Normalizes IDs (explicit alias map only), classifies
  field roles, emits conflicts, missing-by-source, and a schema proposal. Deterministic
  (sorted keys/rows); `generated_at` is the only non-deterministic field and is excluded
  from `--check`.
- **`services/api/metrics/gen5_instrument_library_census.json`** — generated census artifact.
- **`docs/audit/GEN5_INSTRUMENT_LIBRARY_SOURCE_CENSUS.md`** — human-readable audit (required):
  summary, source roles, counts, coverage table, conflicts, alias issues, proposed schema,
  rollout, explicit non-disposition statement.
- **`services/api/tests/test_gen5_instrument_library_census.py`** — focused tests.
- **`.cbsp21/patches/gen5-instrument-library-source-census.json`** — per-PR manifest.
- **`SPRINTS.md`** — small GEN-5-A progress note only (does not close GEN-5, does not
  hand-edit the stale historical counts — the census JSON is the current-count authority).

## Canonical Schema Proposal

Included in the audit/report, **not used by runtime code**. Field-role based
(`metadata`, `physical_dimensions`, `body_template`, `body_catalog`, `runtime_spec`,
`assets`, `cam_capability`) with a `source_provenance` group recording the origin of each
field group. See the audit report / census JSON `schema_proposal`.

## Utilities

```
python services/api/scripts/build_instrument_library_census.py --write
python services/api/scripts/build_instrument_library_census.py --check
```

- `--write` regenerate JSON + Markdown.
- `--check` fail if artifacts differ from freshly-computed census (`generated_at` ignored).
- `--json-out` / `--md-out` / `--repo-root` for tests; `--now` / env `GEN5_CENSUS_NOW` freeze the timestamp.

## Test Cases

```
python -m pytest services/api/tests/test_gen5_instrument_library_census.py -q
python services/api/scripts/build_instrument_library_census.py --check   # exit 0 when fresh
```

Coverage: all five source readers, ID normalization, representative IDs
(`stratocaster`, `les_paul`, `flying_v`, `dreadnought`, `om_000`), original-vs-normalized
IDs, source-specific entries reported not dropped, conflicts as structured records,
deterministic output, and **no `app.*` imports**.

## Safety Checks

```
git diff --name-only origin/main...
```

Expected runtime-affecting files changed: **none.** The new utility lives under
`services/api/scripts`, but no router/service imports it.

## Rollout Order

1. Fresh isolated worktree from `origin/main`.
2. Re-run source presence check for the five sources.
3. Add utility → tests → generate JSON → author audit MD → add CBSP21 manifest.
4. Run unit tests, `--check`, CBSP21 gates.
5. Open PR as GEN-5-A. Add SPRINTS.md note in-PR (owner-selected: progress note only).

## Acceptance Criteria

Five sources parsed without importing `app.*`; deterministic JSON census under
`services/api/metrics/`; human audit under `docs/audit/` with the future-schema proposal;
conflicts reported not resolved; no public API/router/service/registry/model/vectorizer
behavior change; tests prove the utility and artifact shape; **GEN-5 remains open**.

## Follow-Up Slices

- **GEN-5-B** — candidate `instrument_library.json` with field-level provenance (no consumers).
- **GEN-5-C** — compatibility loader (`as_model_registry()`, `as_body_dimension_reference()`,
  `as_body_templates()`, `as_body_catalog()`).
- **GEN-5-D** — migrate consumers one at a time (registry router, CAM registry router,
  assets router, `layer_builder.py` scale correction, data-registry body templates,
  `guitars/__init__.py` spec lookup if feasible).
- **GEN-5-E** — retire or generate legacy artifacts, only after consumers migrate.

## Stop-and-Ask Conditions

Stop and ask before proceeding if: the census requires changing any legacy source; a
runtime consumer must change to make the report work; `MODEL_SPECS` can't be inspected
without importing app modules; a conflict appears safety-critical for CAM output; a
proposed schema would implicitly decide geometry/body-outline authority; the artifact is
too noisy to remain deterministic in CI; or the branch needs to touch unrelated dirty
files.
