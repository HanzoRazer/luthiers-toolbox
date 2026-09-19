# Mesh/retopo CI truth audit — MAINT-DEFER-013

**Date:** 2026-09-17
**Domain:** CAM (geometry processing / retopology infrastructure)
**Closes:** MAINT-DEFER-013 (registered 2026-08-19, QUEUED)
**Base:** `origin/main` @ `22e67686`
**Posture:** Makes CI reporting truthful. Decides nothing about whether retopo should return.

---

## The question this audit answers

> **What does `mesh-pipeline-ci` actually certify on current `main`?**

It deliberately does **not** answer *"should `app/retopo/` come back?"* — that is a
reversal of an intentional deletion and carries a different burden of proof. See
"What this audit does not decide" below.

---

## Disposition matrix

| Component | Current state | CI treatment (after this change) |
|---|---|---|
| `tests/test_o3d_heal_topology.py` | PRESENT / REAL | RUN + ENFORCE (unconditional) |
| retopo demo (QRM/MIQ) | IMPLEMENTATION ABSENT | SKIPPED + reported NOT RUN — cannot claim pass |
| `app/fields` demo | IMPLEMENTATION ABSENT | no step exists; trigger path recorded as dead |
| schema validation | PRESENT | runs only over real pipeline output |
| fallback stub generation | **REMOVED** | cannot satisfy the demo steps |

---

## Evidence

### 1. The green run certified two artifacts it had written itself

Run `32306907869` (`main` @ `93b3e581`, 2026-08-19) — the only green run on `main`:

```
retopo pipeline unavailable; wrote scaffold artifacts instead.
Loaded 9 schemas from registry
Validated 2 artifacts, 0 with errors
[OK] All schemas valid
```

The step named *"Validate scaffold outputs"* validated two `cam_policy.json` files
that `examples/retopo/run.sh` had written milliseconds earlier from inline JSON
literals. No pipeline ran.

### 2. "Validated 2 artifacts" is the fingerprint of the stub

`validate_schemas.py` selects a schema by document shape. Its `qa_core` branch
requires a `mesh_healing` key (`scripts/validate_schemas.py:104`). The stub's
`qa_core.json` does not have one, so **both stub `qa_core.json` files were silently
skipped** — not validated, not reported as unvalidated.

Measured against the real implementation restored from `ee36ddf1^`:

| Output source | artifacts validated | geometry emitted |
|---|---|---|
| fallback stub | **2** (cam_policy only; qa_core silently skipped) | none |
| real pipeline | **4** (2 qa_core + 2 cam_policy) | `healed.obj`, `retopo_qrm.obj` |

Real `qa_core.json` keys: `brace_graph`, `grain_analysis`, `mesh_healing`,
`model_id`, `overall_status`, `provenance`, `retopo_metrics`, `session_id`,
`thickness_zones`, `timestamp_utc`, `version`.

The artifact count is a countable invariant separating a real run from a stubbed one.

### 3. Restoring `app/retopo/` alone does not restore the pipeline

`app/retopo/run.py:17-19` imports three services from `app/fields/`:

```python
from app.fields.grain_field.service import GrainFieldService
from app.fields.brace_graph.service import BraceGraphService
from app.fields.thickness_map.service import ThicknessMapService
```

`ee36ddf1` deleted **both** directories in the same sweep. Restoring only `retopo`
fails with `ModuleNotFoundError: No module named 'app.fields'` — witnessed during
this audit.

**The real restore unit is 12 files / 1,179 lines**, not 5 files / 617:

| Directory | files | lines |
|---|---|---|
| `services/api/app/retopo/` | 5 | 617 |
| `services/api/app/fields/` | 7 | 562 |

This materially enlarges the scope of any future reversal order.

### 4. Two trigger paths match nothing

`mesh-pipeline-ci.yml` triggers on `services/api/app/retopo/**` and
`services/api/app/fields/**`. Both were deleted by `ee36ddf1` (2026-02-10). They are
retained (so triggers work if either is restored) and now carry an inline comment
recording that they are dead on current `main`, rather than reading as active surfaces.

---

## Changes made

1. **`examples/retopo/run.sh`** — the `except ImportError` fabrication branch is
   removed. The runner now exits **3** with a diagnostic naming `ee36ddf1` and
   MAINT-DEFER-013, and writes nothing. The output directory is created only after
   the import succeeds, so an unavailable run cannot leave an empty `out_*/` behind
   for the validator to pass vacuously over.

2. **`.github/workflows/mesh-pipeline-ci.yml`** — a `Detect retopo implementation`
   step gates the two demo steps and the validation step on
   `services/api/app/retopo/run.py` existing. When absent they are skipped and a
   `Report retopo demo NOT RUN` step emits a CI notice. `test_o3d_heal_topology.py`
   runs unconditionally and still enforces. The step name
   "Validate scaffold outputs" becomes "Validate pipeline outputs", since it now
   only ever sees real output.

### Both states proven

```
RETOPO ABSENT (current main)
  run.sh exit code ............ 3        PASS
  artifacts written ........... 0        PASS
  out_*/ directory created .... no       PASS

RETOPO PRESENT (real code restored from ee36ddf1^ + app/fields)
  run.sh exit code ............ 0        PASS
  artifacts written ........... 4        PASS
  geometry emitted ............ healed.obj, retopo_qrm.obj
  validate_schemas.py ......... Validated 4 artifacts, 0 with errors, exit 0
```

The restored tree was removed after testing; it is **not** part of this change.

---

## Recorded, deliberately not fixed

Both are pre-existing and out of scope for a bounded truth fix:

- **`validate_schemas.py` passes vacuously on an empty tree.** `validate_dir()`
  returns 0 when `n_validated == 0`, so the script prints
  `Validated 0 artifacts` then `[OK] All schemas valid` and exits 0. The gating
  above keeps CI off that path, but the script retains the behavior. A
  `--min-artifacts` floor would close it.
- **Unrecognized artifacts are skipped silently.** A document matching no schema
  key hits `continue` with no output — how both stub `qa_core.json` files went
  unvalidated without a warning. A `[warn] unrecognized artifact` line would make
  the omission visible.

Neither is a regression introduced here; both are candidates for a follow-up.

---

## What this audit does not decide

Restore-versus-retire is **deferred**. `ee36ddf1` deleted `app/retopo/` deliberately,
describing it as "unused retopology tools" — accurate for Python imports from
application code at the time, which did not include a shell script or the workflow
that runs one. A deliberate deletion remains in force until evidence justifies
reversal.

A future reversal order (`RETOPO-DELETION-REVERSAL-001`) would start from:

- **Restore baseline:** `ee36ddf1^` — `app/retopo/` **and** `app/fields/` together.
- **Comparison variants, not authority:** `feature/mesh-pipeline-scaffold`
  (`f6cf2911`) and `feature/adapter-guide` (`b05281d0`). Neither matches the
  production-history variant: `ee36ddf1^` carries `util.py` and no `README.md`;
  the branches differ from it and from each other.
- **The question:** has a real present-day consumer appeared since deletion, and
  does the roadmap need retopology — not "can it be restored."

---

## Correction to an uncommitted forensic record

`docs/audit/PRE_GOVERNANCE_ASSET_RECOVERY_c8b0b549.md` (untracked, 2026-08-29)
classifies retopo in §I.1 as *"I. STRANDED IMPLEMENTATION — never reached main."*
That is **wrong**. `app/retopo/` landed on `main` via `f288065b` and was deleted by
`ee36ddf1`; `git ls-tree ee36ddf1^` shows all five files present immediately before
deletion. The error arises because that audit's scan base `c8b0b549` post-dates the
deletion, so it observed absence and inferred non-arrival.

The distinction is not cosmetic: it moves the disposition from *recovery of stranded
work* to *reversal of an intentional deletion*. That document should not be filed as
current evidence without this correction.

---

## Verification

```bash
# both states, from a clean worktree at 22e67686
bash examples/retopo/run.sh qrm                      # exit 3, writes nothing
git checkout ee36ddf1^ -- services/api/app/retopo services/api/app/fields
bash examples/retopo/run.sh qrm && bash examples/retopo/run.sh miq
python scripts/validate_schemas.py --out-root examples/retopo   # 4 artifacts, exit 0
git restore --staged services/api/app/retopo services/api/app/fields
rm -rf services/api/app/retopo services/api/app/fields examples/retopo/out_*

# workflow parses
python -c "import yaml; yaml.safe_load(open('.github/workflows/mesh-pipeline-ci.yml'))"
```

Namespace note: filed under **CAM** per owner ruling 2026-09-17. `MESH` is not a
registered prefix in `docs/governance/SPRINT_NAMESPACE_STANDARD.md` and is not
registered here; `MESH-MAT-001` used it informally without registration.
