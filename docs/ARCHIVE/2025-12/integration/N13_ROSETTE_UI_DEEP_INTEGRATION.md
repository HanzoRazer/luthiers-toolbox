the complete, repo-ready /docs/N13_ROSETTE_UI_DEEP_INTEGRATION.md — the full UI/UX integration blueprint for connecting the real N12 Rosette Engine into the front-end, replacing all N11 scaffolding.

This is the definitive specification for the Rosette Designer’s final user interface, component interactions, store flows, canvas rendering, previews, CNC export UI, and multi-ring orchestration.

N13_ROSETTE_UI_DEEP_INTEGRATION.md
Patch Bundle N13 — Full UI/UX Integration of the RMOS Rosette Engine

Version 1.0 — Frontend Architecture & UX Specification

1. Purpose of Patch N13

N13 rewrites the Rosette Designer UI so it can:

Use real N12 rosette calculations

Render real segmentation, slices, previews, CNC paths

Support multi-ring editing, previews, and assemblies

Manage loading, errors, validation, safety, and job events

Present a coherent, production-level RMOS Studio interface

N13 upgrades:

Components

Layout

Previews

UI logic

Stores

API flows

Tool panels

Navigation

UX behavior

Error handling

Visualization pipeline

It finalizes the Rosette Designer experience.

2. UI Architecture Overview

The new Rosette Designer will contain six integrated panels:

Pattern Panel (strip & column builder)

Ring Panel (radius, width, tile length, twist, herringbone, kerf)

Segmentation & Slice Panel (computed results)

Multi-Ring Assembly Panel

Preview Canvas (SVG/Canvas for real geometry)

CNC/Export Panel (G-code, alignment, operator checklist)

The primary view:

RosetteDesignerView.vue


will orchestrate all six panels.

3. Component Hierarchy (Final Structure)

Place under:

packages/client/src/components/rmos/rosette/


Components:

PatternPanel.vue

ColumnStripEditor.vue

RingPanel.vue

SegmentationPanel.vue

SlicesPanel.vue

MultiRingPanel.vue

PreviewCanvas.vue

PreviewControls.vue

ExportCNCPanel.vue

RosetteValidationPanel.vue

RosetteToolbar.vue

Shared UI utilities:

AngleChart.vue

StripFamilyLegend.vue

MaterialMapViewer.vue

Render assets:

/render/rmos/preview_pipeline.ts

/render/rmos/slice_projection.ts

/render/rmos/ring_renderer.ts

4. Rosette Designer Final Layout
 ----------------------------------------------------------
| Rosette Toolbar | Global Pattern Controls               |
 ----------------------------------------------------------
|  Pattern Panel     |  Ring Panel         | Segmentation |
|  Column Editor     |  Ring Settings      | Slice Info   |
|                    |  Tile Settings      |              |
 ----------------------------------------------------------
| Multi-Ring Assembly        | Preview Canvas (Main)      |
 ----------------------------------------------------------
| Validation Panel  | CNC Export Panel | JobLog Status   |
 ----------------------------------------------------------


This layout mirrors N8–N10 standards and provides engineering-at-a-glance visibility.

5. Pinia State Architecture (Deep Integration)

Store:

useRosetteDesignerStore.ts

State
rings: RosetteRing[]
selectedRingId: number | null
column: ColumnDefinition
patternId: string | null
segmentation: Record<ring_id, SegmentationResult>
slices: Record<ring_id, SliceBatch>
assembly: MultiRingAssembly
preview: RosettePreviewState
status: RosetteOperationStatus

Actions

loadPattern(patternId)

savePattern()

setColumnDefinition()

addRing(), updateRing(), deleteRing()

computeSegmentation(ring_id)

generateSlices(ring_id)

assembleMultiRing()

renderPreview()

exportCNC()

validateState()

logJobEvent(type, metadata)

All actions interact with the real N12 backend.

6. API Traffic Map (N12 → N13 UI)

UI calls:

UI Action	Endpoint	N12 Engine Used
Segment Ring	/segment-ring	SegEngine
Generate Slices	/generate-slices	SliceEngine+Kerf
Build Multi-Ring	/assemble	RingEngine
Render Preview	/preview	PreviewEngine
Export CNC	/export-cnc	CNCExporter
Validate	/validate	ValidationEngine

All endpoints now return real geometry objects.

7. Pattern Panel Integration
Features:

Add/remove strips

Adjust width, family, material

Live update preview

Validate minimum strip width

Strip-family color legend

Pattern save/load buttons

Auto-Binding:

Whenever a strip changes, column state updates

Whenever column changes → rings requiring update show “needs recompute”

8. Ring Panel Deep Integration

UI allows user to edit:

radius

width

tile_length

twist_angle

herringbone_angle

kerf

pattern assignment

ring grouping

Auto-Binding:

Change → triggers computeSegmentation(ring_id)

After segmentation → triggers generateSlices(ring_id)

After slices → live preview updated

9. Segmentation Panel

Shows:

tile_count

tile_length (effective)

tile boundaries

tile_angle distribution

warnings (e.g. odd/even tile count issues)

strip-family tile mapping

Interactive:

Hover tile → highlight in preview

Click tile → show slice geometry

10. Slices Panel

Shows geometry delivered by the N12 slice engine:

slice angles

kerf-corrected angles

twist/herringbone effects

endpoints

tile index

material maps

Tools:

Compare “raw vs kerf-corrected”

Show vector direction

Toggle angle markers

11. Multi-Ring Assembly Panel

Displays a tree-view of rings in final rosette:

Ring 1  (Outer)
   – tile_count: 128
   – twist: 5°
   – herringbone: 30°
Ring 2  (Middle)
Ring 3  (Inner)


Shows warnings:

Inter-ring alignment

Radius overlap

Material conflicts

Too many rings

12. Preview Engine Integration
PreviewCanvas.vue

Render pipeline uses actual N12 geometry:

Compute ring paths

Compute tile outlines

Compute slice projections

Render full mosaic in SVG or Canvas

Apply:

color maps

strip-family shading

herringbone visualization

tile separators

slice angle lines (optional overlays)

User Controls:

Zoom

Pan

Fit to screen

Toggle overlays:

segmentation

slice angles

material maps

twist vectors

13. CNC Export Panel

Displays:

selection of ring to export

path preview (miniature toolpath visualization)

estimated runtime

safety warnings

operator checklist preview

Download:

toolpaths.gcode

alignment.json

operator_checklist.pdf

N13 requires full hooking to N12’s CNC Exporter.

14. Validation Panel Integration

Displays:

errors

warnings

info messages

N12 validation results:

kerf drift

segmentation feasibility

material conflicts

unsafe twist values

kerf > tile_length/2

tile_count > 300

Color coding mirrors N10 safety/LiveMonitor styling.

15. LiveMonitor Integration

Whenever the UI calls:

segmentation

slicing

assembly

export

validate

N13 must:

emit events using N10’s LiveMonitor client

show progress indicator

update operator panel with job_id

display warnings automatically

Events include payload from N12:

ring_id

tile_count

drift

CNC-safe flag

duration

16. Safety Integration (N10)

Two safety layers:

Layer 1 — In-UI Validation

UI blocks actions when critical errors occur.

Layer 2 — Server-Side Safety Gate

When exporting CNC:

action = "rosette_cnc"


N13 must:

send safety request to the N10 safety endpoint

display override prompt if required

log results in JobLog

17. JobLog Integration

UI writes:

job_type: "rosette_segmentation"
job_type: "rosette_slicing"
job_type: "rosette_preview"
job_type: "rosette_export"


Users can open a JobLog history panel:

view parameters

view results

compare versions

track operator adjustments

18. Error Handling & UX Fallbacks

N13 introduces robust fallback behavior:

If segmentation fails → revert tile_count to last known good state

If preview fails → show simplified radial preview with warnings

If slices fail → show only segmentation grid

If CNC export fails → show operator suggestions + safety logs

User is never left without a visible UI.

19. Final Integration Checklist
Backend

 Integrate all N12 engines

 Replace all N11 stubs

 Add preview endpoint

 Add CNC export endpoint

 Wire safety & LiveMonitor

Frontend

 Implement all panels

 Replace stub components

 Add real rendering pipeline

 Add loading & error states

 Add live preview updates

 Add multi-ring orchestration

UX

 Ensure everything is connected via stores

 Provide visual warnings

 Provide tooltips & helpers

 Provide operator workflows

20. Deliverables Summary

Patch Bundle N13 delivers:

✔ Full Pattern Panel Integration
✔ Full Ring Panel Integration
✔ Real Segmentation Panel
✔ Real Slice Panel
✔ Real Multi-Ring Assembly Panel
✔ Real SVG/Canvas Preview
✔ Full CNC Export UI
✔ Safety Integration (N10)
✔ LiveMonitor Integration
✔ JobLog Integration
✔ Error-resistant UX pipeline

This turns the Rosette Designer into a fully operational RMOS Studio front-end.

21. File Location

Place at:

/docs/N13_ROSETTE_UI_DEEP_INTEGRATION.md

End of Document

Patch Bundle N13 — RMOS Studio: UI Deep Integration Layer