Instrument geometry duplicates:
  POST:/api/instrument/nut-compensation
  POST:/api/instrument/nut-compensation/compare
  POST:/api/instrument/soundhole
  POST:/api/instrument/soundhole/check-position
## Nut Compensation + Soundhole Duplicate Analysis
Date: 2026-03-29

DECISION: Do NOT remove from instrument_router.

Reason: Split routers (nut_fret_router, soundhole_router) use
different request/response schemas than instrument_router.
They are parallel implementations, not replacements.

nut-compensation:
  instrument_router: action_at_nut_mm + fret_height_mm -> setback_mm
  nut_fret_router:   nut_width_mm + break_angle_deg -> compensation_mm
  STATUS: Different physics models. Both should remain registered.

soundhole:
  instrument_router: standard_diameter_mm in response
  soundhole_router:  missing standard_diameter_mm
  STATUS: Split router is incomplete. Keep instrument_router.

ACTION: These 4 routes are NOT duplicates — they are different
calculators at the same path. The endpoint ratchet should
document them as intentional parallel implementations.

