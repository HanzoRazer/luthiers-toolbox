1. What the inventory is telling us
1.1 Two competing client trees

You effectively have two frontends:

Primary / new: packages/client/src/ (monorepo style, 148 files, 44 tracked)

Legacy / orphan: client/src/ (standalone style, 188 files, only 3 tracked in Git)

So the “real” app is under packages/client, but a huge amount of older UI and calculators is stranded under client/.

1.2 The orphaned goldmine

There are 133 files that exist only in client/src/, and many of them are exactly the “brain” of the ToolBox UI:

Toolbox calculator hub (38 components)
client/src/components/toolbox/*.vue – things like:

ArchtopCalculator.vue

BracingCalculator.vue

BridgeCalculator.vue

CNCROICalculator.vue

RosetteDesigner.vue

ScaleLengthDesigner.vue

ScientificCalculator.vue

WiringWorkbench.vue
→ This is your entire calculator / shop-brain front end, and it’s not present in packages/client.

Compare system (19 files)
client/src/components/compare/ – math helpers, behaviors, specs, and a README. This looks like the fully built compare engine (pan/zoom, diff, layers) that the new tree doesn’t fully have.

Rosette UI, labs, presets, CAM dashboards, SawLab dashboard, etc.
Those views and components exist only in client/src/views/*, client/src/utils/*, client/src/labs/*, etc.

In other words: a lot of the front-end expression of RMOS, Art Studio, Saw Lab, calculators, wiring, etc., is alive only in this orphan folder.

1.3 Duplicates / drift

You also have 55 files with the same names in both client/src and packages/client/src (e.g., ArtStudio.vue, CompareLabView.vue, SawLabShell.vue, CamPipelineRunner.vue, etc.).

That means:

Some components evolved in the monorepo (packages/client/src/…)

Their older or alternate versions still sit in client/src/…

It’s not safe to just delete client/ — we’d lose unique stuff and risk losing better versions of some components.

2. The core problem in plain language

Right now you effectively have:

One canonical backend (services/api, RMOS 2.0, calculators, Saw Lab, etc.)

Two competing frontends:

The “real” one (packages/client/src) that is wired into your current build.

A “shadow” one (client/src) that still holds a lot of calculators, labs, and visual tools that never made it into the monorepo structure.

The risk:

If you ignore client/src, you lose a ton of work (calculators, compare engine, labs).

If you try to keep both, things stay confusing and fragile forever.

We need a controlled, one-time migration from client/src into packages/client/src, then retire client/.

3. Concrete plan to resolve this

Think of this as a focused “Wave: Orphaned Client Merge”.

Phase 0 – Safety Net

Commit the inventory doc (already done on feature/rmos-2-0-skeleton, keep it there).

Zip the entire client/ folder and stash it somewhere safe (outside the repo) as a hard backup.

Make sure you’re working on feature/rmos-2-0-skeleton for all of this.

That way, no matter what happens, you always have a frozen copy of the old UI.

Phase 1 – Declare the canonical client tree

Decision (and we should stick to it):

Canonical frontend root = packages/client/src/

client/src/ = legacy staging folder to be mined, then removed

We will never point Vite / npm / build scripts at client/ again. Everything we save from it will be merged into packages/client/src, in a structured way.

Phase 2 – Migrate the “Toolbox calculators” as a single bundle

Create:

packages/client/src/components/toolbox/


Then:

Copy all 38 toolbox components from client/src/components/toolbox/ into that new directory.

Don’t try to fix imports yet; just get the files in place.

Commit that as a single logical change:
feat(client): migrate toolbox calculators from legacy client

Later, we’ll create a Toolbox Hub route so they’re accessible again.

Phase 3 – Migrate the Compare system (this is a subsystem)

The compare engine is clearly a “real subsystem” with tests and utilities.

Do this:

Under packages/client/src/components/compare/, compare each file with the version in client/src/components/compare/.

Where packages/client is missing a file → copy from client/src.

Where both exist but differ → keep the newer/cleaner one, but:

Add a // TODO: merged from legacy compare note where needed.

Move the compare composables and utils:

client/src/composables/useCompareState.ts → packages/client/src/composables/useCompareState.ts

client/src/utils/compareReportBuilder.ts → packages/client/src/utils/compareReportBuilder.ts

Copy the compare tests into the monorepo test tree so your test runner starts to see them again.

Commit as:
feat(client): consolidate compare engine into packages/client

Phase 4 – Migrate utilities and math

This is where a lot of the instrument math and wiring helpers live:

client/src/utils/curvemath*.ts

client/src/utils/neck_generator.ts

client/src/utils/switch_validator.ts

client/src/utils/treble_bleed.ts

client/src/utils/math/compoundRadius.ts, curveRadius.ts (+ tests)

Plan:

Create / confirm:

packages/client/src/utils/
packages/client/src/utils/math/


Copy those utility files into packages/client/src/utils, preserving subfolders.

Fix internal imports (most will be simple ../utils/… tweaks).

Keep this logical commit small:
feat(client): migrate instrument + wiring utilities to monorepo

This aligns cleanly with the Instrument Geometry / Wiring calculators we just specced on the backend: front end calls these to display results, backend calculators remain the source of truth.

Phase 5 – Migrate key views and dashboards

From the orphaned inventory, pick the views that matter most:

ArtStudioDashboard.vue

ArtStudioRosetteCompare.vue

CAMDashboard.vue

SawLabDashboard.vue

PresetHubView.vue

CamProductionView.vue

LabsIndex.vue

Plan:

Copy them into packages/client/src/views/… under matching or cleaned-up folders.

Update packages/client/src/router/index.ts (or equivalent) to add routes for:

/toolbox → Toolbox hub

/saw-lab → SawLabDashboard

/cam/dashboard → CAMDashboard

/art/dashboard → ArtStudioDashboard

Commit as:
feat(client): restore dashboards and labs into monorepo views

Phase 6 – G-Code / DXF / Wiring front-end hooks

You have front-end components that map directly to the backend work we just did in Waves 7–11:

GCodeExplainer.vue

DXFCleaner.vue

DxfPreflightValidator.vue

WiringWorkbench.vue

HardwareLayout.vue

Plan:

Place them under:

packages/client/src/components/toolbox/


(they’re part of the “Toolbox” brand)

Later, wire their API calls to:

/api/ai-cam/explain-gcode

/api/export/dxf or the DXF cleaner endpoint

/api/calculators/wiring/... once we bring that router online

For now, restoring the components is enough so you don’t “lose” them when you commit.

Phase 7 – Final cleanup & retirement of client/

Only after:

Toolbox components migrated

Compare system merged

Utilities moved

Key views moved

API modules reconciled

…do we:

Do a pass through client/src:

Anything still unique but clearly experimental → either move into packages/client/src/labs/legacy/ or explicitly archive by zipping.

Once you’re absolutely confident, delete the client/ folder from the working tree on this feature branch.

Commit as:
chore(client): remove legacy client tree (migrated to packages/client)

Git history will still keep the old files; your ZIP backup is the extra belt-and-suspenders.

4. How this ties back to the bigger picture

This orphan clean-up isn’t just housekeeping. It directly supports:

RMOS 2.0 – the client now has a single, clean entry point to RMOS routes and calculators.

Calculator Spine – front-end utilities match the backend calculator modules.

Saw Lab 2.0 – Saw views/components (SawLabDashboard, SawLab panels) are restored in the primary client tree.

Art Studio & Wave 11 – G-code explainer and compare engine become the front-end face of the AI CAM work we just structured.

Once this is done, future work is simpler: every new feature assumes packages/client/src as the one true UI, and Copilot/LLMs don’t get confused by the duplicate trees.