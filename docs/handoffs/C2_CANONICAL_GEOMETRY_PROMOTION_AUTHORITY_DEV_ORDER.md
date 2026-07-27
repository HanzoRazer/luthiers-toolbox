# C2 Process-Exclusive Canonical Geometry Authority Dev Order

**Status:** Dev-ready scope  
**Created:** 2026-07-03  
**Lane:** Governance / CI-RED remediation / C2 geometry-origin closure  
**Keystone ruling to operationalize:** Canonical geometry authority is process-derived, not artifact-derived. Geometry becomes authoritative only as the output of the approved canonical process following a governed approval event.

---

## 1. Purpose

Turn the unresolved C2 geometry-origin gate into an enforceable code contract:

> Source geometry may propose, evidence may support, and representation may carry geometry, but canonical body geometry exists only when the approved canonical process produces it after a governed approval event.

This is stronger than the older promotion-only framing. The code must not treat a reviewer click, DXF file, IBG output, vectorizer result, user template, spec excerpt, registry entry, route name, or storage location as authority by itself.

The implementation goal is:

```text
candidate/evidence/source geometry
  -> approved canonical process
  -> governed approval event
  -> process output
  -> canonical body geometry
```

If the approved process cannot handle a legitimate new case, the fix is to extend and re-approve the process. The fix is never to grant authority to one individual artifact as an exception.

This should reduce governance and CI-RED churn by making vectorizer, IBG, templates, DXF, CAM, and registry work reference the same authority boundary instead of re-arguing whether each source is canonical.

This is not another adapter sprint. It is the first code expression of the C2 origin ruling.

---

## 2. Scope

### In Scope

- Add a process-approval record model for canonical geometry authority.
- Add an additive canonical-reference factory that requires that process-approval record.
- Add validation warnings for legacy canonical references that lack process approval metadata.
- Update taxonomy wording so canonical geometry is process output, not IBG/BOE-owned truth.
- Add a router path for process-approved canonical references.
- Add tests proving artifacts, formats, routes, registries, and individual reviewers cannot self-create authority.
- Add/update governance docs so the C2 ruling is referenceable.

### Out of Scope

- No solver, calibration, vectorizer, IBG, export, CAM, or body-geometry behavior changes.
- No DB or persistence migration in the first pass.
- No strict RED flip for legacy canonical references in PR 1.
- No reopening C2-A narrow decisions.
- No C3 enforcement sprint.
- No one-off exception path for an individual geometry artifact.

---

## 3. Decisions

1. **Authority is process-exclusive.**
   Canonical geometry authority is created only by the approved canonical process following a governed approval event.

2. **Artifacts are never direct authority.**
   Instrument specs, user templates, vectorizer output, IBG output, DXF/SVG/STEP files, CAM/runtime geometry, registry entries, and human sketches can be inputs or evidence. They do not become canonical by origin, quality, filename, format, or location.

3. **Approval is governed, not merely human.**
   A human reviewer may participate, but a human actor id alone does not confer authority. The approval must be tied to a canonical process id, process version, approval rule, approval event, source provenance, and process output.

4. **The canonical process is a promotion boundary, not automatic truth.**
   Geometry entering the process remains non-authoritative until the governed approval event records a valid process output.

5. **Process output creates canonical authority.**
   The approved output becomes `canonical_geometry`. Downstream DXF/SVG/STEP/CAM outputs inherit authority from that canonical source as representation or operational derivatives.

6. **MRP/registry records status and provenance, not geometry truth by itself.**
   Registry mutation must not promote geometry without a process-approval record.

7. **New legitimate cases extend the process.**
   If the canonical process cannot cover a new legitimate geometry case, stop and create a process-extension decision. Do not add an artifact-specific bypass.

8. **This work must stay code-owned and narrow.**
   No broad C3 enforcement, no registry rewrite, no solver/calibration changes, no export behavior expansion in the first pass.

---

## 4. Evidence Eligibility Matrix

This table is the implementation translation of the ruling. It does not decide source quality. It decides whether a source has direct authority.

| Candidate source | Eligible as process input? | Direct canonical authority? | Authority path |
|---|---:|---:|---|
| Instrument specification | Yes | No | Evidence/input to approved canonical process |
| User template | Yes | No | Candidate input to approved canonical process |
| Vectorizer output | Yes | No | Evidence input with provenance |
| IBG output | Yes | No | Evidence/candidate input with provenance |
| Human sketch/edit | Yes | No | Candidate input, never authority by opinion alone |
| MRP registry | Metadata only | No | Records provenance/status after process output |
| DXF/SVG/STEP export | Representation only | No | Carries inherited authority state from upstream source |
| CAM/runtime geometry | Operational only | No | Consumes canonical/evidence geometry, does not define it |
| Existing approved canonical geometry | Yes | Already canonical if process-approved | May be referenced or transformed only through governed process rules |

Reviewer question after this lands:

```text
Did this geometry become canonical through the approved canonical process?
Where is the governed approval event and process-output record?
```

Not:

```text
Is this DXF/template/IBG/spec/vectorizer artifact good enough to be canonical?
```

---

## 5. Current Repo Grounding

Existing primitives to reuse:

| Existing file | Current role | Reuse |
|---|---|---|
| `services/api/app/cam/geometry_authority_taxonomy.py` | Defines `canonical_geometry` vs derived layers | Update wording so canonical means process-approved output, not "owned by IBG/BOE" |
| `services/api/app/cam/geometry_authority_reference.py` | Creates canonical and derived authority references | Add process-approval-aware canonical factory and metadata fields |
| `services/api/app/cam/geometry_authority_validation.py` | Detects authority collapse | Add canonical-process validation |
| `services/api/app/cam/geometry_authority_registry.py` | In-memory authority reference registry | Index/validate process-approved canonical references |
| `services/api/app/routers/cam/geometry_authority_router.py` | API for geometry authority references | Add process-approved endpoint or request path |
| `services/api/app/instrument_geometry/body/ibg/body_evidence_candidate.py` | Human review can move candidates to `HUMAN_REVIEWED` | Use as upstream candidate proof, not as canonical by itself |
| `services/api/app/governance/review_enforcement.py` | Blocks system approval/rejection | Reuse actor and review semantics, but do not treat actor alone as authority |
| `services/api/app/governance/authority_state.py` | Blocks direct advisory-to-canonical transitions | Preserve as lower-level guard |
| `docs/governance/coordination/GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md` | Role/state separation | Update references to the process-exclusive boundary |
| `docs/governance/C2_STATUS_RECONCILIATION_2026-06-23.md` | Says geometry-origin is sole open gate | Update only after the process-exclusive ruling is explicitly accepted |

Important existing ambiguity:

`geometry_authority_taxonomy.py` currently describes canonical geometry as "Authoritative design truth owned by IBG/BOE." That should be replaced with "Authoritative design truth produced by the approved canonical process following a governed approval event." IBG/BOE may participate in the process, but ownership is not inferred from IBG/BOE as a source.

---

## 6. Proposed Code Shape

### 6.1 New Process Approval Record

Add:

```text
services/api/app/cam/canonical_geometry_process_approval.py
```

Suggested model:

```python
class CanonicalProcessApprovalRecord(BaseModel):
    approval_record_id: str
    canonical_process_id: str
    canonical_process_version: str
    governed_approval_event_id: str
    approval_rule_id: str
    source_geometry_id: str
    source_geometry_role: str
    source_authority_state: str
    output_geometry_id: str | None
    decision: Literal["approve"]
    approver_id: str
    approver_role: str
    provenance_hash: str
    process_inputs_hash: str
    approved_at: datetime
    notes: str = ""
    metadata: dict[str, Any] = {}
    deterministic_approval_hash: str = ""
```

Required validators:

- `canonical_process_id`, `canonical_process_version`, `governed_approval_event_id`, `approval_rule_id`, `source_geometry_id`, `provenance_hash`, and `process_inputs_hash` must be non-empty.
- `decision` must be `approve`.
- `approver_id` may not be a system actor for approve decisions.
- The approver identity is evidence of participation, not authority by itself.
- `source_authority_state` may not be inferred from `DXF`, `SVG`, `STEP`, route name, or storage location.
- The record must represent an output of the approved canonical process, not a free-standing artifact exception.
- If the source case is not covered by `canonical_process_id` and `canonical_process_version`, validation must fail with a "process extension required" reason.

Suggested helpers:

```python
create_canonical_process_approval_record(...)
validate_canonical_process_approval_record(...)
```

Compatibility note:

If implementation prefers the existing "promotion" vocabulary, it may keep a file named `canonical_geometry_promotion.py`, but the public model and validation language should remain process-centric. Avoid APIs where the implied rule is "human approves artifact, therefore canonical."

### 6.2 Process-Approved Canonical Reference Factory

Modify:

```text
services/api/app/cam/geometry_authority_reference.py
```

Add fields to `GeometryAuthorityReference`:

```python
process_approval_record_id: Optional[str] = None
process_approval_record_hash: Optional[str] = None
canonical_process_id: Optional[str] = None
canonical_process_version: Optional[str] = None
governed_approval_event_id: Optional[str] = None
process_source_geometry_id: Optional[str] = None
```

Add new factory:

```python
create_process_approved_canonical_geometry_reference(
    approval_record: CanonicalProcessApprovalRecord,
    owning_domain: str,
    source_authority: str,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> GeometryAuthorityReference
```

Behavior:

- Produces `authority_layer="canonical_geometry"`.
- Sets `may_define_canonical_geometry=True`.
- Copies process approval metadata into the reference.
- Stores `provenance_hash` from the approval record.
- Does not authorize execution or machine output.
- Does not accept representation-only source claims unless provenance points to the actual upstream geometry source.

Do not delete `create_canonical_geometry_reference()` in the first pass. Mark it as legacy/unapproved in docstring and tests. Deprecation or hard blocking can be a follow-up after call sites are migrated.

### 6.3 Validation Guard

Modify:

```text
services/api/app/cam/geometry_authority_validation.py
```

Add:

```python
def validate_canonical_process_authority(reference: GeometryAuthorityReference) -> tuple[bool, str | None]:
```

Rules:

- For `canonical_geometry`, process-approved references must carry process approval metadata.
- `canonical_process_id`, `canonical_process_version`, `governed_approval_event_id`, and `process_approval_record_hash` must be present.
- Authority cannot be inferred from format, route, serializer, registry location, IBG/vectorizer/template origin, or individual reviewer identity.
- If canonical reference lacks process approval metadata, return a warning in the first PR, not a RED gate, to avoid breaking legacy 7T tests and call sites.
- If a caller attempts an artifact-specific exception, return a failure reason that names process extension as the required path.

Follow-up C3/strict mode can turn missing process approval metadata into RED once all canonical creators are migrated.

### 6.4 Router/API Boundary

Modify:

```text
services/api/app/routers/cam/geometry_authority_router.py
```

Add a new endpoint rather than changing the existing endpoint immediately:

```text
POST /api/cam/geometry-authority/references/canonical/process-approved
```

Request shape:

```json
{
  "owning_domain": "boe",
  "source_authority": "canonical_process",
  "approval_record": {
    "canonical_process_id": "body-geometry-canonicalization",
    "canonical_process_version": "v1",
    "governed_approval_event_id": "...",
    "approval_rule_id": "...",
    "source_geometry_id": "...",
    "source_geometry_role": "evidence",
    "source_authority_state": "governed_evidence_candidate",
    "decision": "approve",
    "approver_id": "human:...",
    "approver_role": "reviewer",
    "provenance_hash": "...",
    "process_inputs_hash": "..."
  },
  "description": "..."
}
```

Expected behavior:

- Governed approval event creates a process-approved canonical reference.
- `system:` approver returns validation error for approve decisions.
- Missing process id, process version, approval rule, approval event, provenance, or process inputs hash returns validation error.
- Export/representation-only source claims are not promoted unless their upstream provenance identifies the actual geometry source.
- Artifact-specific exception requests are rejected with a process-extension-required message.

### 6.5 Documentation Updates

Patch:

```text
docs/governance/coordination/C2_GEOMETRY_ORIGIN_ARBITRATION_PACKET.md
docs/governance/coordination/GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md
docs/handoffs/CAM_7T_GEOMETRY_AUTHORITY_REFERENCES_HANDOFF.md
docs/governance/C2_STATUS_RECONCILIATION_2026-06-23.md
```

New packet status should be explicit:

```text
Status: Proposed/Ratification-ready unless the repo owner explicitly marks this ruling ratified.
Ruling language: Canonical geometry authority is process-derived, not artifact-derived.
Canonical body geometry exists only as the output of the approved canonical process following a governed approval event.
```

The implementation PR should make the ratification status visible in the packet and PR body.

---

## 7. File-by-File Patch Plan

### `services/api/app/cam/canonical_geometry_process_approval.py` new

- Define `CanonicalProcessApprovalRecord`.
- Define `CanonicalProcessApprovalError`.
- Define factory and validation helpers.
- Compute deterministic hash excluding timestamps if the repo pattern prefers stable hashes; otherwise include timestamp only in non-deterministic fields and document it.
- Add explicit "process extension required" failure for source cases outside the approved process scope.

### `services/api/app/cam/geometry_authority_reference.py`

- Import process approval record type.
- Add optional process approval metadata fields.
- Add `create_process_approved_canonical_geometry_reference()`.
- Update `compute_hash()` to include process approval record id/hash for process-approved references.
- Update legacy canonical factory docstring:
  - "legacy/unapproved canonical reference; use process-approved factory for C2 geometry-origin-compliant body geometry."

### `services/api/app/cam/geometry_authority_validation.py`

- Add canonical process authority validation helper.
- Add warnings to validation result when canonical reference lacks process approval record.
- Ensure derived references remain unchanged.
- Ensure export/visualization cannot smuggle `canonical_definition`.
- Ensure an individual artifact exception is rejected unless represented as an approved process extension.

### `services/api/app/cam/geometry_authority_taxonomy.py`

- Change canonical layer description:
  - From: "Authoritative design truth owned by IBG/BOE"
  - To: "Authoritative design truth produced by the approved canonical process following a governed approval event"
- Add `requires_process_approval: bool` if the team wants typed taxonomy metadata. If added, tests must assert only canonical has it.

### `services/api/app/routers/cam/geometry_authority_router.py`

- Add request model for process-approved canonical creation.
- Add route `POST /references/canonical/process-approved`.
- Register and validate the returned reference.
- Keep existing route unchanged for compatibility in the first pass.

### `services/api/tests/cam/test_canonical_geometry_process_approval.py` new

Cover:

- Governed process approval record is valid.
- System actor approve decision is rejected.
- Missing process id/version/rule/event/provenance is rejected.
- Process-approved canonical reference carries process approval metadata.
- Process-approved canonical reference validates green.
- Legacy canonical reference without process approval metadata gets warning, not RED.
- Export geometry cannot become canonical by format/path claim alone.
- IBG/vectorizer/template/spec inputs remain non-authoritative until process-approved output exists.
- Artifact-specific exception requests fail with process-extension-required reason.

### `services/api/tests/cam/test_geometry_authority_references.py`

- Update canonical description assertions only if they exist.
- Add targeted tests for new `requires_process_approval` metadata if introduced.
- Do not rewrite the 100-test suite broadly.

### Docs

- Add `docs/governance/coordination/C2_GEOMETRY_ORIGIN_ARBITRATION_PACKET.md`.
- Update GAMS to point to the process-exclusive authority boundary.
- Update CAM 7T handoff language so future developers do not keep repeating "IBG/BOE owns canonical truth."

---

## 8. Utilities

No new standalone utility is required for PR 1.

Use existing project checks:

```text
scripts/ci/check_cbsp21_patch_input.py
scripts/ci/check_cbsp21_gate.py
app/ci/check_complexity
```

Optional low-risk helper if implementation noise grows:

```text
services/api/app/cam/canonical_process_ids.py
```

Purpose:

- Centralize the first approved canonical process id and version constants.
- Avoid string drift across the model, router, tests, and docs.

Do not add this helper unless at least three files need the same literal values.

---

## 9. Test Cases

### Unit

1. `test_governed_process_approval_creates_record`
2. `test_system_actor_cannot_approve_process_output`
3. `test_missing_process_identity_blocks_approval_record`
4. `test_missing_provenance_blocks_approval_record`
5. `test_process_approved_canonical_reference_includes_approval_hash`
6. `test_canonical_reference_without_process_approval_warns_in_transition_mode`
7. `test_export_representation_cannot_self_promote_to_canonical`
8. `test_ibg_vectorizer_template_and_spec_inputs_are_not_direct_authority`
9. `test_artifact_exception_requires_process_extension`
10. `test_derived_geometry_still_requires_source_reference`
11. `test_existing_non_canonical_authority_collapse_guards_still_red`

### Router

1. `POST /references/canonical/process-approved` succeeds with governed approval event metadata.
2. Same route rejects `system:` approver for approve decisions.
3. Same route rejects missing process id/version/rule/event.
4. Existing canonical route remains available but returns unapproved metadata or warning.
5. `/ci` summary counts warnings for unapproved canonical references.

### Regression

Run:

```text
PYTHONPATH=services/api py -3.11 -m pytest services/api/tests/cam/test_geometry_authority_references.py services/api/tests/cam/test_canonical_geometry_process_approval.py -q
PYTHONPATH=services/api py -3.11 -m pytest services/api/tests/test_ibg_intake_gate.py services/api/tests/test_ibg_constitutional_integration.py -q
PYTHONPATH=services/api py -3.11 -m pytest services/api/tests/test_dxf_lifecycle_ibg_provenance_guards.py services/api/tests/test_ibg_export_provenance.py -q
```

Run local CI gates:

```text
py -3.11 scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
py -3.11 scripts/ci/check_cbsp21_gate.py --manifest .cbsp21/patch_input.json --changed-files <final PR file set>
py -3.11 -m app.ci.check_complexity --baseline app/ci/complexity_baseline.json
```

---

## 10. Rollout Order

### PR 1 - Process Approval Record + Additive Factory

Goal: introduce the model without breaking existing references.

Files:

- `canonical_geometry_process_approval.py`
- `geometry_authority_reference.py`
- `geometry_authority_validation.py`
- `geometry_authority_taxonomy.py`
- new tests

Acceptance:

- Process-approved canonical references are possible only with governed approval metadata.
- Human actor id alone is insufficient.
- Existing canonical tests still pass with compatibility warnings.
- No runtime export or solver behavior changes.

### PR 2 - Router/API Adoption

Goal: expose the process-approved creation path.

Files:

- `geometry_authority_router.py`
- router tests
- CAM 7T docs

Acceptance:

- New process-approved endpoint passes.
- System actors rejected for approve decisions.
- Existing endpoint remains compatibility path.

### PR 3 - Governance Packet + Status Reconciliation

Goal: make the C2 origin decision referenceable.

Files:

- `C2_GEOMETRY_ORIGIN_ARBITRATION_PACKET.md`
- `GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md`
- `C2_STATUS_RECONCILIATION_2026-06-23.md`

Acceptance:

- C2 geometry-origin is no longer "not packeted."
- The packet names the process-exclusive decision and scope without reopening C2-A.

### PR 4 - Strict Enforcement Follow-up

Goal: after call sites migrate, turn unapproved canonical references from warning to RED.

Non-goal for PR 1. Do not do this early.

---

## 11. Human Approval / Stop Gates

Stop and ask before implementation if any of these arise:

- The repo owner does not intend the sentence "Canonical geometry authority is process-derived, not artifact-derived" as a ratified implementation decision.
- The implementation would treat a human reviewer decision outside the approved canonical process as enough to create authority.
- The implementation would remove or rewrite the existing 7T route instead of adding a process-approved path.
- A production export path would change behavior.
- A registry or persistence migration becomes necessary.
- A non-human/system actor needs to approve process output.
- The PR would classify IBG, vectorizer, DXF, SVG, STEP, CAM, MRP, templates, or specs as automatic authority.
- The PR would add a one-off exception path for an individual artifact instead of requiring process extension.

Direct repo-owner/governance approval still needed:

- Ratify the C2 geometry-origin packet text.
- Ratify the initial canonical process id/version and approval-rule vocabulary.
- Approve the date/status wording used in `C2_STATUS_RECONCILIATION_2026-06-23.md`.
- Decide when to flip compatibility warnings to strict RED enforcement.

---

## 12. Expected Cleanup Effect

This will not magically close all CI-RED items, but it should collapse the coupling:

- Vectorizer becomes evidence until process-approved output exists.
- IBG becomes evidence/candidate until process-approved output exists.
- User template becomes candidate until process-approved output exists.
- Instrument spec becomes declared evidence/input where applicable, not full body-outline authority by default.
- DXF/SVG/STEP remain representation lanes.
- CAM remains operational consumer.
- MRP records provenance/status, not geometry truth.
- Canonical geometry becomes a recorded output of the approved canonical process following a governed approval event.

After this lands, future PR review asks:

```text
What approved canonical process produced this geometry?
Where is the governed approval event?
What process output record/hash backs the canonical reference?
```

That is the code-level form of the keystone decision.
