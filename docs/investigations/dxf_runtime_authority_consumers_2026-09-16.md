# Runtime consumers of the DXF catalog — census and enforcement (2026-09-16)

**Order:** DXF-RUNTIME-AUTHORITY-001 (successor to DXF-CATALOG-GATE-001 / PR #378).
**Baseline:** `bca96983` — 33 catalog files, 6 PASS, 27 QUARANTINED, 0 FAIL.
**Stage 0 method:** searched current `main` for `.dxf`, `instrument_geometry`, `ezdxf.readfile`,
DXF path constructors, `body/dxf/`, `reference_dxf/` and `LesPaul_CAM_Closed`, then classified
every hit by whether it can reach manufacturing output.

## The governing sentence

> **Quarantine records describe known failure; they never grant manufacturing authority.
> Manufacturing authority is a separate positive assertion over a specific catalog asset and its
> exact bytes.** (Owner ruling, 2026-09-16.)

Replacing a file therefore does not restore manufacturing on its own: the replacement's digest has
to be authorized before any manufacturing path will read it.

## Stage 0 census

| Consumer | Catalog asset / path | Reachable from | Output | Manufacturing reach | Authority checked before this order | Class |
|---|---|---|---|---|---|---|
| `generators/lespaul_body_generator.py` (`LesPaulBodyGenerator.__init__`, `from_project`) | `body/dxf/electric/LesPaul_CAM_Closed.dxf`, hard-coded | `POST /api/cam/guitar/les_paul/body/gcode`; `BodyGenerator.for_model("lespaul")`; direct construction | `.nc` G-code | **Yes** | **No** | RUNTIME_MANUFACTURING |
| `generators/lespaul_dxf_reader.py` | whatever path the generator passes | the generator only | parsed geometry | via the generator | No | RUNTIME_MANUFACTURING (reader) |
| `generators/body_generator.py` | passes a path to the Les Paul generator | CAM routers | delegates | via the generator | No | RUNTIME_MANUFACTURING (factory) |
| `generators/stratocaster_body_generator.py`, `acoustic_body_generator.py`, `electric_body_generator.py` | none — they use Python outlines from `body/outlines.py` | CAM routers | `.nc` G-code | No DXF read | n/a | RUNTIME_MANUFACTURING, no catalog DXF |
| `instrument_geometry/body/outlines.py::get_dxf_path()` | any catalog body DXF, by model id | **nothing** — no caller in `app/`, `tests/` or `scripts/` | a `Path` | None today | n/a | DEAD (hands out catalog paths; a future caller would need the resolver) |
| `cam/body_region_selector.py`, `cam/dxf_consolidator.py`, `cam/layer_consolidator.py`, `cam/line_deduplicator.py`, `cam/unified_dxf_cleaner.py`, `cam/contour_reconstructor.py`, `dxf/preflight_service.py`, `cam/dxf_preflight.py` | caller-supplied path or temp file | upload / export routes | cleaned DXF, reports | Yes, for user geometry | n/a — non-catalog contract | RUNTIME_MANUFACTURING, non-catalog |
| `cam/archtop/*`, `core/dxf_geometry.py` | CLI args / demo paths | `__main__` blocks, no importer | files | No | n/a | SCRIPT_ONLY / DEAD |
| `app/ci/check_dxf_files.py`, `scripts/validate_dxf_assets.py` | every catalog DXF | CI workflows | verdicts | No | the gates *are* the check | CI |

**The surface is one manufacturing consumer**, with three entry points, and it is the one the #378
record named. Nothing else in runtime resolves a catalog path. That is why this order stayed
bounded instead of splitting into increments.

## What was built

1. **Schema v3 — positive authorization.** `dxf_catalog_registry.json` gains a
   `manufacturing_authority` section holding `authorized` entries: `{asset, asset_sha256,
   authority: ALLOWED, basis}`. The quarantine block is untouched and still forbids any authority
   but `BLOCKED`; the schema rejects a registry where one asset is both quarantined and authorized.
   **The section is empty today** — no catalog asset is authorized for manufacturing.
2. **Neutral substrate** `app/instrument_geometry/dxf_authority.py`: path normalization (traversal
   cannot present an outside file as a catalog asset), classification, the authorization lookup and
   the digest comparison. Stdlib only; no HTTP, no ezdxf, and no import of `app/ci`. Both CI
   (`dxf_catalog_schema.py`, `dxf_catalog_policy.py`) and the runtime generators read authority
   through it, so they cannot disagree. The CI policy keeps everything else — contract clauses,
   geometry, quarantine judgement.
3. **Enforcement at the manufacturing boundary**, in `LesPaulBodyGenerator.__init__`: the choke
   point all three entry points pass through, before the reader is constructed. `ezdxf.readfile`
   itself is *not* authority-aware — a blocked asset stays readable for inspection, diagnosis,
   migration and adjudication. BLOCKED means forbidden to manufacture from, not forbidden to examine.
4. **The silent fallback is deleted.** `from_project()` used to substitute `LesPaul_body.dxf` when
   the CAM template was missing. A missing manufacturing input now refuses outright.
5. **Deterministic client refusal:** `ManufacturingAuthorityBlocked` (a `ValueError`, so existing
   handlers already map it) carries asset, disposition, reason and exit condition, and the Les Paul
   route returns **422** with that payload — catalog-relative asset name only, no filesystem paths.

## Behaviour change

`POST /api/cam/guitar/les_paul/body/gcode` returned G-code from an `UNADJUDICATED` asset. It now
returns 422 `DXF_MANUFACTURING_AUTHORITY_BLOCKED`, and will keep doing so until a replacement asset
is adjudicated and its digest authorized. This is the intended outcome of the order, not a
regression: no other route changes, because no other runtime path reads a catalog DXF.

## Deliberately not done

Repairing or converting any asset; changing any quarantine record or disposition; promoting
anything to authorized; deciding `WIRING_CHANNEL` or `CUTOUT` semantics; touching instrument
dimensions; changing the non-catalog upload contract; adding any bypass or override.

## Note on this file's name

The order named `dxf_runtime_authority_consumers_2026-09-15.md`; the work landed on 2026-09-16 and
the file is dated for the day it was written.
