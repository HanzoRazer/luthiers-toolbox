# Blackwoods reconciliation — TONEWOOD-BLACKWOODS-RECONCILIATION-003

Documentation consolidation only. This record does not revalidate a measurement and does not create a scientific, purchasing, regulatory, engineering, or manufacturing authority.

No measurement in either document was independently revalidated by this reconciliation.

## Source commit

Branch base, and the commit this work was cut from: `bb90047eb70cff94b53b6cf2dc8a4fe1ed46d67c` (merge of PR #487, “docs(policy): FPL-true template example + provenance test (C-13 follow-up)”). `origin/main` had not moved past that commit when the branch was cut. The merge base of this branch and `origin/main` was that commit.

Content lineage of both documents, from `git log --follow`:

| Event | Commit | Date | Subject |
|---|---|---|---|
| Both files introduced | `5304594435158ecdc0469bfbda38b9b893761333` | 2026-08-15 | docs(tonewood): recover + consolidate the tonewood reference library (#266) |
| Last edit before this order | `661f398d44d11c9e77b08e471c7276d4a1356a36` | 2026-11-14 | docs(tonewood): verify and correct the tonewood reference library (tranche 1) |

No earlier path turned up under `--follow`. Tranche 2 (FPL values) did not edit either file.

## Which document is the shared reference

Search of `docs/tonewood` for acacia / blackwood filenames found one Acacia-family document:

`docs/tonewood/tonewood_comparison_acacia_family_blackwoods_koa.md`

`docs/tonewood/README.md` lists that file as the Acacia + Albizia family comparison. `tonewood_comparison_mahogany_koa_family.md` names Koa beside mahogany, monkeypod, and guanacaste. It is not an Acacia-family survey. No second plausible Acacia-family canonical document was found, so no owner ruling was required before editing.

Focused comparison, kept and rewritten in role only:

`docs/tonewood/tonewood_comparison_blackwoods_african_vs_malaysian.md`

The title was kept. It names the trade names being compared.

## Where this file sits

`docs/investigations/` had no `tonewood-verification-*` directory. Tonewood verification 001 and 002 are CBSP21 patch ids. The living log is `docs/tonewood/VERIFICATION_LOG.md`. This file is the first directory in the `tonewood-verification-*` series the order named. It does not open a second investigation title, and it does not replace the log.

`SPRINTS.md` was not edited. Tonewood verification 001, 002, and the C-13 follow-up are not indexed there. `docs/SPRINTS_MAINTENANCE.md` applies to sprints registered in that file. In `VERIFICATION_LOG.md`, O-05 is resolved as duplication only (see the last section).

## Hashes

SHA-256 of the file bytes.

original_sha256_blackwoods: 3059c59a319073918a48d7948e3d18d2c9ecb13895f7aa464bb9fc1515147f58

original_sha256_acacia: e8998f6876a86d4ce2f4b5f1b2d2ff0a5f3ac511b4953f38635f4c8e54bdb7dd

final_sha256_blackwoods: 79aae5d8b3f32fd6ff6a356298fee7091a014510c3479eecd1b8cbe54d774ad5

final_sha256_acacia: 941dfb61c1ab279576d05a392df1f966183fed3baa83603e75d46c46896ef242

## Heading overlap matrix

Same heading text in the two documents before this order. The tables under those headings were not the same table.

| Heading in both | What each one held | What this order did |
|---|---|---|
| At a Glance | Blackwoods: African vs Malaysian. Acacia: Koa, Tasmanian, Australian, Mangium | Blackwoods table kept, numbers unchanged. Acacia table unchanged |
| Physical Properties | Malaysian column matched the Tasmanian column. African column existed only in the blackwoods document | Both tables kept. No cell rewritten |
| Derived Acoustic Properties | Same split. Blackwoods impedance ~4.78 / ~2.75. Acacia family table uses 2.75 for Tasmanian without a tilde | Both tables kept |
| Thermal Properties | Malaysian column matched Tasmanian. African thermal row was only in the blackwoods document | Both tables kept |
| CNC Machining | Same split. Blackwoods also has RPM, SFM, and width-of-cut rows the family table does not | Both tables kept |
| Lutherie Profile | Pair versus four Acacia species | Both tables kept |
| Data Gaps to Address | Pair gaps versus family gaps. The Acacia document has this heading twice | Blackwoods gap table kept. A note records that the African “sustainability status” cell is stale beside the CITES sentence already in the lutherie table. The row was not deleted |
| References | Both cite the same historical `wood_species.json` path, the Wood Database, Rory McGuinness, and `c = √(E/ρ)`, `Z = ρc`. The Acacia document also cites viability, Mugavu, and Bob Taylor | Blackwoods list kept as written. No citation retargeted |

Verbatim passage in both, kept in both: the C-07 identity caution beginning “No source in this repo establishes that Malaysian Blackwood is *Acacia melanoxylon*.” The comparison cannot be read without it. The family document is where the caution sits next to the nomenclature table.

Overlap that was a ranking, not a shared definition: the six-row table under The “Malaysian Blackwood” Question (density 1,270 / 640, impedance ~4.78 / ~2.75, and the qualitative damping, overtone, and fundamental rows). Those figures already stood in the blackwoods tables. The family copy was removed and replaced with a link. See Relocated material.

Headings only in the blackwoods document (comparison material, kept): the glassy-versus-warm section, acoustic mechanism, modal-research notes, working hypothesis, analysis, application implications, neck effect.

Headings only in the Acacia document (shared reference, kept): Nomenclature Clarification, Koa vs Blackwood, Mangium, the family summary, Part II Albizia, the combined spectrum. A Focused comparisons section was added. Those headings are prohibited from returning in the blackwoods document.

## Blackwoods section dispositions

Every original block has one disposition. `MOVE_TO_SHARED_REFERENCE` is unused: nothing that belonged in the family survey existed only in the blackwoods document without also being a comparison ranking, and comparison rankings were not imported. `REPLACE_WITH_LINK` is unused on these rows. The family document’s ranking table was replaced with a link; that edit is under Relocated material. `REQUIRES_SEPARATE_VERIFICATION` is unused: this order does not open a new measurement task.

| Original section | Disposition |
|---|---|
| Source and generated lines | PRESERVE_HISTORICAL_ONLY |
| Estimated Janka banner | KEEP_WITH_CAVEAT |
| Identity caution | KEEP_WITH_CAVEAT |
| Intro paragraph | KEEP_WITH_CAVEAT |
| At a Glance | KEEP_COMPARISON |
| Physical Properties | KEEP_COMPARISON |
| Derived Acoustic Properties | KEEP_COMPARISON |
| What Creates the "Glassy" vs "Warm" Tone Difference? | KEEP_COMPARISON |
| The Builder's Observation | KEEP_COMPARISON |
| The Physics Behind It | KEEP_COMPARISON |
| Acoustic Mechanism Comparison | KEEP_COMPARISON |
| Think of the Back/Sides as a Filter | KEEP_COMPARISON |
| Thermal Properties | KEEP_COMPARISON |
| CNC Machining | KEEP_COMPARISON |
| Lutherie Profile | KEEP_COMPARISON |
| Why This Matters for Modal Research | KEEP_COMPARISON |
| Resonance Peaks | KEEP_COMPARISON |
| Q Factor (Quality Factor) | KEEP_COMPARISON |
| Decay Time | KEEP_COMPARISON |
| Impedance Mismatch at Boundaries | KEEP_COMPARISON |
| Working Hypothesis | KEEP_COMPARISON |
| Analysis | KEEP_COMPARISON |
| Not Actually Similar Woods | KEEP_WITH_CAVEAT |
| Application Implications | KEEP_COMPARISON |
| The Neck Effect | KEEP_COMPARISON |
| Data Gaps to Address | KEEP_WITH_CAVEAT |
| References | PRESERVE_HISTORICAL_ONLY |

Notes on the rows that are not a straight keep:

- Source and generated lines stay, including Generated 2026-06-22. They were not refreshed to look like a new data pull.
- The Janka banner stays because 1,960 ᵉ is still in the glance and physical tables. The ᵉ marks were not added or removed.
- The identity caution stays in full. The new role banner and the identity table point at the family document; they do not replace the caution.
- The intro sentence that called the two trade names botanically unrelated species was corrected on review (owner, 2026-11-16): they are different genera in the same family, Fabaceae, and the trade names do not establish species equivalence. It is still immediately limited: the Malaysian column is the Tasmanian *A. melanoxylon* record, not a confirmed identification of wood sold under that trade name.
- Not Actually Similar Woods stays. Its Malaysian genus cell, like the At a Glance family cell and the Physical Properties scientific-name and family cells, now carries the caveat in the table itself: reference record, trade-name identity not established (owner review, 2026-11-16).
- Data Gaps to Address stays, including the African “sustainability status” cell. The known-gaps section says that cell is stale beside the CITES Appendix II annotation #15 sentence already in the lutherie table (C-06). Species+ was not queried again.
- References stay, including the path `docs/audit-sources/tap_tone_pi/tap_tone_pi/materials/wood_species.json`. That path does not resolve in this checkout. It was not pointed at another file.

## Relocated material

Removed from `tonewood_comparison_acacia_family_blackwoods_koa.md`, section The “Malaysian Blackwood” Question:

- The ranking table whose rows were density 1,270 / 640, acoustic impedance ~4.78 / ~2.75, damping, overtone retention, and fundamental emphasis.
- The sentence that Malaysian Blackwood is simply *Acacia melanoxylon* grown in Malaysia.
- The nomenclature key-insight sentence that Tasmanian, Malaysian, and Australian Blackwood are all *Acacia melanoxylon*.

Where the figures went: they were already in the blackwoods comparison (derived acoustic table and the mechanism tables). After the edit, a numeric-token diff against the pre-change Acacia file shows one fewer occurrence each of `640`, `1,270`, `~4.78`, and `~2.75`. `640` and `1,270` still occur in the Acacia document as family-boundary anchors. `2.75` without a tilde still occurs on the Tasmanian derived-impedance row. `~4.78` and `~2.75` still occur in the blackwoods document. No token was replaced with a different value.

The two identity sentences were not given a new source. The C-07 caution, which was already in the same document, is what remains.

The blackwoods document lost no numeric token. Tokens added there are restatements (annotation #15, the year 2020, the existing MOE example 11.82) or the order id. They are not new measurements.

`scripts/check_tonewood_fpl_values.py --summary` after the edit: 119 aliases resolve; 640 cells checked, 0 mismatches; 9 range cells not compared (0 exclude the FPL value); 1,295 property cells skipped. The C-12 log line says 1,299 skipped. The difference is the four unmapped cells in the ranking table removed above (density and impedance, two columns). No mapped cell changed. `scripts/check_tonewood_cirad_citations.py`: 0 mismatches.

## Retained similarities

The Malaysian column in the focused comparison is still the Tasmanian *A. melanoxylon* record. Density 640, Janka 1,160 lbf / 5,160 N, MOE 11.82 GPa, MOR 96.5 MPa, specific gravity 0.58, shrinkage 4.38 / 8.38, specific modulus 18.5, speed ~4,300, impedance ~2.75, and the thermal and CNC rows that match the family document’s Tasmanian column were copied forward unchanged. Deleting them would have removed the comparison. The identity table says what that column is.

Family-versus-African-Blackwood anchors already in the Acacia document (about 1,270 kg/m³, impedance about 4.8, cutting energy 0.98 J/mm³, the summary axes) stay. They are the family’s boundary, not a second Malaysian ranking.

## Citation changes

No citation was pointed at a new work. The Wood Database, Rory McGuinness, Bob Taylor, CITES_STATUS.md, and the acoustic formulas remain as each document already had them. The historical `wood_species.json` path was not replaced. The withdrawn identity sentences had no citation to preserve.

## Unresolved identity questions

Left open on purpose:

- What wood sold as Malaysian Blackwood is. This repo still has no source that it is *Acacia melanoxylon*. The caution’s report that plantation acacia in Malaysia is mainly *A. mangium* and its hybrids is unchanged and was not re-investigated.
- The nomenclature table still says the Malaysian row’s region is “Planted in Malaysia” beside scientific name *Acacia melanoxylon* (unverified). Its notes cell now says the row is provisionally mapped to *A. melanoxylon* for comparison and the trade name’s botanical identity is not established (owner review, 2026-11-16).
- Australian Blackwood was shown as “likely” *A. melanoxylon* with the note “Same species, regional variant”. No source in this repo establishes that, so on owner review (2026-11-16) the note was removed and both its rows and the key insight now say “provisionally mapped”, not established.
- The reference path under `docs/audit-sources/tap_tone_pi/.../wood_species.json` still does not resolve here.

## What O-05 means after this order

O-05 in `docs/tonewood/VERIFICATION_LOG.md` is resolved as duplication only. C-09 had already settled the extreme-density overlap. This order settles the remaining sentence, that the blackwoods document repeated a section of the Acacia document. It does not close O-01, O-02, O-03, O-08, O-11, or the Granadillo remainder of O-06.
