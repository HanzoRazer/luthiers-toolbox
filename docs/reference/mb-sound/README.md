# MB Sound — pinned external reference corpus

**Toolbox does not own MB Sound data.** It consumes a canonical, immutable corpus
held by `HanzoRazer/luthier-acoustics-data` at release `mb-sound/v1.0.0`.

| | |
|---|---|
| Canonical repository | `HanzoRazer/luthier-acoustics-data` (private) |
| Release | `mb-sound/v1.0.0` — 114 specimens, 114 envelopes |
| Cohort path | `cohorts/external/mb_sound/` |
| Machine-facing pin | [`CORPUS_DEPENDENCY.json`](./CORPUS_DEPENDENCY.json) |
| Custody transfer record | [`MIGRATION_DATA-MIG-002.md`](./MIGRATION_DATA-MIG-002.md) |

## What lives where

This directory previously held the MB Sound process documentation — the DO-SIP-013
program record, extraction playbook, field glossary, namespace, treatment cohorts and
staging artifacts. Those documents are now canonical at
`cohorts/external/mb_sound/process/` in the data repository, and the payloads that
formerly sat under `services/api/app/data_registry/system/materials/empirical_tonewood/`
are canonical at `cohorts/external/mb_sound/specimens/`.

Both were removed from Toolbox in DATA-MIG-002 after every file was proven
byte-identical to the release. Nothing was lost: the migration record carries the full
hash table, and the canonical release is immutable and tagged.

## Verifying the pin

```
# offline, against a local clone — no credentials needed
python scripts/verify_reference_corpus_pin.py --corpus-repo /path/to/luthier-acoustics-data

# online, via gh (the canonical repository is private, so this needs auth)
python scripts/verify_reference_corpus_pin.py
```

The verifier fails closed. Any mismatch in release identity, manifest digest, corpus
digest, record count or schema version is an error; an unreachable canonical release is
reported `UNRESOLVED` rather than silently passing.

`tests/test_mb_sound_corpus_dependency.py` exercises the pin and the verifier fully
offline against synthetic manifests, so CI needs no network and no credentials. Live
resolution is a deliberate, manual step.

## What is still Toolbox's

Retained here because they are Toolbox-specific, not canonical evidence:

- `scripts/mb_sound_*.py` — extraction, OCR, merge and validation tooling from the
  original intake. **Non-authoritative**: the corpus they built is no longer owned here,
  and the canonical repository carries its own copies under `tools/mb_sound/`.
- `docs/calculators/acoustics/mb_sound_panel_laboratory_records/` and
  `.../nicoletti_mb_sound_acoustic_study_set/` — annotated lecture notes and the
  crosswalk mapping MB points onto `docs/LUTHERIE_MATH.md` solvers. These are Toolbox
  interpretation of an external source, not the source itself.

## What this pin does not authorise

Pinning establishes access and identity. It does not make MB Sound observations a
source of design defaults, does not validate any formula or generator, does not assert
agreement with any Tap Tone Pi or Laboratory measurement, and does not rank species.
Individual measured specimens must not be folded into `wood_species.json` as handbook
species means.
