the complete /docs/RMOS_STUDIO_TUTORIALS.md file, written in a clear professional/engineering tone but structured for human learning and step-by-step operational guidance. It is designed as the official onboarding and training guide for users and developers.

RMOS_STUDIO_TUTORIALS.md
RMOS Studio – Official Tutorial Series & Workflow Training Guide

Version 1.0 — Training & Instructional Document

1. Purpose

This document provides a structured tutorial series for learning RMOS Studio.
It bridges the gap between high-level engineering specifications and practical end-user workflows.

The tutorials demonstrate:

How to design rosette patterns

How to build columns & strips

How to configure rings

How to apply segmentation, slice angles, kerf, and twist

How to generate CNC and saw exports

How to utilize logs and manufacturing plans

Each tutorial includes practical exercises, expected outcomes, and validation checkpoints.

2. Tutorial Structure

The tutorial series is divided into five difficulty tiers:

Beginner – Basic navigation and operations

Intermediate – Pattern editing and ring configuration

Advanced – Algorithm-driven design and multi-ring assemblies

Expert – CNC export and manufacturing workflow

Mastery – Precision workflows, troubleshooting, and QA

Each tier builds upon previous competencies.

3. Beginner Tutorials
Tutorial 1 — Navigating the RMOS Studio Interface
Objective

Learn how to use the Global Parameter Bar, Column Editor, Ring Panel, Preview Panels, and JobLog.

Steps

Open RMOS Studio.

Locate the Global Parameter Bar at the top.

In the left panel, open Pattern & Column Editor.

Click on each tab and observe changes in center and right panels.

Open JobLog (bottom-right) and study entries.

Checkpoint

Able to identify the role of each panel.

Can follow UI response to global parameter changes.

Tutorial 2 — Creating Your First Column
Objective

Build a simple three-strip column.

Steps

In Column Editor, click “Add Strip.”

Set widths: 1.0 mm, 0.5 mm, 1.0 mm.

Assign alternating colors.

Assign strip families (A, B, A).

Observe updated Horizontal Output Preview.

Checkpoint

Column displays correct strip ordering.

No validation errors appear in Ring Panel.

Tutorial 3 — Saving and Loading Patterns
Steps

Create a column.

Click Save Pattern in the Global Parameter Bar.

Name it "BeginnerPattern01".

Reload the pattern.

4. Intermediate Tutorials
Tutorial 4 — Building a Traditional Spanish Pattern (Preset)
Objective

Use the preset generator and modify parameters.

Steps

Open Pattern → Presets → Traditional Spanish.

Set the following parameters:

thin strip = 0.5 mm

thick strip = 1.0 mm

alternating bands

Apply earth-tone colors.

Review tile visualization.

Exercise

Modify the preset by:

Adding a central accent strip

Changing thickness ratios

Tutorial 5 — Configuring a Ring
Objective

Assign your column to a ring.

Steps

Open Ring Configuration Panel.

Create a ring with:

radius = 45 mm

width = 3 mm

tile length = 2.4 mm

Assign your column pattern.

Review the Multi-Ring Preview.

Checkpoint

No validation errors should occur.

Tutorial 6 — Applying Twist & Herringbone Modes
Objective

Learn how twist angles and alternating slice angles work.

Steps

In Ring Panel:

Set twist_angle = 5°

Set herringbone_angle = 30°

Observe alternating angles in Horizontal Preview.

View angle markers in Multi-Ring Preview.

5. Advanced Tutorials
Tutorial 7 — Multi-Ring Rosette Design
Objective

Combine 3 rings into a complete rosette.

Steps

Create 3 rings:

Ring 1: radius 40 mm, width 2.5 mm

Ring 2: radius 45 mm, width 3 mm

Ring 3: radius 48 mm, width 1.5 mm

Assign different column patterns to each.

Apply varying twist/herringbone settings.

Validate all rings.

Review final rosette in Multi-Ring Panel.

Checkpoint

Tile counts computed correctly.

Visual alignment consistent.

Tutorial 8 — Manual Column Editing for Professional Designs
Steps

Start with a blank column.

Add 10+ strips manually.

Set precise widths using mm inputs.

Group strips into families (Wood, Accents, Composite, Adhesive).

Review manufacturing warnings.

Tutorial 9 — Custom Pattern Generator Logic
Objective

Simulate algorithm-driven pattern creation.

Steps

Enable Advanced Mode → “Pattern Engine.”

Choose “Parameter Sweep.”

Sweep widths from 0.4 mm → 1.2 mm in increments.

Observe generated pattern variations.

Save the best results.

6. Expert Tutorials
Tutorial 10 — Full Tile Segmentation Analysis
Objective

Understand segmentation mathematics.

Steps

Open a ring and click “Preview Tile Segmentation.”

Record:

circumference

tile_count

effective_tile_length

Compare preset vs manual tile length.

Exercise

Force increased tile_count by reducing tile length.
Observe segmentation and drift warnings.

Tutorial 11 — Slice Generation & Kerf Compensation
Objective

Inspect slice geometry including kerf offsets.

Steps

Generate slices.

Open slice inspector:

raw angle

twist

herringbone pattern

kerf-adjusted angle

Compare raw vs kerf-adjusted toolpath diagrams.

Tutorial 12 — Manufacturing Plan and Material Usage
Steps

Generate the Manufacturing Plan.

Study:

strip-family lengths

volume calculations

expected scrap

Compare actual vs estimated when modifying parameters.

7. Mastery Tutorials
Tutorial 13 — Exporting Full CNC Package
Steps

Generate SliceBatch for a ring.

Open CNC Export Panel.

Export:

G-code

Alignment metadata

Operator CNC checklist

Load G-code into a CNC simulator (recommended: CAMotics).

Validate alignment visually.

Tutorial 14 — Troubleshooting & QA Workflow
Steps

Create a ring with deliberate errors:

too narrow width

excessively high twist

invalid strip widths

Attempt segmentation.

Study warnings/errors in the Validation Panel.

Fix issues and confirm pipeline success.

Tutorial 15 — Production-Ready Rosette Workflow
Steps

Create patterns (traditional, checkerboard, custom).

Build 3–7 rings.

Validate model.

Generate slices.

Apply CNC export.

Produce manufacturing plan.

Generate JobLog package.

Deliverable

A complete RMOS Studio production bundle.

8. Reference Exercises

Include at least these practical designs:

Two-tone checkerboard ring

Spanish mosaic pattern

Herringbone ring with twist

Multi-ring classical rosette

Complex multi-family column

Each design reinforces a part of the RMOS pipeline.

9. User Tips & Best Practices

Keep strip widths ≥ 0.5 mm for ease of manufacturing.

Favor even tile counts for symmetric patterns.

Validate early and often.

Use preset patterns as starting points.

Use snapshots of Multi-Ring Preview for design comparison.

Use JobLog for tracking adjustments between tests.

10. File Location

This document belongs in:

/docs/RMOS_STUDIO_TUTORIALS.md

End of Document

RMOS Studio — Tutorial & Training Series Guide (Professional Edition)