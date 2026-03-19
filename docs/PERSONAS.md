# Production Shop — User Personas

Both reviews flagged: product is overfit to creator's mental model,
needs explicit persona definitions.

---

## Persona 1: The Solo CNC Luthier (Primary)

- Runs their own shop, owns a CNC router
- Builds 10-50 instruments per year
- Technically proficient, not a software developer
- **Pain:** CAD → CAM → machine workflow is fragmented
- **Needs:** One system that handles design through G-code with safety checks
- **Entry point:** CAM workspace
- **Values:** Repeatability, safety, precision

---

## Persona 2: The Boutique Shop Operator

- 2-5 person shop, production volume
- Needs consistent results across operators
- **Pain:** Knowledge lives in one person's head
- **Needs:** Documented processes, preflight gates, setup verification
- **Entry point:** Setup cascade + RMOS
- **Values:** Consistency, documentation, traceability

---

## Persona 3: The Advanced Hobbyist

- Builds 2-5 instruments per year
- Has CNC access (own or shared)
- Strong domain knowledge, learning CAM
- **Pain:** Professional tools cost too much or require too much training
- **Needs:** Guided workflows, sensible defaults, good error messages
- **Entry point:** Geometry calculators → DXF export
- **Values:** Learning, quality, affordability

---

## Persona 4: The Acoustic Designer

- Focused on acoustic performance
- May or may not have CNC
- Deep interest in plate physics, bracing
- **Pain:** No tools connect acoustic measurement to manufacturing decisions
- **Needs:** Plate analysis, graduation maps, tap-tone integration
- **Entry point:** Acoustic plate design
- **Values:** Acoustic accuracy, physics-based decisions

---

## Out of Scope Personas (explicitly not targeted)

- Enterprise multi-site operations
- Non-luthier woodworking
- General audio production
- DIY beginners with no CNC experience

---

## Design Principle from Personas

Every workflow should be answerable by Persona 1 without reading documentation.

Every workflow should produce output that satisfies Persona 2's traceability requirements.
