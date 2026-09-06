# SCOPE

## Current production baseline

```text
repo              HanzoRazer/luthiers-toolbox
ref               origin/main (fetched at Phase 0)
PRODUCTION SHA    cab91edacaedc66a0492c35275ce2c255935bf8e
isolated specimen /tmp/ltb-prod-specimen  (detached, read-only intent)
```

Repository-production, not deployed-production.

## Historical comparator

```text
HISTORICAL COMPARATOR SHA = cab91edacaedc66a0492c35275ce2c255935bf8e
source                    Lab PR #17 (033-legacy-wiring-reachability-census)
```

PR #17 census artifacts are **not present in this environment**. Historical
numeric counts are therefore not restated from memory. Current census output
is stored only under this investigation. Do not overwrite PR #17 evidence
(none is present here to overwrite).

If a count comparison is written, it must say:

```text
current count = X
historical count = Y
comparison not normalized
```

unless the same instrumentation and scope are demonstrably comparable.

## Five-specimen maximum

Exactly five candidates are selected for runtime verification, with diversity
across subsystems and failure shapes. Selection is a **manual evidence table**,
not a scoring agent.

Do not expand to all wrapper candidates during this increment.

## Production read-only rule

- Do not modify production source.
- Do not repair a discovered wiring defect.
- Do not change route mounts, wrappers, defaults, or Vectorizer behavior.
- Do not modify Manufacturing Spine, RMOS, CBSP21, or EQ-A01.
- Do not recover `SPRINTS.md`.
- Do not fix `dump_and_assert_routes.py`. If it is run, run it as-is, preserve
  the result, and use a Lab-side output redirect so production `metrics/` is
  not written.

## Excluded workstreams (change / expand)

```text
production remediation
autonomous candidate selection
general-purpose ranking engine
generic orchestration framework
self-expanding audit loops
cross-repository agent infrastructure
Vectorizer behavior change
Manufacturing Spine change
RMOS change
CBSP21 change
EQ-A01 change
SPRINTS.md recovery
```

Witnessing a specimen that lives in an excluded workstream is allowed.
Changing that workstream is not.

## Route-truth defect

The known `dump_and_assert_routes.py` defect remains separate.

```text
ROUTE-TRUTH DEFECT TOUCHED? = NO
```

## Severe-finding stop rule

Stop the remaining specimens only if all three hold:

1. RUNTIME CONFIRMED — current production entrypoint executes wrong/unintended
   implementation
2. MATERIAL CAPABILITY — customer-facing or manufacturing-affecting
3. MATERIAL CONSEQUENCE — could alter manufacturing output, customer result,
   authority/safety behavior, or materially misrepresent capability

Static ambiguity alone does not trigger this stop.
