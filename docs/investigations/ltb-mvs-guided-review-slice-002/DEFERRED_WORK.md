# Deferred with the stop

`LTB-MVS-GUIDED-REVIEW-SLICE-002` did not start the vertical slice. The following stays unbuilt until the Phase 0 prerequisite lands.

| Item | State |
| --- | --- |
| `POST /api/physical-engineering/beginner-proposal/review` | Not added |
| Server dependency provider | Not added. No production resolver or policy to inject |
| Guided client form and route | Not added. No MVS host was identified |
| Proposal persistence, approval persistence, evidence upload | Still out of scope |
| CAM, DXF, G-code, downloads | Still out of scope |
| `PEP-MESH-SEAM-003` | Still a separate geometry seam |
| `MAINT-DEFER-017`, `MAINT-DEFER-018` | Still queued. This stop does not repair them |
| `tools/grounding_agent` | Untouched |

The merged harness `run_beginner_proposal()` remains the only beginner entry point. A future route calls it once, with server-owned dependencies, and copies `advisory_allowed`, `evidence_required`, or `rejected`.
