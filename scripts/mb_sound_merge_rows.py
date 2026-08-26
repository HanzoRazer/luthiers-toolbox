#!/usr/bin/env python3
"""Retired entrypoint — the MB Sound corpus is no longer held in this repository.

HISTORICAL / NON-AUTHORITATIVE extraction tooling. This script merged rows into a
monolithic panels.json layout that the per-specimen corpus replaced, and that
corpus has since moved out of Toolbox entirely.

The MB Sound cohort is canonical in HanzoRazer/luthier-acoustics-data, release
mb-sound/v1.0.0. Toolbox consumes it by pin — see docs/reference/mb-sound/.
Specimens are not authored here; new observations belong to the canonical
repository, not to a Toolbox-local copy.

Retained for provenance only. It does nothing and exits non-zero.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "mb_sound_merge_rows.py is retired.\n"
        "Toolbox no longer holds an MB Sound corpus to merge into; the cohort is\n"
        "canonical in HanzoRazer/luthier-acoustics-data @ mb-sound/v1.0.0 and is\n"
        "consumed here by pin. See docs/reference/mb-sound/.\n"
        "To validate a cohort you have checked out elsewhere:\n"
        "  python3 scripts/mb_sound_validate_corpus.py --corpus-path <path-to>/mb_sound",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
