One practical next step (optional but recommended)

If you want to make this even more frictionless for future bundles, we can add a tiny doc snippet to your repo (or fold it into your GOVERNANCE.md) that states:

“New endpoints must pass tests/test_route_governance.py”

“Routers are adapters; computation belongs in canonical modules per the service-layer table”

But you’ve already provided the canonical mapping, so this is truly optional. 

Canonical Service Layer Structu…

If you want, tell me which area you’re shipping next (RMOS, CAM, DXF, calculators), and I’ll structure the bundle so all new logic lands in the correct canonical layer by default, with router code kept “thin enough” to satisfy the Fortran Rule test.