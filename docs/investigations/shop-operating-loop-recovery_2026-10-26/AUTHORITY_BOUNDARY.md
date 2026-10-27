# Authority boundary

The order holds these authorities separate:
- commercial
- design
- evidence
- validation
- CAM
- human authorization

A commercial or workflow status may never grant manufacturing authority. This
file records where the code keeps that separation and where it does not.

## Kept separate (no change needed)

| Authority | Holder | How it is kept |
|---|---|---|
| VALIDATION (advisory) | SOL-E01 beginner proposal gate | Any claim other than `advisory_only` is rejected. `advisory_allowed` is "eligible for review", never "cut". |
| EVIDENCE | SOL-E01 stored evidence resolver | Frozen records with a supersede chain, resolved separately from validation |
| CAM | SOL-E02 generator readiness | Fail-closed with no READY state. Every project G-code router calls `_readiness_gate` first: `cam_workspace_router.py`, `acoustic_cam_router.py`, `body_gcode_router.py:106,169,244`, `flying_v_cam_router.py`, `neck/gcode_router.py:75,149,244`. |
| COMMERCIAL | SOL-B01, SOL-B04 | No manufacturing gate consumes any cost value. CNC-PS `business/*` imports no CAM, RMOS or saw code (CNC-JOB-QUOTE-WORKFLOW-001 §Decisions). |
| CAM-assist courier | SOL-A07 | "transporting authority ≠ creating authority". The handoff "does not authorize execution". |

## Boundary conflicts found (recorded, not fixed)

| # | Where | Conflict | Severity as evidenced |
|---|---|---|---|
| R4 | SOL-E03 `manufacturing_state` | `PUT /api/projects/{id}/design-state` accepts the whole `InstrumentProjectData`, including `manufacturing_state.status`, `cam_approved` and `approved_by` (instrument_project.py:759; projects/router.py:181). No role check or approval event exists. `_project_gcode_common.py:69-79` reads that status as a G-code precondition, and its 422 tells the user to set it. | **Self-asserted approval acting as a CAM gate input. Latent today.** Continuation pass: of the 10 readiness records, only `les_paul_body` passes the readiness layer (`GOVERNED_BY_ASSET_AUTHORITY`, generator_readiness.py:242), and it delegates to the asset gate. `resolve_manufacturing_authority` on `LesPaul_CAM_Closed.dxf` returns **BLOCKED** (quarantine `UNADJUDICATED`), enforced at lespaul_body_generator.py:45. So no project G-code route currently reaches emission. **It becomes live the day that DXF is cleared:** the self-asserted status (which only rejects `draft`) would then be the only project-level gate. |
| — | SOL-E04 InstrumentHub CNC Prep | The UI says "approve for production" when `spec` and `instrument_type` are non-null (useInstrumentProject.ts:95-97). It links to CAM views and marks the stage complete when `cam_approved` is set. | Display authority manufactured from a heuristic. It cannot generate G-code by itself. |
| — | SOL-E05 `WorkflowSession.approve()` | Accepts any `ActorRole`. PATCH sets `status` and `current_step` freely. | Approval not role-gated. No HTTP caller of `approve()` was found. |
| R7 | SOL-D05 CAM job intelligence | Derived numbers are labelled `actual_time_s` | A truthfulness defect, not an authority grant. It must not feed any variance report. |
| R5 | SOL-E09 vs LTB MVS | CCS ratified boundary claims guided authoring and job composition | Ownership overlap (plausible) |
| R1/R2 | SOL-A01/A06, SOL-B01/B04 | Two job identities and two estimators, with incompatible contracts | Competing owners |

## Rule for any next increment

Shop-execution records (who did which operation, when, with what material)
are a **SHOP_EXECUTION evidence** authority:
- They may cite evidence ids and CAM readiness verdicts.
- They must not carry an approval field.
- They must not write `manufacturing_state`.
- They must not satisfy any CAM gate.

A UI may display E01/E02 verdicts and must not compute its own.
