# Latent Build Workflow — Discovery, Executive Developer Handoff

**Date:** 2026-07-16 · **Scope:** repo-wide, CNC-physical assets · **Mode:** DISCOVERY, not grading

---

## Read this first — what this document is and is not

The canonical electric-body build workflow **is not yet defined**. This scan therefore does **not**
score the repo against an ideal it does not have. It inventories what the repo actually contains and
reconstructs the workflow the repo already *implies*, with every gap phrased as an **open question**
for the owner to resolve — never as a scored deficit.

This is **one of three inputs** to the later workflow-definition task. The other two are
guitar-building books and CNC-specific sources. The deliverable that matters most here is
**§7, the open-questions list** — that list is the bridge to the next phase.

**Not** a beginner-readiness score. **Not** a consolidation/retirement recommendation
("which is canonical?" is flagged, never resolved here). **Not** a fabricated ideal workflow.

### Annotation key

Every claim below carries an evidence class and a witness strength. Per
`feedback_grep_absence_vs_positive_trace` and `feedback_gates_are_claims_to_verify`, absence is a
**lead, not a fact**, and is labelled as such.

| Tag | Meaning |
|---|---|
| `[PRESENT]` | The asset exists and was read. |
| `[ABSENT]` | Looked for it; found nothing. Still a *lead* — may be wired via a path not seen. |
| `[IMPLIED]` | The repo presupposes it without stating it. **Highest-value findings — this is the tacit knowledge.** |
| `⊕ witnessed` | I read the file/line myself in this session. |
| `⊙ scanned` | Reported by a discovery pass, **not personally re-witnessed**. Treat as a claim. |

---

## Bottom line

The repo is a **working CNC platform whose documented scope ends at the `.nc` file** — and it says so
itself (`docs/PRODUCT_DEFINITION.md:17`, `docs/SAFETY.md:33`). The gap between "G-code exists" and "a
guitar body gets made" is **structural and declared, not accidental**. Three findings carry the weight:

1. **The datum is a point in the air.** X0/Y0 = the lower-left corner of the body outline's DXF
   *bounding box* — not a feature you can touch off, and it varies with whatever DXF is fed in. The
   repo *can* probe a real corner; nothing calls it. **This is the tacit-knowledge core.**
2. **The shipped product is the less complete of two rival workflows.** The live API generator emits
   OP20–63 in one program. A tracked standalone script sharing **zero code** with it emits OP10–OP93
   across 3 phases with fixture pins, purfling, and a carved top. Its outputs live in `exports/`,
   which is **gitignored**.
3. **The missing OP10 is the fingerprint.** The shipped `.nc` starts at OP20 because OP10 —
   *fixture/registration holes* — is the omitted step. The registration system the documented
   workflow depends on is exactly the piece the code leaves out.

And the code openly defers to a workflow that lives in the owner's head, not the repo
(`services/api/app/generators/lespaul_gcode/perimeter.py:38` ⊕):

> `This is the main body outline cut (OP50 in your workflow).`

---

## 1. Asset inventory

Ground truth before analysis. The repo is overwhelmingly software — 2,565 `.py`, 812 `.vue`, 780
`.ts`, 762 `.md`, 252 `.json` tracked. The CNC-physical seam is thin:

| Category | Count | Location | Tag |
|---|---|---|---|
| G-code, tracked | 1 real example + 3 post goldens + 3 baselines | `services/api/app/generators/examples/LesPaul_Body_Complete.nc` (19,086 lines); `services/api/tests/golden/mvp_rect_with_island__{grbl,linuxcnc,mach4}.nc` | `[PRESENT]` ⊕ |
| G-code, **untracked** | ~8 multi-phase programs | `exports/{les_paul_1959,explorer_1958,smart_guitar_v1}/` — gitignored at `.gitignore:436` | `[PRESENT]` ⊕ |
| DXF | 122 tracked | `services/api/app/instrument_geometry/body/dxf/{electric,acoustic,other}/`; `docs/archive/instrument_references/`; `phase4_output/` | `[PRESENT]` ⊕ |
| Body G-code generators (live) | 3 | `generators/lespaul_gcode/`, `generators/stratocaster_body_generator.py`, `cam/flying_v/pocket_generator.py` | `[PRESENT]` ⊕ |
| Full-build scripts (standalone) | 3 (3,483 lines) | `scripts/generate_{les_paul,explorer,smart_guitar}_full_build.py` | `[PRESENT]` ⊕ |
| Tool library | 12 tools + 7 materials, **real values** | `services/api/app/data/tool_library.json` | `[PRESENT]` ⊕ |
| Machine profiles | **4 rival models** | `cam/machines.py` (7 presets), `assets/machine_profiles.json`, `data/machines.json`, `cam/postprocessor_boundary.py` | `[PRESENT]` ⊙ |
| Fixture model | 6 fixtures, real keepout geometry | `cam/cam_golden_artifact_fixtures.py` — behind an **unmounted** router | `[PRESENT]` ⊙ |
| Build-workflow docs | 4, **all archived** | `docs/archive/2026/handoffs/{GIBSON_EXPLORER_1958,LES_PAUL_1959,FLYING_V_1958,SMART_GUITAR_V1}_CNC_HANDOFF.md` | `[PRESENT]` ⊕ |
| Pre-cut checklist | 1 | `docs/SMART_GUITAR_PRE_CUT_CHECKLIST.md` | `[PRESENT]` ⊙ |
| CAM governance docs | ~25 | `docs/architecture/CAM_*.md` — meta-docs about **code structure**, not machining | `[PRESENT]` ⊙ |
| Doc-specified registries | — | `data/machine_profiles/`, `data/tool_library/` | `[ABSENT]` ⊕ (all 6 candidate paths checked) |

**Observation, not criticism:** the governance/architecture surface substantially outnumbers the
cutting surface.

---

## 2. The workflow the repo IMPLIES

Reconstructed from the Les Paul assets — the most complete lane in the repo.

```
OP10  Fixture / registration holes (4 pins, waste material)
OP20  Neck pocket rough        ─┐
OP21  Pickup cavities rough     ├─ T1 10mm
OP22  Electronics cavity rough ─┘
OP25  Cover plate recess (BACK face)
OP30  Neck pocket finish       ─┬─ T2 6mm
OP31  Pickup cavities finish   ─┘
OP40  Wiring channels (T3 3mm)
OP50  Body perimeter contour, 6 tabs, full 1.75" depth
OP60–63  Drilling: pot shafts / bridge posts / tailpiece studs / screw pilots
OP70–71  Purfling channel + inner ledge
OP80–81  Carved top: rough + finish (ball-nose raster)
```

### ASSET-BACKED
OP20, OP21, OP22, OP25, OP30, OP31, OP40, OP50, OP60–63 — emitted by live code
(`generators/lespaul_gcode/generator.py:44-103` ⊕) and present in the tracked `.nc` ⊕.

### ASSUMED, but no asset *in the shipped product*
- **OP10 (fixture/registration holes)** `[IMPLIED]` ⊕ — the shipped generator has no OP10; its `.nc`
  **starts at OP20**. The numbering gap is the fingerprint of the omitted step.
- **OP70/71 (purfling), OP80/81 (carved top)** `[IMPLIED]` ⊕ — `lespaul_config.py:83`
  `carve_depth_in: 0.5`, `:140` `top_carve: bool = True`; Strat defines `belly_contour_depth_mm: 9.5`
  / `arm_contour_depth_mm: 6.4` and plumbs `belly_contour`/`arm_contour` into its spec
  (`stratocaster_body_generator.py:137-138`). **No toolpath reads any of them.** The specs model a
  carved, contoured body; the generators produce a flat slab.
- **The flip** `[IMPLIED]` ⊕ — no `M0`/`M1`/pause exists anywhere in the generators.

### Is the ordering ENCODED?
Only as **hardcoded Python, once, per part**. `generate_full_program()` is a straight-line method and
the OP numbers are **string literals inside comment text** — nothing can query, reorder, or validate
the sequence.

- The general pipeline graph is a **stub**: `cam_core/pipeline_ops/graph.py:10-11` returns
  `"edges": []` / `"graph_not_implemented"` ⊙.
- The executor route `/cam/pipeline/run` **does not exist**; `cam_pipeline_preset_run_router.py:124`
  forwards to it → `POST /presets/{id}/run` always 502s ⊙ `[ABSENT]` *(lead — needs a runtime check)*.
- The spec validator iterates ops **independently**, no predecessor logic
  (`services/pipeline_spec_validator.py:139-243` ⊙).

**The dependency *knowledge* exists, but only as English.** `cam/neck/orchestrator.py:71-79` ⊙
docstrings the real machining rationale — "clears channel before profile carving", "cut after
fretboard surface is finished" — while the code is straight-line boolean flags that let you disable an
upstream op with no check that it invalidates a downstream one.

### The DATUM — the highest-value finding

**A convention exists: X0/Y0 = the lower-left corner of the body outline's DXF bounding box.**
`generators/lespaul_dxf_reader.py:157-163` ⊕:

```python
def _calculate_origin_offset(self):
    """Calculate offset to translate DXF coordinates to work-zero."""
    if self.body_outline:
        self.origin_offset = (
            self.body_outline.bounds['min_x'],
            self.body_outline.bounds['min_y'],
        )
```

Corroborated by the archived doc — `LES_PAUL_1959_CNC_HANDOFF.md:139` ⊕: *"Origin at lower-left of
DXF bounds."* **Z0 = top of stock** `[IMPLIED]` ⊕ (cuts run negative; safe Z `+0.75`; perimeter
bottoms at `-total_depth + tab_height`, i.e. it never cuts into a spoilboard).

Three consequences — each a **question**, not a verdict:

1. **It is a point in the air.** A bbox corner is not a physical feature of a guitar body. It is
   derived from whatever DXF is loaded, so it **silently varies per file**.
2. **A real datum is reachable but uncalled.** `cam/probe_patterns.py:82` ⊕ emits genuine
   `G10 L20 P{offset} X#104 Y#105` corner probing, with routers under `routers/probe/`. **No CAM
   module references it** ⊙; the coordinate governance doc does not know it exists.
3. **G54 is emitted inconsistently.** The body generators emit `G54` ⊕; the GRBL and LinuxCNC
   goldens emit **no work offset at all** ⊕ — part zero is whatever the operator left active.

**Convention drift** ⊙ — `CoordinateSystem` is duplicated as four unrelated classes with divergent
origins (`local_nut_left_face`, `nut_edge`, `workpiece_origin`, `top_face`) and z-zeros
(`top_of_stock` vs `top_of_fretboard`). Several carry the self-label
`coordinate_confidence="documented_from_current_code"` — the code **admits** the convention was
reverse-engineered from behavior. Separately, `instrument_geometry/coordinate_system.py` (a
well-tested ~700-line design frame, nut-origin, **bass = −X**) contradicts the governance doc's
**bass at high X**. Nothing reconciles them.

> **Doc trap — flagged loudly.** `docs/architecture/CAM_COORDINATE_SYSTEM_GOVERNANCE.md` is marked
> `Status: LOCKED` and reads normative, but it is an **audit snapshot** referenced by **zero code**
> ⊙, and live code has since drifted from it in at least three places. The words *datum, WCS, G54,
> spoilboard, locating pin, dowel, registration, fixture* **do not appear in it at all** ⊙. The docs
> that *admit* they are plans are the honest ones.

---

## 3. Hidden assumptions — each as a question

Each: "the repo appears to assume X — is that intentional, and is it stated anywhere?"

- **Units** ⊕ — Les Paul hardcodes `G20` **inches**; Strat hardcodes `G21` **mm**; all
  post-processors are mm. `lespaul_config.py:12` admits *"The repo convention is mm (G21), but this
  legacy generator uses inches."* → *Is the inch lane intentional legacy, and which unit governs a build?*
- **Post-processor bypass** ⊕ — the body generators emit G-code **directly** and never touch the
  GRBL/LinuxCNC/Mach4 post system. Two independent emission paths. → *Is the body lane meant to be posted?*
- **Machine** ⊕ — `MACHINES` names `txrx_router` (48×48×4") and `bcamcnc_2030ca` (48×24×4"); the
  `.nc` header says `Machine: TXRX Labs Router`. → *Is TXRX the target, or an artifact of where this was first cut?*
- **Spindle / tool change** ⊕ — `S18000 M3`, `G4 P2` dwell, `T1 M6` changes; but `machines.py`
  defaults `has_atc=False`, `max_tools=1` ⊙. → *ATC, or is M6 a manual-change prompt the operator is expected to know?*
- **Stock** ⊕/⊙ — 1.75" mahogany, assumed square and large enough. **Squareness appears nowhere in
  the repo** ⊙. `drilling_export.py:237-244` silently defaults stock to `100.0 × 20.0mm` magic
  numbers ⊙. → *Where does blank prep (flatten/thickness/square) happen — before the repo's scope?*
- **Workholding** ⊕ — archived handoffs say "double-sided tape + registration pins"; `perimeter.py`
  cuts full depth leaving 6 tabs × 0.5" × 0.125". → *Is tape+pins+tabs the standing method?*
- **Spoilboard** ⊕ — only `machines.py:82` (docstring: *"work_z_min_mm: Minimum working Z (e.g., -50
  for spoilboard)"*) and `:117` (`work_z_min_mm: float = -25.0`, enforced at `:165`) gesture at it.
  → *Is there a sacrificial board, and does the tool bottom out on it?*
- **Feeds/speeds** ⊕/⊙ — **real, not placeholders**: `tool_library.json` has 12 tools
  (rpm/feed/plunge/DOC) + 7 materials with feed multipliers (mahogany k=0.85, ebony k=0.7). But the
  body generators use their own separate `TOOLS`/`STRAT_TOOLS` and **never consult the library** ⊕.
  → *Which table is authoritative?*

---

## 4. Workflow-asset maturity

### The most complete workflow in the repo is not the shipped one ⊕

| | Live API lane | Standalone script lane |
|---|---|---|
| Path | `app/generators/lespaul_gcode/` | `scripts/generate_les_paul_full_build.py` (1,259 lines) |
| Reachable | `POST /api/cam/guitar/les_paul/body/gcode` (**mounted**, `routers/cam/guitar/__init__.py:68`) | CLI only |
| Ops | OP20–63 | **OP10–OP93** (+ fixture holes, purfling, carved top, **and the neck**) |
| Phases | 1 monolithic program | 3 (back / purfling / carved top) |
| Fixture holes | ✗ | ✓ 4 pins in waste, `-0.375"` peck |
| Flip | ✗ | phase-split |
| Shared code | — | **none** — independent reimplementation (stdlib + `scripts.utils.gcode_verify` only) |

The scripts' outputs live in `exports/` — **gitignored** (`.gitignore:436`) ⊕. The repo's most mature
build artifacts would **vanish on a fresh clone**.

### Complete / unfinished / experimental / superseded

| Asset | State | Evidence |
|---|---|---|
| `LesPaul_Body_Summary.json` | **superseded/stale** | lists 7 ops; its own `.nc` emits 11 (OP25, OP60–62 missing) ⊕ |
| `STRAT_TOOLS["finishing_6mm"]` | **unfinished** | defined but **never called** — Strat has no rough/finish split ⊕ |
| `cam/carving/` (3D rough→semi→finish) | **unmounted, test-only** | no router imports it; only `tests/test_carving_pipeline.py` ⊙ |
| `cam/fhole/` | **unmounted, test-only** | zero importers outside its package ⊙ |
| `cam_assist_router.py` | **dead** | absent from `cam_manifest.py`; `routers/cam/__init__.py` empty ⊙ |
| `cam_golden_artifact_fixtures.py` | **real but orphaned** | 6 fixtures, real clearance-zone geometry; only importer is the dead router; marked permanently non-executable ⊙ |
| `cam_core/feeds_speeds/materials.py` | **placeholder, self-labelled** | `"""Material property placeholders."""` ⊙ |

### Flagged — "which is canonical?" (NOT resolved here)

- API generator **vs.** full-build script — for Les Paul, Explorer, Smart Guitar.
- Tracked `LesPaul_Body_Complete.nc` **vs.** untracked `LesPaul_1959_Phase1_MahoganyBack.nc`.
- **Four** machine models; **three** post-processor systems that disagree (a `mach4` golden exists
  with **no** `mach4` post) ⊙.
- **Four** safe-Z defaults: 50.0 / 25.0 / 10.0 / 5.0 mm ⊙.
- Two contradicting coordinate frames (bass = +X vs −X) ⊙.

---

## 5. Two items I want to surface above the question-mark line

The discovery discipline says phrase gaps as questions. I have done that throughout. But two items
would **consume a body** if the implied workflow were run as literally encoded, and burying them in a
question list would be hiding behind the framing. They are still the owner's call — but they belong
at the front of the workflow-definition conversation, not the back.

1. **Rear-face ops are emitted inline into a single continuous top-face program.** ⊕
   `stratocaster_body_generator.py:171-183` emits pickup cavities and neck pocket (top), then spring
   cavity (`:403` `"SPRING CAVITY (REAR)"`) and control cavity (`:426` `"CONTROL CAVITY (REAR)"`), one
   coordinate system, one file. The only flip marker is an **emitted comment string** —
   `:405 self._emit_comment("NOTE: Flip workpiece for rear operations")` — not state. The Les Paul is
   the same shape: `generator.py:57` `generate_cover_recess` is labelled `# OP25: Cover recess (back)`
   and sits between top-face OP22 and top-face OP30. `body_gcode_router.py:319-331` ⊙ concatenates the
   back-face control cavity and the top-face neck pocket under one preamble on the live
   `operations="all"` path.
2. **OP10 drills 4 pins `-0.375"` deep into 1.75" stock.** ⊕ `generate_les_paul_full_build.py:336-348`
   — holes at 0.5" inset from each bbox corner, **in waste material**, `peck_drill(..., -0.375, ...)`.
   Phase 1 is back-face-up. After the flip those holes face **down**, and at 0.375" they are not
   through 1.75" stock. *How does the part re-register on side 2?* I could not answer this from the
   repo — it may well be resolved by shop practice the assets don't record.

---

## 6. What a first-time user hits — the first stop

Discovery only; the full beginner-readiness grade waits until the workflow exists.

`docs/getting-started/quickstart.md:90-100` ⊙ offers the body workflow as a **seven-node mermaid
diagram**: `DXF Import → Validate → Set Stock → Pocket → Contour → Drilling → Export G-code`. It ends
exactly where the physical build begins.

**The first stop:** *you have an `.nc` file and a blank, and nothing tells you where to put the blank
or how to tell the machine where it is.* The datum is a bounding-box corner you cannot touch off.

This is **declared, not accidental** — `docs/SAFETY.md:33` ⊙ (*"Does not verify workholding or fixture
security"*) and `docs/PRODUCT_DEFINITION.md:17` ⊙ (scope = *"machine-ready G-code"*). The build
knowledge that does exist was captured **incidentally, per-instrument**, as a byproduct of generator
sessions — then **archived**.

---

## 7. The open-questions list — the bridge

The single most valuable output. Every gap, ambiguity, and undefined convention, phrased as a
question for the workflow-definition task to answer.

### Datum & registration
1. Where is X0/Y0 **physically**, and how does the operator put the part there — given a DXF bbox
   corner isn't a feature you can touch off?
2. Should the datum be the **OP10 fixture pins** instead, making pins the primary reference?
3. OP10 drills 4 pins `-0.375"` deep into 1.75" stock; after the flip they face down. **How does the
   part re-register on side 2?**
4. Is Z0 = top of stock **re-zeroed per face** (the handoff says *"Re-zero Z for each face"*) — who
   does that, and when?
5. Should `probe_patterns.py` (real, working, unused) be wired in as the datum-setting step?
6. **Bass = +X or −X?** Which of the two coordinate frames governs?
7. Should `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` still say `LOCKED` when no code references it and
   code has drifted?

### Sequence & flip
8. Is **OP10 part of the canonical workflow** — and if so, why doesn't the shipped generator have it?
9. Does the flip belong **in** the program (phase split, `M0` pause) or in an operator's head?
10. Should back-face and top-face ops **ever** be emitted into one continuous program?
11. Drilling runs **after** the perimeter cut — the part is held only by 6 tabs while being drilled.
    Intentional?
12. Should op order be **data** (the graph the stub promises) or stay hardcoded Python?
13. `OP10` = fixture holes in the **body** namespace but = truss rod channel in the **neck** namespace
    (`neck_headstock_generator.py:112` ⊕). Should the numbering be shared?

### Missing operations
14. Where does **blank prep** (flatten, thickness, square) happen — before the repo's scope?
15. `top_carve`, `belly_contour`, `arm_contour` are accepted flags with depths defined, but nothing
    cuts them. Should the API lane carve, or is carving script-only by design?
16. Is `cam/carving/` (unmounted, tested) the intended home for OP80/81?
17. Where do **roundover/chamfer, sanding, and final thicknessing** live?

### Canonicity & provenance
18. **API generator or full-build script — which is the product?**
19. Should `exports/` stay gitignored, given it holds the most complete build artifacts?
20. Which tool table governs: `tool_library.json`, `TOOLS`, or `STRAT_TOOLS`?
21. **Inches or mm** for the body lane?
22. Should the body generators go through the **post-processor** system?
23. Which **machine** is the target, and does it have an ATC?
24. Should the **fixture registry** (real geometry, dead router) be wired in, or retired?

---

## 8. Leads worth re-witnessing before anyone acts

Per house rule, `⊙ scanned` items are **claims, not facts** — and "no consumer found" is an **upper
bound** on deadness, not proof (cf. `project_ci_red_016c_legacy_export_map_calibration`, where a
scanner blind spot was the ground zero of false "consumer-less" verdicts).

- `/cam/pipeline/run` 502 — confirm at runtime, don't infer from grep.
- `cam/carving/`, `cam/fhole/`, `cam_assist_router.py` "unmounted" — confirm against
  `router_registry/manifests/cam_manifest.py`, the authoritative mount list.
- `cam/rosette/prototypes/`, `cnc_jig_geometry.py`'s role during cutting, and
  `saw_lab/batch_router.py`'s `setup_key="setup_1"` — flagged by the scan, not concluded.
- The four rival `CoordinateSystem` classes and four safe-Z defaults — re-witness before any
  reconciliation PR.

---

## Appendix — mechanics

- **Branch/PR:** none. This document was written on `docs/wp-002-adjudication`, an unrelated stream;
  it is **uncommitted** and should land on its own branch (`feedback_stage_by_explicit_path`:
  one stream = one branch = one PR).
- **Memory:** `project_latent_build_workflow_discovery.md` (indexed in `MEMORY.md`).
- **Doc policy:** `docs/handoffs/` stays active for 60 days, then archives per `CLAUDE.md`.
- **Method:** direct reads plus three parallel discovery passes (CAM module map; datum/machine/
  tooling; build-workflow docs). Absence claims for `data/machine_profiles/` and `data/tool_library/`
  were **independently re-witnessed** across all six candidate paths before being reported.

---

**These are the 24 open questions the repo cannot answer about its own workflow. Answering them —
with the books, CNC sources, and owner knowledge — is the workflow-definition task.**
