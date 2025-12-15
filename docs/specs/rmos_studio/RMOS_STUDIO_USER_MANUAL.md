the complete /docs/RMOS_STUDIO_USER_MANUAL.md file, written in a professional but accessible user-facing tone. This is designed as the primary manual for day-to-day RMOS Studio operation—distinct from engineering documentation.

RMOS_STUDIO_USER_MANUAL.md
RMOS Studio – User Manual & Operating Guide

Version 1.0 — End-User Documentation

1. Introduction

Welcome to RMOS Studio, the Rosette Mosaic Operating System for creating professional, repeatable, and manufacturable rosette patterns.

RMOS Studio enables you to:

Design custom and preset mosaic patterns

Create and edit strip-based columns

Build multi-ring rosette assemblies

Apply tile segmentation, twist, and herringbone effects

Generate production-ready saw slices

Export CNC toolpaths and alignment metadata

Produce manufacturing plans and operator checklists

Log and track every production run

This manual guides you through the entire workflow—from first use to final CNC export.

2. System Requirements
Component	Requirement
Operating System	Windows, macOS, Linux
CPU	2 GHz dual-core or higher
Memory	8 GB RAM recommended
Display	1080p or higher resolution
Storage	~250 MB free
Input	Mouse + keyboard
Optional	CNC simulator (CAMotics recommended)
3. The RMOS Interface

The interface is divided into six key regions:

Global Parameter Bar (Top)

Pattern & Column Editor (Left)

Horizontal Output Preview (Center)

Ring Configuration Panel (Right)

Multi-Ring Preview (Bottom Center)

Manufacturing Planner + JobLog (Bottom Right)

Each region updates automatically depending on your pattern and ring configuration.

4. Getting Started
4.1 Creating a New Project

From the main menu, select File → New Project.

Enter a project name (e.g., Rosette_Training_01).

RMOS loads a clear workspace with default settings.

4.2 Loading an Existing Project

Select File → Open Project.

Choose a .json or .rmos project file.

All rings, columns, patterns, and job logs are restored.

5. Working With Columns

Columns are the foundation of RMOS patterns.
A column is a vertical stack of strips, each representing a color or material.

5.1 Adding Strips

Open Pattern & Column Editor (left side).

Press Add Strip.

Adjust:

Width (UI units → mm)

Color

Material

Strip Family (e.g., Wood, Accent, Composite)

Tip: Width 1.0 UI = 1.0 mm.

5.2 Editing Strip Properties

Click any strip to edit:

Color

Width

Material

Family

Locked status (prevents accidental edits)

5.3 Removing Strips

Select strip

Press Delete Strip

5.4 Saving Your Column as a Pattern

In Global Parameter Bar → Save Pattern

Patterns may be:

User-created

Modified from presets

Algorithmically generated

6. Using Preset Patterns

RMOS Studio includes professional preset templates:

Traditional Spanish

Herringbone

Two-Tone Checkerboard

Multi-Band / Accent-Based Patterns

To use them:

Open Pattern → Presets

Select a preset

Adjust parameters (strip thickness, colors, alternation rules)

7. Ring Configuration

Rings represent circular mosaic bands in your final rosette.

7.1 Creating a Ring

Right panel → Add Ring

Set:

Radius

Width

Desired tile length

Kerf

Pattern assignment (column)

7.2 Applying Twist

Adjust Twist Angle (°) to rotate tile boundaries.

Common uses:

Visual alignment

Artistic offset curves

7.3 Enabling Herringbone Mode

Under Pattern Options:

Set Herringbone Angle

Tiles now alternate: +angle / -angle

8. Tile Segmentation (Automatic)

RMOS automatically computes:

Tile count

Tile spacing

Effective tile length

Angular boundaries

This ensures the circumference is always covered perfectly.

If tile_length_mm does not divide evenly, RMOS adjusts using:

tile_effective_length = circumference / tile_count

9. Viewing Previews
9.1 Horizontal Output Preview

Shows the tile layout as if your strips were turned into horizontal tiles.

Features:

Zoom

Grid overlay

Slice angle display

Pattern boundaries

9.2 Multi-Ring Preview

Displays the entire rosette as concentric circles.

Use it to:

Check alignment

Inspect transitions between rings

Verify twist and herringbone effects

Review final aesthetics

10. Manufacturing Workflow

This section explains how to turn your digital design into a real rosette.

10.1 Generating Slice Geometry

Right panel → Generate Slices

RMOS produces:

Raw slice angles

Twist-modified angles

Herringbone alternations

Kerf-adjusted angles

Slices are used for saw cutting or CNC toolpaths.

10.2 Using the Manufacturing Planner

Bottom-right panel → Manufacturing Planner

Displays:

Strip-family material requirements

Tile count

Scrap estimation

Volume calculations

Operator checklist

10.3 Exporting CNC Package

Go to Export → CNC Package

Includes:

G-code

Alignment metadata

Slice batch file

Production summary

PDF operator checklist

Load into a CNC simulator for validation.

11. Job Logging & Revision Tracking

RMOS maintains a detailed log of:

Planning parameters

Execution data

Deviations

Operator notes

Revision history

Each manufacturing session is saved as a Run Package.

Useful for:

Professional documentation

Warranty support

Repeatability

Shop management

12. Validations & Warnings

RMOS checks all geometry and parameters at every step.

Errors (Red)

Block operations.
Examples:

strip width < 0.4 mm

ring.width < column.width

kerf ≤ 0

invalid segmentation

Warnings (Yellow)

Allow continuation but should be reviewed.

Examples:

excessive twist

tile_count > 200

narrow strips

high scrap estimate

13. Tips for Best Results

Keep strip widths ≥ 0.5 mm for reliable machining

For classical rosettes, choose tile_counts between 60–120

Reduce kerf for narrow rings

Minimize twist when using herringbone

Keep colors high contrast in UI for visibility

Validate your design before generating slices

Always export a Run Package for record-keeping

14. Troubleshooting Guide
Issue	Likely Cause	Solution
Tiles misaligned	extreme twist	reduce twist angle
Slice drift	kerf too large	lower kerf or increase radius
Segment errors	invalid tile_length	use longer tile lengths
CNC export disabled	failed validation	open Validation Panel
Column doesn’t fit	ring width too small	increase width or shrink column
Checkerboard looks uneven	odd tile count	adjust tile length
15. Keyboard & Mouse Shortcuts
Action	Shortcut
Zoom in/out	Mouse wheel
Reset view	R
Toggle grid	G
Duplicate strip	Ctrl + D
Undo	Ctrl + Z
Redo	Ctrl + Y
Export project	Ctrl + Shift + E
16. Glossary

Strip — a vertical band forming part of a column

Column — stack of strips, used to construct tiles

Tile — horizontal slice of a column used to build rings

Ring — circular band in the rosette

Kerf — thickness removed by the cutting blade

Slice — actual cut operation derived from tile geometry

Herringbone — alternating slice-angle pattern

Twist — rotational offset of all tile boundaries

Run Package — complete manufacturing dataset for one execution

17. File Location

This document belongs in:

/docs/RMOS_STUDIO_USER_MANUAL.md

End of Document

RMOS Studio — User Manual (End-User Edition)