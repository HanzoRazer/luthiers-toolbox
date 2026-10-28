# Source state — SHOP-JOB-DESIGN-PIN-001

Date: 2026-10-28. Captured before the snapshot writer existed. The project serializer was not changed.

## Canonical source

The routed production workspace is SOL-A01: `Project.data` written by `serialize_design_state` in `services/api/app/projects/service.py`. The router is `PUT /api/projects/{project_id}/design-state`. The client reads it from `packages/client/src/api/projects.ts`.

`serialize_design_state` is `InstrumentProjectData.model_dump(mode="json", exclude_none=False)` plus `schema_version` forced to `CURRENT_SCHEMA_VERSION` (`1.1`). Two calls on the same object return equal dicts. Sorting keys does not change the canonical JSON digest.

The frozen witness is `fixtures/baseline_acoustic_guitar_design_state.json`, produced by `create_default_design_state("acoustic_guitar")` then `serialize_design_state`. Payload digest `f35324c276d931e53da0c38d068031206e96fac95a5be8f058b16737e2e54e23`. It is a synthetic default, not a customer project.

## Included

Every key the serializer emits is copied:

`schema_version`, `instrument_type`, `spec`, `blueprint_geometry`, `bridge_state`, `neck_state`, `material_selection`, `body_config`, `analyzer_observations`, `manufacturing_state`, `manufacturing_artifacts`, `custom_data`.

Nulls stay null. Lists stay lists. Numbers stay JSON numbers. `spec.scale_length_mm` on the witness is `645.0` and `spec.nut_width_mm` is `43.0`.

## Not in the design payload

These live on the project row or the HTTP envelope, not in `serialize_design_state`. Capture does not receive them:

`name`, `description`, `owner_id`, `created_at`, `updated_at`, `features_used`, `commit_message`.

There is no separate transient-UI field inside `InstrumentProjectData`. Nothing inside the serializer output is stripped.

## Schema identity

`InstrumentProjectData` has `schema_version` and no `schema_id`. The snapshot stores `project_schema_id: null` and `project_schema_version: "1.1"` for this witness. Absence is not filled in with an invented schema id.

## Units and coordinate frame

Dimensions are millimeters or degrees in the field name (`scale_length_mm`, `nut_width_mm`, `neck_angle_degrees`, `axis_angle_deg`). There is no coordinate-frame object and this increment does not add one.

When blueprint geometry is present, `body_outline_mm` is an `(x, y)` list in millimeters, counterclockwise, and `axis_angle_deg` is degrees from vertical. The default witness has `blueprint_geometry: null`. A capture test copies a manual outline and shows those numbers unchanged.

## What is not promoted

`manufacturing_artifacts` may carry optional `toolpaths_sha256` and `feasibility_sha256`. Those stay inside the design payload. They are not copied into `artifact_refs`, because a reference has one `content_digest` and choosing between the two hashes would invent a policy. `artifact_refs` and `generator_refs` are empty unless the caller supplies them with a real sha256.

`manufacturing_state.status` is copied when the project has one, including the stored value `cam_approved`. That is the project blob. The snapshot type has no approval field and does not read the status.

## Rejected while copying

Non-finite numbers, booleans on numeric fields (`*_mm`, `*_deg`, `*_degrees`, `*_lbs`, `*_pct`, and the named counters), absolute or `..` paths, and keys named like credentials (`password`, `secret`, `token`, `api_key`, `authorization`, `credential`). Refusal leaves the project unsaved by this package. The project save path is not involved.

## Other design stores that are not this source

Rosette and art-studio snapshots, the client undo stack, and RMOS `RosetteDesignSnapshot` are different products. They are not the routed instrument-project workspace.
