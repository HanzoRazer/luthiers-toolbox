# Mesh-pipeline scaffold and plate-solver debt — MAINT-DEFER-009 / 010

**Registered:** 2026-08-19
**Surfaced by:** review of PR #305 (MESH-MAT-001). Neither item is caused by that PR.
**Status:** QUEUED — evidence recorded, no fix applied

---

## MAINT-DEFER-009 — `mesh-pipeline-ci` demo steps import a module that was deleted

### Verdict

`ee36ddf1` (2026-02-10, "refactor(api): remove orphaned feature modules (Phase 4)")
deleted `services/api/app/retopo/` — 612 lines across five files, including
`run.py`, which defined `run_pipeline`. Its own commit body describes the package
as *"unused retopology tools."*

It was not unused. Two consumers were left behind and neither was updated:

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

### This is older and broader than PR #305

`mesh-pipeline-ci` has been **failure on every run on `main`** as far back as the
run history goes: 2026-03-08, 2026-02-10 (×2), 2026-02-07 (×2), 2026-01-21.

Note the ordering: the workflow was already red on 2026-01-21, *before* the
2026-02-10 deletion. So the deletion is not the origin of the red — but it did
make the two demo steps structurally unfixable, because the code they call no
longer exists at any commit reachable from `main`.

### Restore trigger

One of, explicitly chosen — this is a disposition question, not a bug fix:

1. **Restore** `services/api/app/retopo/` from `ee36ddf1^` if the retopology lane
   is still wanted, and let the example and workflow work again; or
2. **Retire** the scaffold — delete `examples/retopo/`, drop the three demo steps
   from `mesh-pipeline-ci.yml`, and let the workflow test only what exists.

Done-condition either way: `mesh-pipeline-ci` reaches a terminal green on `main`,
or the workflow no longer claims to exercise a pipeline the repo does not have.

### Scope limits

No fix applied. The failure *rate* is not at issue here — the job is
deterministically red, not flaky. Whether the retopology lane should come back is
an owner decision; this record does not presume it.

---

## MAINT-DEFER-010 — `solve_rayleigh_ritz` eigensolver: explicit inverse, and a fallback that lies

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
   less stable than solving directly. `K` and `M` are symmetric here, so the
   natural call is a symmetric-definite generalized solver
   (`scipy.linalg.eigh(K, M)`), or at minimum `np.linalg.solve` rather than
   `np.linalg.inv`. `inv(M) @ K` is also not symmetric, which is why the general
   `eig` is being used instead of `eigh`.

2. **The fallback comment does not describe the fallback.** It says *"Fallback to
   scipy if available"*; scipy is never imported and never called. What actually
   runs is `np.diag(K) / np.diag(M)` — the ratio of diagonals, i.e. every
   off-diagonal coupling discarded — with `np.eye(...)` for the mode shapes, i.e.
   every mode shape replaced by a unit vector. That is not a degraded solve of the
   stated problem; it is a different calculation returning the same shape.

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
blast radius — every existing plate-prediction number could move — so it needs its
own PR, its own witnesses, and a decision about whether scipy may be added. It
should NOT ride along with a feature branch.
