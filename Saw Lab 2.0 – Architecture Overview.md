Saw Lab 2.0 – Architecture Overview
RMOS-Integrated CNC Saw-Blade Manufacturing Engine

Luthier’s ToolBox – 2026 Edition

0. Purpose of This Document

Saw Lab 2.0 is the upgraded and fully RMOS-integrated version of the CNC Saw Lab subsystem.
This document explains:

What Saw Lab 2.0 is

Why it exists

How it works

How it integrates with RMOS 2.0

How its modules are structured

How developers should use it

This is not code — it is a map of the Saw Lab 2.0 system.

1. What Saw Lab 2.0 Is

Saw Lab 2.0 is:

A specialized toolpath and physics engine for CNC saw-blade cutting, implemented as a toolpath mode under RMOS 2.0.

It supports:

thin-kerf saw blades

rip and crosscut strategies

kerf-aware geometry removal

blade-specific risk scoring

saw-specific calculators (bite load, rim speed, kickback, heat)

material-aware cutting behavior

stock slicing / strip planning

Saw Lab 2.0 is not a standalone system anymore.
It is a first-class manufacturing mode inside RMOS, parallel to router-bit CAM (CAM_N16 lineage).

2. How Saw Lab 2.0 Fits Into RMOS
RMOS 2.0 delegates toolpaths as:
If tool_id starts with "saw:" → use Saw Lab 2.0  
else → use Router Toolpath Engine (CAM_N16)


This means:

Same feasibility engine

Same BOM engine

Same geometry engine (ML or Shapely)

Same API entrypoints

Same RMOS context

Saw Lab 2.0 is activated automatically based on selected tool.

3. High-Level Architecture
Saw Lab 2.0
├── Blade + Material Models
├── Saw Calculators (heat, rim speed, deflection, bite, kickback)
├── Saw Geometry Layer (kerf offsets, boolean removal)
├── Kerf-Aware Path Planner
├── Toolpath Builder (RMOS-compatible)
└── Risk Evaluator (aggregates calculator results)


Everything flows through RMOS:

RMOS → Saw Engine → Saw Lab → ToolpathPlan → G-code generator

4. Directory Structure

Installed under:

services/api/app/saw_lab/


The structure:

saw_lab/
  models.py               ← blade, material, cut context
  geometry.py             ← kerf offsets + boolean ops via RMOS geometry engine
  path_planner.py         ← rip/crosscut path generation
  toolpath_builder.py     ← convert saw cuts → RmosToolpathPlan
  risk_evaluator.py       ← aggregate saw-specific calculator results
  calculators/
      saw_heat.py
      saw_rimspeed.py
      saw_deflection.py
      saw_bite_load.py
      saw_kickback.py


Plus one RMOS integration module:

toolpath/saw_engine.py

5. Key Architectural Principles
5.1 RMOS Controls Everything

Saw Lab no longer handles:

feasibility scoring

geometry kernels

BOM independently

external decision logic

All decisions must flow through RMOS.

5.2 Saw Lab Is a “Mode” of RMOS Toolpath Engine

Router and saw workflows share:

Feasibility system

Geometry engine

BOM framework

ToolpathPlan data model

This guarantees unified behavior across the ecosystem.

5.3 Geometry Always Goes Through RMOS

Saw Lab 2.0 must use:

engine = get_geometry_engine(context)


Why?

Shapely ability for high-complexity cuts

ML engine compatibility with legacy features

Consistent geometry for both router and saw workflows

This replaces any internal Saw Lab geometry logic from the original subsystem.

5.4 Calculators Are Modular and Saw-Specific

Saw Lab uses five calculators:

Calculator	Purpose
Rim speed	checks surface speed constraints
Bite load	mm/tooth feed, core to safety & burning
Heat	burn threshold and thermal load
Deflection	plate flex vs cut forces
Kickback	feed direction, hook angle, tooth shape

The RMOS feasibility scorer will integrate them automatically.

5.5 Path Planner Produces MLPaths Only

The planner generates MLPath objects only.
It does not:

produce G-code

handle Z depth

manage spindle settings

Those are downstream concerns.

The planner is responsible for:

rip and crosscut generation

spacing between cuts

kerf compensation

cut ordering

basic sequencing logic

5.6 Toolpath Builder Produces RMOS Toolpath Plans

Saw Lab toolpath builder emits:

RmosToolpathPlan
RmosToolpathOperation


Example:

RmosToolpathOperation(
    op_id="rip_cut_1",
    strategy="SAW_CUT",
    estimated_runtime_min=1.4,
)


All toolpaths — router or saw — use the same underlying RMOS format.

5.7 Risk Evaluator Wraps All Saw Calculators

The risk evaluator:

calls each saw calculator

aggregates risk scores

determines warnings

feeds results into RMOS feasibility scorer

This ensures safety and manufacturability remain consistent.

6. The Saw Lab 2.0 Data Flow
Design (Art Studio, AI, or Constraint-First)
        ↓
RMOS Feasibility Engine
        ↓
IF tool_id starts with "saw:":
        ↓
Saw Engine (RMOS)
        ↓
Saw Lab:
   - Cut planner
   - Kerf geometry
   - Risk eval
   - Toolpath builder
        ↓
RmosToolpathPlan
        ↓
G-code generator


The entire workflow is deterministic and RMOS-controlled.

7. Responsibilities by Module
7.1 models.py

Contains:

SawBladeSpec

SawMaterialSpec

SawCutContext

SawLabConfig

These represent the core saw-cutting environment.

7.2 geometry.py

Handles kerf-based geometry modifications.

Responsibilities:

Expand a centerline into a kerf zone

Subtract kerf regions from stock

Use RMOS geometry engine for:

offsetting

boolean operations

cleanup

7.3 path_planner.py

Creates cut paths such as:

rip lines

crosscut lines

compound angle paths

board slicing / strip extraction

multi-pass kerf planning

Planners return:

List[SawCutPath]

7.4 calculators/*

Each calculator returns:

measurement

risk score

optional warnings

Saw-specific physics live here.

They plug into RMOS automatically when tool_id indicates a saw blade.

7.5 risk_evaluator.py

Aggregates all calculator outputs.

Produces summary risk:

rim_speed_risk
bite_risk
kickback_risk
heat_risk
max_risk


Used by RMOS feasibility engine to classify designs.

7.6 toolpath_builder.py

Converts SawCutPath objects to RMOS toolpath operations.

Defines:

sequential order of operations

estimated runtime

strategy names

toolpath grouping

Outputs a complete RmosToolpathPlan.

7.7 saw_engine.py

The RMOS entrypoint that maps:

RosetteParamSpec + RmosContext → Saw ToolpathPlan


This is where RMOS delegates saw-mode tasks.

8. How Developers Should Use Saw Lab 2.0
✔ To add new saw blade types

Modify or extend SawBladeSpec and tool libraries.

✔ To add new saw cutting strategies

Extend path_planner.py with new path generation functions.

✔ To improve physics accuracy

Replace placeholder math in the calculators.

✔ To integrate with AI

AI proposes designs → RMOS calls feasibility → RMOS may call Saw Lab.

✔ To debug toolpaths

Enable Shapely geometry engine with:

context.use_shapely_geometry = True

9. How Saw Lab 2.0 Enables New Features

Once fully integrated, RMOS + Saw Lab unlock:

Automatic strip layout planning

Saw-based acoustic brace fabrication

Production slicing of tonewood plates

Automated stock optimization

Hybrid saw + router workflows

AI-assisted cut planning

Kerf-aware material budgeting

Fail-safe cutting (kickback prevention rules)

Saw Lab becomes a true manufacturing subsystem.