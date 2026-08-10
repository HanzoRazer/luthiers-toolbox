# MAINTENANCE-BACKLOG-AUDIT-002 — Repository-Wide Maintenance, Remediation & Stranded-Work Status Audit

**Date:** 2026-08-09
**Substrate:** `origin/main` @ `0179a032` (2026-08-05), confirmed identical to live GitHub `main`
**Posture:** READ-ONLY. No authority was mutated. No `SPRINTS.md` edit, no BR lifecycle change, no queue
reorder, no CI-RED closure, no production code change. Every disposition below is **advisory**.
**Supersedes as evidence layer:** the 2026-08-07 Cursor maintenance scan (never committed; see F-11)
**Downstream:** `SPRINTS-MAINT-RECON-001` remains **dormant** until this audit is adjudicated.

---

## 0. Reviewer quick-check (verify these first)

Because this is an evidence record that drives sequencing decisions, spot-check the highest-value
claims against source before adjudicating. Each row below is falsifiable in one command.

| # | Highest-value claim | Verify against | One-command check |
|---|---|---|---|
| F-01 | Nightly witness red 100/100; unparseable Makefile recipe | `services/api/Makefile:47-49`; run `31291019670` | `sed -n '47,49p' services/api/Makefile \| cat -A` → line 48 `import sys` has no leading TAB |
| F-02 | Energy endpoint 500, red 30/30 | run `31294738659`, job `api-smoke`, step "M.3" | `gh run view 31294738659 --log-failed \| grep "HTTP Error 500"` |
| F-03 | CAM 8J reconstructed + merged | `60528f02` (PR #97) | `git log --oneline -1 60528f02` |
| F-04 | Consumer map materialized (2.15 MB) + calibrated | `acadef99` (#201), `a2d24bed` (#204); `services/api/metrics/endpoint_consumer_map.json` | `git cat-file -s 0179a032:services/api/metrics/endpoint_consumer_map.json` → 2154764 |
| F-05 | **CORRECTED — see finding** | `wood_species.json` species records | `spruce_sitka`/`spruce_engelmann` have **no** `modulus_of_elasticity_gpa` (still null); only `douglas_fir`=12.17 changed |

> **Independent review (2026-08-09):** F-01, F-02, F-03, F-04 were re-verified against source and are
> accurate to the byte/step/SHA. **F-05 was found factually wrong and is corrected in place** (two
> misattributed MOE values); **F-07's "no ledger row" claim was corrected** (a BR-036 row exists). See
> the amendment log (§7).

## 0a. Finding index

| Finding | Evidence type | Primary source | Suggested owner action |
|---|---|---|---|
| F-01 | Live CI + static | `api_health_check.yml`, `services/api/Makefile`, run `31291019670` | Fix notifier **with/before** Makefile tab; give BR-007 a wave position |
| F-02 | Live CI (500) | `adaptive_pocket.yml`, run `31294738659` | Admit new BR + `CI-RED-*`; probe uvicorn traceback |
| F-03 | Merged commit + files | `60528f02` (#97) | Closure witness vs 8J acceptance, then close |
| F-04 | Merged commits + artifact | `acadef99`/#201, `a2d24bed`/#204 | Adjudicate BR-008 close → unblock BR-028 |
| F-05 | Data read (**corrected**) | `wood_species.json` | **Do NOT close M4** — two spruce nulls still unfilled |
| F-06 | Doc vs doc | `NEXT_REMEDIATION_CANDIDATE.md` | Refresh stale next-candidate (doc-only) |
| F-07 | Static (grep) | register / ledger | Give BR-036 a register section + wave (ledger row exists) |
| F-08 | Static set-diff | queue vs ledger | Reconcile unlisted BR-007/034/036/042/044 |
| F-09 | Self-declared | `BACKLOG_ADJUDICATION_LEDGER.md` | Intake write-back discipline (fixes F-08 root) |
| F-10 | Absence probe | `docs/audit/` | Disambiguate "M6"; decide Sprint M6 status |
| F-11 | Absence search | (uncommitted PDF) | This audit landing is the correction |
| F-12 | Checkout state | local production checkout | Do not use checkout as evidence substrate |
| F-13 | Static | `SPRINTS.md:2` | Service the parking-lot header |

---

## 1. Substrate and method

### Why `origin/main` and not the working tree

The local production checkout `C:\Users\thepr\Downloads\luthiers-toolbox` **cannot serve as audit
substrate**:

| Property | Value |
|---|---|
| Branch | `smart-guitar-cavity-geometry-1` (not `main`) |
| Position vs `origin/main` | **59 behind**, 2 ahead |
| HEAD date | 2026-07-21 |
| Missing | the **entire `docs/remediation/` tree** — 204 files / 28,565 insertions |

`docs/remediation/` is precisely the BR-suite evidence this audit adjudicates
(`REPOSITORY_DEFECT_REGISTER.md`, `BACKLOG_ADJUDICATION_LEDGER.md`, `REMEDIATION_EXECUTION_QUEUE.md`,
`NEXT_REMEDIATION_CANDIDATE.md`, `UNFINISHED_SPRINT_REGISTER.md`,
`DEFERRED_AND_NONPRODUCTION_WORK.md`). An audit run against that tree would have reported the entire
remediation program as non-existent.

`origin/main` locally resolves to `0179a032`; `gh api repos/HanzoRazer/luthiers-toolbox/commits/main`
returns the same `0179a032`. The local remote-tracking ref is current with GitHub, so no fetch was
required and none was performed.

### Probe discipline

`REPOSITORY_DEFECT_REGISTER.md` (BR-042 entry) records a Windows-specific hazard: `git show <ref>:<path>`
**silently produces false-absent results under Git Bash on Windows**. All existence probes in this audit
therefore used `git ls-tree` and `git grep` against refs. `git show` was used only to read files already
proven present by `ls-tree`. This audit inherits that discipline rather than re-deriving it.

### Evidence classes used

Following the register's own confidence vocabulary: `CONFIRMED` means a symptom was reproduced or a
live run observed; `STATIC-FACT CONFIRMED` means the code or data says so on inspection. No finding
below is promoted past what its evidence supports.

---

## 2. Findings

Ordered by consequence. Each states the contradiction, the evidence, and an **advisory** disposition.

---

### F-01 · The nightly API health witness has never been green in the observable window — and its remediation item holds no queue position

**CONFIRMED (live CI observation).**

> **Evidence at a glance** — workflow `.github/workflows/api_health_check.yml` (job `api-health`) ·
> reproduction run `31291019670` (@ `0179a032`) · root-cause file `services/api/Makefile:47-49`.

| Fact | Evidence |
|---|---|
| `API Nightly Health Check` on `main` | **failure on 100 of the last 100 runs.** Zero successes in the sampled window |
| Continuous daily red | unbroken `failure` every night 2026-07-11 → 2026-08-09 |
| Its remediation item exists | **BR-007** — "CI-RED-020B API health+smoke nightly witness recovery", `UNFINISHED_SPRINT_WORK`, readiness **`ready`**, blocking decision "verify 020B merge-instability resolved (PR #177)" |
| Its handoffs exist and are complete | `docs/handoffs/CI_RED_020B_dev_order.md`, `CI_RED_020B_addendum.md`, `CI_RED_020B_API_HEALTH_SMOKE_NIGHTLY_WITNESS_RECOVERY_HANDOFF.md`, `PR_177_CI_RED_020B_MERGE_INSTABILITY_HANDOFF.md` |
| **BR-007 appears in no execution wave** | `REMEDIATION_EXECUTION_QUEUE.md` Waves 0–4 enumerate BR-001..006, 008..033, 043, 045. **BR-007 is absent from every wave and from the exclusion list.** |

**The contradiction:** the repository holds a `ready` remediation item, with a dev-ready handoff, for a
witness that has been red for ~100 consecutive days — and the execution queue that is supposed to
sequence remediation does not list it at all. This is not a deprioritized item; it is an unlisted one.

#### Root cause — diagnosed 2026-08-09 (amendment)

**The health check never runs. This is not an API defect.** Two independent failures compound.

**(a) The verification target is unparseable.** The job declares
`defaults.run.working-directory: services/api` (`.github/workflows/api_health_check.yml:14-16`), so its
`make api-verify` step resolves to **`services/api/Makefile`**, not the root `Makefile`. There, lines
47–49:

```make
	@$(PYTHON) - <<'PY'
import sys
ok=True; errs=[]
```

Line 47 is tab-indented; **the heredoc body is not**. Every line of a make recipe must begin with a TAB —
make strips one tab and passes the remainder to the shell. Because `import sys` carries no leading tab,
make stops treating it as recipe text, attempts to parse it as a rule, finds neither `:` nor `=`, and
emits precisely what CI reports:

```
Makefile:48: *** missing separator.  Stop.
```

`git blame` attributes all three lines to **`9cb9804c` (2025-11-09) — the initial commit**. The target has
been unparseable for the file's entire history. The step exits 2 before uvicorn starts, which is why every
run also logs *"No files were found with the provided path: services/api/api_health.json"* — there is no
health artifact because nothing was ever health-checked.

**(b) The failure alarm is disconnected — this is why ~100 nights passed unnoticed.**

| Notify step | Observed failure | Cause |
|---|---|---|
| Slack notify on failure | exit code 3 | `WEBHOOK` resolves **empty** in the step env; `curl` posts to an empty URL |
| Email notify on failure | `Input required and not supplied: from` | `dawidd6/action-send-mail@v3` invoked without the required `from` input; additionally warns `Unexpected input(s) 'content_type'` |

**Evidence:** run `31291019670` (2026-08-09, head `0179a032`), job `api-health`; failing steps recorded by
GitHub as *"Verify geometry imports; Slack notify on failure; Email notify on failure"*.

**Advisory disposition:** highest-value candidate surfaced by this audit. A health witness that is
always red provides no signal, so any regression it would have caught is currently undetected.
**Fix (b) before or with (a):** repairing the Makefile alone restores a witness whose alarm still fires
into a dead wire, which reproduces the same silent-failure condition on the next regression. Both are
small, bounded, and independent of BR-007's broader scope — but BR-007 still needs an explicit wave
position, since it is the item under which this work would be authorized.

---

### F-02 · A second scheduled workflow is also permanently red, unregistered

**CONFIRMED (live CI observation).** `Adaptive Pocket (API)` — **failure on 30 of the last 30 runs**,
unbroken 2026-07-11 → 2026-08-09. Workflow file `.github/workflows/adaptive_pocket.yml` is present on
`main`.

> **Evidence at a glance** — workflow `.github/workflows/adaptive_pocket.yml` (job `api-smoke`) ·
> reproduction run `31294738659` (@ `0179a032`) · failing step "M.3 - Energy endpoint returns totals
> and segments" → `HTTP Error 500`.

No `CI-RED-*` entry in `SPRINTS.md` covers it, and no BR item names it. Per `SPRINTS.md`'s own framing
— *"SPRINTS.md is the parking lot — the live index where open work registers at session end
(`CI-RED-*`…)"* — a permanently-red scheduled workflow is exactly what that index exists to hold.

#### Root cause — diagnosed 2026-08-09 (amendment). A different defect from F-01, and a live production 500.

**`Adaptive Pocket (API)` does not share F-01's Makefile cause.** Its `api-smoke` job fails at a single
step — **"M.3 - Energy endpoint returns totals and segments"** — with:

```
urllib.error.HTTPError: HTTP Error 500: Internal Server Error
```

The smoke script reaches the endpoint and the endpoint returns 500 before the segment-shape assertions
(`code`, `len_mm`, `vol_mm3`, `energy_j`, heat-partition sum) can be evaluated. Unlike F-01, the API
here **does start** — this is a real server error on a live route, reproduced nightly for 30
consecutive scheduled runs.

**Evidence:** run `31294738659` (2026-08-09, head `0179a032`), job `api-smoke`.

**This is an unregistered production defect.** It appears in `REPOSITORY_DEFECT_REGISTER.md` under no
BR ID, and in `SPRINTS.md` under no `CI-RED-*` entry. Under the register's own confidence vocabulary it
would qualify as **`CONFIRMED`** — the symptom is *reproduced by a scheduled run*, not inferred from a
code read. It is the only item this audit surfaced that meets the register's admission bar for a new
defect entry.

**Advisory disposition:** admit to the defect register as a new BR item with the run above as its
reproduction basis, and register a `CI-RED-*` entry in `SPRINTS.md`. This audit did **not** diagnose
*why* the energy endpoint 500s — that requires the uvicorn traceback from the run artifacts and is the
obvious next probe.

---

### F-03 · BR-006 (CAM 8J) was reconstructed and merged two months ago; it is still queued as pending with "data-loss urgency"

**CONFIRMED (merged commit on `main` + production modules present).**

BR-006 is carried across three control documents as outstanding:

| Document | What it says about BR-006 |
|---|---|
| `REMEDIATION_EXECUTION_QUEUE.md` Wave 1 | **Rank 3** — "CAM 8J pocketing reconstruction (source `.py` lost)", `UNFINISHED_SPRINT_WORK`, "**data-loss urgency**; medium" |
| `UNFINISHED_SPRINT_REGISTER.md` | implemented scope = "spec + orphaned `.pyc`"; missing scope = "**reconstruct `.py` lane (source lost)**"; "READY/UNBLOCKED" |
| `BACKLOG_ADJUDICATION_LEDGER.md:58` | `UNFINISHED_SPRINT_WORK`, severity **high**, "reconstruct lane (**data-loss risk**)" |

Ground truth on `origin/main`:

| Fact | Evidence |
|---|---|
| The lane was reconstructed and merged | **`60528f02` (2026-06-09), PR #97** — *"feat(cam): Pocketing CamIntentV1 endpoint migration (**Dev Order 8J, reconstructed**)"* |
| Production source exists | `services/api/app/cam/pocketing/intent_adapter.py`, `intent_schema.py`, `feasibility.py`, `__init__.py` |
| Router exists | `services/api/app/cam/routers/pocketing/intent_router.py` |
| Tests exist | `services/api/tests/cam/test_pocketing_intent_migration.py`, `test_pocketing_design_schema.py` |
| Subsequently maintained | `70b13d89` (fence violations in CAM intent routers, PR #101), `eaf94add` (route introspection, PR #169) |

**The contradiction:** the register's stated missing scope — "reconstruct the `.py` lane, source lost" —
was performed by a commit whose message names the very Dev Order (8J) the register cites, **two months
before this audit**. The item has since been maintained twice. It is ranked #3 in the active Wave 1
queue under a "data-loss urgency" that no longer applies.

**Advisory disposition:** strongest "completed but never administratively closed" finding in the code
lane. Requires a closure witness (confirm the reconstructed lane satisfies the original 8J Dev Order's
acceptance criteria) before closing — reconstruction happened, but this audit did not verify
*completeness* against the 8J spec.

---

### F-04 · BR-008's deliverable is materialized and calibrated on `main`, yet it is still recorded as a blocker gating BR-028

**CONFIRMED (generated artifact + generator + tests on `main`).**

| Document | What it says about BR-008 |
|---|---|
| `BACKLOG_ADJUDICATION_LEDGER.md:60` | `UNFINISHED_SPRINT_WORK`, Tier B, readiness **`blocked(016)`**, "consumer-map prerequisite for 016 consolidation" |
| `UNFINISHED_SPRINT_REGISTER.md` | implemented = "map **drafted**"; missing = "consolidation prerequisite" |
| `REMEDIATION_EXECUTION_QUEUE.md` Wave 2 | Rank 3, "**gates BR-028**" — and BR-028 Rank 5 is marked "**after** BR-008" |

Ground truth on `origin/main`:

| Fact | Evidence |
|---|---|
| Map materialized | **`acadef99` (2026-07-06), PR #201** — *"docs(ci): **materialize** CI-RED-016 endpoint consumer map"* |
| Map calibrated + corrected | **`a2d24bed` (2026-07-07), PR #204** — *"CI-RED-016-C: calibrate legacy `/exports` consumer map (map correction + disposition)"* |
| Generated artifact present | `services/api/metrics/endpoint_consumer_map.json` — **2,154,764 bytes** |
| Generator present | `services/api/scripts/build_endpoint_consumer_map.py` |
| Generator is tested | `services/api/tests/test_endpoint_consumer_map_builder.py` |
| Audit doc present | `docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md` (6,941 b) |
| Disposition doc present | `docs/audit/CI_RED_016C_LEGACY_EXPORT_CLUSTER_DISPOSITION.md` |
| CBSP21 patch record | `.cbsp21/patches/ci-red-016b-endpoint-consumer-map.json` |

**The contradiction is compound, and the second half is the expensive one:**

1. "Map **drafted**" understates a 2.15 MB generated artifact produced by a tested generator, then
   independently *calibrated* by a follow-up PR.
2. BR-008's readiness is `blocked(016)` — but the deliverable landed **under** the CI-RED-016 program
   itself (PRs #201/#204 are 016 and 016-C work). The prerequisite and its blocker are the same program.
3. **BR-028 (endpoint-sprawl consolidation, Wave 2 Rank 5) is recorded as blocked on BR-008.** If
   BR-008's deliverable is in fact satisfied, BR-028 is being held behind a gate that has already
   opened.

**Advisory disposition:** adjudicate whether PRs #201/#204 satisfy BR-008's acceptance. If yes, BR-008
closes and **BR-028 becomes unblocked** — a queue-position change with real sequencing consequence.
This audit establishes the artifacts exist and are tested; it did **not** verify they meet the original
`CI_RED_016B_ENDPOINT_CONSUMER_MAP_HANDOFF.md` acceptance criteria.

---

### F-05 · Sprint M4 is only partially satisfied — one of three MOE gaps is filled; the two spruce nulls remain

**CONFIRMED (data read on `main`).**

> **⚠️ Review correction (2026-08-09).** As originally written, this finding claimed *"M4's premise is
> factually false; all three gaps are filled"* and gave `spruce_sitka = 11.34`, `spruce_engelmann =
> 9.5`. **Both values were misattributed and are wrong.** Direct inspection of the species records shows
> `spruce_sitka` and `spruce_engelmann` carry **no `modulus_of_elasticity_gpa` field at all** — the nulls
> are **not** filled. The `11.34` belongs to **`walnut_black`**; the `9.5` belongs to **`spruce_european`**
> (a different spruce). Only `douglas_fir` actually changed. The finding, table, and disposition below are
> corrected; the corrected verdict is the near-opposite of the original — **M4's premise still holds for
> the two spruces, so M4 must not be closed on this basis.**

`SPRINTS.md` → DATA INTEGRITY → Sprint M4 (**Status: QUEUED**, Priority MEDIUM) states:

| Species | SPRINTS.md "Current Value" | SPRINTS.md Issue | SPRINTS.md Expected |
|---|---|---|---|
| `spruce_sitka` | `null` | Missing | ~10.3–11.9 GPa |
| `spruce_engelmann` | `null` | Missing | ~8.9 GPa |
| `douglas_fir` | 10.0 GPa | Low | ~13.5 GPa old-growth |

Actual, in `services/api/app/data_registry/system/materials/wood_species.json` on `origin/main`
(`species.<key>.physical.modulus_of_elasticity_gpa`):

| Species | Actual `modulus_of_elasticity_gpa` | Verdict vs the sprint's own target |
|---|---|---|
| `spruce_sitka` | **ABSENT (still null)** | gap **NOT** filled — no MOE field on the record |
| `spruce_engelmann` | **ABSENT (still null)** | gap **NOT** filled — no MOE field on the record |
| `douglas_fir` | **12.17** | no longer 10.0; moved toward, not to, the stated ~13.5 |

For reference, the values the original finding misread: `walnut_black` = 11.34, `spruce_european` = 9.5.
Neither is a target species of M4.

**The (corrected) contradiction:** M4's `douglas_fir` "Current Value" of 10.0 is stale — it is now
12.17, so that one row describes data that has changed. But the two `null`s M4 was written to eliminate
are **still null**. M4's core premise is therefore **substantially accurate**, not false.

Note also the **path has moved**: M4 and the surrounding DATA INTEGRITY prose refer to
`wood_species.json` as though at its historical location; on `main` it lives at
`services/api/app/data_registry/system/materials/wood_species.json`.

**Advisory disposition (corrected):** **Do NOT narrow-and-close M4.** Its primary work — populate MOE for
`spruce_sitka` and `spruce_engelmann` from an authoritative source (per the wood-data sourcing policy) —
is **still owed**. The only defensible update is to refresh `douglas_fir`'s stale "Current Value"
(10.0 → 12.17) in `SPRINTS.md` and re-state the target as a residual judgment call (plantation vs
old-growth). This audit did **not** verify provenance/source attribution for the `douglas_fir` value.

---

### F-06 · `NEXT_REMEDIATION_CANDIDATE.md` names a next Dev Order that is finished

**CONFIRMED (document vs document, both on `main`).**

`docs/remediation/NEXT_REMEDIATION_CANDIDATE.md` is headed **"Status: SCOPE CORRECTION REQUIRED
(2026-07-21)"** and states:

> **BR-002A** (store-path archaeology / contract proof — **the actual next Dev Order**) →
> **BR-002B** (additive repair, authorized only after 002A is green).

and:

> Ledger items **BR-001 / BR-002 / BR-004** stay `CONFIRMED_DEFECT`; their readiness is now
> **`SCOPE CORRECTION REQUIRED`** pending BR-002A.

Against `REMEDIATION_EXECUTION_QUEUE.md` and `BACKLOG_ADJUDICATION_LEDGER.md` on the same commit:

- BR-002A **executed** (PRs #227–#230); BR-002B **executed and merged** (PR #231, 2026-07-23).
- BR-001 / BR-002 / BR-004 are **`COMPLETE` / FIXED (BR-002B)**, not `CONFIRMED_DEFECT`.
- The queue states: *"The next bounded candidate is now **BR-036**."*

**The contradiction:** the document whose entire purpose is to name the next candidate names a Dev Order
completed 17 days before this audit, and asserts a lifecycle state (`CONFIRMED_DEFECT`) that three other
documents contradict. This is the single highest-traffic staleness in the remediation set — it is the
file a reader consults *first* to answer "what's next."

**Advisory disposition:** this is the prior scan's `NEXT_REMEDIATION_CANDIDATE` lead, and it
**reproduces**. Correcting it is a documentation act, not a lifecycle change.

---

### F-07 · BR-036 is designated "the next bounded candidate" but has neither a ledger row nor a defect-register entry

**STATIC-FACT CONFIRMED.**

`REMEDIATION_EXECUTION_QUEUE.md` closes with: *"**The next bounded candidate is now BR-036** — the deeper
`batch_tree` shape defect surfaced during BR-002B (`isinstance(a, dict)` guards exclude the `RunArtifact`
objects `as_items` actually returns from the real store → empty trees)."*

But:

- `REPOSITORY_DEFECT_REGISTER.md` has per-defect sections for BR-001, 002, 003, 004, then 037–045.
  **There is no BR-036 section.** BR-036 appears only as prose inside the BR-002B resolution notes
  (`:56`).
- `BACKLOG_ADJUDICATION_LEDGER.md` **does carry a BR-036 table row** (`:88`, `CONFIRMED_DEFECT`, severity
  **high**, readiness `ready`), **plus** a blockquote note (`:90`, "BR-036 severity raised med → high").
  So in the ledger BR-036 is present, not missing.
- BR-036 holds **no wave position** in the execution queue (it appears only as prose — "the next bounded
  candidate is now BR-036" and "surfaced as BR-036 (out of scope)" — never as a ranked wave item).

> **⚠️ Review correction (2026-08-09).** As originally written this finding asserted BR-036 had *"no
> table row — only a blockquote note"* in the ledger. That is wrong: a full BR-036 row exists at
> `BACKLOG_ADJUDICATION_LEDGER.md:88`. Corrected above. The finding's substance survives on the other two
> legs (no dedicated **register section**, no **wave position**), but the "no ledger row" leg is retracted.

**The (corrected) contradiction:** the designated next unit of work has a ledger row but **no dedicated
register section and no wave position**. Its severity was formally raised to `high` in a note attached to
a different item's review, yet it is not sequenced anywhere.

**Advisory disposition:** BR-036 needs a register entry and ledger row before it can be authorized, or
the "next bounded candidate" designation should point somewhere adjudicated. (A bounded BR-036 Dev
Order draft exists outside the repository and remains unauthorized — consistent with this finding, and
itself an instance of F-11's pattern.)

---

### F-08 · The execution queue is not a complete projection of the adjudication ledger

**STATIC-FACT CONFIRMED (mechanical set difference).**

Ledger and register carry BR-001 … BR-045. The execution queue's Waves 0–4 plus its explicit exclusion
list account for: BR-001–006, 008–033, 043, 045.

**Unaccounted for — present in ledger/register, absent from every wave and from the exclusion list:**

| Item | State per register/ledger | Why the omission matters |
|---|---|---|
| **BR-007** | `UNFINISHED_SPRINT_WORK`, **`ready`** | subject is red 100/100 nights — see F-01 |
| **BR-034** | `MAINTAINABILITY_DEBT`, **`ready`** | stale xfail marker that now XPASSes; trivially closable |
| **BR-036** | severity raised to **high** | designated next candidate — see F-07 |
| **BR-042** | **`CONFIRMED`**, re-witnessed 2026-07-28 | blocked on an owner ruling that conflicts with a standing RETIRE decision; no wave means the ruling has no forcing function |
| **BR-044** | `CONFIRMED_DEFECT` / `STATIC-FACT CONFIRMED`, high | "QUEUED — NOT AUTHORIZED" with nowhere to be queued *to* |

BR-037/038 are correctly absent (resolved / refuted). BR-039/040/041 are unadjudicated scan candidates
and their absence is defensible under the register's own intake rule.

**The contradiction:** three documents are described as a living, burn-down system that each Dev Order
updates in lockstep. In practice the queue lags the register: items entering via the dated intake
sections (scan intake, Tier D intake, materials intake) reach the register without reaching the queue.

---

### F-09 · Two governance records disagree, and the ledger says so about itself

**STATIC-FACT CONFIRMED (self-declared, still open).**

`BACKLOG_ADJUDICATION_LEDGER.md` contains:

> **Ledger/register divergence, noted not fixed.** BR-037…BR-042 appear in [the register] … but were
> admitted through dated register sections that did not write back here. BR-043 does write back.
> Reconciling BR-037…042 is pre-existing and outside this Dev Order.

This is an honest, correctly-scoped deferral — and it is **still true on `main`**. BR-037–042 have
register entries and no ledger rows. The divergence has now outlived the Dev Order that declared it
out of scope; nothing has since claimed it.

**Advisory disposition:** this is the mechanism behind F-08. Fixing F-09 (write-back discipline for
intake sections) prevents F-08 from recurring; fixing F-08 item-by-item does not.

---

### F-10 · "M6" names two unrelated obligations, and the Sprint M6 deliverable does not exist

**CONFIRMED (absence probed by `ls-tree`).**

| "M6" | What it is | State |
|---|---|---|
| **Sprint M6 — Unfinished Work Audit** (`SPRINTS.md` DATA INTEGRITY, line ~2275) | read-only audit of scaffolded/suspended/orphaned/superseded code. Deliverable: **`docs/audit/unfinished_work_audit_2026-05.md`** | **QUEUED.** Deliverable **ABSENT** from `docs/audit/` on `main` |
| **C2 M6 Readiness Audit** | governance-convergence milestone | **PRESENT** — `docs/governance/coordination/C2_M6_READINESS_AUDIT.md`, landed by **PR #211** (2026-07-10), *"docs(governance): add M6 readiness audit"* |

**The contradiction:** a merged PR titled *"add M6 readiness audit"* exists, and Sprint M6 is an audit
sprint, but they are **different obligations in different programs**. A reader reconciling SPRINTS.md
against merged history can very easily read #211 as satisfying Sprint M6. It does not: Sprint M6's
scan categories (sandboxed experiments, stale in-flight sprints, superseded implementations) and its
named deliverable path are untouched.

**Advisory disposition:** disambiguate the identifier. Note also that Sprint M6's scope substantially
**overlaps this audit** — F-03, F-04, F-05 are exactly "work that was superseded or completed but never
formally closed." AUDIT-002 partially discharges Sprint M6 without being authorized to close it.

---

### F-11 · The prior maintenance audit was never committed — the maintenance discipline's own anti-pattern, applied to its own output

**CONFIRMED (exhaustive absence search).**

The 2026-08-07 Maintenance Backlog Status Audit — the intended evidence basis for this work — exists
**only** as a browser print-to-PDF:

`C:\Users\thepr\Downloads\Maintenance backlog status audit _ Cursor.pdf` (126,239 b, 2026-08-07 01:16)

Searched and **absent**: `docs/audit/` on `main`; both repos' tracked files; both repos' all-branch
history (`--diff-filter=A` across all refs); 14 stashes; `C:\tmp` (all worktrees, full depth);
`Downloads` full depth. A companion file `SPRINTS_MAINTENANCE_STOCKPILE_AUDIT_2026-08-0*` was searched
for by the same method and **does not exist anywhere reachable**.

`docs/SPRINTS_MAINTENANCE.md` **Rule 6** states:

> Do **not** rely on orphan docs, PR comments, or chat-only notes as the system of record.

and lists as **anti-pattern #7**: *"Untracked deferral — holding work out of a merge without a
DEFERRED MAINTENANCE entry."*

**The contradiction:** a maintenance status audit that survives only as a chat-session PDF print is
precisely the failure mode the maintenance discipline forbids — committed against the discipline's own
deliverable. Its findings were unrecoverable, forcing this full regeneration.

**Advisory disposition:** the correction is AUDIT-002 landing as a committed file. Recommend also that
the recurring-audit process in `SPRINTS_MAINTENANCE.md` §"Deliverables" be read as **binding** on
audits produced in assistant sessions, not only on those produced at a terminal.

---

### F-12 · The production checkout has drifted far enough to produce false audit results

**CONFIRMED (see §1).** 59 commits behind, on an unrelated feature branch, missing `docs/remediation/`
entirely, 5 dirty files including two untracked handoffs
(`CAM_BUILD_WORKFLOW_DISCOVERY_DEV_HANDOFF.md`, `HANDOFF-2026-07-21-UNREACHABLE-ZERO-INVARIANT.md`)
and an untracked `services/api/scripts/worktree_reaper.py`.

Additionally: `SPRINTS.md`, `SPRINTS_MAINTENANCE.md`, `ROUTER_MAP.md` and
`MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` all carry mtimes of 2026-08-09 00:49–00:53 while git
reports them **clean**. Those are checkout artifacts, not edits — a filesystem timestamp in this
checkout is not evidence of recent work.

**Advisory disposition:** this checkout must not be used as an evidence substrate. The two untracked
handoffs are candidate rescues (the same pattern as merged PRs #234/#235/#236) but were **not**
assessed by this audit.

---

### F-13 · `SPRINTS.md` header staleness

`SPRINTS.md` line 2: **`Last updated: 2026-07-05`**. Merged to `main` since that date: PRs #201, #204,
#210–#250 — including the entire BR-002A/002B remediation execution, BR-037's fix, BR-043, BR-045,
CONV-001, and the three rescue PRs. Per `SPRINTS_MAINTENANCE.md` Rule 1 ("update at session end") and
Rule 4 (`last_verified` semantics), the parking lot has not been serviced in ~5 weeks of active merge
traffic.

---

## 3. Negative controls — leads that did NOT reproduce

Recording these matters as much as the positives; each was probed with the same method and **remains
accurately open**. The control set is what makes the positive findings above trustworthy.

| Item | Claim under test | Result |
|---|---|---|
| **BR-013** | RMOS workflow `approve` route not wired | **STILL OPEN.** `services/api/tests/test_rmos_workflow_e2e.py:63` — `@pytest.mark.skip(reason="Approve endpoint not yet exposed via API - state_machine.approve() exists but no route")`. Register is accurate |
| **BR-015** | `runs_v2` `strict=True` pending post-migration | **STILL OPEN.** `app/rmos/runs_v2/store.py:169` — `strict=False,  # TODO: Enable strict=True after migration`. Register is accurate |
| **BR-021** | CI gates suppressed | **STILL OPEN.** `client_lint_build.yml:42` — `continue-on-error: true  # TODO: Fix 400+ pre-existing type errors then remove this`; `vue_decomposition_gate.yml:31` — `continue-on-error: true`. Register is accurate (line number differs from the ledger's cited `:79`) |
| **Sprint M2.5** | 3 deferred silent-fallback sites | **STILL OPEN, all three.** `glue_joint_calc.py:80` — `MIN_SURFACE_MM2.get(glue_type, 400.0)`; `pickup_position_calc.py:441` — `PICKUP_WIDTHS_MM.get(pickup_type, 25.0)`; `top_deflection_calc.py` density default. SPRINTS.md is accurate |
| **Sprint M5** | CIRAD API absent | **STILL OPEN.** Source CSVs present (`docs/reference/cirad/`, `docs/reference/cirad-density/`) but **no** `app/materials/registry/cirad.py`, `cirad_density.py`, or `cirad_router.py`. SPRINTS.md is accurate |
| **BR-017 / PR #224** | IBG readiness-report content stranded off `main` | **STILL STRANDED.** No `readiness_report` / `repository_readiness` path on `main`. Register is accurate |
| **CI-RED-018** | router-count baseline stale | **CORRECTLY CLOSED.** SPRINTS.md marks CLOSED 2026-06-15; the register independently re-verified `ci/router_count_gate.py` reports 253/1228 = baseline exactly. Two records agree |
| **BR-038** | two stores write `data/art_jobs.json` | **CORRECTLY REFUTED.** Register's refutation holds; no write site exists. Acting on the original claim would have regressed working code |

---

## 4. Prior-scan lead reconciliation

The 2026-08-07 Cursor scan is treated as a **lead sheet, not authority**. Its notable findings, as
enumerated by the owner, were independently re-derived from `origin/main`:

| Prior lead | Verdict | Where |
|---|---|---|
| Stale `NEXT_REMEDIATION_CANDIDATE` | **REPRODUCED** | F-06 |
| BR-006 / CAM 8J | **REPRODUCED, and stronger than stated** — not merely stale, the work is merged and twice-maintained | F-03 |
| BR-008 / CI-RED-016B | **REPRODUCED, and stronger than stated** — deliverable materialized *and* calibrated; falsely gates BR-028 | F-04 |
| BR-007 / CI-RED-020B | **REPRODUCED, and materially escalated** — the witness is red 100/100 runs and BR-007 holds no queue position | F-01 |
| Sprint 3 BOE | **NOT REPRODUCED as stated** — see below |
| M2.5 – M5 | **SPLIT:** M2.5 and M5 accurately open (negative controls); **M4 only partially satisfied** — `douglas_fir` refreshed, but both spruce MOE nulls remain (corrected; see F-05) | F-05, §3 |
| M6 | **REPRODUCED, plus a new finding** — deliverable absent *and* the identifier collides with C2 M6 | F-10 |
| Documentation contradictions | **REPRODUCED and extended** | F-06 – F-09 |

**Sprint 3 BOE — could not be adjudicated from repository state alone.** The Sprint 3 REOPENED block
records *"BOE backend endpoint does not exist — documented but never implemented"* with resolution
"implement, remove claim, or identify alternate (decision pending)". On `main` there is substantial
body-outline capability — `app/cam/translators/dxf/body_outline_translator.py` with tests,
`body_outlines.json`, `blueprint/save_router.py` accepting `body_outline_mm`, `binding_router.py`
consuming `body_outline` — but **no endpoint matching the specific BOE backend contract** the Sprint 3
audit named. Whether the "identify alternate" branch of that decision was taken and never recorded, or
the endpoint genuinely remains absent, requires the original
`docs/audit/sprints_md_verification_2026-04-25.md` acceptance text. **Flagged as unresolved; not
claimed either way.**

---

## 5. Coverage and limits

Stated explicitly so this audit is not read as more complete than it is.

**Covered:** `origin/main` @ `0179a032` — the full `docs/remediation/` control set;
`SPRINTS.md` (all sections, structural pass + targeted deep reads of DATA INTEGRITY, CI-RED, NEXT
SESSION, Sprint 3); `docs/SPRINTS_MAINTENANCE.md`; `docs/audit/` inventory (31 files) with targeted
reads; `docs/governance/` inventory (~190 files, inventory-level only); live GitHub state — 1 open PR,
40 most-recent merged PRs, CI run history including 100-run and 30-run streak sampling on the two
failing workflows; targeted `git grep` re-witness of 14 specific BR/sprint claims.

**Not covered — and therefore not asserted:**

1. **No test suites were executed.** CI state is read from GitHub Actions history; test-existence is
   read statically. Nothing here rests on a local run.
2. ~~**The root cause of F-01 / F-02 was not diagnosed.**~~ **LIFTED 2026-08-09 (amendment).** Both were
   diagnosed from CI logs and confirmed against `origin/main`; see the root-cause subsections under F-01
   and F-02. They proved to be **three** distinct defects, not two: a Makefile recipe that has never
   parsed, a notification path that cannot deliver, and an unrelated live 500 on the energy endpoint.
   **A residual limit remains:** *why* the energy endpoint returns 500 is still undiagnosed — that needs
   the uvicorn traceback from the run artifacts.
3. **`docs/governance/` was inventoried, not read.** ~190 files including the C2 arbitration corpus.
   Cross-record contradictions inside that corpus are out of scope here — with one exception already
   surfaced by the register (BR-042 vs `SYSTEM_CONFLATION_AUDIT_2026-06-21.md:123`, which rules that
   pair "RETIRE" on a basis the register could not reproduce). **That conflict is unresolved and
   remains an owner call.**
4. **Closure witnesses were not performed for F-03 and F-04.** Both establish that deliverables exist;
   neither verifies those deliverables satisfy the originating Dev Order's acceptance criteria. Closing
   either requires that verification.
5. **Branch/stranded-work inventory was partial.** Merged-PR history and BR-017/#224 were checked;
   `salvage/*` and `backup/*` branch contents (BR-031) were not enumerated.
6. **The two untracked handoffs in the production checkout were not assessed** (F-12).
7. **M4's one changed MOE value was not source-verified.** Only `douglas_fir` (12.17) actually changed;
   whether it carries the per-field source attribution M1's discipline requires was not checked. (The two
   spruce records have no MOE value to verify — see corrected F-05.)
8. **Sprint M6's own scan was not performed.** This audit overlaps it but does not discharge it (F-10).
9. **The prior Cursor PDF was not read.** Leads were taken from the owner's enumeration. The full lead
   sheet may contain findings not reconciled in §4.

---

## 6. Recommended sequencing (advisory only — no authority is claimed)

1. **Adjudicate F-01** — BR-007 / the permanently-red nightly witness. Highest consequence: a blind
   regression detector, with a ready handoff and no queue position. Now diagnosed and **small**: a tab
   on `services/api/Makefile:48-49+` and a repaired notification path. Fix the notifier **with or
   before** the Makefile — otherwise the next regression fails silently exactly as this one did.
2. **Admit F-02 to the defect register** — the energy-endpoint 500 is the only newly-surfaced item that
   meets the register's `CONFIRMED` bar (reproduced by 30 consecutive scheduled runs), and it is
   currently tracked nowhere.
3. **Adjudicate F-03 and F-04 as closure candidates.** Both need a witness pass, not new work. F-04
   additionally unblocks BR-028.
4. **Correct F-06** — `NEXT_REMEDIATION_CANDIDATE.md`. Pure documentation; highest read-traffic error.
5. **Resolve F-09 before F-08.** Write-back discipline for intake sections is the mechanism; the
   individual missing queue rows are the symptom.
6. **Rule on F-07** — BR-036 needs a register entry and ledger row, or the "next candidate"
   designation should move.
7. **Disambiguate F-10** and decide whether Sprint M6 is superseded by this audit or still owed.
8. **F-05** — do **not** close M4; its two spruce MOE nulls are still unfilled (corrected). The only
   safe update is refreshing `douglas_fir`'s stale `SPRINTS.md` value (10.0 → 12.17).

`SPRINTS-MAINT-RECON-001` becomes executable **after** this audit is adjudicated, not before — it
assumes an evidence base, and this document is that base.

---

## 7. Provenance

| Field | Value |
|---|---|
| Audit substrate | `origin/main` @ `0179a032`, verified against live GitHub `main` |
| Live CI observation window | 2026-07-11 → 2026-08-09 (100 runs sampled on the nightly witness) |
| Probe method | `git ls-tree` / `git grep` on refs; `git show` only on proven-present paths |
| CI log evidence (amendment) | runs `31291019670` (api-health) and `31294738659` (api-smoke), both @ `0179a032` |
| Authorities mutated | **none** |
| Production code changed | **none** |
| Supersedes | 2026-08-07 Cursor scan (uncommitted; see F-11) |

### Amendment log

| Date | Change |
|---|---|
| 2026-08-09 | Initial audit (`b22e7d5f`). |
| 2026-08-09 | **Root-cause amendment.** F-01 and F-02 diagnosed from CI logs and confirmed against `origin/main`; §5 limit 2 lifted (one residual noted); §6 resequenced. F-01 resolved into two defects — an unparseable make recipe dating to the initial commit, and a non-delivering notification path. F-02 resolved into a separate live production 500, unregistered anywhere. Still read-only: no Makefile, workflow, register, or `SPRINTS.md` change. |
| 2026-08-09 | **Independent review + factual corrections.** F-01–F-04 re-verified against source (byte size, run IDs, Makefile TAB, commit SHAs) — all accurate. **F-05 corrected:** `spruce_sitka`/`spruce_engelmann` MOE are **absent (still null)**, not `11.34`/`9.5` — those values belong to `walnut_black` and `spruce_european`; finding verdict inverted (M4 **not** substantively satisfied; do not close). **F-07 corrected:** a BR-036 ledger row exists (`:88`); the "no ledger row" leg retracted (register-section + wave legs stand). Added §0 reviewer quick-check, §0a finding index, and per-finding "Evidence at a glance" headers for F-01/F-02. Still read-only w.r.t. production/authorities; the only files touched are this audit doc and its manifest. |
