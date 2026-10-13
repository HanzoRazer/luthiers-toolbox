# Vectorizer Harvest and Freeze Closeout

**Date:** 2026-10-11  
**Disposition:** **RETAIN_RESEARCH_ONLY**  
**Runtime decision:** current canonical production vectorizer remains in service unchanged.

## Scope

This closeout resolves the recovery/retirement workstream for the relocated Tier A semantic/cognitive lineage. It does not repair vectorizer algorithms, alter production routes, change DXF output, or promote sandbox research.

## What is retained for research only

- former `services/photo-vectorizer/cognitive_extractor.py`;
- former `services/photo-vectorizer/cognitive_extraction_engine.py`;
- former `extract_body_grid.py` through `extract_body_grid_v5.py`;
- former `services/blueprint-import/vectorizer_phase2.py`;
- their preserved counterparts in `HanzoRazer/vectorizer-sandbox`;
- benchmark and forensic evidence including Cuatro, Melody Maker, L-00, archtop, VEC-ROOT-001, and PR #425 evidence.

These assets may support benchmarking, archaeology, reproducibility, and future design hypotheses. They carry no production or fabrication authority.

## Operational boundary

The production runtime remains the governed `luthiers-toolbox` spine. The relocated Tier A modules are absent from `services/` and must remain absent. `scripts/governance/check_semantic_sandbox_imports.py` is the existing fail-closed import boundary and is already included in the unified governance runner and governance compliance tests.

No duplicate freeze checker is added by this closeout.

## ENHANCED reconciliation

`CleanupMode.ENHANCED` is reachable by an explicit mode through the canonical blueprint endpoint, but reachability is not lifecycle promotion. Current authority is **SANDBOX / API-exposed experimental**. It is not a production-qualified vectorizer mode and is not the default Blueprint Reader path.

## Preserved unresolved defects

The following remain intentionally unfixed in this closeout:

- **F-2:** `test_entity_count_reduction` can pass on the absent `entity_count` attribute via a zero fallback;
- **F-3:** without EasyOCR, `mask_text=True` can behave as no masking while the conversion still reports success;
- resource cost of the Melody Maker real-plan regression lane;
- representational limits such as intra-contour decomposition of structural profile versus ornament.

These remain separate implementation/research questions. Their existence does not restore operational authority to the relocated lineage.

## Preserved production paths

This closeout does not change:

- `CleanupMode.REFINED` production behavior;
- the photo vectorizer production path;
- `dxf_compat` contracts;
- constitutional IBG intake;
- Blueprint Reader defaults;
- CAM authority or manufacturing outputs.

## Reactivation rule

Research-only assets may return to production only through:

`sandbox evidence -> provenance -> deterministic instrumentation -> governance review -> intake contract -> new runtime implementation`.

Direct import, copy-back, submodule coupling, or treating a research document as executable authority is prohibited.

## Deletion rule

This closeout does **not** authorize deletion of preserved sandbox lineage, benchmark evidence, forensic records, or unresolved Cuatro artifacts. Any later cleanup must first prove that unique research/evidence value has been harvested.

## Completion statement

The recovery/retirement workstream is closed with **RETAIN_RESEARCH_ONLY** for the relocated Tier A lineage. The runtime spine stays operational and unchanged; research remains available outside the production authority boundary.
