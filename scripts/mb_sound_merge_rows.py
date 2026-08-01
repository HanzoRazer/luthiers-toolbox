#!/usr/bin/env python3
"""Deprecated entrypoint — empirical corpus uses per-specimen JSON files.

Prefer writing specimens directly under:
  services/api/app/data_registry/system/materials/empirical_tonewood/mb_sound/specimens/

Then:
  python3 scripts/mb_sound_validate_corpus.py --write-validation
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "mb_sound_merge_rows.py is retired for the monolithic panels.json layout.\n"
        "Add specimens/*.json under empirical_tonewood/mb_sound/ then run:\n"
        "  python3 scripts/mb_sound_validate_corpus.py --write-validation",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
