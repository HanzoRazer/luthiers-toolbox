# IBG Sprint 1 / Sprint 2 Ruling

**Sprint:** IBG/AGE Precursor Forensic Sprint (read-only)  
**Question:** The IBG git series begins at **Sprint 3** (`33aaf3d3`, 2026-04-17). What were Sprints 1 and 2?

Ruling vocabulary (only): `RECOVERED` · `PARTIALLY_RECOVERED` · `NOT_FOUND` · `INCONCLUSIVE`

Do not manufacture sprint boundaries to obtain `RECOVERED`.

Three numbering systems exist in-repo. They must not be collapsed.

---

## Numbering system A — Shop `SPRINTS.md` (from `77560aec` 2026-04-04)

| Label | Title | Ruling |
| ----- | ----- | ------ |
| Shop Sprint 1 | Vectorizer Reconciliation | **RECOVERED** (this is not IBG) |
| Shop Sprint 2 | Repo Split and Standalone Products | **RECOVERED** (this is not IBG) |
| Shop Sprint 3 | Remediation and Gap Closure | **RECOVERED** (this is not IBG) |
| Shop Sprint 4 | Photo Vectorizer Production Readiness | **RECOVERED** (this is not IBG) |
| Shop Sprint 9 | InstrumentBodyGenerator | **RECOVERED** as the shop label for IBG (`SPRINTS.md` section; IBG file headers; Dev Order) |

April 6 commits `68120ea1` / `727c05e2` (“Sprint 2 audit”, “Sprint 2 Step 1 complete”) belong to **system A**, not IBG.

---

## Numbering system B — IBG Dev Order steps (`docs/planning/instrument_body_generator.md`)

Document date 2026-04-16; first git add `95385be9` 2026-04-19. Header: **Sprint: Sprint 9**.

| Step | Content |
| ---- | ------- |
| 1 | Scaffold `body_contour_solver.py` (A–E) |
| 2 | Test: Cuatro Venezolano Quibor |
| 3 | Test: partial vectorizer DXF |
| 4 | DXF output |
| 5 | `ConstraintExtractor` |
| 6 | `InstrumentBodyGenerator` coupler |

These are **steps**, not “Sprint 1/2”. Mapping commit “Sprint 3” onto Dev Order Step 3 would be manufactured: Step 3 is a *test*, while `33aaf3d3` adds solver/bridge + “production-readiness fixes.”

Required `SESSION_AUDITS.md`: **NOT_FOUND** in git.

---

## Numbering system C — IBG commit subjects (2026-04-17–18)

| Commit | Subject |
| ------ | ------- |
| `ca2b2347` | `feat(ibg): wire layer_consolidator as step zero` (**no sprint number**) |
| `33aaf3d3` | `feat(ibg): Sprint 3 production-readiness fixes` |
| `471bc902` | `feat(ibg): Sprint 4 — move IBG to production` |
| `3ed636a9` | `feat(ibg): Sprint 5 — replace hardcoded sagitta…` |
| `6816cd7f` | `fix(ibg): reject centerline noise…` (unnumbered) |
| `c9ebf8a8` | `feat(ibg): Week 1 API endpoints` |
| `40d5e3f9` | `feat(ibg): Week 2 — run_in_executor…` |

File headers on the same files say **Sprint 9**, not Sprint 3.

---

# Sprint 1

**Sprint 1: PARTIALLY_RECOVERED**

Interpret as: *the IBG-internal predecessor implied by commit “Sprint 3”.*

### Evidence

- No commit subject `Sprint 1` under `feat(ibg)` (`git log --all --grep='Sprint 1'` hits shop/vectorizer docs, not IBG).
- `arc_reconstructor.py` header `Date: 2026-04-15` first appears in git at Sprint 4 (`471bc902`, 1611 lines). Sandbox solver at Sprint 3 already imported it — untracked sibling.
- `layer_consolidator.py` `d6bcd03f` same day 01:59, before IBG evening commits — CAM consolidator, later called IBG step zero.
- Dev Order Step 1 (`body_contour_solver`) matches the *kind* of work later committed as part of “Sprint 3,” not as “Sprint 1.”
- `SESSION_AUDITS.md` never committed, so session-level Sprint 1 cannot be corroborated.

### What can be established

- Shop Sprint 1 is recovered and is **vectorizer reconciliation**, not IBG.
- Some IBG math/gap-bridging source was authored (docstring) before the first IBG commit and landed late (`471bc902`).
- The first IBG *commit* (`ca2b2347`) is an integrator that assumes unpublished siblings — consistent with prior local work, not with a missing published Sprint 1 tag.

### What cannot be established

- That anyone named that local work “Sprint 1.”
- A commit, PR, or audit log for IBG Sprint 1.
- Identity of Sprint 1 with Dev Order Step 1 (tempting, not labeled).

---

# Sprint 2

**Sprint 2: INCONCLUSIVE**

### Evidence

- Shop Sprint 2 is recovered (repo split / publish workflow) and is **not IBG**.
- No `feat(ibg): Sprint 2` commit.
- Dev Order Step 2 is a Cuatro unit test. No `test_cuatro_solver.py` add found in the IBG April window (`git log --all --diff-filter=A -- '**/test_cuatro_solver.py'` not used as a recovered sprint).
- After Sprint 5 the numbering jumps to **Week 1 / Week 2**, another scheme, which further shows labels were session-ad hoc.

### What can be established

- A shop Sprint 2 existed and was documented 2026-04-04–06.
- IBG work occurred 2026-04-15–17 that is not labeled Sprint 2 in git.

### What cannot be established

- Whether an IBG-internal Sprint 2 existed, was skipped, was squashed, or was never a real increment.
- Any boundary between “Sprint 1 local work” and “Sprint 2 local work.”

---

## Hypothesis tests (Dev Order §21)

Do not privilege H1.

| ID | Hypothesis | Result |
| -- | ---------- | ------ |
| **H1** | Sprints 1/2 existed under the IBG name | **Not shown.** IBG-named commits start at Sprint 3; files say Sprint 9. |
| **H2** | Sprints 1/2 existed before the IBG name | **Partial.** `arc_reconstructor.py` dated 2026-04-15 (before “Instrument Body Generator” string on 04-17). Consolidator `d6bcd03f` is named CAM, not IBG. No sprint numbers on those artifacts. |
| **H3** | `ca2b2347` consolidated prior experimental work and numbering reflects that | **Partial.** `ca2b2347` is not a git squash (single new 419-line file + consolidator wiring). It *does* assume prior modules. Sprint numbers 3–5 are on *later* commits, so `ca2b2347` itself does not encode “1+2 were squashed here.” |
| **H4** | Sprints 1/2 were planning/session artifacts never represented by repository commits | **Supported.** Dev Order demanded `SESSION_AUDITS.md` (absent). Docstring dates 04-15/04-16 precede commits. Planning doc itself is committed only 04-19. |
| **H5** | Sprint 3 numbering came from another sprint sequence and there were no IBG Sprints 1/2 | **Possible and unrefuted.** Shop Sprint 3 is a *different* title (Remediation), so IBG “Sprint 3” is probably not shop Sprint 3. It may still be “third IBG session” with 1–2 never written down. Absence of 1/2 commits is compatible with H5. |
| **H6** | Available repository evidence is insufficient | **Yes, for IBG-internal 1/2 identity.** Sufficient for shop Sprint 1/2 and shop Sprint 9. |

---

## RQ-1 answers (independent)

1. Exist under different commit terminology? **Yes, in part:** shop Sprint 1/2; shop Sprint 9; Dev Order Steps 1–6; IBG “Sprint 3–5”; “Week 1–2.”
2. Uncommitted/planned work? **Supported** (H4).
3. Squashed into `ca2b2347`? **No** as a git squash; **partial** as an integrator of unpublished files.
4. Developed under another component name? **Partial:** `arc_reconstructor` / `LayerConsolidator` / `BodyContourSolver` before the IBG coupler commit.
5. Originated outside the repository? **UNKNOWN** (sandbox later claimed; unavailable). Not required to explain the April 15–17 local-file pattern.
6. Cannot be recovered? **IBG-internal Sprint 1/2 labels cannot be recovered as commits.**

`UNKNOWN` remains acceptable for the missing session audits and sandbox archaeology copies.
