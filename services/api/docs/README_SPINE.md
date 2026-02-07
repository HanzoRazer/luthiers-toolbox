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

### CI fails but tests pass locally

**Symptom**

* All spine tests pass on your machine
* CI fails with:

  * `ModuleNotFoundError`
  * unexpected skips
  * different behavior in moment or policy tests
* Re-running locally *still* passes

**Most common causes (in order)**

#### 1) Virtualenv leakage

Your local shell is picking up packages from:

* a global Python install
* a different virtualenv
* an editable install from another repo

CI is clean. Your machine is not.

**Fix**

1. Deactivate all envs:

   ```bash
   deactivate || true
   ```
2. Delete and recreate:

   ```bash
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Re-run:

   ```bash
   make test-spine
   ```

**Rule of thumb**

> If CI fails but your machine passes, assume your machine is lying.

---

#### 2) PYTHONPATH bleed

Your shell has `PYTHONPATH` set from:

* another project
* a shell profile
* an IDE run configuration

This can silently make imports succeed locally and fail in CI.

**Fix**

* Run once with a clean environment:

macOS / Linux:

```bash
PYTHONPATH= pytest -q tests/test_replay_smoke.py
```

Windows PowerShell:

```powershell
$env:PYTHONPATH=""
pytest -q tests/test_replay_smoke.py
```

* If that fails, your local success depended on leaked paths.

**Permanent fix**

* Prefer one of:

  * `pip install -e .`
  * proper `pyproject.toml`
* Do **not** rely on implicit repo-root imports.

---

#### 3) Editable install mismatch (`pip install -e .`)

CI often installs the package *fresh*.
Locally, you may have an editable install pointing at:

* a different branch
* a different path
* stale code

**Fix**

1. Check editable installs:

   ```bash
   pip list | grep -E "\-e|editable"
   ```
2. Remove unexpected ones:

   ```bash
   pip uninstall <package-name>
   ```
3. Reinstall clean:

   ```bash
   pip install -e .
   ```

**Sanity check**

```bash
python -c "import app.agentic.spine; print(app.agentic.spine.__file__)"
```

Make sure the path is **this repo**, not somewhere else.

---

#### 4) Test order dependency (CI runs differently)

CI may:

* randomize test order
* shard tests
* use a different filesystem ordering

If a test depends on global state, CI will expose it.

**Fix**

* Ensure tests:

  * do not mutate shared globals
  * do not rely on module import side effects
* If in doubt, add:

  ```bash
  pytest --maxfail=1 --disable-warnings -q
  ```

And run with:

```bash
pytest --random-order
```

(if you add that plugin later).

---

**Rule of thumb**

> CI is the reference machine.
> Your laptop is a convenience layer.

If CI fails, fix the environment assumptions — not the tests.

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

---

### How to add a new event type without breaking the spine

Use this checklist. Do not skip steps.

#### Step 1: Schema (contracts layer)

- [ ] Add event type to `AgentEventV1` if using typed enum
- [ ] Document the new `event_type` string in the event catalog
- [ ] Define `payload` shape (what fields? required vs optional?)
- [ ] Add to `docs/EVENT_MOMENTS_CATALOG_V1.md` if it can trigger moments

**Do not proceed until the schema is committed.**

---

#### Step 2: Test fixtures (conftest.py)

- [ ] Add a fixture function: `ev_<your_event_name>`
- [ ] Use `mk_event()` helper with correct `event_type` and `payload`
- [ ] Include realistic `source`, `privacy_layer`, `occurred_at`

Example:

```python
@pytest.fixture
def ev_my_new_event():
    return mk_event(
        eid="evt_new_01",
        etype="my_new_event",
        payload={"key": "value"},
    )
```

---

#### Step 3: Moment detector (if event triggers moments)

- [ ] Update `app/agentic/spine/moments.py` (or `tap_tone_pi/agentic/spine/moments.py`)
- [ ] Add detection logic in `detect_moments()`
- [ ] Respect priority suppression rules (ERROR > OVERLOAD > ... > FIRST_SIGNAL)
- [ ] Add test case in `tests/test_moments_engine_v1.py`

**If the event does NOT trigger moments, skip this step.**

---

#### Step 4: UWSM evidence (if event implies user preference)

- [ ] Update `app/agentic/spine/uwsm_update.py` `_extract_evidence()`
- [ ] Choose evidence type: `explicit` (user said it) or `behavioral` (user did it)
- [ ] Assign a `rule_id` (e.g., `UWSM_<DIM>_<SIGNAL>_v1`)
- [ ] Add test to verify evidence extraction

**If the event does NOT imply preference, skip this step.**

---

#### Step 5: Smoke fixture (if event is common)

- [ ] Consider adding to `tests/fixtures/smoke_session.jsonl`
- [ ] Only if the event is part of a typical session flow
- [ ] Keep the fixture minimal (4-6 events max)

---

#### Step 6: Cross-repo parity

- [ ] Sync changes to **both** repos:
  * `luthiers-toolbox/services/api/app/agentic/spine/`
  * `tap_tone_pi/tap_tone_pi/agentic/spine/`
- [ ] Adjust import paths (`app.` vs `tap_tone_pi.`)
- [ ] Run `make test-spine` in **both** repos

---

#### Step 7: Run the full suite

```bash
make test-spine
```

If any test fails:

1. Fix it
2. Do not merge until green
3. Do not "skip for now"

---

#### Anti-patterns (do not do these)

| Anti-pattern | Why it breaks things |
|--------------|----------------------|
| Add event type without fixture | Tests can't exercise it |
| Add moment detection without test | Silent regressions |
| Add UWSM evidence without rule_id | Audit trail is broken |
| Sync one repo but not the other | Contract parity fails |
| Add to smoke fixture unnecessarily | Bloats replay tests |

---

#### Quick sanity check

After adding a new event type, you should be able to:

```bash
# 1. Parse it
python -c "from app.agentic.spine.replay import load_events; print('OK')"

# 2. Detect moments from it (if applicable)
python -c "from app.agentic.spine.moments import detect_moments; print('OK')"

# 3. Run replay with it
python -m app.agentic.spine.replay tests/fixtures/smoke_session.jsonl --mode M0
```

If any of these fail, you missed a step.

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
