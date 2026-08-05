# BR-044A TC-12 — API Adapter Radiation-Ratio Finding

**Repository:** `HanzoRazer/luthiers-toolbox`  
**Branch:** `br-044a`  
**Evidence baseline:** `0179a032`  
**Finding status:** VERIFIED CODE FACT  
**Production behavior changed:** No

## Question

Does the frontend stiffness-index path receive the backend's canonical `radiation_ratio` value when tonewood records are loaded through the API?

## Finding

No. The backend's canonical `radiation_ratio` does not reach `StiffnessIndexPanel` through the current frontend API adapter.

The current frontend path is:

```text
GET /api/registry/tonewoods
    -> ApiTonewoodRecord
    -> apiRecordToEntry()
    -> TonewoodEntry
    -> computeIndices()
    -> calcRadiationRatio()
```

At each frontend contract boundary, `radiation_ratio` is absent:

1. `ApiTonewoodRecord` does not declare a `radiation_ratio` field.
2. `apiRecordToEntry()` does not map a `radiation_ratio` field.
3. `TonewoodEntry` has no radiation-ratio property.
4. `computeIndices()` therefore recomputes radiation ratio locally for both hardcoded and API-backed records.

The only occurrence of `radiation_ratio` in `tonewoodData.ts` is explanatory prose; it is not a transported data field.

## Consequence for BR-044

The component is not choosing a frontend value instead of an available backend value. The backend value is structurally unavailable to this component.

Therefore both live data paths use the same frontend-local calculation:

```text
hardcoded records -> local computeIndices()
API records       -> apiRecordToEntry() -> local computeIndices()
```

This means the confirmed `x1000` radiation-ratio defect affects both the built-in fallback path and the API-backed path after adaptation.

## Architectural implication

The BR-044B repair should preserve a canonical local pure implementation because local calculation is currently the only implementation available to this component for either path.

A future "consume backend value where present" enhancement is not a one-line preference change. It requires at least:

- adding `radiation_ratio` to `ApiTonewoodRecord`;
- adding a canonical radiation-ratio field to the local `TonewoodEntry` contract, or defining a separate adapted-record contract;
- mapping the field in `apiRecordToEntry()`;
- defining precedence when both transported and locally computable values exist;
- adding parity and conflict-handling tests.

Those type and adapter changes belong explicitly in BR-044B scope if backend-value transport is authorized.

## Decision impact

This finding strengthens the recommended BR-044B authority model:

> Maintain a canonical, pure frontend implementation of `radiation_ratio = c / rho` for offline/fallback operation and for API records that do not transport the derived value. Treat backend-value transport and parity checking as an explicit additive contract change, not as an assumption about the current adapter.

## Non-findings

This evidence does not establish:

- that the backend endpoint itself omits `radiation_ratio` from every serialized response;
- that backend transport must be added in BR-044B;
- that hardcoded tonewood data should be removed;
- that qualitative rating thresholds are empirically valid;
- that any production source should change during BR-044A.

## Next use

Incorporate this finding into:

- `BR-044A_FRONTEND_RADIATION_RATIO_PROOF.md`;
- the final consumer and data-flow inventory;
- the BR-044B file-by-file patch plan;
- remediation register, ledger, dependency-map, and queue updates.
