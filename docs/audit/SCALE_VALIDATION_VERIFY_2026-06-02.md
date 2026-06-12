# Scale Validation — Cold Independent Verification (2026-06-02)

**Scope:** READ-ONLY. Establish ground truth for three questions from source/manifests/tests only. No prior triage/audit report was opened. No repo files changed (this report is the only write).
**Method:** ripgrep (`rg`) + direct file reads. Every claim cites the command or `file:line` that establishes it. Searches were run with the `Grep`/`Read` tools (ripgrep-backed); equivalent `rg` commands are quoted for reproducibility.
**Tooling limitation:** repo-wide `rg` across `packages/` (the TS/Vue tree with `node_modules`) timed out at ~25s repeatedly; `services/` Python sweeps completed and are authoritative. Where `packages/` could not be exhaustively swept, the result is marked **UNKNOWN** with the command to run.

---

## Headline cross-finding (surfaced plainly, not softened)

`validate_scale_before_export` exists as **two different functions in two different modules**, with **different signatures and return types**:

- `services/api/app/services/scale_validation.py:79` → `(width_mm, height_mm, spec_name=None) -> Optional[str]` — the module of Q1/Q3.
- `services/blueprint-import/vectorizer_phase3.py:2336` → `(mm_per_px, scale_factor, classified, spec_name=None) -> Tuple[float, bool]` — the implementation of Q2.

The Q2 production call site (`vectorizer_phase3.py:3570`) calls the **local** `vectorizer_phase3.py:2336` version (same module, no import). The `scale_validation.py` module (Q1/Q3) is imported by **exactly one** file — a test — and by **zero production code**. These two facts together: the live "scale validation before export" logic runs from a name-colliding local function, while the standalone `scale_validation.py` module has no production importer.

---

## Q1 — Importers of `services/api/app/services/scale_validation.py`

**Commands run:**
- `rg -n "scale_validation" services --type py`
- `rg -n "scale_validation" packages -g "**/*.{ts,js,vue,py}"` → **timed out (~25s)**; see limitation.

**Result in `services/` (complete):** exactly one importer, a test.

| Importer path | Line(s) | What's imported | Prod/Test |
|---|---|---|---|
| `services/api/tests/test_scale_validation.py` | 17–23 | `from app.services.scale_validation import (validate_scale_before_export, get_body_bounds, compute_scale_correction, GENERIC_BOUNDS_MM, _reset_cache)` | **TEST** |

**Production importers in `services/`:** **none found.** (`rg -n "scale_validation" services --type py` returns only the test importer above, plus self-references inside `scale_validation.py` itself at lines 11/101/105/109, which are docstring usage examples, not imports.)

**Not importers (verified, listed to forestall false positives):**
- `services/blueprint-import/vectorizer_phase3.py:2336` (def) and `:3570` (call) reference a **same-named but distinct** function — they do **not** import `scale_validation.py`.
- No manifest/registry reference: `scale_validation` does not appear in `services/api/app/router_registry/manifests/*.py` (covered by the `--type py` sweep; zero hits there). `scale_validation.py` is a service module, not a router, and is not manifested.
- No dynamic/`importlib`/`getattr` reference found: the substring `scale_validation` appears in `services/` Python only at the locations above.

**`packages/` and other top-level dirs:** **UNKNOWN (exhaustive).** The `packages/` sweep timed out at repo scale. `scale_validation` is a Python module identifier with no exposed API-path string, so a valid *Python import* from a TS/Vue package is not a possible import form; a string match there, if any, could only be incidental. To verify the absence directly, run from repo root:
`rg -n "scale_validation" packages -g '!**/node_modules/**'` and `rg -n "scale_validation" -g '!**/node_modules/**' -g '!**/.git/**'`.

**Q1 verdict (evidenced):** In `services/`, `scale_validation.py` has **1 test importer and 0 production importers.** `packages/` exhaustive match is UNKNOWN (tooling timeout), but no valid production import form exists there.

---

## Q2 — Live-path status of `validate_scale_before_export` in `vectorizer_phase3.py`

**Line numbers verified (prompt hints were accurate):** def at `vectorizer_phase3.py:2336`; called at `vectorizer_phase3.py:3570`.
- `rg -n "validate_scale_before_export" services --type py` → def `:2336`, call `:3570`.
- Signature (`:2336`): `def validate_scale_before_export(mm_per_px: float, scale_factor: float, classified: Dict[ContourCategory, List[ContourInfo]], spec_name: Optional[str] = None) -> Tuple[float, bool]`.
- Call (`:3570`): `scale_factor, scale_valid = validate_scale_before_export(self.mm_per_px, scale_factor, classified, spec_name=spec_name)` — 4 args, 2-tuple unpack → resolves to the local `:2336` def.

**Enclosing scope of the call site:** line 3570 is inside method `Phase3Vectorizer.extract` (`def extract` at `:3267`; class `Phase3Vectorizer` at `:2739`). Source: `rg -n "^class |^    def " vectorizer_phase3.py` → nearest preceding `    def` to 3570 is `extract` at 3267; next method `_extract_ocr_dimensions` at 3748.

**Reachability fork inside `extract` (verified):** `extract` accepts `raw_output: bool = False` (`:3293`); at `:3376` `if raw_output:` → `:3378` `return self._raw_extract(...)`. So `raw_output=True` returns **before** line 3570; only the non-raw path reaches the gate at 3570.

### Call chain, hop by hop (to entry points)

**Chain A — FastAPI, `phase3_router` (LIVE):**
1. `POST /blueprint/phase3/vectorize` — `phase3_router.py:102` `vectorize_blueprint` (router prefix `/phase3` at `phase3_router.py:43`).
2. Mounted: `blueprint/__init__.py:45` `router.include_router(phase3_router)` into the `/blueprint` aggregate (`__init__.py:40`), which is manifested at `router_registry/manifests/business_manifest.py:9` (`module="app.routers.blueprint"`).
3. `phase3_router.py:156` calls `extract_guitar_blueprint(...)` (imported via `blueprint/constants.py:101` `from vectorizer_phase3 import extract_guitar_blueprint`).
4. `vectorizer_phase3.py:3942` `def extract_guitar_blueprint(... raw_output: bool = False@:3958)` → `:4019` `vectorizer.extract(... raw_output=raw_output@:4031)` → `raw_output=False`.
5. `Phase3Vectorizer.extract` (`:3267`), `raw_output=False` → `if raw_output` guard at `:3376` NOT taken → reaches **`:3570`** → local `validate_scale_before_export` (`:2336`).
   → **LIVE.**

**Chain B — FastAPI, async job → orchestrator (LIVE, mode-dependent):**
1. `blueprint_async_router.py` manifested at `business_manifest.py:154` (`module="app.routers.blueprint_async_router"`).
2. `blueprint_async_router.py:28/36/196` constructs/calls `BlueprintOrchestrator(... mode=cleanup_mode)`.
3. `blueprint_orchestrator.py:502` (mode `CAM_READY_R2000`) `vectorizer.extract(source_path=..., cam_ready=True, spec_name=...)` — no `raw_output` → defaults False → reaches `:3570`. → **LIVE.**
   - Contrast: `blueprint_orchestrator.py:558` (mode `V2_RAW`) calls `extract(..., raw_output=True)` → early-returns at `:3378` → **does NOT reach 3570.**

**Chain C — CLI (LIVE as a script entry):**
- `vectorizer_phase3.py:4102` `def main()` + `:4181` `if __name__ == "__main__"` + `:4106` `argparse`. `main` reaches `extract`/`extract_guitar_blueprint` (`:4153` passes `raw_output=args.raw`; default non-raw reaches 3570).

**Other callers (test-only, noted separately):** `services/api/tests/test_vectorizer_simple_export.py:30/39`; `services/blueprint-import/tests/test_ocr_integration.py`, `tests/test_photo_pipeline_trial.py`; `train_classifier.py` (CLI/training). `photo_orchestrator.py:227` and `photo_vectorizer_router.py` call a `.extract()` but on a different vectorizer (`PhotoVectorizerV2`) — not verified to be `Phase3Vectorizer`; excluded from the live verdict.

**Q2 verdict (evidenced):** `validate_scale_before_export` at `vectorizer_phase3.py:2336` (called `:3570`) is **ON A PRODUCTION EXECUTION PATH** — reachable from at least two mounted FastAPI endpoints (`POST /blueprint/phase3/vectorize`; the manifested blueprint async router via `BlueprintOrchestrator` `CAM_READY_R2000`) and a CLI entry. The `raw_output=True` / `V2_RAW` path bypasses it.

---

## Q3 — What the four definitions in `scale_validation.py` actually are

All four are module-level **functions** (no classes, no methods). Signatures quoted from the file:

| Line | Name | Signature (quoted) | Kind | One-sentence description |
|---|---|---|---|---|
| 45 | `get_body_bounds` | `def get_body_bounds(spec_name: Optional[str]) -> Tuple[float, float, float, float]:` | function | Returns `(w_min, w_max, h_min, h_max)` mm bounds for a spec — tight (±`SPEC_TOLERANCE`) if the spec is found, else `GENERIC_BOUNDS_MM`. |
| 79 | `validate_scale_before_export` | `def validate_scale_before_export(width_mm: float, height_mm: float, spec_name: Optional[str] = None) -> Optional[str]:` | function | The gate: returns `None` if dimensions are within bounds, else an error-message string (export should be blocked); uses `get_body_bounds`. |
| 144 | `compute_scale_correction` | `def compute_scale_correction(width_mm: float, height_mm: float, spec_name: Optional[str] = None) -> Tuple[float, str]:` | function | Recovery path: computes a suggested multiplicative correction factor + explanation to bring dims into range; does **not** auto-apply. |
| 190 | `_reset_cache` | `def _reset_cache() -> None:` | function | No-op cache reset kept for API/test compatibility (`pass`). |

**Same family or unrelated?** **Same logical family — a single scale-validation pipeline, not unrelated things sharing a file.** Evidence: all three substantive functions take the same `(width_mm/height_mm, spec_name)` shape and share module constants `GENERIC_BOUNDS_MM` (`:39`) / `SPEC_TOLERANCE` (`:42`) and `get_body_dimensions` (imported `:31`). `validate_scale_before_export` (`:112`) directly calls `get_body_bounds`; `compute_scale_correction` is the documented recovery path for when `validate_scale_before_export` fails (`:152-153`). `_reset_cache` (`:190`) is a vestigial test/API-compat no-op, not a separate operation. The module docstring (`:1-24`) frames them as one "Scale Validation Gate — Pre-Export Dimension Check."

---

## Facts established (proven only; no recommendation)

1. `scale_validation.py` has **one importer — a test** (`test_scale_validation.py:17-23`) — and **zero production importers** in `services/` (`packages/` exhaustive match UNKNOWN due to tooling timeout; no valid Python import form exists there).
2. The production "validate scale before export" logic that runs at `vectorizer_phase3.py:3570` is a **different, same-named function** (`vectorizer_phase3.py:2336`, distinct signature/return) and **is live** via `POST /blueprint/phase3/vectorize` and the manifested blueprint async router (orchestrator `CAM_READY_R2000`); the `raw_output`/`V2_RAW` path bypasses it.
3. The four defs in `scale_validation.py` (`get_body_bounds`, `validate_scale_before_export`, `compute_scale_correction`, `_reset_cache`) are all functions forming **one cohesive scale-validation pipeline**, not unrelated code.
