# SPRINTS Maintenance Reconciliation — Evidence Matrix

**Sprint:** SPRINTS-MAINT-RECON-001  
**Document role:** Durable proof for Commit 1 (inventory + re-witness). **Does not mutate `SPRINTS.md`.**  
**Baseline SHA:** `0179a032` (`main` tip at branch creation, 2026-08-04 BR-045A closeout)  
**Reconciliation date:** 2026-08-09  

---

## Evidence source

```text
Evidence source:
External Maintenance Backlog Status Audit
Date: 2026-08-07
Repository mutation during audit: none
Source supplied by owner as attached audit artifact
```

**Provenance note (recovery):** The audit was produced by Cursor cloud agent  
[Maintenance backlog status audit](https://cursor.com/agents/bc-76cfc2a8-e507-4712-a4ce-244f0d2a42de)  
(`bc-76cfc2a8-e507-4712-a4ce-244f0d2a42de`) as artifact  
`/opt/cursor/artifacts/MAINTENANCE_BACKLOG_STATUS_AUDIT_2026-08-07.md`  
(chat/export titled “Maintenance backlog status audit _ Cursor.pdf”).  
It was **not** committed to git. Content was recovered from that agent’s transcript for this sprint.  
**Do not treat the PDF export as a repo path.** The PDF was not copied into this repository.

The audit’s approximate totals (~25–30 active / ~20–25 false) are **orientation only**, not acceptance targets.  
Counts below are derived from the grounded `SPRINTS.md` population after re-witnessing.

---

## Authority boundary

| May do | Must not do |
|--------|-------------|
| Classify `SPRINTS.md` maintenance-state questions | Re-adjudicate BR / CI-RED / GOV ledgers |
| Cite BR / CI-RED as evidence for a SPRINTS claim | Edit `docs/remediation/*` or CI-RED bodies |
| Point to external governance with `EXTERNALLY_GOVERNED` | Invent new backlog items |

Vocabulary (Decision 8):  
`OPEN` · `PARTIALLY_COMPLETE` · `COMPLETED` · `SUPERSEDED` · `OBSOLETE` · `DEFERRED` · `BLOCKED` · `EXTERNALLY_GOVERNED` · `OWNER_DECISION_REQUIRED` · `EVIDENCE_INSUFFICIENT`

---

## Authorized population (from `SPRINTS.md`)

```text
DATA INTEGRITY
- M1–M6, M2.5, M3a, Active Inventory Species Audit
- (related complete companions in same section: NDS phases, FRET-CONSOLIDATION-1, Data File Sync Boundary)

CLEANUP
- CL-1 through CL-14

DEFERRED MAINTENANCE
- MAINT-DEFER-* (and index hygiene for those IDs)

STALE SPRINT CONTROL TEXT
- NEXT SESSION OPENS WITH…
- pending pickup lists
- explicitly carried maintenance obligations in those control blocks

CROSS-REFERENCES (SPRINTS-state questions only)
- Sprint 3 BOE claim
- CAM 8J / BR-006 relationship
- CI-RED-020B relationship
- endpoint-consumer-map / BR-008 / CI-RED-016B relationship
- stale remediation-next references (as they affect SPRINTS operator pointers)
```

---

## High-confidence re-witness results

Independently verified on baseline `0179a032` before any authoritative `SPRINTS.md` edit.

| Audit claim | Re-witness | Result | Confidence |
|-------------|------------|--------|------------|
| CAM 8J / BR-006 reconstructed | Commit `60528f02` (PR #97); modules under `services/api/app/cam/pocketing/` + `cam/routers/pocketing/`; tests `test_pocketing_*.py` present | **True — implementation landed** | High |
| CI-RED-020 CLOSED in SPRINTS | Index row CI-RED-020 **CLOSED** 2026-07-04; cites witness run `28688610338` and 020-B PR #177 | **True — SPRINTS already closed** | High |
| Endpoint consumer map exists (016-B) | `docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md` + `services/api/metrics/endpoint_consumer_map.json` (present, large) | **True — map tranche landed** | High |
| Sprint 3 “BOE endpoint MISSING” stale | `body_export_router.py` implements `POST /api/export/body-outline` (+ validate); tests in `test_body_export_bridge.py`. Claimed path `POST /api/editor/export-dxf` still absent | **Partially true** — a BOE body-export backend **exists** under a different path; absolute “MISSING” is stale; full original Sprint 3 Option-B wiring not proven | High (existence) / Medium (full obligation) |
| NEXT_REMEDIATION_CANDIDATE stale | File still points at BR-002A (2026-07-21); queue says next = **BR-036** | **True — pointer stale** (BR SoR, not SPRINTS body; relevant to operator drift) | High |
| M2.5 still owed | `glue_joint_calc.py:80` and `pickup_position_calc.py:441` still use `.get(..., default)`; `top_deflection_calc.py:42` still `density_kg_m3: float = 400.0` | **True — OPEN** | High |
| M3a CITES tool missing | No `cites_lookup.py` / cites tool module found under `services/api` | **True — OPEN** | High |
| M4 MOE gaps | `spruce_sitka` / `spruce_engelmann`: `modulus_of_elasticity_gpa` **None**; `douglas_fir`: **12.17** (was claimed 10.0 in sprint text) | **PARTIALLY_COMPLETE** — spruce still null; douglas updated vs sprint table | High |
| M5 CIRAD API missing | CIRAD CSVs under `docs/reference/cirad/`; no `cirad_router` / `/api/reference/cirad` in services | **True — OPEN** | High |
| M6 deliverable missing / intent superseded | `docs/audit/unfinished_work_audit_2026-05.md` **absent**; BR suite + 2026-08-07 audit fulfill the stated audit intent | **SUPERSEDED** (provisional — for Commit 2) | High (absence) / Medium (supersession judgment) |
| CL-1/2/5 complete; others queued | Parsed statuses: CL-1/2/5 COMPLETE; CL-3/4/6/9/10/11 Queued; CL-7/8/12/13 awaiting owner; CL-14 optional deferred | **Matches SPRINTS** | High |

---

## Item-by-item matrix

### A. DATA INTEGRITY

| ID | `SPRINTS.md` recorded state | Evidence (re-witness) | Provisional disposition | Confidence | External governance | Notes for later SPRINTS edit |
|----|----------------------------|------------------------|-------------------------|------------|---------------------|------------------------------|
| M1 | COMPLETE 2026-04-30 | Commits cited; section complete | **COMPLETED** | High | — | No change needed |
| M2 | COMPLETE 2026-04-30 | Completes; defers 4 items to M2.5 | **COMPLETED** | High | — | Keep; remainder is M2.5 |
| M2.5 | QUEUED | Three named calculator defaults still present | **OPEN** | High | Related triage may appear under BR-040 (register) — **do not re-adjudicate BR** | Remains genuine unfinished |
| M3a | QUEUED | No cites lookup module | **OPEN** | High | — | Remains genuine unfinished |
| Active Inventory Species Audit | QUEUED HIGH | Padauk template cited; inventory list still aspirational; no close evidence | **OPEN** | Medium | — | Remains genuine unfinished |
| M4 | QUEUED | Sitka/Engelmann MOE null; douglas_fir now 12.17 (≠ sprint “10.0”) | **PARTIALLY_COMPLETE** | High | — | Remainder: spruce MOE + growth-type notes; update douglas row if editing |
| M5 | QUEUED | Reference data on disk; no API | **OPEN** | High | — | Remains genuine unfinished |
| M6 | QUEUED | Deliverable path absent; audit+BR fulfill intent | **SUPERSEDED** | Medium–High | BR remediation program absorbed unfinished-work inventory role | Close/retarget in Commit 2–3; identify replacement = BR suite + this recon |
| NDS 1+1.5 | COMPLETE | In DATA INTEGRITY section | **COMPLETED** | High | — | Out of “aged open” focus |
| NDS Phase 2 | COMPLETE | Same | **COMPLETED** | High | — | — |
| FRET-CONSOLIDATION-1 | COMPLETE | Commits cited | **COMPLETED** | High | — | Audit notes duplicate listing elsewhere — out of population unless control-text |
| Data File Sync Boundary | DOCUMENTED | Doc-only status | **COMPLETED** | High | — | Documentation obligation met |

### B. CLEANUP (CL-1 … CL-14)

| ID | Recorded state | Provisional disposition | Confidence | Notes |
|----|----------------|-------------------------|------------|-------|
| CL-1 | COMPLETE 2026-05-26 | **COMPLETED** | High | — |
| CL-2 | COMPLETE 2026-05-26 | **COMPLETED** | High | — |
| CL-3 | Queued — Ross input | **OWNER_DECISION_REQUIRED** | High | Explicit owner input |
| CL-4 | Queued | **DEFERRED** | High | Hygiene queue |
| CL-5 | COMPLETE 2026-05-26 | **COMPLETED** | High | — |
| CL-6 | Queued | **DEFERRED** | High | — |
| CL-7 | Awaiting Ross confirmation | **OWNER_DECISION_REQUIRED** | High | — |
| CL-8 | Awaiting architectural clarification | **OWNER_DECISION_REQUIRED** | High | — |
| CL-9 | Queued | **DEFERRED** | High | — |
| CL-10 | Queued — defer until other cleanup | **DEFERRED** | High | — |
| CL-11 | Queued | **DEFERRED** | High | — |
| CL-12 | Awaiting Ross decision | **OWNER_DECISION_REQUIRED** | High | — |
| CL-13 | Awaiting decision | **OWNER_DECISION_REQUIRED** | High | — |
| CL-14 | Optional, deferred | **DEFERRED** | High | — |

Cleanup math note (from audit, re-checked): control text claiming “1 complete, 13 queued” would be stale if present — **≥3 complete** (CL-1/2/5). Flag for contradiction search in Commit 2.

### C. DEFERRED MAINTENANCE — `MAINT-DEFER-*`

| ID | Recorded state | Provisional disposition | Confidence | Notes |
|----|----------------|-------------------------|------------|-------|
| MAINT-DEFER-001 | DEFERRED | **DEFERRED** | High | Intentional solo-dev CI deferral |
| MAINT-DEFER-002 | COMPLETE (body); **missing from index table** | **COMPLETED** + index hygiene gap | High | Index row absent — SPRINTS hygiene in Commit 2/3 |
| MAINT-DEFER-003 | QUEUED | **DEFERRED** | High | Load-bearing comments pass |

`ART-STUDIO-DEFER-001` appears in the deferred index but is feature/API deferral tied to GOV-004 — **outside** strict `MAINT-DEFER-*` population; listed only as OUT-OF-SCOPE FINDING if needed.

### D. STALE SPRINT CONTROL TEXT

| Control text | Recorded implication | Evidence | Provisional disposition | Confidence |
|--------------|---------------------|----------|-------------------------|------------|
| NEXT SESSION OPENS WITH (2026-05-28) | Live opener | Unmarked-superseded; later BR/CI work through Aug 2026 | **SUPERSEDED** as live opener | High |
| NEXT SESSION (2026-05-26) | Already “superseded” | Header says superseded | **SUPERSEDED** (already labeled) | High |
| NEXT SESSION (2026-05-02) | Already “superseded” | Header says superseded; still lists pending M2.5–M6 pickup | **SUPERSEDED** opener; pending list partially still valid | High |
| Pending pickup (2026-05-02 block) | M2.5, M3a, M5, M6, Active Inventory | Aligns with DATA INTEGRITY except M6 supersession | **PARTIALLY_COMPLETE** as pointer (M6 stale) | High |

### E. Cross-references (SPRINTS-state only)

| Topic | SPRINTS claim / implication | Evidence | Provisional disposition for SPRINTS text | Confidence | External pointer |
|-------|----------------------------|----------|------------------------------------------|------------|------------------|
| Sprint 3 BOE “MISSING” | Absolute missing endpoint | `body_export_router.py` + `/api/export/body-outline` + tests | **PARTIALLY_COMPLETE** / rewrite claim — not “MISSING” | High | Not a BR close |
| CAM 8J / BR-006 | (Audit: BR ledger false-open) | PR #97 code present | **EXTERNALLY_GOVERNED** for BR ledger; SPRINTS has no CAM-8J OPEN maintenance row to close | High | `TRACKED BY BR REMEDIATION — see BR-006` — **do not mark BR resolved here** |
| CI-RED-020B | SPRINTS CLOSED | Already CLOSED with witness | **COMPLETED** in SPRINTS | High | BR-007 ledger staleness is BR SoR — out of mutation scope |
| endpoint map / 016-B | SPRINTS cites 016-B materialized; CI-RED-016 OPEN | Map artifacts exist | **PARTIALLY_COMPLETE** for 016 umbrella (map done; consolidation open) | High | `TRACKED BY CI-RED — see CI-RED-016` |
| Remediation next pointer | Not in SPRINTS body; operator drift | `NEXT_REMEDIATION_CANDIDATE.md` vs queue BR-036 | **OUT-OF-SCOPE FINDING — NOT ADJUDICATED** for BR files; may note in recon only | High | Do not edit BR docs |

---

## Summary counts (authorized population only)

Derived after re-witness — **not** forced to audit estimates.

| Disposition | Count | Items |
|-------------|------:|-------|
| COMPLETED | 10 | M1, M2, NDS×2, FRET-1, Data Sync, CL-1/2/5, MAINT-DEFER-002 |
| OPEN | 4 | M2.5, M3a, Active Inventory, M5 |
| PARTIALLY_COMPLETE | 2 | M4; Sprint 3 BOE claim (cross-ref) |
| SUPERSEDED | 3 | M6; NEXT SESSION 2026-05-28 as live opener; (05-02/05-26 already labeled) |
| DEFERRED | 8 | CL-4/6/9/10/11/14; MAINT-DEFER-001; MAINT-DEFER-003 |
| OWNER_DECISION_REQUIRED | 5 | CL-3/7/8/12/13 |
| EXTERNALLY_GOVERNED | 2 | BR-006 relationship; CI-RED-016 consolidation remainder |
| EVIDENCE_INSUFFICIENT | 0 | — |
| **Population rows classified** | **~34** | DATA+CL+MAINT-DEFER+control+key cross-refs |

Genuine unfinished ordinary maintenance still visible after recon (provisional):  
**M2.5, M3a, M4 remainder, M5, Active Inventory Species Audit**, plus owner-gated/queued CLEANUP and intentional MAINT-DEFER items.

---

## Unresolved evidence gaps

1. Full Sprint 3 Option-B acceptance (frontend Export DXF → specific historical path) — body export exists; original `/api/editor/export-dxf` claim not met literally.  
2. Whether douglas_fir `12.17` GPa is intentional vs still “too low” vs FPL ~13.5 — owner/product note may be needed when editing M4.  
3. BR ledger false-opens (BR-006/007/008) — **confirmed as evidence** but **not closed in this sprint** (no BR file edits).  
4. `NEXT_REMEDIATION_CANDIDATE.md` — confirmed stale; **not edited** (BR remediation doc).  

---

## OUT-OF-SCOPE FINDINGS — NOT ADJUDICATED

| Finding | Why out of scope |
|---------|------------------|
| BR ledger still lists BR-006/007 unfinished | BR SoR mutation forbidden |
| CI-RED-015 detail header OPEN vs index CLOSED | CI-RED body; only note if SPRINTS control text contradicts |
| ACTIVE Sprints 2/4/6/8/9 age | Not in authorized ordinary-maintenance population |
| CHANGELOG Priority 2/3 wishlist | Not in population |
| Audit ~25–30 / ~20–25 totals | Orientation only |

---

## Commit plan (unchanged)

| Commit | Content | Status |
|--------|---------|--------|
| **1** | This evidence matrix | **This commit** |
| **2** | High-confidence `SPRINTS.md` stale-state edits | Not started |
| **3** | Remaining aged dispositions | Not started |
| **4** | CBSP21 + validation | Not started |

---

*End of Commit 1 evidence document. No `SPRINTS.md` edits in this commit.*
