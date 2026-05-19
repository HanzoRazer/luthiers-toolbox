# C1 Terminal 4: Acoustics/Observational Semantic Inventory

**Phase**: C1 — Collection (no decisions, no changes)  
**Date**: 2026-05-18  
**Scope**: Acoustic measurement semantics, observational data contracts, provenance patterns, confidence vocabulary, geometry consumption without authority

---

## 1. Strategic Role of Terminal 4

Terminal 4 (Acoustics/Observational) serves as the repository's **low-pressure governance reference domain**.

Unlike Runtime/CAM (implicit authority), Geometry/Topology (unratified authority emergence), and Governance Integration (arbitration pressure), the Acoustics domain demonstrates:

| Characteristic | Evidence |
|----------------|----------|
| Explicit assumptions | `assumptions: string[]` mandatory field |
| Declared confidence | `AcousticConfidence` enum required |
| Clean provenance | `ProvenanceBlockV1` with explicit tracking |
| Consumer-without-authority | Geometry consumption without ownership |
| No semantic drift | Schema versions explicitly declared |
| No implicit ontology | All vocabulary documented |

This makes Acoustics a **control group** for comparing higher-pressure domains.

---

## 2. Confidence Vocabulary

### 2.1 AcousticConfidence

**Source**: `packages/client/src/types/acoustics.ts:16`

| Value | Meaning | Usage Context |
|-------|---------|---------------|
| `unknown` | Confidence not established | Default/error states |
| `low` | Most geometry-derived estimates | Helmholtz from dimensions |
| `medium` | Validated estimates | Cross-checked calculations |
| `high` | Measured values | Direct tap tone measurement |

**Governance Pattern**: Confidence is **mandatory**, not optional. This prevents overconfidence in estimates.

---

### 2.2 AcousticStateSource

**Source**: `packages/client/src/types/acoustics.ts:21-27`

| Value | Meaning | Authority Level |
|-------|---------|-----------------|
| `geometry_estimate` | Derived from dimensions | Non-authoritative |
| `measured` | Direct measurement | Observational |
| `calibrated` | Calibrated measurement | Higher confidence |
| `manual` | User-provided | Declared |
| `unknown` | Source not established | Lowest |

**Governance Pattern**: Source tracking preserves data provenance without claiming authority.

---

## 3. Provenance Vocabulary

### 3.1 ProvenanceBlockV1

**Source**: `app/rmos/acoustics/schemas_manifest_v1.py:48-57`

| Field | Type | Purpose |
|-------|------|---------|
| `device_id` | Optional[str] | Capture device identifier |
| `mic_model` | Optional[str] | Microphone model |
| `adc_model` | Optional[str] | ADC model |
| `calibration` | Optional[dict] | Calibration context |
| `ambient` | Optional[dict] | Environmental conditions |

**Governance Pattern**: Provenance is **capture context**, not authority chain. This distinguishes observational provenance from governance provenance.

---

### 3.2 InstrumentBlockV1

**Source**: `app/rmos/acoustics/schemas_manifest_v1.py:33-46`

| Field | Type | Purpose |
|-------|------|---------|
| `instrument_id` | Optional[str] | Instrument identifier |
| `build_stage` | Optional[str] | Stage at capture |
| `operator` | Optional[str] | Who performed capture |
| `model` | Optional[str] | Instrument model |
| `serial` | Optional[str] | Serial number |
| `top_wood` | Optional[str] | Top species |
| `back_wood` | Optional[str] | Back species |

**Governance Pattern**: All fields **optional** — acoustics doesn't require instrument context to function, but tracks it when available.

---

## 4. Schema Versioning

### 4.1 Explicit Version Literals

**Source**: Multiple files

| Schema | Version Field | Pattern |
|--------|---------------|---------|
| `TapToneBundleManifestV1` | `manifest_version: Literal["TapToneBundleManifestV1"]` | Literal type |
| `AttachmentMetaBrowseOut` | `schema_version: str = "acoustics_attachment_meta_browse_v1"` | Default string |
| `RunsBrowseOut` | `schema_version: str = "acoustics_runs_browse_out_v1"` | Default string |
| `AttachmentMetaFacetsOut` | `schema_version: str = "acoustics_attachment_meta_facets_v1"` | Default string |
| `AttachmentMetaRecentOut` | `schema_version: str = "acoustics_attachment_meta_recent_out_v1"` | Default string |
| `RunDetailOut` | `schema_version: str = "acoustics_run_detail_out_v1"` | Default string |

**Governance Pattern**: Schema versions are **explicit and consistent** — no implicit version inference.

---

## 5. Assumptions Vocabulary

### 5.1 AcousticState.assumptions

**Source**: `packages/client/src/types/acoustics.ts:95`

```typescript
/** Assumptions that apply to this state (mandatory) */
assumptions: string[]
```

**Key Invariant**: Assumptions are **mandatory**. This prevents estimated physics from looking like measured truth.

**Examples of assumptions**:
- "Speed of sound = 343 m/s"
- "Top thickness = 2.8mm typical"
- "Shape factor = 0.85"
- "Linear f ∝ h relationship"

---

### 5.2 Calculation Method Tracking

**Source**: `packages/client/src/types/acoustics.ts:86-88`

| Field | Type | Purpose |
|-------|------|---------|
| `speedOfSoundMps` | number | Speed of sound used |
| `estimateMethod` | string | Method identifier |

**Governance Pattern**: Calculation parameters are **recorded**, not hidden. This enables reproducibility.

---

## 6. Gate Vocabulary (Voicing)

### 6.1 VoicingReport.gate

**Source**: `app/calculators/voicing_history_calc.py:104`

| Value | Meaning | Trigger |
|-------|---------|---------|
| `GREEN` | Both plates on target | Delta ≤ tolerance |
| `YELLOW` | Work remaining | Delta > 20 Hz |
| `RED` | Critical issue | Below target or over-thinned |

**Governance Pattern**: Gate semantics are **locally defined** for voicing domain. Unlike 7M validation gates, these are operational status, not governance enforcement.

---

### 6.2 Status Vocabulary

**Source**: `app/calculators/voicing_history_calc.py:91-95`

| Value | Meaning |
|-------|---------|
| `on_target` | Within frequency tolerance |
| `above_target` | Frequency above target (can thin more) |
| `below_target` | Frequency below target (may be over-thinned) |
| `over_thinned` | Below minimum thickness |
| `no_data` | No measurements available |

**Governance Pattern**: Status vocabulary is **domain-scoped** — not generic "status" overloading.

---

## 7. Geometry Consumption Pattern

### 7.1 Consumer-Without-Authority Model

**Source**: `packages/client/src/types/acoustics.ts:29-40`

```typescript
export interface ApertureGeometryLike {
  aperture_type?: string
  area_mm2?: number
  perimeter_mm?: number
  equivalent_diameter_mm?: number
  characteristic_width_mm?: number | null
  path_length_mm?: number | null
  pa_ratio_mm_inv?: number | null
}
```

**Governance Pattern**: Acoustics consumes geometry through a **interface contract** (`ApertureGeometryLike`), not direct dependency. The geometry remains **separate** from acoustic state.

Key invariant from source:
> "Geometry remains separate (ApertureGeometry is not merged into this)"

---

### 7.2 Body Volume Consumption

**Source**: `app/calculators/acoustic_body_volume.py`

| Input | Source | Authority |
|-------|--------|-----------|
| `lower_bout_mm` | Reference specs | Non-authoritative |
| `upper_bout_mm` | Reference specs | Non-authoritative |
| `waist_mm` | Reference specs | Non-authoritative |
| `depth_*_mm` | Reference specs | Non-authoritative |

**Governance Pattern**: Volume calculator consumes dimensional data but **documents all assumptions**:
- Shape factor (0.85 typical)
- Section proportions (40% / 25% / 35%)
- Top thickness (2.8mm typical)
- Speed of sound (343 m/s)

---

## 8. Attachment Semantics

### 8.1 Attachment Kind Vocabulary

**Source**: `app/rmos/acoustics/schemas_manifest_v1.py:29`

```python
kind: str = Field(min_length=1)
# Examples: "audio_raw", "analysis_summary", "plot", "grid", "point_audio_raw"
```

**Values observed**:
| Kind | Meaning |
|------|---------|
| `audio_raw` | Raw audio file |
| `analysis_summary` | Analysis results |
| `plot` | Visualization |
| `plot_png` | PNG plot |
| `grid` | Grid data |
| `point_audio_raw` | Point-specific audio |
| `manifest` | Bundle manifest |
| `viewer_pack` | Viewer-ready package |
| `advisory` | Advisory notification |

**Governance Pattern**: Kind vocabulary is **stable semantic categories** for file classification.

---

### 8.2 Run Status Vocabulary

**Source**: `app/rmos/runs_v2/acoustics_schemas.py:322`

| Value | Meaning |
|-------|---------|
| `OK` | Run completed successfully |
| `BLOCKED` | Run blocked |
| `ERROR` | Run failed with error |

**Governance Pattern**: Run status is **outcome classification**, not workflow state.

---

## 9. Build Stage Vocabulary

**Source**: `app/calculators/voicing_history_calc.py:18-23`

| Stage | Order | Meaning |
|-------|-------|---------|
| `rough_thicknessed` | 1 | Initial thickness |
| `braced_free_plate` | 2 | Bracing applied |
| `assembled_in_box` | 3 | In assembled body |
| `strung_up` | 4 | Under string tension |

**Governance Pattern**: Build stages are **ordered lifecycle** for voicing workflow, not generic state machine.

---

## 10. Cross-Reference with 7M Registry

### 10.1 Terms That Could Be Registered (But Aren't)

| Term | Domain | Current Status | 7M Candidate? |
|------|--------|----------------|---------------|
| `AcousticConfidence` | Acoustics | Domain-local enum | No — domain-scoped |
| `AcousticStateSource` | Acoustics | Domain-local enum | No — domain-scoped |
| `ProvenanceBlockV1` | Acoustics | Schema version | No — implementation detail |
| `attachment_kind` | RMOS | Stable vocabulary | Maybe — if cross-domain |
| `build_stage` | Voicing | Ordered list | No — workflow-specific |

### 10.2 Governance Pattern: Domain-Scoped Vocabulary

The Acoustics domain demonstrates that **not all vocabulary needs 7M registration**.

Domain-scoped vocabulary should remain local when:
1. It doesn't claim cross-domain authority
2. It has clear ownership
3. It doesn't conflict with other domains
4. It serves operational, not governance, purposes

---

## 11. Observational Data Contract

### 11.1 Key Invariants

**Source**: `packages/client/src/types/acoustics.ts:47-53`

```typescript
/**
 * Key invariants:
 * - Confidence is mandatory (prevents overconfidence in estimates)
 * - Assumptions are mandatory (prevents estimated physics looking like measured truth)
 * - Geometry remains separate (ApertureGeometry is not merged into this)
 */
```

These invariants define the **observational data contract**:

| Invariant | Enforcement | Purpose |
|-----------|-------------|---------|
| Confidence mandatory | TypeScript type | Prevents overconfidence |
| Assumptions mandatory | TypeScript type | Preserves epistemic honesty |
| Geometry separate | Interface design | Prevents authority leakage |

---

### 11.2 No Implicit Authority

The Acoustics domain demonstrates the pattern of **observational data without authority claims**:

| Layer | Role | Authority |
|-------|------|-----------|
| Measurement | Capture | None — observational |
| Calculation | Derive | None — documented assumptions |
| Prediction | Estimate | None — explicit confidence |
| Storage | Archive | None — provenance-tracked |

---

## 12. Summary Statistics

### Vocabulary Counts

| Category | Count |
|----------|-------|
| Confidence levels | 4 |
| Source types | 5 |
| Provenance fields | 10+ |
| Schema versions | 6 |
| Attachment kinds | 9 |
| Build stages | 4 |
| Gate values | 3 |
| Status values | 5 |

### Governance Pattern Observations

| Pattern | Evidence | Significance |
|---------|----------|--------------|
| Explicit assumptions | `assumptions: string[]` mandatory | Prevents hidden authority |
| Explicit confidence | `AcousticConfidence` required | Prevents overconfidence |
| Schema versioning | `schema_version` fields | Enables migration |
| Domain-scoped vocabulary | Voicing status, attachment kinds | Appropriate localization |
| Consumer-without-authority | `ApertureGeometryLike` interface | Clean dependency |
| Provenance tracking | `ProvenanceBlockV1` | Preserves capture context |

---

## 13. Semantic Collisions

### No High-Severity Collisions

Terminal 4 has **no high-severity semantic collisions** with other domains.

| Potential Collision | Status | Resolution |
|---------------------|--------|------------|
| `status` overload | Low risk | Domain-prefixed (`run_status`, `voicing_status`) |
| `gate` vocabulary | Low risk | Different axis (outcome vs governance) |
| `provenance` meaning | Clean | Capture context, not governance chain |

This demonstrates that **disciplined domain design prevents collisions**.

---

## 14. Reference Pattern for Other Domains

The Acoustics domain should be used as a **reference pattern** for governance remediation:

### What Acoustics Does Right

1. **Mandatory confidence** — prevents overconfidence
2. **Mandatory assumptions** — preserves epistemic honesty
3. **Clean geometry consumption** — interface, not dependency
4. **Domain-scoped vocabulary** — no unnecessary registration
5. **Explicit schema versions** — enables migration
6. **Provenance as context** — not authority chain
7. **No implicit ontology** — all vocabulary documented

### What Other Domains Can Learn

| Domain | Current Issue | Acoustics Solution |
|--------|---------------|-------------------|
| IBG | De facto authority | Consumer-without-authority model |
| CAM Topology | Semantic overload | Domain-scoped vocabulary |
| Runtime | Implicit assumptions | Mandatory assumptions field |
| Geometry | Ungoverned primitives | Explicit schema versioning |

---

## C1 Rule Observed

> C1 makes semantic collisions visible. C1 does not make semantic decisions.

No changes were made. This inventory is evidence for C2 reconciliation.

The Acoustics domain demonstrates **healthy governance patterns** that should inform C2 arbitration for higher-pressure domains.
