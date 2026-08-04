# Cohort governance — nothing drops to the sandbox floor

**Purpose:** Every lecture / webinar / shop-workflow / physics cohort that enters the knowledge layer must be **highly annotated**, **lane-filed**, and **machine-searchable**. This document is the intake + retention contract.

**Audience:** Developers and agents adding transcript packs before calculator / lab UI work.

**Related:**
- Developer orientation: [`KNOWLEDGE_PACK_DEVELOPER_ORIENTATION.md`](./KNOWLEDGE_PACK_DEVELOPER_ORIENTATION.md)
- Machine catalog: [`cohort_catalog.json`](./cohort_catalog.json)
- Human search index: [`POINT_SEARCH_INDEX.md`](./POINT_SEARCH_INDEX.md)
- Physics lane: [`PHYSICS_KNOWLEDGE_INDEX.md`](./PHYSICS_KNOWLEDGE_INDEX.md)
- Shop lane: [`SHOP_BUILDING_KNOWLEDGE_INDEX.md`](./SHOP_BUILDING_KNOWLEDGE_INDEX.md)
- Coverage gate: `scripts/knowledge_packs/check_cohort_coverage.py`
- Catalog rebuild: `scripts/knowledge_packs/build_cohort_catalog.py`

---

## 0. The floor problem (what we are preventing)

Without governance, cohorts tend to:

1. Land as a transcript dump with weak annotation
2. Sit in a folder nobody indexes
3. Get half-wired into CBSP21 / PR
4. Lose searchable point IDs when titles drift
5. Mix physics meters with shop dialect into one fake calculator story
6. Leave critical gaps (mobility δ, on-screen targets) unspoken

**Definition of “on the floor”:** a cohort that is not findable from orientation → lane index → pack → point ID → crosswalk / gap, or that fails the coverage gate.

---

## 1. Intake checklist (mandatory — in order)

Do **not** skip steps. Do **not** commit a pack that fails the coverage gate.

| Step | Action | Evidence |
|------|--------|----------|
| 1 | **Choose primary lane** by toolbox deliverable (physics meters/models/lab SOP vs shop dialect/process/intake). Dual-file only when both deliverables are real. | Lane index row |
| 2 | **Create pack folder** under `docs/calculators/acoustics/<pack_id>/` | Directory exists |
| 3 | **Ship five required files** (see §2). `PROCESS_WORKFLOW.md` is **optional in the general template** and **conditionally required** when the pack is a full build / multi-stage process. | Completeness = complete |
| 4 | **Annotate densely** — every durable claim gets a stable `PREFIX##` point ID + short title in the annotated notes | Point count > 0 |
| 5 | **Crosswalk every point** (or explicit NO-CALC / gap) in `CROSSWALK_TOOLBOX.md` | Crosswalk present |
| 6 | **Record gaps** in `GAPS_NOT_RECORDED.md` (never invent missing numbers) | Gaps file present |
| 7 | **Register in lane index(es)** | PHYSICS and/or SHOP index |
| 8 | **Update orientation §0** if pack is developer-facing | Orientation row |
| 9 | **Gore physics only:** update `GORE_LECTURE_SERIES_SUMMARY.md` theme table | Gore summary (if applicable) |
| 10 | **Rebuild catalog + search index** | `python scripts/knowledge_packs/build_cohort_catalog.py` |
| 11 | **Run coverage gate** | `python scripts/knowledge_packs/check_cohort_coverage.py` → PASS |
| 12 | **CBSP21:** add every new/changed path to `.cbsp21/patches/gore-lecture-series-packs-1-5.json` | 100% coverage |
| 13 | **Commit + push + update PR** | Git + PR body |

---

## 2. Required pack anatomy (annotation contract)

| File | Role | Annotation bar |
|------|------|----------------|
| `README.md` | Scope, speaker, primary lane, dual-file note, point prefix, standing NO-CALC | Must state **lane** + **point_prefix** |
| `SOURCE_TRANSCRIPT.md` | Cleaned ASR / transcript with provenance | Must include source URL + capture date + ASR caveat |
| `ANNOTATED_*_NOTES.md` | Dense point list (`ID — title` then body) | Prefer `## ID — Title` headings; every claim that could affect a calculator gets an ID |
| `CROSSWALK_TOOLBOX.md` | Point → toolbox surface + **NO-CALC** | Explicit reject rules for unsafe productization |
| `GAPS_NOT_RECORDED.md` | Missing numbers / stills / unit profiles | Gap IDs (`G-*`) when they block meters |
| `PROCESS_WORKFLOW.md` | Ordered stage spine for shop / multi-stage builds | **Optional** in general; **mandatory** for full-build / multi-stage process packs |

**Annotation density target:** enough points that a developer can search the catalog by keyword and land on a specific claim — not a 3-bullet “summary” of a 2-hour talk.

**Point ID rules:**
- Format: `PREFIX` + zero-padded digits (e.g. `GL13`, `BK07`, `P12`, `G-GL01`)
- Prefix is pack-owned; collisions across packs are OK **because search is disambiguated by `pack_id`**
- Do not renumber published IDs; add new IDs or gap IDs instead
- Gap IDs use `G-` + pack/theme + digits

---

## 3. Searchability contract

### 3.1 Machine catalog — `cohort_catalog.json`

Rebuilt by:

```bash
python scripts/knowledge_packs/build_cohort_catalog.py
```

Contains:
- Every pack under `docs/calculators/acoustics/*/` that has a README
- Completeness flags for the five required files
- Lane filing (physics / shop / both / unfiled)
- Every extracted point ID + title + path + line
- Aggregate `unfiled_packs` and `incomplete_packs` lists

**Rule:** `summary.unfiled_packs` and `summary.incomplete_packs` must be empty before merge.

### 3.2 Human search index — `POINT_SEARCH_INDEX.md`

Same rebuild writes a markdown table of all points sorted by ID. Use for PR review and grep-friendly browsing.

### 3.3 Lane indexes

Every pack must appear in at least one of:
- `PHYSICS_KNOWLEDGE_INDEX.md`
- `SHOP_BUILDING_KNOWLEDGE_INDEX.md`

Unfiled packs are treated as **on the floor** — coverage gate fails.

### 3.4 Developer orientation

Orientation §0 must remain the single entry map. New high-value packs get a row; do not rely on folder discovery alone.

---

## 4. Durable musts vs current enforcement

**Durable knowledge-governance musts** (keep even if tooling changes):

1. Every cohort is **lane-filed** (physics and/or shop).  
2. Every cohort is **annotated** with searchable point IDs.  
3. Every durable claim is **crosswalked** or explicitly NO-CALC.  
4. Missing numbers are **gapped** (`G-*`), never invented.  
5. Cohorts are **indexed** so they do not drop to the sandbox floor.

**Current repo enforcement mechanisms** (implementation of the musts — may evolve):

```bash
python scripts/knowledge_packs/build_cohort_catalog.py   # → cohort_catalog.json + POINT_SEARCH_INDEX.md
python scripts/knowledge_packs/check_cohort_coverage.py  # fails on unfiled / incomplete / zero points / CBSP21 omissions
```

Coverage gate fails if any of:
1. Catalog rebuild fails  
2. Any pack is **unfiled**  
3. Any pack is **incomplete** (missing one of the five required files)  
4. Any pack has **zero annotated points**  
5. CBSP21 patch file does not list every pack file path for registered packs  

Pass criteria printed as `COHORT COVERAGE: PASS`.

---

## 5. Lane filing rule (reminder)

Tag by **toolbox deliverable**, not shared vocabulary:

| Lane | Deliverable |
|------|-------------|
| Physics | Meters, models, lab SOPs, unit profiles, mobility / deflection / modes |
| Shop | Dialect cards, stage gates, intake UX, anti-patterns, process spines |

Dual-file when both are real (e.g. Jacob I-beam physics + applied X; Garrett Lee deflection lab + thinning process).

**Never** merge school dialects into one calculator because words overlap (“light stiff top”).

---

## 6. Standing NO-CALC / gap discipline (non-negotiable)

These prevent false productization while packs stay searchable:

- **G-R01** (alias **G-M09**) — mobility δ unit profile unlocked before any mobility badge; canonical record: [`CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`](./CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md)
- **No invented on-screen numbers** — e.g. Garrett Lee deflection targets → **G-GL01** until still/OCR
- **No species→tone defaults** from shop folklore packs
- **No global thickness defaults** from one builder’s map
- Gaps stay in `GAPS_NOT_RECORDED.md` and in the catalog as `G-*` points when annotated

Searchability includes gaps: a missing number must be findable as a gap ID, not silently omitted.

---

## 7. Repository workflow compliance (CBSP21) — not conceptual governance

This section is **repo-local PR/process retention**, not a universal property of the knowledge model.

Patch: `.cbsp21/patches/gore-lecture-series-packs-1-5.json`

Every new pack file path must appear in both:
- `files_expected_to_change`
- `files[]` with path + notes

Coverage check enforces pack file paths ⊆ CBSP21 file list for packs already represented in the patch. When adding a brand-new pack, add **all** of its files in the same change as the pack itself.

---

## 8. Agent / human operating loop (copy-paste)

```text
1. New transcript arrives
2. Choose primary lane (+ dual if needed)
3. Create pack_id/ with 5 files (+ PROCESS_WORKFLOW if multi-stage)
4. Annotate with PREFIX## points; crosswalk; gaps
5. Update PHYSICS and/or SHOP index
6. Update orientation §0 (and Gore summary if Gore physics)
7. python scripts/knowledge_packs/build_cohort_catalog.py
8. python scripts/knowledge_packs/check_cohort_coverage.py   # must PASS
9. Update CBSP21 patch lists
10. Commit, push, update PR
```

If step 8 fails: **stop**. Fix filing / completeness / CBSP21 before any calculator work.

---

## 9. Definition of done for a cohort

A cohort is retained (not on the floor) when:

- [ ] Five required files present and non-empty
- [ ] Annotated points extracted into catalog (count ≥ 1)
- [ ] Filed in physics and/or shop index
- [ ] Crosswalk + NO-CALC written
- [ ] Gaps recorded (even if “none known” is explicit)
- [ ] Listed in orientation when developer-facing
- [ ] Present in `cohort_catalog.json` with `completeness == complete` and `lanes != []`
- [ ] CBSP21 lists every pack path
- [ ] `check_cohort_coverage.py` → PASS

---

*Governance for knowledge-layer cohorts — annotation + search + coverage gate. Does not authorize calculator shipping.*
