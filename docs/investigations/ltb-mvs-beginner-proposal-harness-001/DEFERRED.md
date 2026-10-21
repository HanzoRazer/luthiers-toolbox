# Deferred from LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001

This milestone stops once a beginner request can be formed into the existing proposal and the gate's result can be shown unchanged. The following stays out.

| Item | Why it stays out |
| --- | --- |
| Guided beginner UI | No interface in this increment. The service is internal Python. |
| HTTP API route | No route was added. A route would be a later milestone, not a convenience fold-in. |
| Evidence subject-revision applicability | `ResolvedEvidence` has no subject or revision field. A check would be a new rule. |
| Geometry seam `PEP-MESH-SEAM-003` | The proposal gate still treats geometry as an untrusted claim. This harness does not close that gap. |
| `MAINT-DEFER-017` | Production `VITE_API_BASE` omits `/api`. Queued in `SPRINTS.md`. Not this harness. |
| `MAINT-DEFER-018` | Archive-suite detector matches comments. Queued in `SPRINTS.md`. Not this harness. |
| `tools/grounding_agent` | Live handoff-conformance tool. Not modified. |
| Numeric production limits | Policy thresholds remain caller-supplied test values. |
| CAM, DXF, G-code, export, manufacturing authority | Not part of screening. |
| Next MVS increment | A guided shell may be the successor. It is not authorized by this document. |

`advisory_allowed` in a later shell must still mean the gate's human-review flag. A shell must not translate it into permission to cut.
