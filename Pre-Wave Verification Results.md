Pre-Wave Verification Results
✅ Test 1: Untracked Files
Result: 752+ untracked files confirmed. First 60 shown include:

.github/ISSUE_TEMPLATE/bundle_*.md — 44 bundle templates
.github/workflows/*.yml — 5 workflow files
.vscode — VS Code settings
Various markdown docs
Status: As expected from earlier audit.

✅ Test 2: Imports of Critical Directories
Result: 26 import statements depend on the critical directories:

Import Pattern	Files Using It
from app.calculators.*	12 files (tests + subpackages)
from app.data.tool_library	4 files (tooling_router, tests)
from app.data.validate_tool_library	2 files (tooling_router, tests)
Critical Finding: tooling_router.py directly imports from app.data.tool_library — this router will break if data isn't committed.

⚠️ Test 3: Suspect app/app/ Directory
Result: Directory EXISTS with nested data:


services/api/app/app/└── data/    └── cnc_production/        ├── saw_runs.json        └── saw_telemetry.json
Issue: This is a namespace collision (app.app.data). However, the files are JSON data files, not Python modules.

Comparison:

Path	Contents
app/app/data/cnc_production/	2 JSON files (saw_runs, saw_telemetry)
cnc_production	Same 2 JSON files (likely duplicate)
⚠️ Test 4: ltb_calculators Usage
Result: ACTIVELY USED by ltb_calculator_router.py:


from ..ltb_calculators import (...)
Finding: This is NOT a duplicate of calculators. They serve different purposes:

Package	Purpose	Modules
ltb_calculators/	General-purpose calculators	basic, financial, fraction, scientific, luthier
calculators	CAM/RMOS calculators	fret_slots, temperaments, bracing, saw, rosette, wiring
Recommendation: Change audit document — ltb_calculators should be Promoted (Wave 1), not archived.

🔴 Questions Before Proceeding
app/app/ directory — The nested structure contains 2 JSON files that may also exist in cnc_production. Should I:

A) Delete app/app/ entirely (if files are duplicates)
B) Merge unique files into data then delete
C) Leave as-is for now (defer to Wave 6)
ltb_calculators/ — The audit marked this as "Archive" but it's actively imported by a router. Should I:

A) Promote to Wave 1 (Core) alongside calculators
B) Keep it as separate Wave (after calculators)
C) Merge into calculators package
Wave 0 Commit — The .gitignore fix is staged. Should I commit it now before continuing, or bundle it with Wave 0.5 (modified files)?

Test files in tests — The audit says move to tests. Should I:

A) Move them during Wave 4 as planned
B) Leave in place (FastAPI convention allows app/tests/)
C) Move now before starting waves