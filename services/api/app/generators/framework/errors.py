"""The GFR framework's single error hierarchy.

One root, so a caller can catch everything the framework raises with one
`except` and never has to know which submodule produced it. `validation.py`
imports `GeneratorValidationError` from here rather than defining its own —
two parallel hierarchies is the failure this module exists to prevent.

    GeneratorFrameworkError
    +-- GeneratorValidationError   (also ValueError)
    +-- GeneratorCatalogError
        +-- DuplicateGeneratorIdError
        +-- GeneratorNotFoundError

`GeneratorValidationError` additionally inherits `ValueError` so that existing
code doing `except ValueError` around record construction keeps working. That
mixin is deliberate: rejecting a malformed value *is* a ValueError, and callers
should not have to learn a framework-specific base class to handle the ordinary
case.

The catalog errors are declared here in the same commit as the root even though
nothing raises them yet — the catalog itself arrives in GFR-001B. Declaring the
whole hierarchy at once is the point of having a single root; adding the leaves
later would mean deciding their parentage twice.
"""

from __future__ import annotations


class GeneratorFrameworkError(Exception):
    """Root of every error raised by the generator framework.

    Catch this to catch anything the framework raises, from any submodule.
    """


class GeneratorValidationError(GeneratorFrameworkError, ValueError):
    """A record's values are semantically invalid.

    Raised by `validate_generator_record()`. Structural type violations are
    *not* this — they raise `TypeError` from `GeneratorRecordV1.__post_init__`,
    because a record holding the wrong Python types should never come into
    existence in the first place.

    Also a `ValueError`, so ordinary `except ValueError` handling still works.
    """


class GeneratorCatalogError(GeneratorFrameworkError):
    """A catalog operation failed.

    Declared in GFR-001A with the rest of the hierarchy; raised from GFR-001B
    onward, when the catalog exists.
    """


class DuplicateGeneratorIdError(GeneratorCatalogError):
    """Two records claim the same `generator_id`.

    Declared in GFR-001A; raised from GFR-001B onward.
    """


class GeneratorNotFoundError(GeneratorCatalogError):
    """A lookup named an identifier the catalog does not hold.

    Declared in GFR-001A; raised from GFR-001B onward, by `require()`.
    """


__all__ = [
    "GeneratorFrameworkError",
    "GeneratorValidationError",
    "GeneratorCatalogError",
    "DuplicateGeneratorIdError",
    "GeneratorNotFoundError",
]
