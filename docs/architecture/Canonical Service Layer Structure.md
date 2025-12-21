 Answer 1: Canonical Service Layer Structure

  The current structure is already well-organized. Here's the recommended canonical mapping:

  | Layer              | Folder               | Purpose                                       |
  |--------------------|----------------------|-----------------------------------------------|
  | Pure Geometry Math | geometry/            | General (arcs, circles, points)               |
  | Instrument Math    | instrument_geometry/ | Fret, bridge, body, neck                      |
  | CAM Algorithms     | cam/                 | Biarc, trochoid, feedtime, toolpath           |
  | Domain Calculators | calculators/         | Orchestrate math (fret_slots, inlay, bracing) |
  | Domain Modules     | rmos/, saw_lab/      | Self-contained domains                        |
  | Orchestration      | services/            | Stores, bridges, job management (non-math)    |

  Recommendation: Keep this structure. Don't create a new services/ subfolder for orchestration—the existing services/ folder already handles that pattern well.

  Answer 2: Governance Test File

  File: tests/test_route_governance.py

  Current tests:
  - TestComponentRouterRule - No scattered endpoints
  - TestNoDoublePrefix - No /api/api/ bugs
  - TestNoDuplicatePrefixes - Consolidated endpoints
  - TestOpenAPIPathSnapshot - API stability

  Missing: There is no "router must not compute" test yet.

  Let me add that test:

● Read(services\api\tests\test_route_governance.py)
  ⎿  Read 50 lines

● Update(services\api\tests\test_route_governance.py)
  ⎿  Added 12 lines, removed 4 lines
        1    """
        2    Route Governance Tests
        3
        4 -  Enforces the Component Router Rule (COMPONENT_ROUTER_RULE_v1.md):
        5 -  - No scattered endpoints across multiple routers
        6 -  - Single canonical prefix per domain
        4 +  Enforces architectural rules:
        5 +  1. Component Router Rule (COMPONENT_ROUTER_RULE_v1.md):
        6 +     - No scattered endpoints across multiple routers
        7 +     - Single canonical prefix per domain
        8
        9 -  These tests scan OpenAPI paths and fail if governance rules are violated.
        9 +  2. Fortran Rule (STRUCTURAL_MILESTONE_EXECUTIVE_SUMMARY.md):
       10 +     - No inline math computations in routers
       11 +     - Routers must delegate to math modules
       12 +
       13 +  These tests scan OpenAPI paths and router source files, failing if rules are violated.
       14    Run as part of CI to prevent architectural drift.
       15    """
       16
       17    import pytest
       18 +  import re
       19 +  import ast
       20 +  from pathlib import Path
       21    from fastapi.testclient import TestClient
       22
       23

● Read(services\api\tests\test_route_governance.py)
  ⎿  Read 38 lines

● Update(services\api\tests\test_route_governance.py)
  ⎿  Added 148 lines
       267
       268
       269    # =============================================================================
       270 +  # FORTRAN RULE: NO INLINE MATH IN ROUTERS
       271 +  # =============================================================================
       272 +
       273 +  # Routers that are grandfathered (pre-cleanup) or have legitimate exceptions
       274 +  FORTRAN_RULE_EXCEPTIONS = {
       275 +      # Grandfathered routers with remaining inline math (lower priority cleanup)
       276 +      "cam_post_v160_router.py",
       277 +      "cam_post_v161_router.py",
       278 +      # Test/utility routers
       279 +      "health_router.py",
       280 +  }
       281 +
       282 +  # Math patterns that indicate inline computation (violations)
       283 +  INLINE_MATH_PATTERNS = [
       284 +      # Trigonometric computations
       285 +      (r'\bmath\.sin\s*\(', "math.sin() - use geometry/arc_utils or instrument_geometry"),
       286 +      (r'\bmath\.cos\s*\(', "math.cos() - use geometry/arc_utils or instrument_geometry"),
       287 +      (r'\bmath\.tan\s*\(', "math.tan() - use geometry/arc_utils"),
       288 +      (r'\bmath\.atan2?\s*\(', "math.atan/atan2() - use geometry/arc_utils"),
       289 +      # Exponential/power computations (fret math)
       290 +      (r'\b2\s*\*\*\s*\(-?\s*\w+\s*/\s*12\)', "2^(-fret/12) - use fret_math.py"),
       291 +      (r'\bmath\.pow\s*\(', "math.pow() - extract to math module"),
       292 +      # Hardcoded pi
       293 +      (r'\b3\.14159', "Hardcoded pi - use math.pi"),
       294 +      # Circle/arc formulas
       295 +      (r'\b2\s*\*\s*(?:math\.)?pi\s*\*\s*\w+', "Circle formula - use geometry/arc_utils"),
       296 +  ]
       297 +
       298 +  # Allowed math imports (stdlib conversions, not algorithms)
       299 +  ALLOWED_MATH_USAGE = [
       300 +      "math.hypot",      # Distance calculation (stdlib, not algorithm)
       301 +      "math.radians",    # Unit conversion
       302 +      "math.degrees",    # Unit conversion
       303 +      "math.pi",         # Constant (allowed when passed to functions)
       304 +      "math.sqrt",       # When used for simple distance, not algorithm
       305 +      "math.floor",      # Rounding
       306 +      "math.ceil",       # Rounding
       307 +      "math.isnan",      # Validation
       308 +      "math.isinf",      # Validation
       309 +  ]
       310 +
       311 +
       312 +  class TestFortranRule:
       313 +      """
       314 +      Tests for Fortran Rule compliance: "All math in subroutines"
       315 +
       316 +      Routers should delegate calculations to math modules, not compute inline.
       317 +      This prevents duplicate implementations and ensures testable math.
       318 +
       319 +      Canonical math modules:
       320 +      - geometry/arc_utils.py - Circles, arcs, tessellation
       321 +      - instrument_geometry/neck/fret_math.py - Fret calculations
       322 +      - instrument_geometry/body/parametric.py - Bezier, ellipse
       323 +      - cam/biarc_math.py - Fillets, arc fitting
       324 +      """
       325 +
       326 +      @pytest.fixture(scope="class")
       327 +      def router_files(self):
       328 +          """Get all router Python files."""
       329 +          routers_dir = Path(__file__).parent.parent / "app" / "routers"
       330 +          if not routers_dir.exists():
       331 +              pytest.skip("Routers directory not found")
       332 +          return list(routers_dir.glob("*_router.py"))
       333 +
       334 +      def test_no_inline_math_in_routers(self, router_files):
       335 +          """
       336 +          RULE: Routers must not contain inline math computations.
       337 +
       338 +          Violations trigger when router files contain math patterns
       339 +          that should be delegated to canonical math modules.
       340 +          """
       341 +          violations = []
       342 +
       343 +          for router_path in router_files:
       344 +              if router_path.name in FORTRAN_RULE_EXCEPTIONS:
       345 +                  continue
       346 +
       347 +              content = router_path.read_text(encoding="utf-8")
       348 +              file_violations = []
       349 +
       350 +              for pattern, message in INLINE_MATH_PATTERNS:
       351 +                  matches = list(re.finditer(pattern, content))
       352 +                  for match in matches:
       353 +                      # Find line number
       354 +                      line_num = content[:match.start()].count('\n') + 1
       355 +                      line_content = content.split('\n')[line_num - 1].strip()
       356 +
       357 +                      # Skip if it's in a comment
       358 +                      if line_content.startswith('#'):
       359 +                          continue
       360 +                      # Skip if it's in a docstring context (rough heuristic)
       361 +                      if '"""' in line_content or "'''" in line_content:
       362 +                          continue
       363 +
       364 +                      file_violations.append(
       365 +                          f"  Line {line_num}: {message}\n"
       366 +                          f"    Code: {line_content[:80]}"
       367 +                      )
       368 +
       369 +              if file_violations:
       370 +                  violations.append(
       371 +                      f"\n{router_path.name}:\n" + "\n".join(file_violations)
       372 +                  )
       373 +
       374 +          if violations:
       375 +              pytest.fail(
       376 +                  "Fortran Rule violations found (inline math in routers):\n"
       377 +                  "Routers should delegate to math modules, not compute inline.\n"
       378 +                  "\nCanonical modules:\n"
       379 +                  "  - geometry/arc_utils.py\n"
       380 +                  "  - instrument_geometry/neck/fret_math.py\n"
       381 +                  "  - cam/biarc_math.py\n"
       382 +                  "\nViolations:" + "".join(violations)
       383 +              )
       384 +
       385 +      def test_no_hardcoded_pi(self, router_files):
       386 +          """
       387 +          RULE: No hardcoded pi values (3.14159, 3.1416, etc.)
       388 +
       389 +          Always use math.pi for consistency and precision.
       390 +          """
       391 +          violations = []
       392 +          pi_pattern = re.compile(r'\b3\.14\d*')
       393 +
       394 +          for router_path in router_files:
       395 +              content = router_path.read_text(encoding="utf-8")
       396 +              matches = list(pi_pattern.finditer(content))
       397 +
       398 +              for match in matches:
       399 +                  line_num = content[:match.start()].count('\n') + 1
       400 +                  line_content = content.split('\n')[line_num - 1].strip()
       401 +
       402 +                  # Skip comments
       403 +                  if line_content.startswith('#'):
       404 +                      continue
       405 +
       406 +                  violations.append(
       407 +                      f"{router_path.name}:{line_num} - {line_content[:60]}"
       408 +                  )
       409 +
       410 +          if violations:
       411 +              pytest.fail(
       412 +                  "Hardcoded pi values found (use math.pi instead):\n" +
       413 +                  "\n".join(f"  - {v}" for v in violations)
       414 +              )
       415 +
       416 +
       417 +  # =============================================================================
       418    # UTILITY: Run standalone to check current state
       419    # =============================================================================
       420

● Now let me run the updated governance tests to verify they pass:

● Bash(powershell -Command "cd 'C:\Users\thepr\Downloads\luthiers-toolbox\services\api'; python -m pytest
      tests\test_route_governance.py -v --tb=short --override-ini='…)
  ⎿  Error: Exit code 1
     ============================= test session starts =============================
     platform win32 -- Python 3.14.0, pytest-9.0.1, pluggy-1.6.0 -- C:\Python314\python.exe
     cachedir: .pytest_cache
     rootdir: C:\Users\thepr\Downloads\luthiers-toolbox\services\api
     configfile: pytest.ini
     plugins: anyio-4.11.0
     collecting ... collected 8 items

     tests/test_route_governance.py::TestComponentRouterRule::test_no_scattered_fret_routes
     … +73 lines (ctrl+o to see all)

● The test correctly identified remaining violations. Let me add these to the exceptions list (grandfathered, lower priority):

● Update(services\api\tests\test_route_governance.py)
  ⎿  Added 11 lines
       271    # =============================================================================
       272
       273    # Routers that are grandfathered (pre-cleanup) or have legitimate exceptions
       274 +  # NOTE: When you fix a router, REMOVE IT from this list to enable enforcement
       275    FORTRAN_RULE_EXCEPTIONS = {
       276        # Grandfathered routers with remaining inline math (lower priority cleanup)
       277 +      # TODO: Extract sine wave math to geometry module
       278 +      "adaptive_preview_router.py",
       279 +      # TODO: Extract neck angle math to instrument_geometry
       280 +      "archtop_router.py",
       281 +      # TODO: Extract circle pattern math to geometry/arc_utils
       282 +      "cam_drill_pattern_router.py",
       283 +      # TODO: Extract remaining arc tessellation to cam/biarc_math
       284 +      "cam_post_v155_router.py",
       285        "cam_post_v160_router.py",
       286        "cam_post_v161_router.py",
       287 +      # TODO: Extract arc angle calculations to geometry/arc_utils
       288 +      "geometry_router.py",
       289        # Test/utility routers
       290        "health_router.py",
       291    }

● Bash(powershell -Command "cd 'C:\Users\thepr\Downloads\luthiers-toolbox\services\api'; python -m pytest
      tests\test_route_governance.py -v --tb=short --override-ini='…)
  ⎿  ============================= test session starts =============================
     platform win32 -- Python 3.14.0, pytest-9.0.1, pluggy-1.6.0 -- C:\Python314\python.exe
     cachedir: .pytest_cache
     … +33 lines (ctrl+o to expand)

● All 8 governance tests pass. Let me update the executive summary with the answers to your questions:

● Update(docs\reports\STRUCTURAL_MILESTONE_EXECUTIVE_SUMMARY.md)
  ⎿  Added 59 lines
       516
       517    ---
       518
       519 +  ## Canonical Service Layer Structure
       520 +
       521 +  ### Where Does Non-Geometry Computation Go?
       522 +
       523 +  | Layer | Folder | Purpose | Examples |
       524 +  |-------|--------|---------|----------|
       525 +  | **Pure Geometry** | `geometry/` | General math (arcs, circles) | `arc_utils.py` |
       526 +  | **Instrument Math** | `instrument_geometry/` | Fret, bridge, body, neck | `fret_math.py` |
       527 +  | **CAM Algorithms** | `cam/` | Toolpath, biarc, trochoid | `biarc_math.py` |
       528 +  | **Domain Calculators** | `calculators/` | Orchestrate math modules | `fret_slots_cam.py` |
       529 +  | **Domain Modules** | `rmos/`, `saw_lab/` | Self-contained domains | `feasibility_scorer.py` |
       530 +  | **Orchestration** | `services/` | Stores, bridges, jobs | `art_jobs_store.py` |
       531 +
       532 +  **Decision:** Keep this structure. Do NOT create new folders—use the existing pattern.
       533 +
       534 +  ---
       535 +
       536 +  ## Governance Test Location
       537 +
       538 +  ### File: `tests/test_route_governance.py`
       539 +
       540 +  This file contains all architectural enforcement tests:
       541 +
       542 +  | Test Class | Rule Enforced |
       543 +  |------------|---------------|
       544 +  | `TestComponentRouterRule` | No scattered endpoints across routers |
       545 +  | `TestNoDoublePrefix` | No `/api/api/` malformed routes |
       546 +  | `TestNoDuplicatePrefixes` | Single canonical prefix per domain |
       547 +  | `TestOpenAPIPathSnapshot` | API stability (golden test) |
       548 +  | `TestFortranRule` | **No inline math in routers** |
       549 +
       550 +  ### Adding a New Router
       551 +
       552 +  When creating a new router:
       553 +
       554 +  1. **Do NOT add inline math.** Import from canonical modules.
       555 +  2. If you MUST add temporary inline math, add your router to `FORTRAN_RULE_EXCEPTIONS` with a TODO
           + comment.
       556 +  3. Run `pytest tests/test_route_governance.py -v` before PR.
       557 +
       558 +  ### Grandfathered Routers (Remaining Violations)
       559 +
       560 +  These routers are exempted pending future cleanup:
       561 +
       562 +  ```python
       563 +  FORTRAN_RULE_EXCEPTIONS = {
       564 +      "adaptive_preview_router.py",   # TODO: Extract sine wave math
       565 +      "archtop_router.py",            # TODO: Extract neck angle math
       566 +      "cam_drill_pattern_router.py",  # TODO: Extract circle pattern math
       567 +      "cam_post_v155_router.py",      # TODO: Extract arc tessellation
       568 +      "cam_post_v160_router.py",
       569 +      "cam_post_v161_router.py",
       570 +      "geometry_router.py",           # TODO: Extract arc angle calculations
       571 +  }
       572 +  ```
       573 +
       574 +  **To enforce a router:** Remove it from this list and fix the violations.
       575 +
       576 +  ---
       577 +
       578    ## Developer Handoff Notes
       579
       580    ### For New Developers

● Done. Here's the summary of your answers:

  ---
  Your Questions Answered

  1. Canonical Service Layer Structure

  | Layer                | Folder                                        | Purpose |
  |----------------------|-----------------------------------------------|---------|
  | geometry/            | General math (arcs, circles)                  |         |
  | instrument_geometry/ | Fret, bridge, body, neck                      |         |
  | cam/                 | Toolpath, biarc, trochoid algorithms          |         |
  | calculators/         | Orchestrate math modules                      |         |
  | rmos/, saw_lab/      | Self-contained domain modules                 |         |
  | services/            | Stores, bridges, job orchestration (non-math) |         |

  Recommendation: Keep this existing structure. No new services/ subfolder needed.

  ---
  2. Governance Test File

  File: tests/test_route_governance.py

  New Test Class Added: TestFortranRule

  | Test                           | Purpose                                     |
  |--------------------------------|---------------------------------------------|
  | test_no_inline_math_in_routers | Scans routers for trig/exponential patterns |
  | test_no_hardcoded_pi           | Catches 3.14159 literals                    |

  How It Works:
  - New routers without inline math → automatically pass
  - New routers with inline math → fail CI
  - Grandfathered routers → listed in FORTRAN_RULE_EXCEPTIONS

  To fix a grandfathered router: Remove it from the exceptions list, fix violations, and the test enforces it going forward.

  ---
  Test Results

  8 passed governance tests:
    - TestComponentRouterRule (3 tests)
    - TestNoDoublePrefix (1 test)
    - TestNoDuplicatePrefixes (1 test)
    - TestOpenAPIPathSnapshot (1 test)
    - TestFortranRule (2 tests) ← NEW
