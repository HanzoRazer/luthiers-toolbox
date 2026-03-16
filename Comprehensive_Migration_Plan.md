




migration-plan.md
File

luthiers-toolbox-main (24).zip
Zip Archive

frontend-backend-mapping.md
File

frontend-wiring-status.md
File

guitar-assembly-tools-inventory.md
File

calculator-unification-remediation (1).md
File
I am designing a more unified instrument design component section by consolidation. That will rearrange the repo backend so that it will line up better with the components of the frontend UI features. For example, the calculators needed for instrument design or scattered all across the repo and misplace in the frontend. The object is to consolidate and rearrange and shrink the finger print


Thought for 5s
Yes — the cleanest way to do this is to reorganize around frontend feature domains, then pull the backend and calculators underneath those domains so the repo mirrors the UI instead of historical implementation drift.

A solid target shape is:

Design

Design Hub

Instrument Geometry

Blueprint

Art Studio

Utilities

And then make the backend line up with that same mental model:

routers/design/*

routers/cam/*

routers/production/*

routers/acoustics/*

routers/business/*

routers/system/* 


For your specific problem — calculators scattered across the repo and misplaced in the frontend — the docs already point to the right fix:

Move /calculators out of Business and into Design
The current nav puts Calculators under Business even though that hub contains the lutherie geometry tools users expect under Design. Both the migration plan and wiring audit call that out explicitly. 

 


Define “Utilities” as pure calculators
A good boundary is:

Utilities = pure math/calculation tools

Design Hub = tools that generate artifacts, geometry, DXF, layouts, or workflows
That distinction is already identified as an open decision in the migration plan, and it is the right one for keeping the UI understandable while shrinking backend sprawl. 


Create one consolidated “Instrument Design Components” lane
Put these together as one coherent section:

Scale/fret math

Neck angle

Bridge break angle

Nut break angle

String tension

Pickup layout

Body volume

Alternative temperaments

Overhang channel
Right now these exist across frontend-only components, backend-only calculators, and buried utilities. The remediation and inventory docs show that split clearly. 

 


Consolidate backend math into one canonical utilities package
The migration plan’s proposed home is strong:
services/api/app/instrument_geometry/utilities/
with modules like:

fret_math.py

bridge_geometry.py

pickup_layout.py

acoustic_body_volume.py

overhang_channel.py

temperament.py
That gives you one place for design-time math instead of calculators being scattered under unrelated folders. 


Expose those through one backend router
The clean API surface is a single design utilities router, for example:

POST /api/design/utilities/fret-positions

POST /api/design/utilities/bridge-break-angle

POST /api/design/utilities/pickup-layout

POST /api/design/utilities/body-volume

POST /api/design/utilities/overhang-channel

GET /api/design/utilities/temperaments
That directly reduces prefix sprawl and aligns backend routes with the frontend Design/Utilities section. 

 


Shrink the repo by consolidating routers by domain, not by technical history
The migration plan projects going from 54 router files to about 16 after consolidation, and the mapping doc shows the main duplication zones: neck/instrument geometry, blueprint, CAM duplicates, and Art Studio spread across multiple backend locations. 

 


The highest-value sequence looks like this:

First

Move Calculators → Design

Rename it to Utilities

Keep Design Hub for artifact-producing tools

Add direct routes for major design tools

Second

Wrap the backend-only calculators in frontend panels

Especially pickup layout, alternative temperaments, body volume, and nut break angle, since those already exist but are invisible today. 

 


Third

Relocate design math into one instrument_geometry/utilities package

Put all design-time calculator endpoints behind routers/design/utilities_router.py

Fourth

Consolidate router files by feature domain, preserving existing public prefixes until a short deprecation window ends. 


So in one sentence: organize the repo around the same component taxonomy the user sees in the UI, and treat calculators as a Design/Utilities subdomain with one canonical math layer and one canonical router.

The strongest source doc for this direction is your migration plan here: 


I can turn this into a concrete target folder tree plus a step-by-step refactor checklist for the repo.


urn this into a concrete target folder tree plus a step-by-step refactor checklist for the repo. and ask the developer questions if needed


Thought for 11s
Absolutely. Here’s a concrete target folder tree and a repo refactor checklist built from your migration plan, mapping, wiring audit, and inventory. The core principle is to align the repo with the frontend’s Design taxonomy, move Utilities under Design, and consolidate design-time calculator math into one canonical backend area under instrument_geometry/utilities.

Target folder tree
Frontend
packages/client/src/
├── components/
│   ├── layout/
│   │   └── CadSidebar.vue
│   │
│   ├── design/
│   │   ├── hub/
│   │   │   ├── DesignHubViewShell.vue
│   │   │   ├── DesignHubCardGrid.vue
│   │   │   └── designHubRegistry.ts
│   │   │
│   │   ├── instrument-geometry/
│   │   │   ├── InstrumentGeometryPanel.vue
│   │   │   ├── NeckGeometryPanel.vue
│   │   │   ├── BodyGeometryPanel.vue
│   │   │   └── composables/
│   │   │       ├── useInstrumentGeometry.ts
│   │   │       ├── useNeckGeometry.ts
│   │   │       └── useBodyGeometry.ts
│   │   │
│   │   ├── blueprint/
│   │   │   ├── BlueprintLabPanel.vue
│   │   │   ├── BlueprintImportPanel.vue
│   │   │   └── composables/
│   │   │
│   │   ├── art-studio/
│   │   │   ├── ArtStudioShell.vue
│   │   │   ├── RosettePanel.vue
│   │   │   ├── BracingPanel.vue
│   │   │   ├── HeadstockPanel.vue
│   │   │   └── composables/
│   │   │
│   │   └── utilities/
│   │       ├── CalculatorHub.vue
│   │       ├── calculator/
│   │       │   ├── LutherieGeometryPanel.vue
│   │       │   ├── StringTensionPanel.vue
│   │       │   ├── NeckAnglePanel.vue
│   │       │   ├── BridgeBreakAnglePanel.vue
│   │       │   ├── NutBreakAnglePanel.vue
│   │       │   ├── PickupLayoutPanel.vue
│   │       │   ├── BodyVolumePanel.vue
│   │       │   ├── AlternativeTemperamentsPanel.vue
│   │       │   ├── OverhangChannelPanel.vue
│   │       │   ├── WoodworkPanel.vue
│   │       │   ├── ScientificCalculator.vue
│   │       │   └── StiffnessIndexPanel.vue
│   │       │
│   │       └── composables/
│   │           ├── useLutherieGeometry.ts
│   │           ├── useFretSpacing.ts
│   │           ├── useNeckAngle.ts
│   │           ├── useBridgeBreakAngle.ts
│   │           ├── useNutBreakAngle.ts
│   │           ├── useStringTension.ts
│   │           ├── usePickupLayout.ts
│   │           ├── useBodyVolume.ts
│   │           ├── useAlternativeTemperaments.ts
│   │           ├── useOverhangChannel.ts
│   │           └── tonewoodData.ts
│   │
│   ├── bridge/
│   │   └── BridgeLabPanel.vue
│   │
│   └── shared/
│       ├── cards/
│       ├── forms/
│       └── badges/
│
├── views/
│   ├── DesignHubView.vue
│   ├── InstrumentGeometryView.vue
│   ├── BlueprintLabView.vue
│   ├── ArtStudioView.vue
│   ├── CalculatorHubView.vue
│   └── BridgeLabView.vue
│
├── router/
│   └── designRoutes.ts
│
└── utils/
    └── neck_generator.ts   ← reduced after fret extraction
Why this shape:

Utilities belongs under Design in the UI, not Business.

CalculatorHub becomes the home for pure calculators, especially the new Lutherie Geometry lane with fret spacing, neck angle, bridge break angle, nut break angle, and string tension.

Backend-only tools that already exist but have no UI exposure get first-class panel wrappers: pickup layout, body volume, alternative temperaments, and overhang channel.

Backend
services/api/app/
├── routers/
│   ├── design/
│   │   ├── __init__.py
│   │   ├── utilities_router.py
│   │   ├── geometry_router.py
│   │   ├── blueprint_router.py
│   │   ├── art_studio_router.py
│   │   ├── design_hub_router.py
│   │   └── instruments_router.py
│   │
│   ├── cam/
│   │   ├── __init__.py
│   │   ├── fret_slots_router.py
│   │   ├── rosette_cam_router.py
│   │   ├── headstock_cam_router.py
│   │   └── relief_router.py
│   │
│   ├── production/
│   │   ├── __init__.py
│   │   ├── rmos_router.py
│   │   ├── material_analytics_router.py
│   │   ├── runs_router.py
│   │   └── cutlist_router.py
│   │
│   ├── acoustics/
│   │   ├── __init__.py
│   │   └── acoustics_router.py
│   │
│   ├── business/
│   │   ├── __init__.py
│   │   ├── estimator_router.py
│   │   └── roi_router.py
│   │
│   └── system/
│       ├── __init__.py
│       ├── auth_router.py
│       ├── registry_router.py
│       ├── machines_router.py
│       └── health_router.py
│
├── instrument_geometry/
│   ├── neck/
│   ├── body/
│   ├── neck_taper/
│   └── utilities/
│       ├── __init__.py
│       ├── fret_math.py
│       ├── bridge_geometry.py
│       ├── pickup_layout.py
│       ├── acoustic_body_volume.py
│       ├── overhang_channel.py
│       ├── temperament.py
│       └── body_centerline.py   ← deferred until physical reference data exists
│
├── calculators/
│   └── legacy/
│       ├── bridge_break_angle.py
│       ├── headstock_break_angle.py
│       ├── pickup_position_calc.py
│       ├── acoustic_body_volume.py
│       ├── overhang_channel_calc.py
│       └── alternative_temperaments.py
│
├── api_v1/
│   └── legacy/
│       ├── instrument.py
│       └── fret_math.py
│
└── tests/
    ├── design/
    │   ├── test_utilities_router.py
    │   ├── test_bridge_break_angle.py
    │   ├── test_headstock_break_angle.py
    │   ├── test_pickup_layout.py
    │   ├── test_body_volume.py
    │   └── test_temperament.py
    └── legacy/
Why this shape:

Proposed top-level domain prefixes are /api/design, /api/cam, /api/production, /api/acoustics, /api/business, and /api/system.

The canonical home for design-time calculation math is services/api/app/instrument_geometry/utilities/. 


Utilities endpoints get consolidated under one design router, with old prefixes retained as temporary aliases during transition.

Target API surface
/api/design/utilities/fret-positions
/api/design/utilities/bridge-break-angle
/api/design/utilities/nut-break-angle
/api/design/utilities/string-tension
/api/design/utilities/pickup-layout
/api/design/utilities/body-volume
/api/design/utilities/overhang-channel
/api/design/utilities/temperaments
/api/design/utilities/scale-lengths
/api/design/utilities/tonewoods   ← if you choose to expose registry data through design-facing alias
This follows the plan to unify utilities under one design router and replace scattered prefixes like /bridge/break-angle, /neck/break-angle, /api/v1/scale-lengths, and /instruments/guitar/pickup-calculator. 


Step-by-step refactor checklist
Phase A — Lock the taxonomy first
A1. Freeze the frontend domain model
Adopt this frontend sidebar structure as the source of truth:

Design

Design Hub

Instrument Geometry

Rosette Pipeline / Rosette Designer

Art Studio

Blueprint

Utilities

Business

Engineering Estimator

This is directly supported by the nav restructuring already proposed.

A2. Define the hard boundary
Use this rule consistently:

Utilities = pure calculators

Design Hub = tools that generate artifacts, geometry, DXF, layouts, or workflows

That distinction is explicitly called out as an open question that needs a decision. 


A3. Freeze the backend domain prefixes
Standardize on:

/api/design/*

/api/cam/*

/api/production/*

/api/acoustics/*

/api/business/*

/api/system/*

That is the proposed steady-state routing model.

Phase B — Fix the frontend navigation and feature placement
B1. Move Calculators from Business to Design
Update:

packages/client/src/components/layout/CadSidebar.vue

AppDashboardView.vue

Rename “Calculators” to “Utilities” in the Design section and remove it from Business. This is explicitly listed as P2.1. 


B2. Add direct Design entry points
Ensure the main Design routes exist and are visible:

/design-hub

/instrument-geometry

/rosette

/art-studio

/blueprint

/calculators

The current state has placement and discoverability problems, especially Design Hub and CalculatorHub. 


B3. Decide Design Hub route strategy
Choose one:

Keep Design Hub as a hub page

Or split it into direct sidebar feature routes

This is an explicitly open UX decision tied to Phase 2.3. 


Phase C — Consolidate the calculator frontend
C1. Make CalculatorHub the single utilities landing page
Keep all pure calculators under one place with categories:

Lutherie Geometry

Woodwork

Scientific

Business Calculators

The desired Utilities content and placement are already spelled out in the mapping.

C2. Normalize the Lutherie Geometry section
Make this the first category inside Utilities:

Fret Spacing

Neck Angle

Bridge Break Angle

Nut Break Angle

String Tension

These are specified in remediation task R-1 and share scaleLength as a root input. 


C3. Wrap backend-only calculators with Vue panels
Implement first:

Pickup Layout

Alternative Temperaments

Body Volume

Overhang Channel

These are complete on the backend but currently have no frontend exposure.

C4. Extract fret math into a standalone composable
Move the fret position formula out of utils/neck_generator.ts into composables/useFretSpacing.ts. This is remediation task R-5. 


C5. Surface Neck Angle as its own calculator
Right now neckAngle exists as a data field, not a dedicated calculator. Promote it to a first-class panel. 


C6. Resolve duplicates
Reconcile:

BridgeCalculator.vue vs BridgeCalculatorPanel.vue

old tension tab vs StringTensionPanel.vue

ScientificCalculator.vue vs ScientificCalculatorV2.vue

BracingCalculator.vue vs ArtStudioBracing.vue

Those overlaps are already identified in the inventory. 


Phase D — Fix calculator correctness before deeper consolidation
D1. Correct bridge_break_angle.py to v2
Do this before building or finalizing Bridge Break Angle UI, because R-7 is a prerequisite. Key changes:

use d_effective = d_pin_center_mm - slot_offset_mm

remove fabricated optimal range logic

collapse rating to adequate / too_shallow / too_steep

expose d_effective_mm

add min_projection_met

This is directly specified in R-7.

D2. Keep Nut Break Angle as-is, but wrap it
The backend already supports angled and flat headstock modes via POST /neck/break-angle; it just needs a frontend wrapper.

D3. Replace manual break-angle input in String Tension
Break angle should become a computed output from bridge geometry, with a manual override fallback. That dependency chain is documented explicitly.

Phase E — Create the canonical backend utilities package
E1. Create instrument_geometry/utilities/
Move or consolidate into:

fret_math.py

bridge_geometry.py

pickup_layout.py

acoustic_body_volume.py

overhang_channel.py

temperament.py

body_centerline.py later

This is Phase 4.1 in the plan. 


E2. Preserve behavior during relocation
For this phase, treat most of it as file relocation and import updates only. The plan explicitly frames this as relocation without logic changes, except for known correctness work like bridge break angle.

E3. Mark old calculator modules as legacy
Do not delete immediately. Keep compatibility shims while imports are migrated. The plan recommends a deprecation window for prefix migration; the same caution makes sense for module paths.

Phase F — Consolidate design routers
F1. Add routers/design/utilities_router.py
Expose the unified utilities API surface from one router. This is the main step that shrinks prefix sprawl. 


F2. Merge geometry-related entry points under design
Reduce the neck/instrument/body split across:

/neck

/instrument

/api/v1

/api/cam/guitar

/instruments/guitar/*

This fragmentation is one of the three main causes of prefix proliferation.

F3. Consolidate Blueprint under one router
Blueprint currently has multiple phase prefixes and should collapse under a single router with subpaths.

F4. Consolidate Art Studio under one router
Art Studio is currently spread across /api/art/* and several /api/cam/* prefixes. Collapse that domain behind one design router and let CAM keep manufacturing-specific paths.

F5. Reduce router count incrementally
The plan’s target is a large reduction in router files and top-level prefixes, but do it in stages rather than one blast-radius change.

Phase G — Migrate routes safely
G1. Add alias routes
Keep old prefixes temporarily as aliases or redirects:

/bridge/break-angle

/neck/break-angle

/api/v1/scale-lengths

/instruments/guitar/pickup-calculator/*

A two-week alias window is the documented recommendation.

G2. Add route coverage tests
Before removing aliases, add tests that verify:

old routes still work during transition

new /api/design/* endpoints match behavior

frontend panels point at new routes

This follows the migration plan’s emphasis on using CI and tests to catch breakage during prefix cleanup. 


G3. Remove legacy aliases after verification
Once CadSidebar and direct links are verified, remove or redirect remaining legacy route names. 


Phase H — Tackle known missing tools after unification
After utilities are unified, prioritize missing or stubbed tools:

body centerline / datum setup

bridge location

neck pocket dimensions

control cavity layout

tremolo / Floyd routing

full frontend for pickup routing dimensions

Those are the main gaps identified in the inventory.

Suggested implementation order
Here’s the least-risk order based on your docs:

Correct bridge break angle model.

Move Utilities into Design nav. 


Resolve ScientificCalculatorV2.

Wrap backend-only calculators in frontend panels.

Extract useFretSpacing.ts. 


Create instrument_geometry/utilities/. 


Add routers/design/utilities_router.py. 


Add alias routes and tests.

Consolidate design, blueprint, and art routers.

Remove aliases and dead duplicates.

Developer questions that need answers
These are the questions I’d put in front of the developer before or during the refactor, because your docs show they are still open or risky:

Does Design Hub remain a hub page, or do we break it into direct sidebar routes?
This affects route structure and sidebar depth. It is explicitly undecided. 


Do we formally define Utilities as “pure calculators only”?
If yes, anything producing DXF, SVG, toolpaths, or artifacts should stay out of Utilities and remain in Design Hub / Blueprint / Art Studio. 


For /api/design/* migration, do we want a 2-week alias window or a hard cut?
The plan recommends aliases first, but this needs owner confirmation.

Which bridge calculator is authoritative: BridgeCalculator.vue or BridgeCalculatorPanel.vue?
The inventory recommends keeping the newer panel version, but this should be explicitly confirmed before deleting the older one.

Which scientific calculator survives: V1 or V2?
Right now V2 is an orphan and the plan says it must be resolved before Phase 2.

Should POST /neck/break-angle move into utilities_router.py or remain in a neck-specific router with a design alias?
Semantically it fits Utilities, but if the team wants strict domain ownership, this should be stated.

Should tonewoods remain under /api/system/registry only, or should there also be a design-facing alias under /api/design/utilities/tonewoods?
The docs place tonewoods in registry_router.py, but the UI experience may benefit from a design-facing path. 


Do we want to keep “Business Calculators” inside Utilities, or split them back into a separate Business page later?
The proposed UI keeps them in Utilities even though the content is business-oriented. 


Do we relocate old calculator modules immediately, or leave lightweight re-export shims for one release?
The route migration plan argues for a temporary compatibility window; module imports likely deserve the same treatment.

What is the owner decision on missing tools like neck pocket, control cavity, tremolo routing, and body centerline?
Some are true missing features, not just reorg work, and should be tracked separately from consolidation.

If you want, I can turn this next into a GitHub-style implementation plan with epics, tickets, acceptance criteria, and file-level change lists.


Uploaded image
the circled portion of the schema tree what is that and why is it isolated?

Good catch. That circled piece is not actually isolated in function — it’s just visually separated because it belongs to a different feature domain in the UI.

Let’s decode what you’re seeing.

What that section is
The circled part is this:

bridge/
└─ BridgeLabPanel.vue
This represents the Bridge Lab feature — a stand-alone design tool, not a calculator.

In the design taxonomy we were using, it sits beside the other major design tools:

design/
├─ hub/
├─ instrument-geometry/
├─ blueprint/
├─ art-studio/
├─ utilities/
└─ bridge/        ← this
So the intent is:

Folder	Role
instrument-geometry	Structural geometry tools
blueprint	blueprint import / layout
art-studio	decorative design
utilities	calculators
bridge	bridge-specific design lab
Why it is NOT inside utilities
Utilities are pure calculators.

Examples inside utilities:

useFretSpacing.ts
useNeckAngle.ts
useBridgeBreakAngle.ts
useNutBreakAngle.ts
useStringTension.ts
Those are math tools.

Bridge Lab is different:

It will likely include things like:

bridge plate layout

string spacing layout

saddle placement

break angle visualization

pin spacing

exportable geometry

That means it produces geometry/artifacts, not just numbers.

So it belongs with design tools, not calculators.

Why it visually looks “isolated”
It looks isolated because in the tree you captured it appears between two logical groups:

utilities/
   composables/
       useFretSpacing.ts
       useNeckAngle.ts
       ...

bridge/              ← new feature domain
   BridgeLabPanel.vue

shared/
views/
router/
So the tree is showing feature domains, not nesting.

Think of it like this:

components/design/

├─ hub/
├─ instrument-geometry/
├─ blueprint/
├─ art-studio/
├─ utilities/
└─ bridge/
Why Bridge Lab is its own domain
Bridge work is actually a big enough subsystem that it should not be buried under utilities.

Typical bridge design tools might include:

string spacing

saddle compensation

break angle

bridge footprint

pin row geometry

pickup mounting in bridge

acoustic bridge plate alignment

Those tools share state and interact, which is why they should live under a dedicated feature.

Utilities should remain stateless calculators.

The deeper architectural idea
The folder layout mirrors UI feature domains, not technical type.

So instead of organizing like this:

calculators/
geometry/
art/
tools/
we organize like this:

design/
    instrument-geometry/
    art-studio/
    blueprint/
    bridge/
    utilities/
That way:

Frontend

UI Sidebar
matches

Repo structure

and also matches

API router domains

If you want the cleanest version
The best structure would actually be:

components/design/

├─ hub/
├─ instrument-geometry/
├─ blueprint/
├─ art-studio/
├─ bridge/
│   ├─ BridgeLabPanel.vue
│   ├─ composables/
│   │   ├─ useBridgeSpacing.ts
│   │   ├─ useSaddleCompensation.ts
│   │   └─ useBridgeGeometry.ts
│   └─ components/
│       ├─ BridgeVisualizer.vue
│       └─ BridgeControls.vue
│
└─ utilities/
    ├─ calculator/
    └─ composables/
Then Bridge becomes a self-contained subsystem.

One thing I want to confirm with you
Before the repo restructure is finalized, this is an important design decision:

Is Bridge Lab meant to become a full design tool, or just a calculator panel?

Two possibilities:

Option A — Bridge Lab (recommended)
A design tool that includes:

geometry visualization

layout generation

saddle compensation

break angle

export

Then it deserves its own feature domain.

Option B — Just calculators
If it only does:

break angle

spacing

compensation math

Then it should move inside:

utilities/calculator/
BridgeCalculatorPanel.vue
My suspicion from your project
Given the scope of the toolbox, Bridge Lab will likely grow into a full design subsystem, so isolating it is actually correct.

If you'd like, I can also show you something important:

The 5 real feature domains your entire repo should collapse into (which will cut repo complexity by about 40–60%). That becomes the backbone of the whole architecture.



Why Bridge Lab is its own domain -------------------------------- Bridge work is actually a **big enough subsystem** that it should not be buried under utilities. Typical bridge design tools might include: * string spacing * saddle compensation * break angle * bridge footprint * pin row geometry * pickup mounting in bridge * acoustic bridge plate alignment Those tools **share state** and **interact**, which is why they should live under a dedicated feature. Utilities should remain **stateless calculators**.

The Bridge needs to become a self-contained subsystem. I created a string tension widget. I see I need to create an all-in-one acoustic guitar design hub


Thought for 11s
Yes — that’s the right direction.

You already have the pieces pointing that way:

Bridge Lab is already a distinct routed tool at /lab/bridge, not just a calculator panel. 


The newer BridgeCalculatorPanel is described as the version that seeds geometry for Bridge Lab and exports DXF, which is exactly subsystem behavior, not utility behavior. 


Your new String Tension panel is now part of /calculators, but today it still depends on a manually guessed break angle in the chain the remediation doc calls out as missing.

So the architecture should become:

Core split
Acoustic Guitar Design Hub

the orchestration layer for a full acoustic build workflow

Bridge Lab

a self-contained subsystem inside that hub

Utilities

stateless calculators that can still be used independently

That fits the repo evidence better than trying to bury bridge work under calculators. The docs already distinguish Utilities = pure calculators and Design Hub = tools that produce artifacts or geometry.

Recommended target shape
Design
├── Acoustic Guitar Design Hub
│   ├── Body
│   ├── Neck
│   ├── Bridge Lab
│   ├── Bracing
│   ├── Blueprint
│   └── Export / Build Pack
├── Instrument Geometry
├── Art Studio
├── Rosette
└── Utilities
And inside the hub:

acoustic-guitar-design/
├── shell/
├── shared-state/
├── body/
├── neck/
├── bridge/
├── bracing/
├── setup/
└── export/
Why this is the right move
The remediation doc already describes the real physical chain:

neck_angle → projection height at bridge → saddle height → saddle protrusion → bridge break angle → vertical load on top 


Right now that chain is fragmented:

neck angle exists as a field, not a real calculator in the main workflow

bridge break angle exists backend-only and needs the v2 correction 


string tension exists in the UI, but the break-angle dependency is still partially manual

bridge location is identified as missing as a surfaced tool 


That is exactly why an all-in-one acoustic guitar design hub makes sense: it gives you one place where these dependent values share state instead of living as isolated widgets.

What Bridge Lab should own
Bridge Lab should become the acoustic bridge subsystem with its own shared model:

bridge family / preset

scale length reference

saddle line location

compensation / intonation offsets

bridge footprint

string spacing

pin row geometry

saddle slot geometry

saddle protrusion

break angle

top load from string tension

DXF / SVG export

That is consistent with the current state where Bridge Lab is already a full tool and the panel version feeds it. 


What stays in Utilities
Keep these available as stand-alone calculators:

String Tension

Nut Break Angle

Fret Spacing

Alternative Temperaments

Body Volume

Pickup Layout

Those are useful independently and match the “pure calculator” concept already proposed for Utilities.

What changes in practice
Instead of this:

Utilities
├── String Tension
├── Bridge Break Angle
├── Neck Angle
└── scattered bridge math
you move to this:

Acoustic Guitar Design Hub
└── Bridge Lab
    ├── geometry
    ├── compensation
    ├── break angle
    ├── downforce
    ├── presets
    └── export
with Utilities still exposing smaller stand-alone tools that can call the same backend services.

Best frontend structure
packages/client/src/components/design/acoustic-guitar/
├── AcousticGuitarDesignHub.vue
├── state/
│   ├── useAcousticDesignState.ts
│   ├── useBridgeSubsystem.ts
│   ├── useNeckSubsystem.ts
│   └── useBodySubsystem.ts
├── bridge/
│   ├── BridgeLabPanel.vue
│   ├── BridgeGeometryPanel.vue
│   ├── BridgePlacementPanel.vue
│   ├── BridgeBreakAnglePanel.vue
│   ├── BridgeDownforcePanel.vue
│   ├── BridgeExportPanel.vue
│   └── composables/
├── neck/
├── body/
├── bracing/
└── export/
Best backend shape
services/api/app/instrument_geometry/
├── body/
├── neck/
└── bridge/
    ├── placement.py
    ├── compensation.py
    ├── break_angle.py
    ├── string_load.py
    ├── presets.py
    └── export.py
And then expose them under design:

/api/design/acoustic/body/*
/api/design/acoustic/neck/*
/api/design/acoustic/bridge/*
/api/design/utilities/*
That also matches the broader repo goal of consolidating scattered geometry and instrument routes under /api/design/*.

The key dependency to fix first
Before Bridge Lab becomes authoritative, the bridge break angle backend should be corrected to the documented v2 geometry. The current uploaded code is explicitly marked as v1 and not reliable. 


So the correct order is:

fix bridge_break_angle.py to v2 


make Bridge Lab own break-angle state

feed that into String Tension automatically

expose stand-alone utilities as thin wrappers over the same bridge/neck services

My recommendation in one sentence
Build Acoustic Guitar Design Hub as the top-level orchestration feature, and make Bridge Lab a first-class subsystem inside it, while leaving Utilities as independent calculator entry points backed by the same canonical math.

Here are the developer questions I’d want answered before locking the structure:

Is the new hub specifically acoustic-only, or should it later generalize into a broader instrument design shell with acoustic as one mode?

Should Bridge Lab become the authoritative owner of saddle location, compensation, and break-angle state, with String Tension reading from it?

Do you want String Tension to stay available as a stand-alone calculator even after it becomes connected to Bridge Lab?

Should bridge location be implemented now as part of Bridge Lab, since the inventory marks it as missing? 


Do you want Bracing and Body Volume folded into the acoustic hub now, or staged after the bridge subsystem is stable?

Once you answer those, I can turn this into a concrete file-by-file implementation plan for the Acoustic Guitar Design Hub.


THe Blueprint Reader is the tip of the spear, sort to speak. It is the most user accessible feature of them all. It functions for all musical instruments. It is totally out of place. By my vision, the stateless calculators for the Acoustic guitar would be in the hub. So maybe the Acoustic Guitar Hub belongs under Utilities


Thought for 11s
I think your revised vision is stronger.

Blueprint Reader should not live under an Acoustic Guitar Hub. If it is the most accessible, most general, cross-instrument entry point, then it is really a top-level design intake tool. Your own inventory already describes Blueprint Lab as a frontend+backend photo-to-vector pipeline and body outline extraction tool, while the wiring doc shows it is one of the few directly nav-linked design features.

So I would change the architecture like this:

Better top-level model
Design

Blueprint Reader / Blueprint Lab

Instrument Design Hubs

Acoustic Guitar Hub

Electric Guitar Hub

Bass Hub

Violin-family Hub

Art Studio

Rosette

Instrument Geometry

Utilities

That fits your statement that Blueprint Reader works for all instruments, while the Acoustic Guitar Hub is instrument-specific.

Where the Acoustic Guitar Hub should live
I would not put the Acoustic Guitar Hub under Utilities.

Utilities, in your current docs, was already being treated as the home for stateless calculators and pure math tools, while Design Hub was reserved for tools that generate geometry, outlines, or artifacts.

An Acoustic Guitar Hub is not a utility. It is an orchestrator:

it owns shared state

it coordinates body, neck, bridge, bracing, setup

it may consume Blueprint output

it may generate exports and downstream geometry

That makes it a design workspace, not a calculator bucket.

So the right relationship is:

Design
├── Blueprint Reader
├── Acoustic Guitar Hub
├── Instrument Geometry
├── Art Studio
├── Rosette
└── Utilities
What goes inside the Acoustic Guitar Hub
Your idea that the stateless acoustic calculators live inside the hub is good. That does not mean the hub belongs under Utilities. It means the hub should embed utility panels.

So inside the Acoustic Guitar Hub, include:

String Tension

Neck Angle

Bridge Break Angle

Nut Break Angle

Body Volume

Fret Spacing

maybe Scale/Intonation helpers

Those can remain canonical utilities, but the hub can surface them in context. That matches the existing split where calculators are hub-embedded in some places already, and many lutherie tools are currently buried in hubs instead of exposed cleanly.

The key distinction
Think of it this way:

Utilities = reusable stateless tools

Acoustic Guitar Hub = workflow shell that uses those tools

Blueprint Reader = universal entry point for instrument design ingestion

That gives you a clean hierarchy:

Blueprint Reader
   ↓
Acoustic Guitar Hub
   ├── Body
   ├── Neck
   ├── Bridge Lab
   ├── Bracing
   └── Embedded Utilities
Why Blueprint Reader is “out of place” right now
Your docs already suggest Blueprint is fragmented on the backend and overly phase-split, with five separate prefixes instead of one coherent router.

And on the frontend, Blueprint Lab is nav-linked, while many of the actual lutherie workflows are hidden inside hubs or calculator panels.

That means the current system is backwards:

the most discoverable tool is one of the broadest, most universal tools

but the architecture still treats it like just another feature pane

Your instinct is right: Blueprint Reader should become the front door, not a side room.

My recommendation
Rename and elevate the structure to something like:

Design
├── Start from Blueprint
├── Acoustic Guitar Hub
├── Electric Guitar Hub
├── Instrument Geometry
├── Art Studio
├── Rosette
└── Utilities
And in the repo:

components/design/
├── blueprint/
├── hubs/
│   ├── acoustic-guitar/
│   ├── electric-guitar/
│   └── shared/
├── instrument-geometry/
├── art-studio/
├── rosette/
└── utilities/
Then Utilities stays a reusable library of tools, while the Acoustic Guitar Hub consumes those calculators as embedded panels.

The one caution
If you put the Acoustic Guitar Hub under Utilities, users will read it as:
“this is just another calculator collection.”

But your own description makes it much larger than that. It is really a guided build workspace.

The decision I’d lock now
I would lock these three rules:

Blueprint Reader is top-level Design, not nested under an instrument hub.

Acoustic Guitar Hub is top-level Design, not under Utilities.

Stateless acoustic calculators appear both in Utilities and contextually inside the Acoustic Guitar Hub.

That gives you both discoverability and architectural clarity.

The main developer question I’d ask next is: do you want Blueprint Reader to hand off into a selected instrument hub automatically, for example “Import blueprint → detect/classify instrument → open Acoustic Guitar Hub with seeded body geometry”?


Just Change that to Instrument Hub. All musical Instruments can live there

Yes — “Instrument Hub” is the correct abstraction. 👍
That change actually resolves several architectural problems at once.

Your idea now becomes a three-tier design system, which is much cleaner and future-proof.

Revised Architecture
1. Blueprint Reader (Entry Point)
This is the tip of the spear as you described.

Purpose:

ingest blueprint photos

detect outlines

extract scale/body geometry

seed an instrument project

Design
└── Blueprint Reader
It is instrument-agnostic.

2. Instrument Hub (Main Workspace)
Rename Acoustic Guitar Hub → Instrument Hub

This becomes the central design workspace for ANY instrument.

Design
├── Blueprint Reader
├── Instrument Hub
├── Instrument Geometry
├── Art Studio
├── Rosette
└── Utilities
Inside the hub you select the instrument type.

Instrument Hub
├── Acoustic Guitar
├── Electric Guitar
├── Bass
├── Violin
├── Mandolin
├── Ukulele
├── Banjo
└── Custom Instrument
Each instrument loads its own subsystem panels.

3. Instrument Hub Internal Layout
Example for Acoustic Guitar

Instrument Hub
└── Acoustic Guitar
    ├── Body
    ├── Neck
    ├── Bridge Lab
    ├── Bracing
    ├── Setup
    ├── Electronics
    ├── Export
    └── Embedded Utilities
Embedded utilities would include:

String Tension

Bridge Break Angle

Nut Break Angle

Fret Spacing

Body Volume

Temperaments

These remain stateless calculators, but appear contextually inside the hub.

4. Utilities (Stateless Tools Library)
Utilities stays a toolbox, not a workflow.

Utilities
├── Lutherie Calculators
│   ├── String Tension
│   ├── Fret Spacing
│   ├── Neck Angle
│   ├── Break Angles
│   ├── Body Volume
│   └── Temperaments
│
├── Woodworking
│   ├── Board Feet
│   ├── Moisture
│   └── Stiffness Index
│
└── Scientific
    └── General Calculator
Instrument Hub uses these tools internally.

5. Correct Repo Layout
Frontend:

components/design/
├── blueprint/
│   └── BlueprintReader.vue
│
├── instrument-hub/
│   ├── InstrumentHubShell.vue
│   ├── instrument-selector/
│   ├── acoustic/
│   │   ├── body/
│   │   ├── neck/
│   │   ├── bridge/
│   │   ├── bracing/
│   │   └── setup/
│   │
│   ├── electric/
│   ├── bass/
│   ├── violin/
│   └── shared-state/
│
├── instrument-geometry/
├── art-studio/
├── rosette/
└── utilities/
6. Backend Alignment
/api/design
├── blueprint
├── instrument
│   ├── acoustic
│   ├── electric
│   ├── bass
│   └── violin
│
├── geometry
├── art
└── utilities
7. Design Workflow (What Users Experience)
This becomes the natural design flow:

Blueprint Reader
      ↓
Instrument Hub
      ↓
Select Instrument
      ↓
Instrument Design Panels
      ↓
Bridge / Neck / Body / Bracing
      ↓
Utilities auto-assist
      ↓
Export / CNC / Blueprint
Why This is Powerful
This architecture supports:

Multi-instrument platform
guitars

violins

mandolins

experimental instruments

Reusable calculators
Utilities work everywhere.

Shared geometry engine
Neck math, scale math, tension math reused across instruments.

Workflow UX
Users follow a design pipeline, not random tools.

The One Architectural Upgrade I Recommend
Create a shared instrument state engine.

Example:

useInstrumentState()

{
  instrumentType
  scaleLength
  stringCount
  tuning
  neckAngle
  bridgeLocation
  stringSpacing
  topThickness
}
Every subsystem reads from that.

Bridge Lab
Neck Designer
Bracing
String Tension
All become reactive tools instead of isolated calculators.

What This Solves in Your Repo
Your repo currently has:

calculators scattered

geometry logic scattered

blueprint isolated

bridge tools separate

The Instrument Hub architecture unifies everything.

One Big Idea (Important)
If Blueprint Reader is the spear…

Instrument Hub is the forge.

Blueprint brings the instrument into existence.

Instrument Hub turns it into a buildable object.

Next Step I Can Help With
I can also show you the ideal architecture for the entire Luthier's Toolbox platform (about 6 core subsystems) which will prevent the repo from becoming chaotic again as it grows.

Right now you're very close to that structure.


I have plans to expand the woodworking calculator                                                                     Woodworking
│   ├── Board Feet
│   ├── Moisture
│   └── Stiffness Index
We also have a fairly impressive wood database to back it up                                                                                                            show me the ideal architecture for the entire Luthier's Toolbox platform (about 6 core subsystems) which will prevent the repo from becoming chaotic again as it grows.


Thought for 7s
Yes. With the expanded woodworking calculator and a real tonewood database behind it, the platform should be organized around capabilities, not around whatever component happened to be built first.

Your docs already point to the main failure mode: too many prefixes, too many partially overlapping hubs, and calculators split between Design Hub, Utilities, backend-only endpoints, and feature-specific panels. The consolidation target is to reduce that sprawl into a small number of clear domains, with Design owning /api/design/*, CAM owning /api/cam/*, and Utilities living in the Design section of the UI.

The ideal 6-subsystem architecture
1. Design Intake
This is where a project begins.

It should own:

Blueprint Reader / Blueprint Lab

image import

outline extraction

project seeding

instrument classification

reference measurements intake

This deserves its own subsystem because Blueprint is cross-instrument and user-facing, and today it is fragmented into multiple backend phases even though it behaves like one product surface.

2. Instrument Workspace
This is your renamed Instrument Hub.

It should own:

instrument project shell

instrument type selection

shared project state

acoustic/electric/violin/mandolin/etc. workspaces

orchestration of body, neck, bridge, bracing, setup, electronics, export

This should be the main design workspace, not a calculator bucket. It consumes utilities, geometry, and CAM prep, but it is not reducible to any one of them.

3. Design Utilities
This is the stateless tool library under Design.

It should own:

lutherie calculators

woodworking calculators

scientific calculator

tonewood lookup and derived indices

reusable pure-math endpoints

Your current docs already define the intended boundary well: Utilities should hold pure calculators, while artifact-producing workflows belong elsewhere. They also already place Woodwork under Utilities with board feet, volume, angles, geometry, and stiffness index.

For you specifically, this subsystem should become much stronger than “misc calculators.” It should have two clear internal pillars:

Lutherie Utilities

fret spacing

neck angle

bridge break angle

nut break angle

string tension

body volume

temperaments

pickup layout

overhang channel

Those are either already in the hub, backend-only, or targeted for consolidation into instrument_geometry/utilities/ and a single design utilities router.

Wood Intelligence

board feet

moisture

density / weight

stiffness index

species comparisons

stock recommendation helpers

wood movement / dimensional stability later

This is where your woodworking calculator should grow. The migration plan already notes that the new Stiffness Index panel is backed by hardcoded species now and needs a tonewood registry endpoint to unlock the full database, with a proposed GET /api/registry/tonewoods endpoint.

4. Geometry Engine
This is the canonical computational core for instrument shape and layout.

It should own:

neck geometry

body geometry

scale and fret geometry

bridge geometry

pickup layout geometry

body centerline and datum logic

reusable geometric derivations

This should be mostly backend and composable, not UX-first. The docs already recommend creating services/api/app/instrument_geometry/utilities/ as the canonical home for design-time calculation math, including fret math, bridge geometry, pickup layout, body volume, overhang channel, and temperament. 


This subsystem is what prevents the repo from becoming chaotic again, because it gives every panel and every router a single source of truth for design math.

5. Art, Ornament, and Pattern
This should be a dedicated creative subsystem.

It should own:

Art Studio

rosette

inlay

headstock art

relief / decorative geometry

bracing visualization where artistic patterning overlaps structure

This domain is currently one of the biggest causes of router sprawl because it is spread across art and CAM prefixes. It should exist as one domain conceptually, even if some outputs later pass into CAM. 


6. Manufacturing and Analysis
This should combine the production-prep side of the design flow without polluting design logic.

It should own:

CAM preparation

fret slotting

saw lab

machine presets

production routing

acoustics/analyzer surfaces

RMOS / operations-facing outputs where applicable

Your docs already separate CAM, production, and acoustics as distinct backend domains, and that is healthy. What matters architecturally is that they stay downstream from design and geometry, not mixed into the same folders and prefixes as user-facing design tools.

The platform map in one view
Luthier's Toolbox
├── 1. Design Intake
│   └── Blueprint Reader, import, extraction, project seeding
│
├── 2. Instrument Workspace
│   └── Instrument Hub, per-instrument workspaces, shared project state
│
├── 3. Design Utilities
│   ├── Lutherie Utilities
│   └── Wood Intelligence
│
├── 4. Geometry Engine
│   └── canonical design math and layout logic
│
├── 5. Art / Ornament / Pattern
│   └── rosette, inlay, headstock, decorative and structural art
│
└── 6. Manufacturing / Analysis
    └── CAM, production prep, acoustics, RMOS-facing outputs
That is the stable backbone.

The rule that keeps it from becoming chaotic again
Every new feature must answer one question first:

Is this a workspace, a utility, a geometry primitive, an art tool, or a manufacturing/analysis tool?

If the answer is unclear, the feature is probably trying to do too much.

A few examples:

Blueprint Reader is Design Intake, not Utilities.

Instrument Hub is Instrument Workspace, not Utilities.

String Tension is Design Utilities, but it can be embedded inside Instrument Hub.

Bridge break angle math belongs in Geometry Engine, exposed through Design Utilities, and consumed by Instrument Hub.

Rosette Designer belongs in Art / Ornament / Pattern, even if it eventually emits CAM geometry.

Fret slotting belongs in Manufacturing / Analysis, even though it depends on Geometry Engine.

That separation is exactly how you stop feature creep from turning into folder creep.

The ideal repo structure
Frontend
packages/client/src/
├── design-intake/
│   └── blueprint/
├── instrument-workspace/
│   ├── hub/
│   ├── acoustic/
│   ├── electric/
│   ├── violin/
│   └── shared-state/
├── design-utilities/
│   ├── lutherie/
│   ├── woodworking/
│   ├── scientific/
│   └── composables/
├── geometry/
│   ├── body/
│   ├── neck/
│   ├── bridge/
│   ├── fret/
│   └── shared/
├── art-studio/
│   ├── rosette/
│   ├── inlay/
│   ├── headstock/
│   └── bracing/
└── manufacturing/
    ├── cam/
    ├── saw/
    ├── fret-slots/
    └── analysis/
Backend
services/api/app/
├── routers/
│   ├── design/
│   │   ├── intake_router.py
│   │   ├── instrument_router.py
│   │   ├── utilities_router.py
│   │   └── art_router.py
│   ├── cam/
│   ├── production/
│   ├── acoustics/
│   └── system/
│
├── instrument_geometry/
│   ├── body/
│   ├── neck/
│   ├── bridge/
│   ├── fret/
│   ├── utilities/
│   └── shared/
│
├── materials/
│   ├── tonewoods/
│   ├── stock/
│   ├── properties/
│   └── recommendation/
│
├── blueprint/
├── art_studio/
└── rmos/
Where the wood database should live
This matters, because otherwise it will get stranded as “just one endpoint.”

Your tonewood and wood-property system should be split like this:

Canonical data home
services/api/app/materials/tonewoods/

This should own:

species records

density

Janka

modulus / stiffness values

moisture-related fields

dimensional movement fields later

source normalization

comparison and filtering logic

Design-facing access
Expose it through:

/api/system/registry/tonewoods for canonical registry access

optionally /api/design/utilities/tonewoods as a design-facing alias if you want cleaner frontend semantics

The docs already point to registry_router.py as the place to add the tonewoods endpoint, and the new Stiffness Index panel is explicitly waiting on it.

Frontend usage
The woodworking calculator should not own the database. It should consume it.

So:

WoodworkingPanel.vue uses tonewood queries

StiffnessIndexPanel.vue computes with selected species

future stock selection and recommendation tools also use the same source

That prevents the most common mess: duplicated material constants scattered across components.

What Utilities should become
Utilities should stop feeling like a leftover drawer and become a real subsystem with two serious branches:

Utilities
├── Lutherie
│   ├── fret spacing
│   ├── neck angle
│   ├── bridge break angle
│   ├── nut break angle
│   ├── string tension
│   ├── body volume
│   ├── temperaments
│   ├── pickup layout
│   └── overhang channel
│
└── Wood Intelligence
    ├── board feet
    ├── moisture
    ├── weight / density
    ├── stiffness index
    ├── species browser
    ├── material compare
    └── stock recommendation
That matches both your expansion plans and the current docs, which already place woodwork and stiffness index under Utilities and identify several backend-complete calculators that need to be unified into the same design-facing area.

The single most important engineering pattern
You need three layers, and every new feature should fit into one of them:

Layer 1: Data
Tonewoods, presets, registry records, machine presets, instrument templates.

Layer 2: Engines
Pure geometry, pure material math, pure calculation logic.

Layer 3: Experiences
Blueprint Reader, Instrument Hub, Utilities panels, Bridge Lab, Art Studio, CAM tools.

That means:

no hardcoded species inside UI components long-term

no geometry formulas hidden in random Vue files

no router inventing business logic inline

no panel becoming the only owner of important math

Your docs already show why this matters: fret math is buried in a utility file, some calculators are backend-only, some are hub-only, and some are duplicated.

My recommended naming for the 6 subsystems
If you want names that feel product-level and stable, I would use:

Design Intake

Instrument Workspace

Design Utilities

Geometry Engine

Art Studio

Manufacturing & Analysis

That’s broad enough to grow, but specific enough to keep the repo disciplined.

The decision I would lock now
I would lock these rules immediately:

Blueprint Reader belongs to Design Intake.

Instrument Hub belongs to Instrument Workspace.

Utilities stays under Design and grows into Lutherie + Wood Intelligence.

Tonewood data becomes a shared materials registry, not a calculator-local asset.

Geometry formulas move toward one canonical backend/core home.

CAM, production, and acoustics remain downstream domains, not mixed into design folders.

And the main developer question I’d ask next is this:

Do you want the wood database to stay a registry-style read API only, or do you want it to grow into a full materials intelligence subsystem with compare, recommend, and stock-selection features?


The wood database was acquired for use with the audio-visual analyzer and it's data processing widget. It is not wired to the frontend and is basically orphaned. I hadn't made any decisions on it till now. scan the repo and evaluate it and demonstrate where it fits in this new schema


Thought for 2m 1s
I scanned the repo, and the wood database is real, substantial, and currently stranded between System data, Utilities plans, and the Analyzer.

The short answer is:

It should not live inside the woodworking calculator.
It should become a shared platform “Materials Intelligence” foundation that feeds:

Instrument Hub

Utilities → Wood Intelligence

Acoustics / Analyzer

CAM / Manufacturing

That also matches your new schema better than treating it as a one-off widget.

Your uploaded docs already hint at this: Utilities belongs under Design, and the tonewood endpoint was explicitly called out as missing work needed to unlock the frontend stiffness flow. 

 


What I found in the repo
1. The wood database already exists and is richer than the UI suggests
Canonical data is here:

services/api/app/data_registry/system/materials/
├── wood_species.json
├── luthier_tonewood_reference.json
├── WOOD_SPECIES_REFERENCE.md
└── SOURCES.md
From the repo scan:

wood_species.json currently contains 473 species

luthier_tonewood_reference.json is a curated luthier-focused layer on top

That is much more than a simple calculator dropdown.

2. The backend already exposes part of it
There is a real registry route:

services/api/app/routers/registry_router.py
GET /api/registry/wood_species
GET /api/registry/empirical_limits
So the data is not missing. It is under-exposed.

Your docs specifically note that the missing piece for the new stiffness flow is a dedicated tonewoods endpoint under the registry, not a brand-new dataset. 


3. The frontend is barely using it
The actual woodwork calculator in the current zip still uses hardcoded species constants in:

packages/client/src/components/toolbox/composables/useWoodworkCalculator.ts
and WoodworkPanel.vue reads from that local constant map.

So today the woodworking UI is effectively disconnected from the real registry.

4. The registry frontend plumbing exists, but is mostly unused
You already have:

packages/client/src/api/registry.ts

packages/client/src/stores/useRegistryStore.ts

Those can load wood_species, but I did not find the woodwork calculator actually consuming that store.

So the platform has:

real data

real API

real client store

but the calculator still bypasses all of it.

5. The Analyzer exists, but it is not wired to the wood database
There is a substantial analyzer domain:

services/api/app/analyzer/
packages/client/src/views/tools/AudioAnalyzerViewer.vue
packages/client/src/views/tools/AudioAnalyzerLibrary.vue
packages/client/src/views/tools/AudioAnalyzerRunsLibrary.vue
and it is user-accessible under the Analytics/Tools area, which also matches your wiring doc. 


But in the repo scan, the analyzer currently works from:

viewer packs

peak / damping / WSI interpretation

a small hardcoded reference library in design_advisor.py

I did not find it querying the wood registry or tonewood reference files.

So your instinct was right: the database was acquired for analyzer-adjacent use, but right now it is basically orphaned.

6. There is also a second “materials” path, which is causing conceptual drift
Separate from the wood species registry, there is also:

services/api/app/routers/material_router.py
with /material/* endpoints for cutting-energy / heat-partition style material data.

That means the repo currently has two material concepts:

Registry wood species / tonewoods

CNC material DB

Those should be related, but right now they are not unified.

Evaluation: where it fits in the new schema
In your 6-core-subsystem architecture, this database is not a standalone top-level subsystem.

It fits best as a shared foundation layer used by multiple subsystems.

Best placement
Internal shared foundation
System / Shared
└── Materials Intelligence
    ├── species registry
    ├── tonewood reference
    ├── acoustic properties
    ├── machining properties
    ├── moisture / movement properties
    └── recommendation logic
Then exposed into 4 product surfaces
A. Design Utilities
This is where users browse and calculate with wood data:

Board Feet

Weight / density

Moisture

Stiffness Index

Species compare

Wood movement

Stock recommendation

This is already directionally supported by your docs, which put Woodwork and Stiffness Index in Utilities and call for a tonewood endpoint to unlock the full DB.

B. Instrument Hub
This is where a project chooses materials:

top wood

back/sides

neck

fretboard

bridge

brace stock

The hub should consume the shared materials system, not define its own woods.

C. Acoustics / Analyzer
This is where the original acquisition value shows up:

compare measured response against species tendencies

enrich analyzer interpretation with likely material behavior

correlate WSI, damping, projection, stiffness-to-weight, impedance

build reference cohorts by wood species and construction recipe

Right now the analyzer uses a hardcoded reference library instead of the materials registry.

D. CAM / Manufacturing
This is where species affects execution:

feed/speed limits

burn risk

tearout risk

chipload multipliers

dust hazard

machining notes

The registry already has machining-related data, and there is already an empirical limits layer. That makes this a natural downstream consumer.

So where does it belong in the actual repo?
Canonical backend home
I would move toward this:

services/api/app/
├── materials/
│   ├── registry/
│   │   ├── wood_species.py
│   │   ├── tonewoods.py
│   │   ├── normalization.py
│   │   └── queries.py
│   ├── acoustics/
│   │   ├── wood_acoustics.py
│   │   └── reference_matching.py
│   ├── machining/
│   │   ├── wood_limits.py
│   │   ├── energy_model.py
│   │   └── recommendation.py
│   └── schemas.py
│
├── data_registry/
│   └── system/materials/
│       ├── wood_species.json
│       └── luthier_tonewood_reference.json
This keeps the JSON files where they are for now, but creates a clean service layer around them.

Canonical API shape
/api/system/materials/wood-species
/api/system/materials/tonewoods
/api/system/materials/species/{id}
/api/system/materials/compare
/api/system/materials/acoustics/{id}
/api/system/materials/machining/{id}
/api/system/materials/recommend
Then aliases can exist for user-facing ergonomics:

/api/design/utilities/woods
/api/design/utilities/tonewoods
and analyzer-specific consumers can call internal services directly.

How it maps to your 6 subsystems
Here is the clean mapping.

1. Design Intake
No direct ownership.
Possible future use:

blueprint intake could suggest likely instrument family + typical material sets

2. Instrument Workspace
Consumes materials for:

project material selection

project presets

wood-aware build decisions

3. Design Utilities
This is the main user-facing home for the woodworking calculator expansion:

Wood Intelligence

species browser

compare

stiffness-to-weight

moisture / movement

board feet / cost / weight

4. Geometry Engine
Mostly indirect.
Could consume material values for:

brace sizing helpers

plate stiffness estimation

top/back rough modeling

5. Art Studio
Secondary use:

wood species palette

visual material selection

inlay / rosette material metadata

6. Manufacturing & Analysis
Strong direct use:

CAM species behavior

feed/speed constraints

dust hazard

analyzer interpretation

shop recommendations

So in your new schema:

User-facing home: Design Utilities
Canonical technical home: System / Shared Materials Intelligence
Strongest downstream consumers: Instrument Hub, Analyzer, CAM

What is wrong with it right now
Here’s the repo-level diagnosis.

It is split across 4 disconnected places
data_registry/system/materials/*

registry_router.py

hardcoded frontend wood constants

analyzer reference logic

It has no single owner
It is not clearly owned by:

Utilities

Analyzer

CAM

Instrument Hub

System

So everyone can justify using it, but nobody actually integrates it.

It has two competing “material” concepts
/api/registry/wood_species

/material/*

That should become one broader materials architecture with separate views, not two disconnected systems.

My recommendation: make it a first-class shared domain
I would formalize this as:

Materials Intelligence
A shared platform capability, not a page.

It would own:

species registry

tonewood reference

acoustics traits

machining traits

moisture / movement traits

recommendation helpers

comparison helpers

Then your UI surfaces become:

Design
├── Blueprint Reader
├── Instrument Hub
├── Instrument Geometry
├── Art Studio
├── Utilities
│   └── Wood Intelligence
│       ├── Board Feet
│       ├── Weight / Density
│       ├── Moisture
│       ├── Stiffness Index
│       ├── Species Browser
│       ├── Species Compare
│       └── Stock Recommendation
and the analyzer becomes a consumer:

Analytics / Acoustics
└── Audio Analyzer
    ├── viewer pack interpretation
    ├── material-informed advice
    └── wood/reference comparisons
Concrete “demonstration” of where it fits
If I place it into the architecture we discussed earlier, the map becomes:

Luthier's Toolbox
├── 1. Design Intake
│   └── Blueprint Reader
│
├── 2. Instrument Workspace
│   └── Instrument Hub
│       └── material selection uses Materials Intelligence
│
├── 3. Design Utilities
│   └── Wood Intelligence
│       ├── board feet
│       ├── moisture
│       ├── density / weight
│       ├── stiffness index
│       ├── species browser
│       └── compare/recommend
│
├── 4. Geometry Engine
│   └── optional material-aware structural helpers
│
├── 5. Art Studio
│   └── wood/material metadata for aesthetic workflows
│
├── 6. Manufacturing & Analysis
│   ├── CAM uses machining properties
│   └── Audio Analyzer uses acoustic/material properties
│
└── Shared Foundation
    └── Materials Intelligence
        ├── wood_species.json
        ├── luthier_tonewood_reference.json
        ├── registry services
        └── recommendation/query layer
That is the cleanest fit.

Highest-value next moves
Stop hardcoding woods in useWoodworkCalculator.ts.
Replace that with registry-backed species loading.

Add /api/registry/tonewoods or /api/system/materials/tonewoods.
Your own migration docs already call this out as the missing unlock for the stiffness path. 


Create one materials/ service layer in the backend.
Do not let analyzer, CAM, and utilities each invent their own wood logic.

Unify /material/* with the wood registry conceptually.
One materials domain, multiple views.

Make Audio Analyzer a downstream consumer, not the owner.
The analyzer should use Materials Intelligence, not hide it.

The biggest architectural conclusion from the scan is this:

The wood database fits the new schema as a shared Materials Intelligence backbone, with its main user-facing expression inside Utilities → Wood Intelligence.

I can turn this into a file-by-file refactor plan next, showing exactly which folders and routes to create, what to move, and what to alias.


turn this into a file-by-file refactor plan next, showing exactly which folders and routes to create, what to move, and what to alias. You also suggested somethings that needed to be created. List does items with details to guide the developer


Thought for 47s
Here’s a concrete file-by-file refactor plan based on the repo scan plus your uploaded migration docs.

The guiding rules I used are:

Utilities stays in Design, not Business. 


The long-term backend shape is /api/design/*, /api/cam/*, /api/acoustics/*, /api/business/*, /api/system/*.

Design-time math should consolidate under services/api/app/instrument_geometry/utilities/. 


The wood/tonewood work is currently blocked by the missing registry tonewoods endpoint and the frontend’s hardcoded wood constants.

1) Target placement in the new schema
Shared foundation
services/api/app/materials/
This becomes the canonical service layer for:

wood species registry

curated tonewood registry

acoustic traits

machining traits

compare / recommend helpers

User-facing home
packages/client/src/components/design-utilities/wood-intelligence/
This is where users actually interact with:

Board Feet

Moisture

Density / Weight

Stiffness Index

Species Browser

Species Compare

Stock Recommendation

Downstream consumers
Instrument Hub uses materials for project wood selection

Audio Analyzer uses materials for interpretation

CAM / Manufacturing uses materials for feed/speed and machining guidance

That keeps the database from becoming “owned” by only one calculator or only the analyzer.

2) File-by-file backend refactor plan
A. Keep the raw datasets where they are for now
No risky data move yet.

Keep in place

services/api/app/data_registry/system/materials/
├── wood_species.json
├── luthier_tonewood_reference.json
├── WOOD_SPECIES_REFERENCE.md
└── SOURCES.md
Reason:

these are already the system datasets

existing registry code already reads from this area

migration docs already expect registry-based exposure rather than a fresh data location

B. Create a new backend service layer
Create
services/api/app/materials/
├── __init__.py
├── schemas.py
├── registry/
│   ├── __init__.py
│   ├── wood_species.py
│   ├── tonewoods.py
│   ├── normalization.py
│   └── queries.py
├── acoustics/
│   ├── __init__.py
│   ├── wood_acoustics.py
│   └── reference_matching.py
├── machining/
│   ├── __init__.py
│   ├── wood_limits.py
│   ├── recommendation.py
│   └── hazards.py
└── recommendation/
    ├── __init__.py
    ├── compare.py
    └── suggest.py
Purpose of each new file
materials/schemas.py

Pydantic response/request models

WoodSpeciesSummary

TonewoodRecord

WoodCompareRequest

WoodCompareResponse

WoodRecommendationRequest

WoodRecommendationResponse

materials/registry/wood_species.py

wraps Registry.get_wood_species()

adds filtering helpers

returns normalized species list

supports search, family, density range, guitar relevance

materials/registry/tonewoods.py

loads luthier_tonewood_reference.json

exposes curated luthier-focused records

intended source for the frontend “Load full DB” tonewood view

materials/registry/normalization.py

species ID normalization

alias mapping

canonical names

matching helper between analyzer/CAM/UI strings

materials/registry/queries.py

filter by:

top/back/side/neck/fretboard/bridge suitability

density

stiffness-to-weight

guitar relevance tier

availability tags later

materials/acoustics/wood_acoustics.py

derived acoustic descriptors

stiffness-to-weight helpers

damping proxy helpers

analyzer-facing interpretation helpers

materials/acoustics/reference_matching.py

compare analyzer results against wood cohorts

not full ML, just deterministic cohort matching initially

materials/machining/wood_limits.py

wraps empirical limits

normalizes per-species machining guidance

bridges /empirical_limits and design/CAM consumers

materials/machining/recommendation.py

“good candidate for carving / routing / bracing / neck blank”

ties species traits to shop recommendations

materials/machining/hazards.py

burn risk

tearout risk

dust hazard

splintering notes

useful for CAM and shop UI

materials/recommendation/compare.py

side-by-side wood comparison logic

materials/recommendation/suggest.py

first-pass recommendation engine

example inputs:

role = soundboard

target = warm / bright / stable / light

edition = express/pro

C. Extend the existing registry router first
Modify
services/api/app/routers/registry_router.py
Add
GET /api/registry/tonewoods

optionally GET /api/registry/tonewoods/{wood_id}

optionally query params:

tier

use_case

family

q

This is already called out in your docs as the missing unlock for Stiffness Index.

Keep existing
GET /api/registry/wood_species

GET /api/registry/empirical_limits

GET /api/registry/empirical_limits/{wood_id}

Alias later
Once the new domain router exists:

alias /api/system/materials/wood-species → /api/registry/wood_species

alias /api/system/materials/tonewoods → /api/registry/tonewoods

Do not delete /api/registry/* yet.

D. Create a materials domain router
Create
services/api/app/routers/system/materials_router.py
New routes
GET /api/system/materials/wood-species
GET /api/system/materials/tonewoods
GET /api/system/materials/tonewoods/{wood_id}
POST /api/system/materials/compare
POST /api/system/materials/recommend
GET /api/system/materials/machining/{wood_id}
GET /api/system/materials/acoustics/{wood_id}
Why
This gives the wood database a proper home in the new schema without breaking existing consumers.

E. Unify design-facing utility aliases
Create
services/api/app/routers/design/utilities_router.py
This is already the intended consolidation point for design utilities. 


Add routes
GET /api/design/utilities/tonewoods
GET /api/design/utilities/wood-species
POST /api/design/utilities/wood-compare
POST /api/design/utilities/wood-recommend
GET /api/design/utilities/machining/{wood_id}
GET /api/design/utilities/acoustics/{wood_id}
Important
These should call the same materials/* services, not duplicate logic.

F. Analyzer integration
Modify
services/api/app/analyzer/design_advisor.py
Replace / extend
Right now it uses a small hardcoded REFERENCE_LIBRARY. Move that toward:

keep the current hardcoded library temporarily

add optional materials-backed enrichment

allow analyzer interpretation to ask:

what wood species family is this closest to

what acoustic trait cohort fits the measured behavior

what wood-related design changes should be suggested

Create
services/api/app/analyzer/materials_adapter.py
Purpose:

translate analyzer needs into calls against materials/acoustics/*

avoid coupling analyzer directly to raw registry files

G. Instrument geometry utility consolidation
This is the calculator / design math side, separate from materials, but part of the same cleanup.

Create
services/api/app/instrument_geometry/utilities/
├── __init__.py
├── fret_math.py
├── bridge_geometry.py
├── pickup_layout.py
├── acoustic_body_volume.py
├── overhang_channel.py
├── temperament.py
└── body_centerline.py   # later
This is directly aligned with the migration plan. 


Move
services/api/app/calculators/acoustic_body_volume.py
→ services/api/app/instrument_geometry/utilities/acoustic_body_volume.py

services/api/app/calculators/alternative_temperaments.py
→ services/api/app/instrument_geometry/utilities/temperament.py

services/api/app/calculators/overhang_channel_calc.py
→ services/api/app/instrument_geometry/utilities/overhang_channel.py

services/api/app/calculators/pickup_position_calc.py
→ services/api/app/instrument_geometry/utilities/pickup_layout.py

services/api/app/instrument_geometry/neck/fret_math.py
→ services/api/app/instrument_geometry/utilities/fret_math.py
Consolidate into
services/api/app/instrument_geometry/utilities/bridge_geometry.py
by absorbing logic from:

services/api/app/calculators/bridge_break_angle.py

any bridge placement helpers that belong in shared design-time math

Alias / compatibility
Leave the old modules as lightweight wrappers for one release:

import from the new module

emit deprecation comment in code

no logic duplication

3) File-by-file frontend refactor plan
A. Move Utilities to Design nav
Modify
packages/client/src/components/layout/CadSidebar.vue
Change /calculators from Business to Design. This is explicitly called for in the migration plan.

Also modify
Find and update dashboard / launcher equivalents, likely:

packages/client/src/views/AppDashboardView.vue
or whichever dashboard file currently mirrors sidebar links.

B. Create a real Wood Intelligence frontend area
Create
packages/client/src/components/design-utilities/wood-intelligence/
├── WoodIntelligenceHub.vue
├── panels/
│   ├── BoardFeetPanel.vue
│   ├── MoisturePanel.vue
│   ├── DensityWeightPanel.vue
│   ├── StiffnessIndexPanel.vue
│   ├── SpeciesBrowserPanel.vue
│   ├── SpeciesComparePanel.vue
│   └── StockRecommendationPanel.vue
├── composables/
│   ├── useWoodSpecies.ts
│   ├── useTonewoods.ts
│   ├── useWoodCompare.ts
│   ├── useWoodRecommendation.ts
│   └── useWoodMetrics.ts
└── types.ts
Why
Right now wood logic is buried in:

ScientificCalculator.vue

WoodworkPanel.vue

useWoodworkCalculator.ts

and that keeps it from becoming a coherent subsystem.

C. Replace hardcoded wood constants
Modify
packages/client/src/components/toolbox/composables/useWoodworkCalculator.ts
Current issue
It hardcodes wood densities locally instead of consuming the registry.

Refactor
remove WOOD_SPECIES constant as source of truth

use a composable that fetches from registry

keep a tiny fallback constant map only as offline backup if needed

Create
packages/client/src/components/design-utilities/wood-intelligence/composables/useWoodSpecies.ts
Responsibilities:

fetch /api/registry/wood_species

normalize to dropdown options

expose loading/error state

expose species lookup by id

Create
packages/client/src/components/design-utilities/wood-intelligence/composables/useTonewoods.ts
Responsibilities:

fetch /api/registry/tonewoods

expose curated luthier-focused results

support “Load full DB”

D. Reuse the existing client registry layer
Modify
packages/client/src/api/registry.ts
Add functions
getTonewoods()

getTonewoodById()

compareWoodSpecies()

recommendWoodSpecies()

getWoodAcoustics()

getWoodMachining()

Modify
packages/client/src/stores/useRegistryStore.ts
Add store state
tonewoods

loadingTonewoods

tonewoodError

This store already exists and is the right place to extend rather than creating parallel fetch code.

E. Refactor current woodwork UI into reusable panels
Modify
packages/client/src/components/toolbox/calculator/WoodworkPanel.vue
Plan
Split current mixed tabs into imported sub-panels:

BoardFeetPanel.vue

MoisturePanel.vue

DensityWeightPanel.vue

StiffnessIndexPanel.vue

Then WoodworkPanel.vue becomes a wrapper.

Optional next move
Eventually move the wrapper itself from toolbox/calculator/ to:

components/design-utilities/wood-intelligence/WoodIntelligenceHub.vue
and leave a compatibility export.

F. Instrument Hub integration
Create
packages/client/src/components/instrument-hub/materials/
├── InstrumentMaterialSelector.vue
├── TonewoodRolePicker.vue
└── useInstrumentMaterials.ts
Purpose
Let Instrument Hub select:

top

back/sides

neck

fretboard

bridge

brace stock

This consumes the same registry-backed wood services.

G. Audio Analyzer integration
Create
packages/client/src/views/tools/audio_analyzer/composables/useAnalyzerMaterials.ts
Purpose
fetch material metadata for analyzer comparison

enrich result cards with likely wood family or acoustic trait context

Modify
packages/client/src/views/tools/AudioAnalyzerViewer.vue
and possibly:

packages/client/src/views/tools/audio_analyzer/composables/useAudioAnalyzerPack.ts
to support optional materials-aware interpretation blocks.

4) Routes to create, move, and alias
Create now
System / shared
GET /api/system/materials/wood-species
GET /api/system/materials/tonewoods
GET /api/system/materials/tonewoods/{wood_id}
POST /api/system/materials/compare
POST /api/system/materials/recommend
GET /api/system/materials/acoustics/{wood_id}
GET /api/system/materials/machining/{wood_id}
Design-facing aliases
GET /api/design/utilities/wood-species
GET /api/design/utilities/tonewoods
POST /api/design/utilities/wood-compare
POST /api/design/utilities/wood-recommend
GET /api/design/utilities/acoustics/{wood_id}
GET /api/design/utilities/machining/{wood_id}
Immediate unblock
GET /api/registry/tonewoods
GET /api/registry/tonewoods/{wood_id}
This is the shortest path to unlock existing frontend work.

Keep for now
GET /api/registry/wood_species
GET /api/registry/empirical_limits
GET /api/registry/empirical_limits/{wood_id}
Alias later
/api/system/materials/wood-species → /api/registry/wood_species
/api/system/materials/tonewoods → /api/registry/tonewoods
Then eventually invert that ownership when the new router fully takes over.

5) Existing files to move vs leave
Move soon
services/api/app/calculators/acoustic_body_volume.py
services/api/app/calculators/alternative_temperaments.py
services/api/app/calculators/overhang_channel_calc.py
services/api/app/calculators/pickup_position_calc.py
services/api/app/instrument_geometry/neck/fret_math.py
to instrument_geometry/utilities/ as described above. 


Leave in place for now
services/api/app/data_registry/system/materials/*
services/api/app/routers/registry_router.py
services/api/app/routers/material_router.py
But:

registry_router.py gets extended

material_router.py should be reviewed for overlap and eventually absorbed into a broader materials domain

Leave but adapt
services/api/app/analyzer/design_advisor.py
Keep it working while introducing materials_adapter.py.

6) New items that need to be created
These are the pieces I previously suggested that do not exist yet and should be created deliberately.

Backend creations
services/api/app/materials/__init__.py
Marks the new shared materials domain.

services/api/app/materials/schemas.py
Needed so router contracts do not drift.

services/api/app/materials/registry/wood_species.py
Needed to stop routers from reading raw registry data directly.

services/api/app/materials/registry/tonewoods.py
Needed because the curated tonewood dataset is distinct from the full species DB.

services/api/app/materials/registry/normalization.py
Needed because analyzer, UI, and CAM will otherwise each invent their own naming.

services/api/app/materials/registry/queries.py
Needed for search/filter/sort logic.

services/api/app/materials/acoustics/wood_acoustics.py
Needed to make the database useful to the analyzer.

services/api/app/materials/acoustics/reference_matching.py
Needed for analyzer cohort/reference suggestions.

services/api/app/materials/machining/wood_limits.py
Needed to unify wood species data with empirical machining limits.

services/api/app/materials/machining/recommendation.py
Needed for CAM/shop assistance.

services/api/app/materials/machining/hazards.py
Needed to centralize burn/tearout/dust risk metadata.

services/api/app/materials/recommendation/compare.py
Needed for compare tool.

services/api/app/materials/recommendation/suggest.py
Needed for recommendation tool.

services/api/app/routers/system/materials_router.py
Needed to give the new schema a real API home.

services/api/app/routers/design/utilities_router.py
Needed for design-facing utility consolidation. 


services/api/app/analyzer/materials_adapter.py
Needed so analyzer consumes materials cleanly instead of importing registry code directly.

Frontend creations
packages/client/src/components/design-utilities/wood-intelligence/WoodIntelligenceHub.vue
Needed to turn wood tools into a subsystem instead of scattered tabs.

packages/client/src/components/design-utilities/wood-intelligence/panels/SpeciesBrowserPanel.vue
Needed because the database is far richer than a density dropdown.

.../SpeciesComparePanel.vue
Needed to expose compare functionality.

.../StockRecommendationPanel.vue
Needed if you want the wood DB to become truly useful in build planning.

.../DensityWeightPanel.vue
Needed to separate generic density/weight from board-feet logic.

.../composables/useWoodSpecies.ts
Needed to replace hardcoded species.

.../composables/useTonewoods.ts
Needed to consume curated luthier-facing data.

.../composables/useWoodCompare.ts
Needed for compare UI state.

.../composables/useWoodRecommendation.ts
Needed for recommendation UI state.

packages/client/src/components/instrument-hub/materials/InstrumentMaterialSelector.vue
Needed to connect Instrument Hub to the shared materials system.

packages/client/src/views/tools/audio_analyzer/composables/useAnalyzerMaterials.ts
Needed for analyzer enrichment.

7) Recommended implementation order
Phase 1 — unblock existing UI fast
Add GET /api/registry/tonewoods to registry_router.py.

Add getTonewoods() to packages/client/src/api/registry.ts.

Extend useRegistryStore.ts.

Refactor useWoodworkCalculator.ts to consume registry data.

Make StiffnessIndexPanel use real data instead of hardcoded tonewoods. 


Phase 2 — create the shared materials domain
Add services/api/app/materials/*.

Add routers/system/materials_router.py.

Add design-facing utility aliases.

Phase 3 — hook up downstream consumers
Instrument Hub material selector

Audio Analyzer materials adapter

CAM/machining wood guidance

Phase 4 — finish design utility consolidation
Move calculator modules into instrument_geometry/utilities/. 


Create unified routers/design/utilities_router.py. 


Keep old endpoints as aliases during transition.

8) The developer decisions still needed
Should /api/registry/* remain the canonical public namespace, or become a compatibility layer under /api/system/materials/*?

Should the analyzer consume only curated tonewoods, or the full wood species database?

Do you want the first recommendation engine to be deterministic rules only, or include scoring weights from the start?

Should material_router.py be folded into the new materials domain now, or left alone until wood integration is stable?

For the frontend, do you want Wood Intelligence to remain inside /calculators, or get its own first-class route under Design while still being linked from Utilities?

I can turn this into a GitHub-style ticket breakdown next: epic, tickets, acceptance criteria, and file-level diffs.


DEVELOPER MODE


