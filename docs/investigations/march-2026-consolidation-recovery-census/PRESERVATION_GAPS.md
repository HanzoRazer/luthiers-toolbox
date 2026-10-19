# Preservation gaps

These are items still dependent on a non-durable location.

**Nothing was copied into the repository under this order.** No item meets the imminent-loss bar that
would require stopping for preservation authorisation. Downloads files are at risk only of ordinary
deletion.

**Urgency:**
- `IMMEDIATE`: loss is imminent;
- `HIGH`: a single, non-owned copy;
- `NORMAL`: a single owned copy with value;
- `REFERENCE_ONLY`: low value, or already superseded.

| # | Item | Depends on | Hash recorded | Urgency | Why |
|---|---|---|---|---|---|
| P-1 | **Five headstock modules**: `stores/headstock`, `types/headstock`, `useHeadstock`, `useParametric`, `headstockData` | A claude.ai conversation (`/mnt/user-data/outputs/ps-vue/src/`) | no; contents never seen | **HIGH** | The only copy is in a hosted conversation; the four preserved views cannot compile without them. Recovery is owner-side |
| P-2 | `BridgeBreakAnglePanel.vue` (R-2) | Downloads only: nested inside `Storage\files - 2026-03-17T224205.344.zip` (`files - 2026-03-15T193643.776.zip`) | yes (`BUNDLE_MEMBERS.csv`) | **NORMAL** | The only artefact of a planned feature that is absent from Git |
| P-3 | Three string-tension / stiffness draft variants (same nested ZIP) | Downloads only | yes | REFERENCE_ONLY | Live same-name files exist; these are drafts |
| P-4 | 03-16 vectorizer result sets (9 files: concept SG body + cavities DXF, jumbo archtop, Benedetto rembg/potrace) | Downloads `Storage\` only | yes | NORMAL | Historical extraction outputs, useful as vectorizer regression references. Ownership is the owner's |
| P-5 | Path-pack HTML prototypes (saddle compensation, headstock break angle) + calculator variants | Downloads only (`files - 2026-03-19T235852.556.zip`, `…-03-20T003551.017.zip`) | yes | REFERENCE_ONLY | The live calculators exist; these are design prototypes |
| P-6 | Two `side_bending_calc.py` iterations (03-21) | Downloads only | yes | REFERENCE_ONLY | The live file differs; CALC-001 cites the 123917 iteration |
| P-7 | The external CAM-backend bundle (`files - 2026-03-18T031920.383.zip`) | Downloads `Storage\` | yes (`ee3f5fdb…80aa`) | REFERENCE_ONLY | Every member is in Git; only the prose-pre-edit bytes of two files are unique |
| P-8 | **History 2026-03-30 → 04-05** | Not preserved anywhere located | — | **HIGH** (unrecoverable from Git) | Main starts at a parentless root. Possible sources: claude.ai/Cursor sessions, or `luthiers-toolbox-main (31…33)` snapshots in Downloads (04-02 / 04-08 / 04-09; not walked) |
| P-9 | Pre-rewrite history 03-15 → 03-30 | Tag `v2.4.0-alpha.1` only | — | NORMAL | Reachable today, but only through one tag. Deleting the tag would orphan it |
| P-10 | `docs/BACKLOG.md` committed history (March) | Tag `v2.4.0-alpha.1` only | — | NORMAL | As P-9. The archived copy (`50022d74`) is on `main` |
| P-11 | Unpushed and unmerged branches holding related evidence | `vec-root-001-harness` (pushed), `docs/census-maint-defer-id-fix` (local only), #437 / #438 (open) | — | NORMAL | Outside this census's scope; listed so the dependency is visible |
| P-12 | `luthiers-toolbox-main (28).7z` inside `files - 2026-03-21T123917.995.zip` | Downloads only | zip hash only | REFERENCE_ONLY | A 03-21 repository snapshot; Git already covers that date via the tag |

**Excluded on purpose:** the saved third-party "Kerf Spacing Calculator" web page (68 members) is not
owner material, its licence is unknown, and it carries ad and tracking scripts. It is **never** a
preservation candidate.

**Before anything moves into Git:** P-2 and P-4 are owner-generated and safe to preserve on an explicit
order. Ownership and licence are clear for Claude output the owner commissioned. P-1 must first be
recovered from the conversation.
