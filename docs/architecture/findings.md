# Architecture Findings Registry

This is a **human-curated** list of recurring structural issues (and their preferred fixes).
The scan harness can discover candidates, but only humans should add final entries here.

## Conventions

- Finding IDs are global: `F-001`, `F-002`, ...
- Each entry should include:
  - Location
  - Why it matters
  - Preferred remediation pattern
  - Link to issue/PR if one exists

---

## Template

### F-XXX — <short title>

**Location:** `path/to/file.ext`

**Signals:** `GCODE`, `DIRECT_RESPONSE`, ...

**Impact:** What breaks (governance, provenance, safety, audit).

**Preferred fix:** (e.g., two-lane draft/governed wrapper, shared generator extraction, neutral envelope helper)

**Status:** observed | tracking | planned | fixed

**Links:** Issue / PR / notes
