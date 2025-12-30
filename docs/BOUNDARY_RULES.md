<a id="boundary-rules"></a>

# 🔒 Boundary Rules (Enforced by CI)

This repository participates in a **hard architectural boundary** with its sibling system(s).
CI will **fail the build** if code crosses this boundary.

## Purpose

We intentionally separate **measurement**, **interpretation**, and **manufacturing orchestration** to:

* Prevent domain bleed and hidden coupling
* Keep repositories independently testable and deployable
* Preserve long-term architectural sanity as features expand

---

## ToolBox Repo (`luthiers-toolbox`)

**This repo is the design, modeling, and orchestration system.**

### Allowed

* Consuming Analyzer artifacts (JSON, CSV, WAV, PNG, etc.)
* Interpreting measurement facts into advisories
* Geometry, CAM policy, heuristics, and workflow orchestration

### Forbidden (CI-enforced)

Importing Analyzer runtime namespaces:

| Prefix | Reason |
|--------|--------|
| `tap_tone.*` | Analyzer core measurement code |
| `modes.*` | Analyzer modal analysis |

> **Note**: `schemas.*` is NOT forbidden — ToolBox has its own `app/schemas/` package.
> If Analyzer renames to `tap_tone_schemas`, we'll add that to forbidden list.

### Reason

> ToolBox interprets and acts on measurements; it does not perform them.

---

## Analyzer Repo (`tap_tone_pi`)

**That repo is a measurement instrument.**

### Allowed

* Signal acquisition
* Spectra / IR / coherence
* Direct mechanical measurements (fixture-defined, reproducible)
* Artifact logging + manifests
* Provenance capture (hashing, metadata)

### Forbidden (CI-enforced)

Importing ToolBox namespaces:

| Prefix | Reason |
|--------|--------|
| `app.*` | ToolBox application code |
| `services.*` | ToolBox service layer |
| `rmos.*` | Rosette Manufacturing OS |
| `cam.*` | CAM toolpath generation |
| `compare.*` | Comparison workflows |
| `art_studio.*` | Art Studio design tools |

### Reason

> The Analyzer emits **facts**, not interpretations or design advice.

All integration with ToolBox must happen via **artifacts or HTTP APIs**, never Python imports.

---

## Enforcement

CI runs a **Boundary Guard** that statically scans imports (including `importlib.import_module(...)`) and fails fast on violations.

### Running Locally

```bash
cd services/api
python -m app.ci.check_boundary_imports --profile toolbox
```

### If CI Fails

1. Remove the forbidden import
2. Replace it with:
   * Artifact ingestion (JSON, CSV, etc.)
   * HTTP API call
   * Explicit data handoff

**Do not suppress or bypass this guard.**

---

## Mental Model (Rule of Thumb)

> **Analyzer emits facts. ToolBox interprets facts.**
> If you're *interpreting*, you're in ToolBox.
> If you're *measuring*, you're in Analyzer.

---

## Implementation

| File | Purpose |
|------|---------|
| `services/api/app/ci/boundary_spec.py` | Reusable BoundarySpec framework |
| `services/api/app/ci/check_boundary_imports.py` | CLI runner with profile configs |

See also: [ROUTER_MAP.md](../ROUTER_MAP.md) for ToolBox API organization.
