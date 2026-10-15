# Recovery recommendations

Each line is a **separate bounded order**. Unrelated recovered features must not be combined into one
implementation PR. Nothing below is authorised by this census.

## 🔴 Validate as a potential safety defect (report first; do not wait for the census)

| Order | Scope | Why |
|---|---|---|
| **HEADSTOCK-TRANSITION-GCODE-SAFETY-001** | Validate `/api/headstock/transition/gcode`. Declare its Z datum. Measure the 21 below-Z0 rapids against the stock model. **Containment is done** (#441, `703694c1`: 409 before generation, inventory `FAIL_CLOSED`); the generator fix is not. | At the census base: live, registered, `LIVE_UNGOVERNED` in the inventory, no gate, no `@safety_critical`, no tests. The default request emits `G00 X… Z<0` diagonal rapids at every station. Same family as the neck rapids #398 fixed |

## Preserve (owner action first)

| Order | Scope |
|---|---|
| HEADSTOCK-MODULE-RECOVERY (owner-side) | Ask the 2026-03-17 claude.ai conversation for the full `ps-vue-src/src/` listing and the five modules (P-1). Then check them against the views' imported symbols and place them beside the views in `archive/experimental/2026-03/headstock-suite-refined/`. Never edit the views |
| MARCH-EXTERNAL-PRESERVE-001 (optional) | On an explicit order, commit P-2 (`BridgeBreakAnglePanel.vue`) and P-4 (vectorizer result sets) under `archive/experimental/2026-03/` with this census's hashes |
| REWRITE-GAP-03-30-04-05 (investigation) | Walk the Downloads `luthiers-toolbox-main (31…33)` snapshots for content from the unpreserved window. Read-only |

## Compare against the current canonical feature

| Order | Scope |
|---|---|
| R-2-BREAK-ANGLE-PANEL-PARITY | Compare `BridgeBreakAnglePanel.vue` with the live break-angle UI (`StringTensionPanel` manual mode, `useBreakAngle.ts`) before any restore |
| NECK-CAMSPEC-UI-ADJUDICATION | `CamSpecPanel.vue`: two identical unimported copies; `useCamSpec` is not router-reachable. Keep one or retire both, per the feature-parity policy |
| NECK-PROFILE-EXPORT-ADJUDICATION | `routers/neck/neck_profile_export.py` is present but unregistered: register, archive or retire |
| RADIUS-DISH-UI-WIRING | The backend `/api/acoustics/radius-dish/*` has no client caller; the live client components differ from the bundle's |
| CALCULATOR-UI-COVERAGE | `CONSTRUCTION-005` glue joint and `GEOMETRY-009` back brace: present and tested, but **nothing imports them**. Decide: wire or archive |

## Archive with provenance (no code change)

- **#437:** correct the "history not preserved" sentence. Only 03-30 → 04-05 is lost; tag
  `v2.4.0-alpha.1` holds the rest.
- **`docs/SPRINT_BOARD.md:126`:** "HEADSTOCK-001: dxf_export.py (needs locating)" is stale; annotate it in
  a docs PR.
- **`SPRINTS.md:390` vs `:429`:** the `curve_export_router` contradiction; annotate it.

## Superseded / no action

Archived orchestrator and `machines.py` (closed by owner ruling); unwired router drafts (project,
blueprint save, materials); the three string-tension drafts; side-bending iterations; path-pack HTML
prototypes.

## Requires owner decision

| Decision | Blocks |
|---|---|
| Clearance authority: 25 / 5 / 50 / 10 mm (`NECK-CLEARANCE-AUTHORITY-001`) | Any neck clearance change |
| Tool-change pause `M0` / `M1` on the BCAM 2030A (`NECK-TOOLCHANGE-PAUSE-001`) | PostProcessor configuration |
| Controller dialect contract: nested comments, `T M6`, `G43 H`, `#3000` macros (`GCODE-COMMENT-DIALECT-COMPATIBILITY-001`) | Any syntax change |
| Whether the headstock suite is a feature to finish or a reference to keep | Headstock adjudication |
| DXF version for the 7 PARTIAL Sprint 3 files still emitting R2010 | Sprint 3 closure |

## Is a dedicated consolidation-recovery program justified?

**Yes, but bounded, and not as one campaign.** The census found:

- one safety candidate, now contained (#441) but not fixed;
- one recovered feature with no Git copy (R-2);
- six stranded implementations;
- fifteen partial migrations;
- one lost module set.

That is enough to justify the separate orders above. It is **not** a case for a general restore. 51
components are live byte-identical, 25 live in modified form (inferred from path or name), 13 are
unresolved because the evidence does not pick a successor, and most "partial" items are calculators
whose backends work and whose UI coverage is a product choice.

**Recommended shape:** run the safety order first. Then the owner-side headstock recovery. Then the
adjudications one PR each, smallest first.
