# Storage decision

Implementation: `FileEvidenceRepository` in `services/api/app/physical_engineering/stored_evidence_repository.py`.

## Choice

One canonical JSON file per `evidence_id`, under a caller-supplied directory. The directory is exclusive: every `*.json` file in it is a record. A file that is not this schema is `MALFORMED`.

The publish shape follows the repository's existing atomic artifact files: write a temporary file in the same directory, `fsync`, then publish. This store uses `os.link` rather than `os.replace`. `os.link` fails when the destination exists, so a second writer cannot replace a record. If the existing bytes match, the save is idempotent. If they differ, `DuplicateEvidenceContent` is raised.

There is no default path, no in-memory fallback, and no delete method. `list_for_subject` returns matches sorted by `evidence_id`. It does not pick a latest record by UUID or timestamp.

Reopen is a new `FileEvidenceRepository` on the same directory. A second Python process reading that directory returns the same digest. Both are tested.

## Rejected stores

| Candidate | Why it was not used |
| --- | --- |
| `InMemoryEvidenceResolver` | Test fixture. Process restart drops it. |
| Alembic `art_studio` and `cam_logs` tables | Those schemas belong to rosette jobs and CAM logs. An evidence table there would attach physical evidence to another authority and would require a migration. |
| RMOS sqlite / runs directory | RMOS run artifacts are a different domain. This increment does not import `app.rmos`. |
| `app.governance.provenance_record` | That record carries authority stages. Evidence provenance here only names a source. |

No new database technology was added. No migration was added.

## Test directories

The API suite's autouse fixture writes `learned_overrides.json` into pytest `tmp_path`. Evidence tests use `tmp_path / "evidence"` so that foreign JSON is not inside the store. That fixture file is unchanged.
