# CLAIM RECORD — Investigation 035 (EQ-A01)

Every material finding uses:

```text
STATEMENT
INSTRUMENT
OBSERVATION
SUPPORTED INFERENCE
SCOPE
LIMITATION
FALSIFIER / CONTROL
EVIDENCE
```

Claims below Phase 5 are **baseline / predecessor / selection** only.
Runtime D-status claims are added only after witnesses are frozen.

---

## EQ-A01-035-01 — Production baseline SHA

```text
STATEMENT
  Current origin/main of HanzoRazer/luthiers-toolbox at Phase 0 is
  cab91edacaedc66a0492c35275ce2c255935bf8e.

INSTRUMENT
  git fetch origin main; git rev-parse origin/main

OBSERVATION
  Local HEAD and origin/main both resolve to
  cab91edacaedc66a0492c35275ce2c255935bf8e
  (Merge pull request #353 manufacturing-spine-001 profiling witness).

SUPPORTED INFERENCE
  Investigation 035 repository-production baseline is that SHA.
  It is not independently witnessed as a deployed-production SHA.

SCOPE
  git remote origin of this environment's luthiers-toolbox clone.

LIMITATION
  No deployment SHA was queried.

FALSIFIER / CONTROL
  A later fetch of origin/main yielding a different SHA would supersede
  this as current, without rewriting this Phase 0 freeze.

EVIDENCE
  EXPERIMENTS.md Phase 0; git log -1 origin/main
```

---

## EQ-A01-035-02 — Historical comparator equals current SHA

```text
STATEMENT
  The historical comparator SHA from the 033 census
  (cab91edacaedc66a0492c35275ce2c255935bf8e) is the same commit as current
  origin/main at Phase 0.

INSTRUMENT
  Handoff-stated comparator vs git rev-parse origin/main

OBSERVATION
  Exact match.

SUPPORTED INFERENCE
  Current vs historical SHA identity does not make count series comparable.
  PR #17 census artifacts are not present in this environment.

SCOPE
  SHA identity only.

LIMITATION
  No PR #17 count tables available here to compare instrumentation.

FALSIFIER / CONTROL
  Discovery of PR #17 artifacts with documented instrument identity would
  allow a normalized comparison; until then: comparison not normalized.

EVIDENCE
  SCOPE.md; EXPERIMENTS.md Phase 0
```

---

## EQ-A01-035-03 — Investigation number 035 is free in this tree

```text
STATEMENT
  This luthiers-toolbox tree has no investigations/035-* directory prior
  to this packet. Lab main was not fetchable in this environment.

INSTRUMENT
  glob investigations/** ; gh/repo search for Lab

OBSERVATION
  No investigations/ tree existed on production main. Consolidation Lab
  repository is not in the cloud-agent repo list.

SUPPORTED INFERENCE
  Number 035 is used here. Collision with a Lab-only 035 cannot be
  disproven without Lab access.

SCOPE
  This clone + GitHub search visible to this token.

LIMITATION
  Lab main not fetched. Predecessor 033 directories live in Lab, not here.

FALSIFIER / CONTROL
  A Lab clone showing investigations/035-* already claimed would collide.

EVIDENCE
  README.md Lab placement note; EXPERIMENTS.md Phase 0–1
```

---

## EQ-A01-035-04 — Current Toolbox Vectorizer is a control, not the seed failure

```text
STATEMENT
  Production mounts POST /api/blueprint/vectorize on
  app.routers.blueprint.vectorize_router.vectorize_blueprint, which
  delegates to BlueprintOrchestrator.process_file.

INSTRUMENT
  Static read of vectorize_router.py and blueprint package __init__
  include_router(vectorize_router). Predecessor 033 lineage ruling (handoff).

OBSERVATION
  Router docstring: single production endpoint, thin wrapper over orchestrator.
  Lab 033 Vectorizer lineage correction is cited by handoff as merged; Lab
  files were not re-read here.

SUPPORTED INFERENCE
  IW-03 may use this route as a negative control. This investigation does
  not treat current Toolbox Vectorizer as the original sandbox seam/gap
  failure.

SCOPE
  Static wiring of the blueprint vectorize route on current SHA.

LIMITATION
  Runtime control is a separate claim (IW-03), recorded after witness.

FALSIFIER / CONTROL
  Runtime POST that reaches a different orchestrator or never calls
  vectorize_blueprint.

EVIDENCE
  services/api/app/routers/blueprint/vectorize_router.py
  services/api/app/routers/blueprint/__init__.py
```
