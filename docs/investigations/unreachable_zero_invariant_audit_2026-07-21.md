# Unreachable-zero invariant audit — 2026-07-21

**Status: CHECKED — ABSENT**

Prompted by `docs/handoffs/HANDOFF-2026-07-21-UNREACHABLE-ZERO-INVARIANT.md`
(Master All Strings, DO-003). That handoff makes no claim about this
repository; it asks other repos to run the search, trace derived values,
inspect guards, and report negative results. This is that report.

## Defect shape

> An exact-equality test on a **derived** floating-point value, where valid
> upstream input shifts the value off the tested lattice, making the branch
> unreachable and deleting a whole class of output without error.

## Scope

- Exact equality against zero or fixed floating-point lattice values
- Fret and fan-fret geometry
- CAM depth, retract, clearance, origin, and closure logic

## Result

- No live instance of the Master All Strings defect shape was found.
- No `SpatialPosition`, `relative_semitone_position`, or open-string
  biconditional analogue exists in this repository (the defect model lives in
  Master All Strings, not here).
- Nut-at-zero comparisons operate on **supplied integer fret identifiers**
  (`fret_number == 0` at `fret_math.py:400`, `fretboard_ecosphere.py:377`),
  not derived floats — positions are computed forward, not detected by
  zero-equality.
- Perpendicular-fret geometry uses the two intended defenses: **integer
  snapping** (`round()`, `fret_math.py:237`) and **tolerance-based coincidence
  checks** (`abs(dx) < 0.001`, `abs(angle_rad) < PERP_ANGLE_EPS`;
  `fret_math.py:465-470`, `fretboard_ecosphere.py:498`). A non-integer
  perpendicular-fret parameter cannot make the branch unreachable.
- No exact-equality on a derived float found in CAM depth/retract/clearance.
- Remaining `== 0` hits are collection-emptiness, denominator, return-code, or
  test-assertion guards — structurally different, not the derived-off-lattice
  pattern.
- No output category becomes silently unreachable under valid unusual input.

## Prior prediction — disproven

An earlier pre-audit assessment forecast "5–15 HIGH-priority hits" concentrated
in fret / fan-fret math. **This is a pre-audit hypothesis disproven by
inspection**, not repository evidence: the exact locations it named already use
integer snapping and tolerance bands. Do not carry the predicted count forward
as a finding.

## Disposition

- No remediation item opened.
- Revisit only if new code introduces exact equality on derived geometry or
  toolpath values.
