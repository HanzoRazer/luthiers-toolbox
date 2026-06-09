# Project Instructions

## Overview
Luthiers Toolbox — CAD/CAM platform for guitar builders. FastAPI backend + Vue.js frontend.

## Code Style
- Python: PEP 8, type hints, dataclasses for data models
- Vue: Composition API, TypeScript
- Tests: pytest with TestClient for API endpoints

## Architecture

### Soundhole Type System (commit 985e2ad7)

Spiral soundhole is ONE OPTION in a dropdown, not a standalone tool.

**SoundholeType enum** (`app/calculators/soundhole_facade.py`):
- `ROUND` — traditional circular (default)
- `OVAL` — Selmer/Maccaferri elliptical
- `SPIRAL` — logarithmic spiral slot (Williams 2019)
- `FHOLE` — archtop f-holes

**SpiralParams dataclass** (`app/calculators/soundhole_facade.py`):
```python
@dataclass
class SpiralParams:
    slot_width_mm: float = 14.0      # 14-20mm optimal
    start_radius_mm: float = 10.0    # r0
    growth_rate_k: float = 0.18      # per radian
    turns: float = 1.1
    rotation_deg: float = 0.0
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
```

**Physics**:
- Spiral: `r(θ) = r0 × e^(k×θ)`
- P:A ratio: `2/slot_width` (closed form, independent of k/turns)
- Williams threshold: P:A > 0.10 mm⁻¹ for acoustic efficiency

**Endpoints**:
- `POST /api/instrument/soundhole` — `soundhole_type` field selects type
- `GET /api/instrument/soundhole/types` — returns types + spiral presets

**Presets** (`app/calculators/soundhole_presets.py`):
- `SPIRAL_PRESETS`: standard_14mm, compact_12mm, wide_18mm, carlos_jumbo_upper/lower
- `STANDARD_DIAMETERS_MM`: includes `carlos_jumbo: 102.0`
- `STANDARD_POSITION_FRACTION`: includes `carlos_jumbo: 0.52`

## Development Guidelines
- Use Python via Bash if Edit tool fails with "file unexpectedly modified"
- Run `pytest tests/test_soundhole*.py` to verify soundhole changes

## Testing
- 161 soundhole tests in `tests/test_soundhole*.py`
- Coverage threshold: 20%

## Data Policies

### Wood species data sourcing policy

All species records in `wood_species.json` and consumers (e.g., `wood_movement_calc.py`,
`side_bending_calc.py`) must source shrinkage and density values from authoritative
published references. Attribution is per-field, not per-species.

**Source priority (tangential/radial shrinkage):**
1. **FPL GTR-282 (2021) Table 5-3** — for North American species in this table
2. **Wood Database (Eric Meier, wood-database.com)** — for tropical species not in FPL,
   with URL attribution
3. **unknown_legacy** — values whose origin cannot be traced; flagged for follow-up

**Source priority (density):**
1. **FPL GTR-282** — for species in FPL tables
2. **CIRAD wood-density-database (2018)** — for tropical species; density only,
   NOT tangential/radial shrinkage (CIRAD provides volumetric, not breakdown)
3. **Wood Database** — fallback when neither FPL nor CIRAD has the species

**Forbidden:**
- Estimated tangential/radial from volumetric shrinkage without explicit derivation flag
- Values whose origin cannot be traced to a published reference
- Single-source FPL claims for species not actually in FPL

**Per-field attribution schema:**
```json
{
  "physical": {
    "density_kg_m3": 705,
    "_density_source": "FPL_GTR282_table_5-3",
    "contraction_tangential_pct": 9.9,
    "_shrinkage_tangential_source": "FPL_GTR282_table_5-3",
    "_shrinkage_tangential_table_row": "p.5-7",
    "contraction_radial_pct": 4.8,
    "_shrinkage_radial_source": "FPL_GTR282_table_5-3"
  }
}
```

**Valid source values:**
- `FPL_GTR282_table_5-3` — FPL Wood Handbook 2021, Table 5-3
- `wood_database_meier` — wood-database.com (include URL in `_source_url` field)
- `CIRAD_2018` — CIRAD wood density database (density/volumetric only)
- `unknown_legacy` — unverified value, flagged for follow-up

**Calculator behavior for unknown species:**
- `wood_movement_calc.py`: raise `ValueError` listing supported species
- `side_bending_calc.py`: raise `ValueError` — no silent fallback to defaults

**Reference data locations:**
- `docs/reference/cirad/` — CIRAD wood collection index (34,395 specimens, 9,212 species, 169 countries)
- `docs/reference/cirad-density/` — CIRAD wood density database (4,022 specimens, 872 species, Vieilledent et al. 2018)
  - Contains D12 (density at 12% MC), volumetric shrinkage (R), fiber saturation point (S), basic density (Db)
  - Conversion formula: Db = 0.828 × D12

**Wood data routing:**
- **Characterization** (density, SG, shrinkage, origin): CIRAD databases → wood_species.json
- **Regulatory** (CITES status, trade restrictions): CITES species checklist → wood_species.json cites_status field
- **Acoustic** (MOE, tone character, typical uses): wood_species.json → luthier_tonewood_reference.json

### Documentation archive policy

**Archive location**: `docs/archive/`
**Index**: `docs/archive/INDEX.md`

**60-day rule**: Documents move to archive after 60 days or when superseded by newer versions.

**Archive categories (2026)**:
- `status/` — point-in-time snapshots, session states
- `plans/` — superseded implementation plans
- `remediation/` — completed remediation efforts
- `evaluations/` — completed assessments and audits
- `handoffs/` — pre-March 2026 developer handoffs
- `sprints/` — sprint artifact bundles
- `session-notes/` — extracted session transcript content

**Code archive**: `archive/code/{year}/` — historical Python files not in production

**Stays active** (never archive):
- Architecture docs, specs, guides in `docs/`
- ADRs in `docs/adr/`
- Current handoffs in `docs/handoffs/` (recent 60 days)
- Reference material (`docs/reference/`)
- Tonewood comparison documents

## Governance Authority

The repository uses a 3-tier governance hierarchy. When governance systems conflict,
higher tiers take precedence.

**Tier 1 — Structural Invariants (repository-wide):**
- `docs/governance/ARCHITECTURE_INVARIANTS.md` — code placement rules
- `FEATURE_PARITY_MIGRATION_POLICY.md` — migration discipline

**Tier 2 — Domain Governance (domain-specific):**
- MRP: `docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md`
- CAM: `docs/architecture/CAM_GOVERNED_EXPORT_ARCHITECTURE.md`
- RMOS: `docs/canonical/governance/RMOS_2.0_Specification.md`

**Tier 3 — Operational Policies (runtime behavior):**
- `docs/governance/SPRINT_NAMESPACE_STANDARD.md`
- CAM capability registry and policy engine

**Key documents:**
- Authority hierarchy: `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md`
- Topology map: `docs/governance/GOVERNANCE_TOPOLOGY_MAP.md`
- Manifest index: `docs/governance/MANIFEST_INDEX.md`
- Implementation guide: `docs/handoffs/GOVERNANCE_REMEDIATION_IMPLEMENTATION_GUIDE.md`

**Governance commands:**
```bash
# Tier-based execution (default: ci)
python scripts/governance/check_all.py --tier precommit  # Fast checks (~2s)
python scripts/governance/check_all.py --tier ci         # CI checks (~4s)
python scripts/governance/check_all.py --tier nightly    # Full suite (~130s)
python scripts/governance/check_all.py --list            # Show all checks by tier

# Individual checks
python scripts/check_protected_paths.py         # Protected system modifications
python scripts/check_capability_registry.py     # CAM registry validation
python scripts/governance/check_manifest_index.py  # Manifest index validation
pytest tests/test_governance_compliance.py -v   # Governance test suite
```

**Enforcement tiers:**
- `precommit` — fast checks for pre-commit hooks (<2s each)
- `ci` — moderate checks for CI builds (<30s each, default)
- `nightly` — heavy checks requiring full app init (scheduled builds)
- `manual` — explicit invocation only

## BLOCKING INFRASTRUCTURE — resolve before new DXF work

### DXF output standard: dual-format via dxf_compat

**Free tier output: R12 (AC1009)**
  - LINE entities only via dxf_compat.add_polyline(version='R12')
  - Maximum legacy compatibility for hobbyist users

**Paid tier output: R2000 (AC1015)**
  - LWPOLYLINE entities via dxf_compat.add_polyline(version='R2000')
  - Multi-point closed contours, suitable for CAM workflows
  - Verified safe for DWG TrueView 2026 on 2026-04-28
    Test file: services/api/test_temp/cuatro_R2000_LWPOLYLINE_test.dxf
    Operations verified: open, visual inspection, no freeze
  - Verified through GRBL pipeline 2026-04-29
    Source: docs/investigations/cam_pipeline_r2000_compat_2026-04-29.md
    G-code generation: 2260 lines from BODY_OUTLINE layer

**Common requirements (both formats):**
  - All DXF generators must use dxf_compat — direct ezdxf.new() calls forbidden
  - EXTMIN/EXTMAX: let ezdxf compute extents from actual geometry. Do NOT write
    1e+20 sentinel values — they break CAD viewer zoom-to-fit (blank-canvas bug,
    fixed 2026-04-25 / `2aaff13f`; see History). Populating extents from geometry
    (e.g. blueprint-import `set_document_bounds`) is correct, not a violation.
  - Coordinate precision ≤ 3dp
  - Layer naming follows ContourCategory.value.upper() convention

**History:**
  - 2026-04-02: R12-only gate established after smart_guitar_front_v3.dxf
    caused Fusion 360 freeze (specific malformed LWPOLYLINE incident)
  - 2026-04-28: Gate lifted for R2000 after DWG TrueView verification confirmed
    properly-formed LWPOLYLINE imports cleanly. R12 retained for free tier.
  - 2026-04-25: EXTMIN/EXTMAX sentinel (1e+20) REMOVED — `2aaff13f` found inverted
    sentinels broke CAD viewer zoom-to-fit (valid LINE entities displayed as blank
    canvas); switched to ezdxf computing extents from geometry. This is a SEPARATE
    incident from the LWPOLYLINE freeze above — header-extents, not entity type.
  - 2026-06-09: provenance correction (Surface-D audit). The former "use sentinel
    1e+20" rule was conflated with the 2026-04-02 LWPOLYLINE freeze; it is not — it
    traces to the 2026-04-25 inverted-extents fix, and the sentinel it mandated is
    the exact behavior that fix removed. Rule corrected above.
## VECTORIZER ARCHITECTURE NOTES (three-loop / AGE) — EXPERIMENTAL, SANDBOXED

### Original date: 2026-04-02
### Status: EXPERIMENTAL — NOT approved, NOT implemented in this repo. Owned by `vectorizer-sandbox`.

> **CONFLATION CORRECTION (2026-05-30).** This entire block was previously titled
> "VECTORIZER ARCHITECTURE DECISION — DO NOT BYPASS / APPROVED DESIGN." That framing was
> conflation, corrected per ground truth from Ross (2026-05-30):
>
> - The three-loop feedback architecture (+ AGE) is **experimental, was never approved
>   for use, and was never implemented in this runtime repo.** It has been **sandboxed
>   into its own repo** (`vectorizer-sandbox`, symlinked at `docs/audit-sources/vectorizer-sandbox`;
>   the real embodiment is `src/incubation/agentic_supervisor.py`) until further work is done.
> - "Ross identified the correct solution repeatedly across multiple sessions" was an
>   **unsourced provenance claim** repeated inside these instructions; it is not a decision
>   record and must not be treated as a standing mandate.
> - The runtime **scale-validation gate** (`validate_scale_before_export`, `_safe_dxf_save`
>   in `vectorizer_phase3.py`) is **real and shipped** — it is NOT part of the experimental
>   loop architecture. Keep it.
>
> The text below is **retained as a candidate design sketch for the sandbox**, not as owed
> runtime work. Full removal plan, corrected dispositions, and the runtime↔stub safety
> analysis: `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md`
> (+ `_CORRECTIONS.md`). Do not re-promote this to "approved" without a real decision record.

## The Problem (motivation for the sandbox research line)

The blueprint vectorizer (vectorizer_phase3.py) is an open-loop system.
It extracts, classifies, and exports without knowing whether the output
is correct. Every session has produced point fixes (epsilon values,
version strings, cache headers) that address symptoms without addressing
the architectural gap.

This motivated the experimental three-loop research line — now developed in
`vectorizer-sandbox`, not here. It is not approved runtime work.

---

## The Candidate Architecture: Three Feedback Loops (EXPERIMENTAL — sandbox-owned, not approved)

### Loop 1 — Intra-Frame Validation (within one run)

After extraction, BEFORE export, validate the result is plausible.
If validation fails, retry with a different strategy automatically.
Do NOT export garbage — fail loudly and try again.

```python
class ValidatedExtractor:
    def extract_with_self_check(self, image, spec_name=None):
        result = self.extract(image)

        checks = [
            self.has_reasonable_size(result, spec_name),
            self.has_continuous_boundary(result),
            self.has_no_spikes(result),
            self.aspect_ratio_plausible(result, spec_name),
            self.scale_plausible(result, spec_name),
        ]

        if sum(checks) < 3:
            logger.warning("Extraction implausible, trying fallback strategy")
            return self.extract(image, strategy='fallback')

        return result
```

Instrument spec dimensions from JSON files are the validation targets.
A cuatro body at 524×951mm fails immediately — the spec says ~260×375mm.
A Gibson Explorer at 302×419mm fails immediately — spec says 460×475mm.

### Loop 2 — Cross-Image Learning (across runs)

Cache which extraction strategy worked for which image signature.
When a similar image arrives, start with the strategy that worked.
Do NOT always start from the same defaults.

```python
class AdaptiveExtractor:
    def __init__(self):
        self.strategy_cache = {}  # image_signature → winning_strategy

    def extract(self, image, spec_name=None):
        sig = self.get_image_signature(image)

        if sig in self.strategy_cache:
            return self.extract_with_strategy(
                image, self.strategy_cache[sig]
            )

        results = self.try_all_strategies(image, spec_name)
        best = self.pick_best(results, spec_name)
        self.strategy_cache[sig] = best.strategy
        return best
```

### Loop 3 — User Correction Retraining

When a user corrects a bad DXF, that correction is ground truth.
Feed it back into the classifier. The FeedbackSystem and
TrainingDataCollector already exist in the code but are NEVER CALLED.
Wire them to fire when a correction is received.

---

## The AGE Integration (Agentic Guidance Engine)

> **CONFLATION CORRECTION (2026-05-30).** Two earlier claims in this section
> were verified against the code and found to be conflation, not fact:
>
> 1. **The "mirror tap_tone_pi" framing does not transfer.** `tap_tone_pi`
>    is a *separate external repo* (symlinked at `docs/audit-sources/tap_tone_pi`),
>    with no import or data-flow coupling to the vectorizer in either
>    direction. Its `AnalyzerGuidanceEngine`
>    (`tap_tone_pi/analyzer/guidance/engine.py` — note: the path cited below
>    as `tap_tone/analyzer_guidance_engine.py` does NOT exist) is an
>    **advisory / display-layer** engine whose design contract is "reads
>    finished data only, never modifies measurements." A vectorizer AGE would
>    be a **control-layer** component that redirects the extraction pipeline —
>    the opposite kind of engine. The only shared idea is the generic
>    "call Claude, fall back silently," which needs no cross-repo canonical
>    source. Treat any vectorizer AGE as a standalone design, NOT a port.
> 2. **"Ross requested this in multiple sessions" is unverified provenance.**
>    It is an unsourced claim repeated inside the instructions themselves and
>    must not be treated as a standing mandate. Whether a vectorizer AGE is
>    actually wanted, and at what scope, is an open question for the user —
>    not a settled decision.
>
> The remainder of this section is retained as a *candidate design sketch*,
> not an approved requirement.

A vectorizer AGE, **if built**, would sit as the decision layer above Loop 1.
Instead of heuristic strategy selection, it would evaluate extraction
quality using the Claude API and select the next strategy with reasoning:

```python
class VectorizerAGE:
    """
    Agentic Guidance Engine for the vectorizer (candidate design — standalone,
    NOT a port of tap_tone_pi's advisory-layer engine; see correction above).
    Uses real Claude API calls to evaluate extraction quality
    and select recovery strategy.
    Falls back silently if API unavailable.
    """

    def evaluate_extraction(self, result, spec_name, image_path):
        """
        Ask Claude to evaluate whether the extraction result
        is plausible for the given instrument spec.
        Returns: (is_plausible: bool, recommended_strategy: str, reasoning: str)
        """
        prompt = self._build_evaluation_prompt(result, spec_name)
        try:
            response = self._call_claude_api(prompt)
            return self._parse_evaluation(response)
        except Exception:
            # Silent fallback — never block the pipeline
            return self._heuristic_evaluation(result, spec_name)

    def _build_evaluation_prompt(self, result, spec_name):
        spec = load_instrument_spec(spec_name)
        return f"""
You are evaluating a guitar body vectorization result.

Instrument: {spec_name}
Expected body dimensions: {spec['body']['width_mm']}mm × {spec['body']['height_mm']}mm
Extracted body dimensions: {result.dimensions_mm[0]:.0f}mm × {result.dimensions_mm[1]:.0f}mm
Layers extracted: {list(result.contours_by_category.keys())}
Validation passed: {result.validation_passed}

Is this extraction plausible? If not, which strategy should be tried next:
- aggressive (larger gap close kernel)
- simple (no classification, all contours)
- canny_only (no dual pass)
- scale_correction (apply 2.5x correction factor)

Respond in JSON: {{"plausible": bool, "strategy": str, "reason": str}}
"""
```

---

## Scale Validation — Immediate Requirement

The scale error (2.5× too large) is the current blocking issue.
Before the AGE is built, add this validation gate:

```python
def validate_scale_before_export(self, mm_per_px, scale_factor,
                                  contours, spec_name=None):
    """
    Called BEFORE export_to_dxf().
    Checks that the computed scale produces plausible instrument dimensions.
    If not plausible, attempts correction.
    """
    effective_mm_per_px = mm_per_px * scale_factor

    # Find the largest contour (likely body)
    if not contours:
        return scale_factor, False

    largest = max(contours, key=lambda c: cv2.contourArea(c.contour))
    x, y, w, h = cv2.boundingRect(largest.contour)

    body_w_mm = w * effective_mm_per_px
    body_h_mm = h * effective_mm_per_px

    logger.info(f"Scale validation: body={body_w_mm:.0f}×{body_h_mm:.0f}mm "
                f"(mm_per_px={mm_per_px:.6f} scale={scale_factor:.3f})")

    # Check against spec if available
    if spec_name and spec_name in INSTRUMENT_SPECS:
        spec = INSTRUMENT_SPECS[spec_name]
        expected_w = spec.get('body_width_mm', 350)
        expected_h = spec.get('body_height_mm', 450)
        ratio_w = body_w_mm / expected_w
        ratio_h = body_h_mm / expected_h

        if 0.8 < ratio_w < 1.2 and 0.8 < ratio_h < 1.2:
            logger.info("Scale validation PASSED")
            return scale_factor, True
        else:
            correction = (expected_w / body_w_mm + expected_h / body_h_mm) / 2
            logger.warning(f"Scale validation FAILED. "
                          f"Correction factor: {correction:.3f}x")
            return scale_factor * correction, False

    # Generic plausibility check (no spec)
    max_dim = max(body_w_mm, body_h_mm)
    min_dim = min(body_w_mm, body_h_mm)
    if 200 < max_dim < 700 and 150 < min_dim < 550:
        return scale_factor, True

    # Too large — apply correction
    if max_dim > 700:
        correction = 500 / max_dim
        logger.warning(f"Body too large ({max_dim:.0f}mm), "
                      f"applying {correction:.3f}x correction")
        return scale_factor * correction, False

    return scale_factor, False
```

---

## Implementation Priority Order

1. **Scale validation gate** — add validate_scale_before_export()
   to vectorizer_phase3.py, called before every export_to_dxf() call.
   This unblocks the cuatro and Explorer immediately.

2. **Loop 1 (intra-frame validation)** — add retry logic with
   fallback strategies. Requires scale validation to be working first.

3. **Loop 2 (cross-image caching)** — add strategy_cache to the
   vectorizer class. Low complexity, high value.

4. **AGE integration** — wire VectorizerAGE above Loop 1.
   Requires the Claude API key to be available in the environment.
   Must fall back silently if unavailable.

5. **Loop 3 (user correction retraining)** — wire FeedbackSystem
   and TrainingDataCollector to fire on user corrections.
   This is the long-term quality improvement path.

---

## Rules for Future Sessions

1. DO NOT add new detection methods without adding a validation gate.

2. DO NOT ship a DXF export without running scale validation first.

3. The vectorizer AGE is a CANDIDATE design, not an approved requirement.
   The prior "requested in multiple sessions / must be built" wording rested
   on unverified provenance and a tap_tone_pi analogy that does not transfer
   (see CONFLATION CORRECTION in "The AGE Integration"). Do not treat it as a
   standing mandate; confirm scope with the user before building it.

4. The feedback loop architecture is EXPERIMENTAL and sandbox-owned — NOT approved,
   NOT owed runtime work (corrected 2026-05-30; see the CONFLATION CORRECTION at the top
   of this section). It is not a yardstick for judging runtime point-fixes. The real,
   shipped runtime guardrail is the scale-validation gate — keep that; do not gate it on
   the unbuilt loops.

5. When a session produces a tactical fix that addresses a symptom,
   the approved architecture entry in CLAUDE.md takes precedence.
   Record what was fixed AND why it does not replace the architecture.

---

## Reference Files

- vectorizer_phase3.py — main vectorizer, needs all three loops
- vectorizer_enhancements.py — Phase 3.7 features, partially integrated
- calibration_integration.py — exists but NEVER CALLED, wire to pipeline
- FeedbackSystem — exists but NEVER CALLED, wire to user corrections
- TrainingDataCollector — exists but NEVER CALLED, wire to retraining
- phase4/dimension_linker.py — complete but standalone, integrate after
  Loop 1 and Loop 2 are working

## tap_tone_pi AGE Reference — RETRACTED (2026-05-30)

This section previously cited `tap_tone_pi/tap_tone/analyzer_guidance_engine.py`
as "the AGE pattern to replicate." Retracted as conflation:

  - **The cited path does not exist.** The real file is
    `tap_tone_pi/analyzer/guidance/engine.py` (class `AnalyzerGuidanceEngine`),
    in a SEPARATE external repo with no coupling to this one.
  - **The pattern does not transfer.** That engine is advisory / display-layer
    by design contract ("reads finished data only, never modifies
    measurements") — the opposite of a vectorizer control-layer AGE.

Do not use tap_tone_pi as the reference for any vectorizer work. The only
reusable idea — "call Claude, fall back silently if the key/API is absent" —
is already demonstrated in this repo by `services/blueprint-import/analyzer.py`
(`BlueprintAnalyzer`), which is the local, in-repo precedent if such a
component is ever scoped.

---

## VECTORIZER SPRINT B — Segmentation-First Extraction

Priority: HIGH — closes the 148 open endpoint problem

> **NOTE (2026-05-30):** Sprint B is a **standalone runtime extraction improvement** and is
> NOT loop-dependent — the prior "(Strategy A in Loop 1)" label was rhetorical bolt-on to
> the (experimental, sandboxed) loop architecture. The technique is single-pass and needs no
> loop/AGE machinery; the runtime already produces the `fg_mask` it consumes
> (`vectorizer_enhancements.py`, behind the rembg/grabcut path). KEEP as runtime work.
> Code-verified resolution: `DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md` §8a.

Root cause confirmed by gap analysis:
  - 88 gaps <0.5mm (edge detection noise)
  - 34 gaps >5mm (maximum 27.25mm) — genuine blueprint
    discontinuities that edge detection cannot recover

Segmentation approach (standalone — single-pass, not loop-gated):
  1. Add extract_body_by_segmentation() using
     flood fill from image center point
  2. Add fg_mask priority path — use foreground
     mask from background removal when available
  3. Edge detection becomes fallback only

Expected result: closed contours by construction,
148 open endpoints → 0 for clean blueprints.

Location: services/blueprint-import/vectorizer_phase3.py
Test case: cuatro puertoriqueño PDF

## Feature Parity Migration Policy

See: `FEATURE_PARITY_MIGRATION_POLICY.md`

**Core rule**: No existing canonical implementation may be removed or superseded until parity is verified.

**Migration states** (must be declared explicitly):
1. **Canonical** — the trusted production implementation
2. **Mounted Legacy Component** — legacy embedded in new workspace, owns its own logic
3. **Beta Consolidation Shell** — workspace exists but parity incomplete
4. **Parity Verified** — replacement may proceed

**Approved migration order**: mount → verify → audit → extract → normalize → replace

**Anti-patterns** (prohibited):
- Shell-first replacement
- Implicit deprecation (hiding routes before parity)
- Archive without audit
- "Newer means better" assumptions

**Current status**:
- `SpiralSoundholeDesigner.vue` = canonical implementation
- `ApertureWorkspace.vue` = beta consolidation shell (State 3)

The workspace shell may mount the legacy component. It may NOT replace or remove the legacy implementation until parity is verified.

## Governance Framework

See: `docs/governance/`

**Core documents:**
- `MORPHOLOGY_RECONSTRUCTION_PLATFORM.md` — MRP governance framework
- `BLUEPRINT_READER_PROTECTION_RULES.md` — frozen MVP protection
- `IBG_ROLE_DEFINITION.md` — IBG role boundaries
- `THREE_LOOP_ARCHITECTURE_REFRAMED.md` — loop architecture within MRP
- `MORPHOLOGY_CORPUS_STANDARD.md` — corpus data standards
- `SPRINT_NAMESPACE_STANDARD.md` — sprint naming conventions

**Protection levels:**
- LOCKED — no changes without explicit approval
- STABILIZED — changes require regression verification
- EVOLUTIONARY — changes permitted behind feature flags

**Sprint namespaces:** VECTOR, IBG, BOE, DXF, CAM, RMOS, SPIRAL, MRP
