# Evidence record

Schema id: `ltb_stored_evidence_artifact`. Schema version: `1.0`. Module: `services/api/app/physical_engineering/evidence_artifact_v1.py`.

This is an LTB-local record. It has no approval field and no authority field.

## Fields

| Field | Rule |
| --- | --- |
| `evidence_id` | `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` |
| `evidence_type` | `MEASURED`, `CALCULATED`, `IMPORTED_SOURCE`, or `HUMAN_OBSERVED`. Origin only. |
| `evidence_kind` | Required text token. Examples used by the existing gate: `thickness_map`, `modal_frequency`. Not inferred from `quantity_name`. |
| `subject_id`, `subject_revision` | Required text tokens. No revision fallback. |
| `region_id`, `coordinate_frame` | Required text tokens. |
| `quantity_name` | Required text token. |
| `quantity_value` | Signed decimal string. No leading zeros. `NaN` and infinities are refused. |
| `unit` | `^[a-z][a-z0-9_]*$`. `MM` is refused. There is no unit catalog and no conversion. |
| `uncertainty` | Unsigned decimal string. Required because `ResolvedEvidence.uncertainty` consumes it. No default of zero. |
| `observed_at`, `recorded_at` | Timezone-aware timestamps stored with `datetime.isoformat()`. Naive values are refused. A trailing `Z` is accepted on read as UTC. |
| `provenance` | `source_type`, `source_id`, and `operator_or_process`, each a required text token. |
| `payload_digest` | SHA-256 hex of the canonical payload. |
| `supersedes_evidence_id` | Optional evidence id. A record cannot name itself. |

Evidence classes describe origin. They do not rank quality. Source-reported, drawing-derived, model-assumption, and measured-specimen labels are not added. No confidence score is stored.

## Digest

`evidence_serialization.canonical_payload` drops `payload_digest`, then `json.dumps` with `sort_keys=True`, `separators=(",", ":")`, and `allow_nan=False`. The digest is SHA-256 of those UTF-8 bytes.

The file on disk is `canonical_record`, which includes `payload_digest`. Construction recomputes the digest and raises `EvidenceRecordError("DIGEST_MISMATCH")` when the stored digest does not match. Verification does not rewrite the record.

`quantity_value` and `uncertainty` stay decimal strings in the file so the digest does not depend on binary float formatting. `ResolvedEvidence.value` and `uncertainty` are `float` projections of those strings. The projection is not written back.

## Supersession

Correction is a new record. `FileEvidenceRepository.save` requires the named prior record to exist and to share subject, revision, region, coordinate frame, quantity name, and unit. The prior file is not edited.
