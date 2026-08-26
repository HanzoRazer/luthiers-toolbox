# Moved — MB Sound is now an external pinned corpus

The MB Sound cohort is no longer held in this repository. It is canonical in
`HanzoRazer/luthier-acoustics-data` at release `mb-sound/v1.0.0`
(`cohorts/external/mb_sound/`).

Toolbox consumes it by pin: [`docs/reference/mb-sound/`](../../../../../../../docs/reference/mb-sound/).

It previously lived at `../empirical_tonewood/mb_sound/`, which was removed in
DATA-MIG-002 after every file was proven byte-identical to the canonical release.
See [`MIGRATION_DATA-MIG-002.md`](../../../../../../../docs/reference/mb-sound/MIGRATION_DATA-MIG-002.md).

`mb_sound_panels.json` is an empty tombstone kept only so older references resolve.
It is **not** a corpus layout and must not be populated.
