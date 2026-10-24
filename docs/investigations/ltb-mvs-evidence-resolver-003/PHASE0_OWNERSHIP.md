# Phase 0 — evidence ownership

Checked: 2026-10-23. Tree: `origin/main` `a0861507313a34a0db2043639512f4618f0885a9`. PR #454 is merged. PR #453 commit `8a2f33cb8f2bd869963ae38c23d08fdd2e950722` is reachable. Open pull requests touching physical engineering, artifact persistence, provenance schemas, evidence registries, or database migrations: none.

Search:

```bash
rg -n "StoredEvidenceArtifact|EvidenceResolver|artifact_store|ArtifactStore|repository|provenance_record|content_digest|subject_revision|evidence_ref|evidence_id" services/api
rg -n "physical.engineering.mesh|physical_engineering_mesh|evidence schema|evidence artifact" docs services/api
```

## Answers

| Question | Result |
| --- | --- |
| Is an evidence schema already adopted from Physical Engineering Mesh? | **NONE.** No Mesh schema or version is imported or referenced as a contract in this repository. |
| Is there an existing durable artifact store? | Yes, as a file pattern. `app/art_studio/services/rosette_snapshot_store.py` writes one artifact with a temp file, `fsync`, and `os.replace`. RMOS runs use a directory of JSON files. Alembic models cover rosette jobs and CAM logs, not physical evidence. |
| Is it production-used or test-only? | The rosette snapshot store and the RMOS runs directory are production stores for other domains. `StoredEvidenceArtifact` / `InMemoryEvidenceResolver` are test-only. Their docstring says the artifact is not a database record. |
| Does it preserve payload bytes or only metadata? | Rosette and RMOS stores preserve file bytes. The in-memory fixture preserves caller-supplied payload bytes and a claimed SHA-256. Neither store binds a subject revision, region, unit, and provenance for a proposal citation. |
| How are digests calculated? | The fixture resolver hashes opaque payload bytes with SHA-256 (`sha256_bytes`). No shared canonical-JSON helper was found for evidence records. |
| How are subject revisions represented? | `PhysicalEngineeringProposalV1` carries `subject_revision` as a required text token. There is no separate revision type. |
| How are migrations handled? | Alembic revisions exist for art studio and CAM log tables. Adding evidence there would be a migration into another authority. |
| Can the store be reopened after process restart? | The file stores can. The in-memory fixture cannot. |
| Does `EvidenceResolver` resolve one record or a collection? | One citation. `resolve(self, ref: EvidenceRef) -> ResolvedEvidence`. The protocol names `EvidenceNotFound` and `EvidenceDigestMismatch`. |
| What fields does `validate_proposal()` actually consume? | Through `screening._collect` and `_one_fact_failure`: `ref_id`, `kind`, `value`, `unit`, `uncertainty`, `source_run`, `artifact_sha256`. Thickness screening also requires `kind == thickness_map` and `unit == "mm"`. Duplicate `ref_id` values are rejected before resolve. |

`app/governance/provenance_record.py` was not reused. It records IBG authority stages. Evidence provenance here only names a source.

## Disposition

The evidence record is an **LTB-local record awaiting ecosystem adoption**.

It is not adopted from Physical Engineering Mesh. It is not an adapter to an upstream contract. Schema id: `ltb_stored_evidence_artifact`. Schema version: `1.0`.

LTB owns persistence, the resolver adapter, applicability checks, and translation into the existing `EvidenceResolver` protocol. This record does not claim ecosystem-wide evidence semantics, scientific validation policy, cross-repository authority, or manufacturing admission.

## Stop conditions

None fired.

- No overlapping evidence implementation was in progress.
- No Mesh contract was referenced and then found missing. The contract is absent, so the order allows an explicitly local record.
- The production file-artifact pattern is not test-only. The new store uses that pattern in a directory of its own. It does not mount the in-memory fixture.
- No database migration is required.
- Payload identity is the SHA-256 of canonical JSON, defined in `EVIDENCE_RECORD.md`.
- The resolver does not invent units, subject identity, revision, region, or provenance. The caller supplies the applicability binding, and the record supplies the rest.
- `EvidenceResolver.resolve` still returns one `ResolvedEvidence`. Applicability is bound on the resolver because the protocol does not pass the proposal.
- No other repository has to publish a contract before this local store can exist.

## What was not changed

`proposal_v1.py`, `beginner_proposal_harness.py`, `tools/grounding_agent`, headstock files, archtop comparator work, `MAINT-DEFER-017`, and `MAINT-DEFER-018`.
