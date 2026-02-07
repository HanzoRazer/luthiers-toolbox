# How to run the Agentic Spine locally (can't-screw-up edition)

This repo includes a minimal "agentic spine":
- Contract parity tests
- Moment detector tests
- Decision policy tests
- Replay smoke test (synthetic JSONL fixture)

This guide is the **single source of truth** for running it locally.

---

## 0) Prereqs (do these once)

### Required
- Python **3.11+** (3.12 is fine)
- `pip` available

### Optional
- `make` (Mac/Linux usually have it)
- `nox` (we install it in dev deps below)

Check Python version:

```bash
python --version
```

If that prints < 3.11, stop and upgrade Python before continuing.

---

## 1) One-time setup (recommended path)

From repo root:

```bash
python -m venv .venv
```

Activate:

* macOS / Linux:

  ```bash
  source .venv/bin/activate
  ```

* Windows (PowerShell):

  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install dev deps:

```bash
pip install -r requirements-dev.txt
```

At this point you can run all spine tests.

---

## 2) Run the full spine suite (fastest "do the right thing")

### Option A — Makefile (preferred)

```bash
make test-spine
```

### Option B — Pure pytest (no make needed)

```bash
pytest -q \
  tests/test_event_contract_parity.py \
  tests/test_moments_engine_v1.py \
  tests/test_policy_engine_v1.py \
  tests/test_replay_smoke.py
```

### Option C — Nox (nice for CI parity)

```bash
nox -s spine
```

---

## 3) What each test file covers (so debugging is obvious)

### Contract parity

* `tests/test_event_contract_parity.py`

  * Ensures `AgentEventV1` can be parsed and serialized consistently
  * Uses `pytest.importorskip` so it **won't fail** if the other repo isn't importable

### Moment detection

* `tests/test_moments_engine_v1.py`

  * Validates `detect_moments(events)` against the spine catalog
  * Uses the reference implementation in `app/agentic/spine/moments.py`

### Policy engine

* `tests/test_policy_engine_v1.py`

  * Validates `decide(...)` behavior across modes M0/M1/M2
  * Uses the reference implementation in `app/agentic/spine/policy.py`

### Replay smoke

* `tests/test_replay_smoke.py`

  * Runs the shadow-mode replay harness end-to-end against:

    * `tests/fixtures/smoke_session.jsonl`

---

## 4) Run the replay harness manually (useful for quick inspection)

Shadow mode (no user-facing directive emitted):

```bash
python -m app.agentic.spine.replay tests/fixtures/smoke_session.jsonl --mode M0
```

Advisory mode (directive emitted, no analyzer commands):

```bash
python -m app.agentic.spine.replay tests/fixtures/smoke_session.jsonl --mode M1
```

Verbose audits:

```bash
python -m app.agentic.spine.replay tests/fixtures/smoke_session.jsonl --mode M0 --verbose
```

---

## 5) Common failure modes (and the fix)

### "ModuleNotFoundError: app"

You ran pytest outside repo root or Python can't see the package.

Fix:

* Run from repo root
* Ensure your package is importable (common options):

  * Add a `pyproject.toml` and install editable: `pip install -e .`
  * Or export `PYTHONPATH=.` temporarily:

macOS/Linux:

```bash
export PYTHONPATH=.
pytest -q tests/test_moments_engine_v1.py
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="."
pytest -q tests/test_moments_engine_v1.py
```

### "nox: command not found"

You didn't install dev deps.

Fix:

```bash
pip install -r requirements-dev.txt
```

### Contract parity tests are skipped

This is expected unless both repos are importable in the same environment.
Skips are fine. The spine suite still passes.

---

## 6) Contribution rules (so nobody breaks the spine)

### Golden rules

1. **Contracts are backward compatible**

   * Never remove an event field without bumping major version
2. **Moment detector stays deterministic**

   * No ML / no fuzzy text parsing in the moment layer
3. **Policy in M0 never emits directives**

   * Shadow mode must remain side-effect free
4. **Replay harness must accept JSON + JSONL**

   * Keep it boring and reliable

### If you change event types

* Update:

  * fixtures in `tests/conftest.py`
  * `tests/fixtures/smoke_session.jsonl`
  * moment detector logic if required

---

## 7) "Green CI" checklist

Before opening a PR, run:

```bash
make test-spine
```

If you don't have make:

```bash
pytest -q \
  tests/test_event_contract_parity.py \
  tests/test_moments_engine_v1.py \
  tests/test_policy_engine_v1.py \
  tests/test_replay_smoke.py
```

---

## 8) Quick glossary

* **M0 / Shadow:** decisions computed, nothing emitted to UI (safe)
* **M1 / Advisory:** directives shown, no state changes
* **M2 / Actuated:** view-only analyzer commands (if capability allows)
* **UWSM:** structured working-style preferences, deterministic updates
* **Moment:** derived pattern in event stream (FIRST_SIGNAL, OVERLOAD, etc.)

---

If you find a way to "screw this up," add it to **Section 5** with the fix. That's the point of this README.
