/docs/RMOS_STUDIO_UI_LAYOUT.md file, written in a professional / engineering tone and formatted for immediate drop-in to your repository.

RMOS_STUDIO_UI_LAYOUT.md
RMOS Studio – User Interface Architecture & Layout Specification

Version 1.0 — Engineering Document

1. Purpose

This document defines the UI architecture, layout, and interaction model for RMOS Studio. It specifies:

Core UI regions

Component responsibilities

Interaction rules

Data flow between panels

User input constraints

Required visualization capabilities

This ensures consistency in implementation, testing, and user training across the entire RMOS Studio environment.

2. UI Design Summary

RMOS Studio’s UI is organized into six primary regions:

Top Global Parameter Bar

Pattern & Column Editor (Left Panel)

Horizontal Output Preview (Center Panel)

Ring Configuration Panel (Right Panel)

Multi-Ring Preview Panel (Bottom-Center)

Manufacturing & JobLog Panel (Bottom-Right)

Each region is modular and must support asynchronous updates, real-time previewing, and parameter validation.

3. Global Layout Overview (Text Diagram)
┌───────────────────────────────────────────────────────────────┐
│                    [1] Global Parameter Bar                    │
└───────────────────────────────────────────────────────────────┘
┌──────────────┬───────────────────────────────┬────────────────┐
│              │                               │                │
│ [2] Pattern  │   [3] Horizontal Output       │   [4] Ring     │
│ & Column     │   Preview (Tile Visualization)│   Config Panel │
│ Editor       │                               │                │
│ (Left)       │                               │                │
└──────────────┴───────────────────────────────┴────────────────┘
┌──────────────────────────────┬────────────────┬────────────────┐
│  [5] Multi-Ring Preview       │   [6] MFG      │   [6] JobLog   │
│      Panel (Bottom Center)    │   Planner      │   Panel        │
└──────────────────────────────┴────────────────┴────────────────┘

4. UI Component Specifications
4.1 Global Parameter Bar
Purpose

Provides universal parameters that apply to the entire RMOS project.

Controls

Default Tile Length (mm)

Pattern Family Selector

Color Scheme Selector

Global Twist Offset

Undo / Redo

Save Pattern / Load Pattern

Export Manufacturing Package

Behavior

Updates immediately propagate to dependent UI regions.

Any invalid value triggers a warning indicator (yellow) or error state (red).

Provides access to system-wide commands (export, save, load).

4.2 Pattern & Column Editor (Left Panel)
Purpose

Primary interface for pattern creation and manual editing.

Sections
4.2.1 Column Structure Viewer

Displays vertical strips with:

Width (units → mm representation)

Color swatches

Material icons

Strip-family tags

4.2.2 Column Editing Tools

Add Strip

Remove Strip

Duplicate Strip

Move Up / Down

Normalize Widths

Auto-Color Pattern

Apply Strip-Family Presets

4.2.3 Preset Pattern Module

If a preset was selected:

Configuration sliders

Quick adjustment panel

Random variation (seed-based)

Behavior

Edits update the Horizontal Preview in real time.

Must support drag-and-drop for strip ordering.

Any invalid strip width triggers real-time correction.

4.3 Horizontal Output Preview (Center Panel)
Purpose

Displays a full-resolution horizontal visualization of the resulting tile pattern.

Features

Tile-by-tile display with final tile length consideration

Color-accurate rendering

Optional pixel grid overlay

Slice-angle overlay for angled modes (e.g., herringbone)

Zoom (25–400%)

Pan

Export snapshot

Measurement Indicators

Tile count

Final tile length (computed)

Row width (derived from column)

Behavior

Must always reflect the current column structure.

Updates with tile-length, twist, or angle modifications.

Serves as the user’s primary verification tool.

4.4 Ring Configuration Panel (Right Panel)
Purpose

Define and manage all parameters for each ring.

Components
4.4.1 Ring List

Displays all rings with:

Ring index

Width

Radius

Assigned pattern

4.4.2 Ring Parameter Editor

For selected ring:

Ring Width (mm)

Ring Radius (mm)

Tile Length Override (mm, optional)

Twist Angle (degrees)

Pattern Assignment

Slice-Angle Mode

4.4.3 Constraints & Validation

Immediately shows errors:

Ring width < column width

Radius too small

Tile length invalid

Angle parameters conflicting

Behavior

Updates propagate to Multi-Ring Preview and Saw Pipeline.

Allows ring duplication or deletion.

4.5 Multi-Ring Preview Panel (Bottom-Center)
Purpose

Visualizes the entire rosette assembly in concentric ring form.

Visual Characteristics

True-scale outer and inner radii

Tile segmentation preview

Distinct pattern transitions

Highlight on hover per ring

Color-coded error markers

Controls

Zoom (25–200%)

Toggle tile boundaries

Toggle twist view

Export ring stack snapshot

Behavior

Must always reflect Ring Panel parameters.

Serves as a final design validation tool.

4.6 Manufacturing Planner & JobLog Panel (Bottom-Right)
4.6.1 Manufacturing Planner Panel
Purpose

Convert design into actionable material requirements.

Display Elements

Strip-family usage

Estimated scrap

Material preparation checklist

Tile counts per ring

Volume calculations (mm³ or cm³)

Behavior

Updates in response to ring changes or column edits.

Red flags for excessive scrap or narrow strips.

4.6.2 JobLog Panel
Purpose

Records and displays production planning and execution logs.

Features

Planning entry list

Execution log viewer

Operator notes

Risk assessment

Version history

Export to JSON/PDF

Behavior

Triggers warnings before manufacturing if logs are incomplete.

5. UI Interaction Model
5.1 Real-Time Update Model

Any of the following actions must trigger instant updates in dependent UI areas:

Changing strip width

Editing column order

Changing tile lengths

Adjusting ring radii or widths

Adding twist or angle modifiers

Switching pattern families

The update propagation model is:

Column Editor → Horizontal Preview → Ring Config → Multi-Ring Preview → Planner → JobLog

5.2 Error and Warning Indicators
Warning (Yellow)

Reduced strip width approaching minimum

High tile count (segmentation > 200 tiles)

Radius values borderline small

Error (Red)

Column width > ring width

Negative or zero tile lengths

Invalid twist values

Inconsistent segmentation geometry

Errors must block:

Saw Pipeline Generation

Manufacturing Plan Generation

5.3 Export Interactions

Exports must include:

Export Pattern → JSON

Export Column Structure → CSV / JSON

Export Multi-Ring Stack → PNG/SVG

Export Manufacturing Package → Folder with:

Tile data

Saw batch config

Material usage report

6. Accessibility & Performance Requirements

UI must render smoothly up to 300 tiles per ring.

Column editor must support up to 40 strips per column.

All previews must be GPU-accelerated where possible.

Color selection must include keyboard-accessible controls.

High-contrast mode required for color-blind users.

7. UI Expansion Path (Future)

Photorealistic rendering mode

3D curvature/radial distortion preview

Multi-material strip preview

Pattern library browser

Parametric jig calibration UI

CNC-integrated export modes

8. File Location

This document belongs in:

/docs/RMOS_STUDIO_UI_LAYOUT.md

End of Document

RMOS Studio — UI Layout Specification (Engineering Version)