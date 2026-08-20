# Mesh-pipeline scaffold and plate-solver debt — MAINT-DEFER-013 / 010

**Registered:** 2026-08-19
**Surfaced by:** review of PR #305 (MESH-MAT-001). Neither item is caused by that PR.
**Status:** QUEUED — evidence recorded, no fix applied

---

## MAINT-DEFER-013 — `mesh-pipeline-ci` demo steps import a module that was deleted

### Verdict

`ee36ddf1` (2026-02-10, "refactor(api): remove orphaned feature modules (Phase 4)")
deleted `services/api/app/retopo/` — 612 lines across five files, including
`run.py`, which defined `run_pipeline`. Its own commit body describes the package
as *"unused retopology tools."*

That description was accurate for application code, and still left live callers behind.
At `ee36ddf1^` the only importers of `app.retopo` were the package's own `run.py` and
`examples/retopo/run.sh`; nothing under `services/api/app/` imported it. So the sweep's
"unused" was true within the scope it checked — Python imports from application code — and
that scope did not include a shell script, or the workflow that runs one.

**The transferable lesson is the detection criterion, not the deletion.** An orphan check
that reads only Python imports will keep removing code that shell, CI, and docs still call.

Two consumers were left behind and neither was updated:

- `examples/retopo/run.sh:16` — `from app.retopo.run import run_pipeline`
- `.github/workflows/mesh-pipeline-ci.yml:52-56` — runs that script twice
  (`qrm` and `miq` presets), then validates its outputs at `:58-59`

So the workflow invokes a script that imports a package this repository no longer
contains. `git ls-tree -r origin/main` confirms `services/api/app/retopo` is absent.

### Failure

```
ModuleNotFoundError: No module named 'app.retopo'
```

Witnessed on PR #305, job `96184751868`, step **Run example (QRM preset)**.

The earlier symptom in the same job was a *collection* error
(`No module named 'services'`), fixed by adding `PYTHONPATH=.` in `184670a7`.
That fix was correct and it exposed this deeper one — the classic pattern where
repairing the outer failure reveals what it was masking.

### Correction — the workflow is green now, and this record's first draft was wrong

The first draft of this document said `mesh-pipeline-ci` was "failure on every run on `main`"
and that the two demo steps were "structurally unfixable". **Both statements are wrong** and are
corrected here rather than silently edited, because the original wording was cited in PR #309.

Actual run history on `main` — 7 runs retained by GitHub, **6 failure and 1 success**:

| conclusion | date | head |
|---|---|---|
| failure | 2026-01-21 | `d61d17dd` |
| failure | 2026-02-07 | `aa197b6f` |
| failure | 2026-02-07 | `c4f1749f` |
| failure | 2026-02-10 | `19a4d33e` |
| failure | 2026-02-10 | `9d20f8b8` |
| failure | 2026-03-08 | `3ec0b1cb` |
| **success** | **2026-08-19** | **`93b3e581`** |

Two caveats on that table: GitHub retains a limited run window, so "7 runs" is what is *visible*,
not necessarily what ever ran. And the earliest visible failure (2026-01-21) predates the
2026-02-10 deletion, so the deletion is not the origin of the red — it is one contributor to a
job that was already failing.

### What made it green

`examples/retopo/run.sh` gained an `except ImportError` branch, merged alongside PR #305 as
`93b3e581`. When `app.retopo` cannot be imported the script now writes `qa_core.json` and
`cam_policy.json` itself, and the workflow's next step validates those.

`services/api/app/retopo` is **still absent**. Nothing was restored. The steps were made to pass
without the pipeline they claim to exercise, so "structurally unfixable" was doubly wrong: they
were fixable, and they were fixed — by removing the dependency on the thing being tested.

### Why it still belongs in the queue

The stub is honest at the artifact level: `overall_status` is `review_required` and a note names
the absent module. Nothing is disguised to someone who opens the file. But the two demo steps now
exercise the fallback's own JSON literals rather than a pipeline, so a green `mesh-pipeline-ci`
no longer carries the meaning a reader will take from it. The debt moved from visible to
invisible, which is the harder state to notice later.

### Restore trigger

One of, explicitly chosen — a disposition question, not a bug fix. The stub has made
this three-way rather than two:

1. **Restore** `services/api/app/retopo/` from `ee36ddf1^` if the retopology lane is
   still wanted, and let the example and workflow exercise it again; or
2. **Retire** the scaffold — delete `examples/retopo/`, drop the three demo steps from
   `mesh-pipeline-ci.yml`, and let the workflow test only what exists; or
3. **Keep the stub deliberately** — which is a legitimate choice, but then the workflow
   should stop naming those steps as if they run a pipeline, so a reader is not misled
   by the step name alone.

Done-condition either way: `mesh-pipeline-ci` reaches a terminal green on `main`,
or the workflow no longer claims to exercise a pipeline the repo does not have.

### Scope limits

No fix applied. The failure *rate* is not at issue here — the job is
deterministically red, not flaky. Whether the retopology lane should come back is
an owner decision; this record does not presume it.

---

## MAINT-DEFER-014 — `solve_rayleigh_ritz` eigensolver: explicit inverse, and a fallback that lies

### Verdict

`services/api/app/calculators/plate_design/rayleigh_ritz.py:650-657` solves what
its own comment calls a generalized eigenproblem by forming an explicit inverse
and then silently degrading to something that is not a solve at all:

```python
# Solve generalized eigenvalue problem: K v = λ M v
# where λ = ω²
try:
    eigenvalues, eigenvectors = np.linalg.eig(np.linalg.inv(M) @ K)
except np.linalg.LinAlgError:
    # Fallback to scipy if available
    eigenvalues = np.diag(K) / np.diag(M)
    eigenvectors = np.eye(len(eigenvalues))
```

Three separate problems:

1. **Explicit `inv(M)` .** Forming the inverse and multiplying is less accurate and
   less stable than solving directly. Symmetry was measured rather than assumed: for a
   4x4 basis under both SIMPLY_SUPPORTED and CLAMPED, `K` and `M` come out **exactly**
   symmetric (relative asymmetry `0.00e+00`) and `M` is positive definite (min eigenvalue
   `3.15e-02`). A symmetric-definite generalized solver is therefore applicable on the
   problem's own terms rather than as a stylistic preference
   (`scipy.linalg.eigh(K, M)`), or at minimum `np.linalg.solve` rather than
   `np.linalg.inv`. `inv(M) @ K` is also not symmetric, which is why the general
   `eig` is being used instead of `eigh`.

2. **The fallback comment does not describe the fallback.** It says *"Fallback to
   scipy if available"*; scipy is never imported and never called. What actually
   runs is `np.diag(K) / np.diag(M)` — the ratio of diagonals, i.e. every
   off-diagonal coupling discarded — with `np.eye(...)` for the mode shapes, i.e.
   every mode shape replaced by a unit vector. That is not equivalent to the stated
   generalized solve; it is a diagonal approximation returning similarly shaped outputs.

3. **The degradation is silent.** Nothing in the returned structure records that
   the fallback ran, so a caller cannot distinguish a real solve from diagonal
   ratios with identity mode shapes. Downstream, `:660-661` then takes
   `np.real(eigenvalues)`, discarding any imaginary part that non-symmetric `eig`
   can produce, without flagging that it did so.

### Provenance

All of this **predates PR #305**, which touched only `gauss_legendre` in this file.
It is recorded now because that PR put the file under review and because
MESH-MAT-001's predictor is a new consumer of this solver — the first one whose
outputs are published as governed sidecars.

### Restore trigger

Solve the generalized problem directly (`scipy.linalg.eigh(K, M)` if scipy is an
acceptable dependency here, else `np.linalg.solve`-based symmetric handling), and
make any fallback **explicit in the result** rather than silent — either raise, or
return a flag the caller must read. Correct the comment to describe whatever the
fallback actually does.

Done-condition: a test that feeds a plate with known analytic modal frequencies
(simply-supported isotropic is closed-form) and asserts agreement to a stated
tolerance, plus a test proving the fallback path is observable from the outside.

### Scope limits

No fix applied. Changing an eigensolver is a real numerical change with its own
blast radius — existing plate-prediction outputs could move, and by how much is not
established here since no before/after comparison was run — so it needs its own PR, its
own witnesses, and a decision about whether scipy may be added. It
should NOT ride along with a feature branch.
