# How to review this acoustics knowledge corpus

**Audience:** PR reviewers and maintainers  
**Scope:** `docs/calculators/acoustics/` + `docs/LUTHERIE_MATH.md` Appendix B + unfinished-§§ handoff

---

## File roles (do not conflate)

| Role | Examples | Trust as… |
|------|----------|-----------|
| **Policy / architecture** | `COHORT_GOVERNANCE.md`, `LUTHERIE_MATH.md` Appendix B, unfinished-§§ handoff | Normative for routing & intake |
| **Canonical blockers** | `CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md` (**G-R01**) | Single conflict record |
| **Lane indexes** | `PHYSICS_KNOWLEDGE_INDEX.md`, `SHOP_BUILDING_KNOWLEDGE_INDEX.md` | Directory, not product law |
| **Synthesis** | `GORE_LECTURE_SERIES_SUMMARY.md`, orientation | Curated map — defer to packs on conflict |
| **Source packs** | `*/ANNOTATED_*.md`, `*/GAPS_*.md`, `*/CROSSWALK_*.md`, `*/SOURCE_*.md` | Primary evidence + NO-CALC |
| **Generated artifacts** | `cohort_catalog.json`, `POINT_SEARCH_INDEX.md` | Machine output — **non-curated**; regenerate only |

---

## Suggested review order (high risk first)

1. `docs/LUTHERIE_MATH.md` Appendix B + unfinished-§§ handoff  
2. `CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md` + Pack 3 / Pack 5 gap registers  
3. `COHORT_GOVERNANCE.md` (musts vs enforcement)  
4. Holmberg `CROSSWALK` / `WORKBOOK_INVENTORY` / `GAPS`  
5. Pack-level annotated notes only when a crosswalk row points there  

Do **not** treat `POINT_SEARCH_INDEX.md` keyword noise as taxonomy review failures.

---

## Standing productization holds

- No mobility / exceptional badges until **G-R01** closes  
- No Holmberg preset cut lists  
- No parallel spreadsheet engines as product runtimes  
- Gaps stay searchable (`G-*`); never invent missing numbers
