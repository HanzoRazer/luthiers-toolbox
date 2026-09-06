# PATCH PROPOSAL

```text
NO PRODUCTION PATCH AUTHORIZED
```

This increment is evidence gathering only.

It does not:

- modify production source
- repair a discovered wiring defect
- change route mounts
- delete wrappers
- consolidate implementations
- change defaults
- fix `dump_and_assert_routes.py`
- modify Vectorizer behavior
- modify Manufacturing Spine, RMOS, CBSP21, or EQ-A01

## Future remediation boundary (S3 severe stop)

FINDINGS.md records a severe stop on S3: runtime-confirmed first-match of
`POST /api/cam/polygon_offset.nc` is N17 `polygon_offset`, while OffsetLab
posts governed-shaped `stepover` (0–1 fraction of `tool_dia`).

Any later remediation is a **separate, owner-adjudicated production act**.
It would be bounded to:

```text
ENTRYPOINT                 POST /api/cam/polygon_offset.nc
EXPECTED (OffsetLab schema) polygon_offset_nc  (stepover as fraction)
ACTUAL (this SHA)           utility polygon_offset / N17 (stepover as mm)
TERMINAL EFFECT             N17 G-code; 0.4 mm pass insets vs 2.4 mm implied
ALSO CONSUMES THIS URL      n17_n18.ts
NOT IN SCOPE HERE           /api/cam/polygon_offset.preview
```

Do not silently delete the N17 handler if it still has a legitimate client.
Do not change OffsetLab defaults in this packet. No implementation code is
provided here.

S1 (unmounted FE URL), S2 (HTTP ownership with shared facade), and S4
(legacy DXF URL) are not authorized production patches in this increment.

If the owner later opens a production change, it is a new PR against
production, not a continuation of Investigation 035.
