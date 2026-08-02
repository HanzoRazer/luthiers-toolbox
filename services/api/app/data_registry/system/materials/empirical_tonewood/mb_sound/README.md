# MB Sound — versioned empirical tonewood corpus

**Draft intake boundary only.** Does not change generator defaults, `TonewoodEntry` authority, plate solvers, or production behavior.

| | |
|--|--|
| Dataset | Maderas Barber MB Sound |
| Scale (target) | ~4 species, ~60 individually tested specimens |
| Status | Draft PR intake — incomplete corpus |
| Program | DO-SIP-013 … DO-SIP-017 (see `docs/reference/mb-sound/DO_SIP_PROGRAM.md`) |
| Process docs | `docs/reference/mb-sound/` |

## Pipeline (architectural)

```text
MB Sound source material
        ↓
Draft data PR  (#244 — this tree)
        ↓
Dataset inventory and validation
        ↓
Specimen records  (specimens/*.json)
        ↓
Species and treatment cohorts  (species/*/)
        ↓
Empirical Material Registry  (future — not this PR)
        ↓
Future plate, damping, matching, and cohort adapters  (DO-SIP-016+)
```

## Layer separation (per specimen)

| Layer | Meaning |
|-------|---------|
| `source` | Copied/transcribed vendor labels and values |
| `normalized` | Canonical units + provisional field alignment |
| `derived` | Toolbox recomputed quantities (empty until DO-SIP-014) |
| `validation` | Source vs recomputed / consistency checks |
| `unresolved` | Unknown definitions or protocols |
| `artifacts` | References to video/audio/spectra (no binary ingest here) |

## Layout

```text
mb_sound/
  manifest.json
  species/
    adirondack_torrefied/   # TORREFIED suite (mb-adt-*)
    adirondack/             # plain/untreated suite (mb-ad-* reserved)
    red_cedar/
    alpine_spruce/
    european_spruce/
  specimens/mb-*.json
  source_artifacts/artifact_manifest.json
  validation/{consistency_results,unresolved_fields}.json
```

## Treatment discrimination (required)

Same botanical species can appear in **multiple MB Sound suites**. Do not conflate them.

| Suite | `species_id` | `treatment` | Cohort | Specimen prefix |
|-------|--------------|-------------|--------|-----------------|
| Torrefied Adirondack | `spruce_adirondack` | `torrefied` | `adirondack_torrefied` | `mb-adt-` |
| Plain Adirondack | `spruce_adirondack` | `plain` | `adirondack` | `mb-ad-` |
| Red Cedar (plain) | `cedar_western_red` | `plain` | `red_cedar` | `mb-rc-` |
| Alpine Spruce (plain) | `spruce_european` | `plain` | `alpine_spruce` | `mb-as-` |

See `docs/reference/mb-sound/TREATMENT_COHORTS.md`.

## Non-claims

- Not Inv-026-A materials specification authority  
- Not DO-SIP-013 complete until full ~60-specimen gates pass  
- Not a substitute for `wood_species.json` handbook averages  
