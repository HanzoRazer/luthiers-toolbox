# Current active developer handoffs

**Updated:** 2026-08-04  
**Policy:** Active handoffs live here under `docs/handoffs/`. Older material may be in [`docs/archive/`](../archive/INDEX.md). This index is the quick find list for in-flight work.

---

## Acoustics / Lutherie Math (2026-08)

| Doc | Branch availability | What it is |
|-----|---------------------|------------|
| [`LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md`](./LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md) | **`main`** (merged via [#243](https://github.com/HanzoRazer/luthiers-toolbox/pull/243)) | Unfinished §§ stacks A–D; recommended work order |
| [`G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md`](./G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md) | PR [#248](https://github.com/HanzoRazer/luthiers-toolbox/pull/248) until merge | Close G-R01 with Carrico evidence — separate PRs A–D |

### Direct GitHub links (browser)

- Unfinished §§ (main): https://github.com/HanzoRazer/luthiers-toolbox/blob/main/docs/handoffs/LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md  
- G-R01 Carrico order (PR branch): https://github.com/HanzoRazer/luthiers-toolbox/blob/cursor/g-r01-carrico-dev-order-83c1/docs/handoffs/G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md  
- Canonical mobility blocker (main): https://github.com/HanzoRazer/luthiers-toolbox/blob/main/docs/calculators/acoustics/CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md  

### Local sync

```bash
git fetch origin
git checkout main
git pull origin main
# unfinished §§ handoff is here after pull

# G-R01 order until #248 merges:
git fetch origin cursor/g-r01-carrico-dev-order-83c1
git checkout cursor/g-r01-carrico-dev-order-83c1
# or: git show origin/cursor/g-r01-carrico-dev-order-83c1:docs/handoffs/G_R01_MOBILITY_UNIT_PROFILE_CARRICO_DEV_ORDER_2026-08-04.md
```

---

## Related (not handoffs, but same lane)

| Doc | Path |
|-----|------|
| Math hub + Appendix B | [`docs/LUTHERIE_MATH.md`](../LUTHERIE_MATH.md) |
| Corpus review guide | [`docs/calculators/acoustics/HOW_TO_REVIEW_THIS_CORPUS.md`](../calculators/acoustics/HOW_TO_REVIEW_THIS_CORPUS.md) |
| Mobility blocker G-R01 | [`docs/calculators/acoustics/CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md`](../calculators/acoustics/CANONICAL_BLOCKER_MOBILITY_UNIT_PROFILE.md) |
