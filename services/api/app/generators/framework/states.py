"""Generator lifecycle and authority — the two independent status axes.

Part of the GFR catalog value contracts. Vocabulary only; imports nothing from
the framework and nothing from any generator implementation.

Two axes, deliberately separate:

    GeneratorLifecycle   how far along the implementation is
    GeneratorAuthority   how much weight its output carries

They are independent because the repository has real cases of every interesting
combination — an EXPERIMENTAL generator can be ADVISORY, and an ACTIVE one can
be SUPERSEDED while a replacement lands. Only a small number of pairings are
contradictory, and those are rejected semantically by
`validate_generator_record()`, never structurally.

Neither axis says anything about reachability. A record marked ACTIVE is a claim
about intent, not evidence that production traverses it; establishing that is a
runtime-witness question and out of scope for a catalog.
"""

from __future__ import annotations

from enum import Enum


class GeneratorLifecycle(str, Enum):
    """How far along an implementation is.

    `(str, Enum)`; `.value` is pinned by the vocabulary tests.
    """

    EXPERIMENTAL = "experimental"
    """Exists and runs, but its contract may change without notice. Not a
    stability promise to any caller."""

    ACTIVE = "active"
    """Maintained, and its contract is stable enough to build against."""

    DEPRECATED = "deprecated"
    """Still present and still callable, but a replacement is named and callers
    are expected to migrate. Distinguished from RETIRED: this one still works."""

    RETIRED = "retired"
    """No longer callable. The record is kept so the identifier resolves and its
    history stays readable rather than becoming a dangling reference."""


class GeneratorAuthority(str, Enum):
    """How much weight a generator's output carries.

    `(str, Enum)`; `.value` is pinned by the vocabulary tests.
    """

    CANONICAL = "canonical"
    """The authority for its category and capability set. At most one record
    should hold this for a given responsibility — but the catalog does not
    enforce uniqueness, because deciding which of two claimants is canonical is
    an adjudication, not a value-contract rule."""

    SUPPLEMENTARY = "supplementary"
    """Legitimate and maintained, but not the authority — a specialization, a
    variant, or an alternative approach that coexists with the canonical one."""

    ADVISORY = "advisory"
    """Output is guidance only and must not be manufactured from directly.
    Typically paired with EXPERIMENTAL, though the axes stay independent."""

    SUPERSEDED = "superseded"
    """Something else now holds this responsibility. Distinguished from the
    DEPRECATED lifecycle: DEPRECATED is about the implementation's future,
    SUPERSEDED is about its standing relative to another record. A record can be
    ACTIVE and SUPERSEDED at once — it works, but it is no longer the answer."""


__all__ = ["GeneratorLifecycle", "GeneratorAuthority"]
