# Adjudication

## Decided in this increment (by owner ruling, 2026-10-03)

| Item | Ruling |
|---|---|
| Ellipse OCR-failure test | Keep the real conversion; add only a ceiling above the reproduced 1,116 entities; no `max_entities`, no fixture change; not a performance problem |
| Melody Maker execution | Share one masked and one unmasked conversion across the three tests (module-scoped fixture); keep every assertion |
| Dedicated workflow | `workflow_dispatch` + path triggers; **no schedule** (no response owner for an unattended run); not required; uploads metrics |
| Cuatro roles | Both `ROLE_UNRESOLVED`; `benchmark witness` and `plan-package artifact` recorded as unproven candidates; no deletion, move or deduplication |
| Vocabulary | No sandbox output-role vocabulary exists; `ARCHIVAL_TRACE` / `DESIGN_CANDIDATE` not introduced; `CAM_READY` not inherited |

## Not decided — findings raised for the owner

These were found while measuring. None is acted on here; each would be its own order.

| ID | Finding | Why it is not fixed here |
|---|---|---|
| F-2 | `test_entity_count_reduction` cannot fail: it reads `result.entity_count`, which `BlueprintResult` does not have, so both counts default to 0 | Strengthening an assertion is outside a containment increment; the ruling was to preserve assertions |
| F-3 | Without EasyOCR (as on CI), `mask_text=True` silently does no masking and reports `SUCCESS`, so the "with masking" test does not test masking in CI | Production behaviour; BR-037 covers only the OCR-*failed* case |
| F-4 | A Melody Maker conversion peaks at about 4.7 GB working set locally | Resource budget for the dedicated lane, not a default-CI matter |
| F-5 | `VECTORIZER_COMPONENT_LIFECYCLE.md` (`ENHANCED` = `SANDBOX`) and `VECTORIZER_CANONICAL_PATHS.md` (`enhanced` = `PRODUCTION`) disagree | Governance reconciliation |
| F-6 | VEC-ROOT-001 §5a says `body_lexicon.md` "has never been committed"; it was committed in vectorizer-sandbox four days earlier | Editing a merged audit is out of scope |

## Next adjudication — named, not executed

**vectorizer recovery versus retirement using the reconciled benchmark evidence**

Inputs it would use: VEC-ROOT-001 and its §8 criteria; the `c8ad3ae4` harness; the reproduced
anchor (forensic audit §12); `VECTORIZER_COMPONENT_LIFECYCLE.md`; and this census. Nothing in this
increment pre-decides it.
