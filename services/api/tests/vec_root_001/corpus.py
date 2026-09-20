"""Corpus declaration for the VEC-ROOT-001 harness.

The plans cannot live in the repository. They are declared here by filename and
SHA-256 so that a missing corpus is reported as NOT_RUN_SOURCE_ABSENT and a
*swapped* corpus is reported as a hash mismatch -- never as a pass.

Corpus root resolution order:
  1. $VEC_ROOT_001_CORPUS
  2. <repo>/Guitar Plans        (gitignored, see .gitignore:462)
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CORPUS_ROOT = REPO_ROOT / "Guitar Plans"

SOURCE_ABSENT = "NOT_RUN_SOURCE_ABSENT"
DEPENDENCY_ABSENT = "NOT_RUN_DEPENDENCY_ABSENT"
OPT_IN_REQUIRED = "NOT_RUN_OPT_IN_REQUIRED"


@dataclass(frozen=True)
class Plan:
    """A corpus plan, pinned by hash.

    ``sha256`` is the raster VEC-ROOT-001 was measured against. The cuatro raster
    is 2232x4000 and could NOT be regenerated from
    ``El Cuatro/cuatro puertorique<n-tilde>o.pdf`` by any uniform render: 93 DPI
    yields 3999 rows, a 4000-row fit yields 2233 columns. It is therefore pinned
    as a file, not as a render recipe.
    """

    key: str
    filename: str
    sha256: str
    note: str


CUATRO = Plan(
    key="cuatro",
    filename="VEC-ROOT-001_cuatro_puertoriqueno_2232x4000.png",
    sha256="2d7f85f5040d3d21f5fe9918e7e8d40205406240534fa858af34ce91e0fcd0f9",
    note="cuatro puertoriqueno, 2232x4000 raster. ROOT-001 section 2a.",
)

L00 = Plan(
    key="l00",
    filename="Gibson-L0-IN.png",
    sha256="2a3fea551282feef07a4ed58d1c1d7880518c690a0a6d6e9ab3148112f80fda7",
    note="Gibson L-00, 2495x1940 raster. ROOT-001 section 2b.",
)

ARCHTOP = Plan(
    key="archtop",
    filename=(
        "Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway"
        "_02_foreground.jpg"
    ),
    sha256="ee2db7346c9fb29b27b48a1eade4e7d473b194b198e552705d51c6f25a383f86",
    note="AI-generated archtop, background removed. ROOT-001 section 11 control.",
)

PLANS = {p.key: p for p in (CUATRO, L00, ARCHTOP)}


def corpus_root() -> Path:
    env = os.environ.get("VEC_ROOT_001_CORPUS")
    return Path(env) if env else DEFAULT_CORPUS_ROOT


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def resolve(plan: Plan) -> tuple[Path | None, str | None]:
    """Return (path, None) when usable, or (None, reason) when not.

    A hash mismatch is NOT a reason to skip -- it is returned so the caller can
    fail loudly. Only genuine absence yields NOT_RUN_SOURCE_ABSENT.
    """
    path = corpus_root() / plan.filename
    if not path.exists():
        return None, f"{SOURCE_ABSENT}: {path}"
    return path, None
