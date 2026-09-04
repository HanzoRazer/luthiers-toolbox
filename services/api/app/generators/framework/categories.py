"""Generator categories — the top-level "what kind of thing does it make" axis.

Part of the GFR catalog value contracts. This module defines vocabulary only; it
imports nothing from the framework and nothing from any generator implementation.

Every member carries a documented system use and a scope statement that
distinguishes it from every other member. The three geometry categories overlap
in subject matter but not in scope, so the distinction is stated explicitly
rather than left to the reader:

    INSTRUMENT_GEOMETRY  cross-component, whole-instrument
    BODY_GEOMETRY        body-specific
    NECK_HEADSTOCK       neck, headstock, fretboard, joint, transition

A category describes the generator's *output domain*. It says nothing about how
the generator is invoked, and nothing about whether it is currently reachable —
those are `GeneratorLifecycle` and the execution subsystem's concern.
"""

from __future__ import annotations

from enum import Enum


class GeneratorCategory(str, Enum):
    """What a generator produces.

    `(str, Enum)` so a record serializes to a stable string. The `.value` of
    every member is part of the catalog's external contract and is pinned by
    `tests/generators/framework/test_vocabulary.py`.
    """

    INSTRUMENT_GEOMETRY = "instrument_geometry"
    """Cross-component geometry spanning more than one instrument region.

    Scope: whole-instrument or multi-region output — a full outline plus neck
    pocket plus bridge placement, or anything whose correctness depends on two
    regions agreeing. Use BODY_GEOMETRY or NECK_HEADSTOCK when the output is
    confined to one region.
    """

    BODY_GEOMETRY = "body_geometry"
    """Body-region geometry only.

    Scope: outlines, bouts, waists, cavities, bindings and body-plane features.
    System use: `app.generators.body_generator`, `bezier_body`,
    `acoustic_body_generator`, `electric_body_generator`,
    `lespaul_body_generator`, `stratocaster_body_generator`.
    """

    NECK_HEADSTOCK = "neck_headstock"
    """Neck, headstock, fretboard, joint and transition geometry.

    Scope: everything from the neck heel forward, plus the body-to-neck
    transition considered from the neck side.
    System use: `app.generators.neck_headstock_generator` and its
    `_config` / `_enums` / `_geometry` / `_presets` siblings.
    """

    CAM_TOOLPATH = "cam_toolpath"
    """Machine-motion output: toolpaths, passes, and cutting sequences.

    Scope: output whose consumer is a machine controller rather than a drawing.
    Distinguished from MANUFACTURING, which covers non-motion production
    artifacts. System use: `app.generators.lespaul_gcode`, `cam_utils`.
    """

    MANUFACTURING = "manufacturing"
    """Production artifacts that are not machine motion.

    Scope: fixtures, templates, jigs, stock layouts, cut lists, setup sheets.
    Distinguished from CAM_TOOLPATH by consumer: a person or a process, not a
    controller.
    """

    WORKFLOW = "workflow"
    """Generators whose output is a sequence of steps rather than geometry.

    Scope: build orders, operation sequences, staged plans. Distinguished from
    MANUFACTURING because the product is the ordering itself, not an artifact
    consumed at a station.
    """

    REFERENCE_PROFILE_INPUT = "reference_profile_input"
    """Generators that produce reference profiles consumed by other generators.

    Scope: curve libraries, measured profiles, and datum sets that exist to be
    read by a downstream generator rather than manufactured directly. This is
    the only category defined by its *consumer* being another generator.
    """

    UTILITY = "utility"
    """Supporting generators with no instrument-domain output of their own.

    Scope: coordinate transforms, unit conversions, sampling helpers and other
    domain-neutral producers. A generator belongs here only when no other
    category applies — UTILITY is the explicit fallback, not a synonym for
    "uncategorised", and a record that could sit elsewhere should.
    """


__all__ = ["GeneratorCategory"]
