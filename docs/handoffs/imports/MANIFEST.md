# Multi-Repo Audit Manifest

**Audit date:** 2026-05-24 (refresh)  
**Coordinator repo:** `luthiers-toolbox`  
**Purpose:** Stable index for cross-repository governance audits. Agents and humans should treat this file as the authoritative path map for audit scope.

---

## Repositories

| Repo | Path | Branch | HEAD (short) | Upstream | Ahead | Behind | Verification |
|------|------|--------|--------------|----------|-------|--------|--------------|
| **luthiers-toolbox** | `C:\Users\thepr\Downloads\luthiers-toolbox` | `main` | `52259793` | `origin/main` | **2** | 0 | **verified** 2026-05-24 |
| **tap_tone_pi** | `C:\Users\thepr\Downloads\tap_tone_pi` | `main` | `c910fcc` | `origin/main` | **27** | 0 | **verified** 2026-05-24 |
| **CAM-Assist-Blueprint** | `C:\Users\thepr\Downloads\CAM-Assist-Blueprint` | `main` | `07e6c04` | `origin/main` | 0 | 0 | **verified** 2026-05-24 |
| **vectorizer-sandbox** | `C:\Users\thepr\Downloads\vectorizer-sandbox` | `master` | `6390c26` | `origin/master` | 0 | 0 | **verified** 2026-05-24 |

### Junction paths (read-only audit access from luthiers-toolbox)

```text
docs/audit-sources/tap_tone_pi/
docs/audit-sources/CAM-Assist-Blueprint/
docs/audit-sources/vectorizer-sandbox/
```

---

## Authoritative handoffs (in scope)

| Document | Location | Role |
|----------|----------|------|
| Multi-repo convergence baseline | `docs/MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` | Primary audit output |
| Authority crosswalk | `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` | Vocabulary + schema mapping |
| luthiers sprint handoff | `docs/SPRINT_ARCHITECTURE_HANDOFF_2026-05-24.md` | Runtime spine, MRP-5, 8C–8E |
| tap_tone sprint handoff | `docs/audit-sources/tap_tone_pi/docs/SPRINT_ARCHITECTURE_HANDOFF.md` | DO-008, Gov audit, DO-78/81 |
| CAM sprint handoff | `docs/audit-sources/CAM-Assist-Blueprint/docs/SPRINT_ARCHITECTURE_HANDOFF_2026-05-24.md` | CAM-A0–A12 |
| Constitutional Stabilization DO 77–82 | `docs/handoffs/imports/constitutional_stabilization_do_77_82/` | **verbatim import** (tap_tone constitutional sprint) |

### Constitutional Stabilization bundle (DO 77–82)

Imported copies (ASCII-safe path; source also at repo root with em-dash folder name):

```text
docs/handoffs/imports/constitutional_stabilization_do_77_82/
├── SPRINT_ARCHITECTURE_HANDOFF.md
├── CONSTITUTIONAL_CONTINUATION_NOTICE.md
├── ADR-0010-advisory-authority-constitutional-boundary.md
├── ADR-0011-measurement-authority-constitutional-definition.md
├── ADR-0012-epistemic-status-taxonomy.md
├── AGE_CONTRACT.md
├── ADVISORY_PRESENTATION_BOUNDARY.md
├── ADVISORY_PRESENTATION_AUDIT.md
└── EPISTEMIC_STATUS_SCHEMA_IMPLICATIONS_REVIEW.md
```

**Cross-repo note (from DO 77 handoff):** Dev Order 77 created `docs/handoffs/TAP_TONE_PI_GOVERNANCE_CONSOLIDATION_AUDIT.md` in **luthiers-toolbox** — structural (tap_tone) vs lexical (luthiers) governance complementarity.

---

## Exclusions (do not audit by default)

| Path | Reason |
|------|--------|
| `C:\Users\thepr\Downloads\*` (parent) | CAM-Assist git root appears to be Downloads; ignore sibling untracked files |
| Large eval outputs / binary zips | Not governance-relevant |
| `vectorizer-sandbox` cognition experiments | R&D; reference only via import gate docs |

---

## Known gaps / PENDING verification

| Item | Status |
|------|--------|
| `CAM-Assist-Blueprint/schemas/review_decision_record.schema.json` | **Resolved** — on branch `cam-a12-review-decision-record` @ `6f8947f`; **not merged to `main`** |
| `docs/research/` Wave 1A/1B spine | **Restored** 2026-05-24 from `origin/research/wave-1a-semantic-memory` (14 files) |
| tap_tone 27 unpushed commits | **PENDING / external verification** — push to origin required for collaboration |
| luthiers 2 unpushed commits + large untracked working tree | **PENDING** — includes this audit bundle and CAM 7U–7W handoffs |
| CAM → luthiers 8E runtime integration | **PENDING** — no verified wire-up on disk |
| IBG `BLOCKED_PROVENANCE` ratification | **Documented** — `docs/governance/IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` |

---

## Deliverables from this audit wave

| Deliverable | Path | Status |
|-------------|------|--------|
| Convergence report (updated) | `docs/MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` | Updated 2026-05-24 |
| Authority crosswalk | `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` | Created 2026-05-24 |
| This manifest | `docs/handoffs/imports/MANIFEST.md` | Created 2026-05-24 |
| Audit junctions | `docs/audit-sources/` | Created 2026-05-24 |

---

## Suggested audit command (for agents)

```text
Workspace: luthiers-toolbox
Read: docs/handoffs/imports/MANIFEST.md
Analyze: docs/MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md
         docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md
         docs/handoffs/imports/
         docs/audit-sources/*/
Mark unverified claims: PENDING / external verification
```
