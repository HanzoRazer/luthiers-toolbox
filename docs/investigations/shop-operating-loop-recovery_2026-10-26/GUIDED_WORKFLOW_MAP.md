# Guided workflow map (track E)

**Finding:** no guided beginner shop-floor flow exists today.
- The piece built to MVS standard, the beginner proposal gate (SOL-E01), is deliberately unrouted. It waits for an owner-approved `ValidationPolicyV1`, which open PR #456 provides the mechanism for but no approved values.
- The live client shell (SOL-E04) computes its own "ready" flag and links straight to CAM.
- No surface records completion and actuals for a non-saw operation (SOL-E10 MISSING).

## What the existing MVS lineage already decided

From `docs/investigations/ltb-mvs-*`:
- **001** built `run_beginner_proposal()`. It passes through `advisory_allowed | evidence_required | rejected` unchanged, and `advisory_allowed` means "eligible for human review", never permission to cut. The fixture is a soundboard thicknessing request: 0.25 mm on `plate-007` at `lower-bout-R17`.
- **002** (guided review slice) stopped before adding a route or a client form. There was no production policy and no MVS client host. It also judged `components/guided/GuidedWorkflow.vue` not to be an MVS host.
- **003** built evidence storage and citation resolution, not exported or routed.
- **004** (PR #456, open) adds policy storage and selection. It fails closed because the policy worksheet has no approver or source for its two thickness fields.

## The six §6E questions, per surface

| Row | Tells user what's next | Explains why blocked | Displays authority without creating it | Evidence / validation / CAM distinguishable | Records completion and actuals | Soundboard demo without CAM exposure |
|---|---|---|---|---|---|---|
| SOL-E01 beginner gate | Yes (`required_evidence`) | Yes (`reason_codes`) | Yes. Any claim but `advisory_only` is rejected. | Yes | **No** | Best fit (thickness fixture), but nothing exposes it |
| SOL-E02 CAM readiness | `exit_condition` text | Yes (`reason`, `evidence`) | Yes. No READY state. | CAM layer only | No | Refuses G-code for `acoustic_soundhole` (REVIEW_REQUIRED). Good containment. |
| SOL-E03 `manufacturing_state` | The 422 says to set it | Yes | **No.** The user can self-assert `cam_approved`. | No | `operations_completed` is a bare string list | — |
| SOL-E04 InstrumentHub | Partial (stage list) | ✅/❌ heuristics | **No.** "Approve for production" on a non-null check. | No | No | **Not safe.** CNC Prep links to `/cam/fret-slots`, `/cam/contour`. |
| SOL-E05 RMOS workflow | `next_step_hint` exists but is not exposed | Governance error strings | **No.** `approve()` accepts any role. | Feasibility vs approval are separate states | No | — |
| SOL-E06 GuidedWorkflow / wizards | Next/complete buttons | "Please complete this step" | n/a (DXF→G-code only) | No | In memory only | No |
| SOL-E07 GateBadge / PrerequisiteNotice | — | **Yes.** Unmet prerequisites shown. | Display only | Can show any gate | No | Yes (display components) |
| SOL-D02 saw execution lifecycle | — | 409s with reasons | Requires `operator_id` | — | **Yes**, for saw batches only | No (saw) |

## Prior concept and boundary records

- `docs/archive/2026/evaluations/PRODUCTION_SHOP_EVALUATION.md:135-198`
  (SOL-E08) recommends a beginner-safe mode, guided top tasks, 5–7 primary jobs
  and persistent job state. None of it was implemented.
- CAM Creation Studio's ratified product boundary (SOL-E09) names "guided
  authoring and progressive disclosure" and "artifact assembly and job
  composition" as Creation Studio roles. **Ruled (R5):** split. Creation
  Studio assembles and reviews the CAM package and does not become the ERP or
  shop traveler. LTB provides the beginner-guided shop-floor interface and
  records operations against the CNC-PS `job_id`.
- `docs/investigations/headstock-integration-feasibility-002_2026-10-19/NEXT_ORDER.md:81`
  expands "MVS" as "manufacturing verification standard". This order uses the
  operating-loop sense. The two are noted, not reconciled.

## Missing guided transitions

1. **Next operation:** no persisted job and operation record exists from which
   to say "do this next" (SOL-E10).
2. **Blocked reason:** reasons exist (E01, E02) but no client renders them.
   Client grep for `GENERATOR_READINESS_BLOCKED|exit_condition` = 0.
3. **Completion and actuals:** no non-saw record exists.
4. **Authority display:** the Hub's CNC Prep stage shows its own heuristic
   instead of E02's verdict.
