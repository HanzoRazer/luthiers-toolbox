# Erratum: "CL-RED" is not a recovery object

**Recorded 2026-10-14 by owner ruling.** Do not use "CL-RED" as a recovery-object name.

| Statement | Evidence |
|---|---|
| **"CL-RED" was a typo for "CI-RED".** | It appeared twice in `docs/handoffs/CI_RED_019_003_LEDGER_RECONCILIATION_HANDOFF.md` and in the manifest intent of `78c62d78` (2026-07-04). #190 (`b0b2a8ad`, merged as `70c07fee`) corrected both: *"Fix two 'CL-RED' -> 'CI-RED' typos"*. A pickaxe search (`git log --all -S "CL-RED"`) finds no other occurrence in history. |
| **CI-RED is unrelated to the March recovery.** | `SPRINTS.md:967-987` holds CI-RED-001…021, all CI-check incidents dated May–July 2026 (sg-spec clone auth, api-verify imports, debt gates, routing truth, enforcement gaps). None names a March bundle, the vectorizer, headstock, neck or CAM output. |
| **`SPRINTS.md` did not exist during March 15–21.** | It is absent from tag `v2.4.0-alpha.1` (2026-03-30). Its earliest appearance is the parentless root `8d91c4c7` (2026-04-05). |
| **The March planning authorities were `BACKLOG.md` and `SPRINT_BOARD.md`.** | Archived `BACKLOG.md` (blob `50022d74`, shipped inside `files - 2026-03-18T031920.383.zip`); `docs/SPRINT_BOARD.md` (blob `a3b3b575`, at the tag and on `main`). See `MARCH_PLANNING_INDEX.md`. |

## The R-12 / R-15 search (negative result, part of the evidence)

No numbered **R-12** or **R-15** item exists in any of these:

- `SPRINTS.md` history: `git log --all -G "\bR-?15\b" -- SPRINTS.md` returns nothing;
- the March planning documents, whose remediation tasks run **R-1…R-8** only;
- the Consolidation Lab, whose orders and rulings run **R0…R8**.

Two other R-series exist and are unrelated to March:

- DEP-SEC-001 residual matrix **R-01…R-11** (August 2026; `SPRINTS.md:1074` cites R-11);
- Inv-037 **R4a** (`SPRINTS.md:1529`).

The located "R12" and "R15" references are **DXF format versions**: R12 = AC1009 (free tier); R15 =
alias of R2000 / AC1015 (`util/dxf_compat.py:15,27,55`). They are traced as a chain in
[`R12_R15_CHAIN.md`](R12_R15_CHAIN.md).
