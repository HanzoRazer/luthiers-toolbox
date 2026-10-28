# Contract — ltb_design_snapshot 1.0

Schema id `ltb_design_snapshot`. Schema version `1.0` only. Any other version fails with `UNKNOWN_SCHEMA_VERSION`. No LTB naming registry required a different schema id.

## Fields

| Field | Rule |
|---|---|
| `design_snapshot_id` | Filename-safe id. Default `dsn_{UTC milliseconds}_{uuid4 hex}`. A caller id is kept. The factory is not called when the caller passes an id. |
| `external_job_ref.system` | `CNC-Production-Shop` only. |
| `external_job_ref.job_id` | Non-empty opaque string, stored exactly, including case. |
| `external_job_ref.verification_status` | `UNVERIFIED_EXTERNAL_REFERENCE` only. |
| `project_ref.project_id` | Non-empty LTB project id. This is the mutable workspace, not the snapshot id. |
| `project_ref.project_schema_id` | Source `schema_id` when the payload has one. Otherwise null. |
| `project_ref.project_schema_version` | Source `schema_version` when the payload has one. Otherwise null. |
| `project_ref.source_state_digest` | SHA-256 of the canonical design payload. For an untransformed capture this equals `design_payload_digest`. |
| `captured_at` | Timezone-aware timestamp. `datetime.isoformat()` writes an offset, not `Z`. |
| `captured_by.actor_id` | Non-empty actor reference. |
| `design_payload` | JSON object copied from the project serializer and recursively frozen in the snapshot object. Engineering fields are not dropped. |
| `design_payload_digest` | SHA-256 of the canonical design payload only. |
| `artifact_refs` | Caller order. Each item needs `artifact_id`, `artifact_kind`, and lowercase `content_digest`. `media_type` and `source_path_hint` are null when omitted. The hint is a relative path. |
| `generator_refs` | Caller order. `generator_id` and `generator_version` are required. Digests are null unless the caller has them. |
| `snapshot_digest` | SHA-256 of the canonical snapshot object with `snapshot_digest` removed. |

## Canonical bytes

JSON objects are serialized with sorted keys, separators `(",", ":")`, and `allow_nan=False`. Unicode is escaped (`café` becomes `\u00e9`), the same default as the shop-operation record. Array order is the caller order and is not sorted. Optional reference fields are stored as null so the bytes stay stable.

Key order in the input does not change a digest. A one-value design change changes `design_payload_digest` and `snapshot_digest`.

## Identity

An existing id with the same canonical bytes is idempotent. An existing id with different bytes raises `DUPLICATE_SNAPSHOT`. The public repository is `save` and `get`. It has no update and no delete.

The directory is exclusive. A JSON file with another `schema_id`, truncated JSON, a digest mismatch, an unknown version, or an absolute path fails closed. Publishing writes a temporary file, `os.link`s it, and deletes the temporary file. One writer per directory. This is not a multi-writer store.

Two captures of the same payload may have different snapshot ids and the same design-payload digest. `project_id` does not change when the design changes. The new snapshot does.
