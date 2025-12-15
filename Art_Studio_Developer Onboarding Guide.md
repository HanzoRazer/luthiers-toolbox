DEVELOPER_ONBOARDING_GUIDE.md

🎸 Luthier’s ToolBox — Developer Onboarding Guide

A complete integrated guide for new contributors to Art Studio, CAM Pipeline, Adaptive Lab, and Relief Lab.

Last updated: 2025-11-20

📚 Table of Contents

Introduction

Project Architecture Overview

Backend (FastAPI)

Frontend (Vue 3 + Vite)

Database Layer

Labs and Art Studio Lanes

Local Development Setup

Clone the Repo

Backend Environment Setup

Frontend Environment Setup

Running Everything Together

Backend Guide

Router Layout

Adding New API Endpoints

Art Studio Backend Responsibilities

Risk & Snapshot Database Models

Frontend Guide

Views & Labs Structure

Global Navigation & Deep Links

Compare Mode Architecture

Preset Filtering & Cross-Lab State

Testing & CI

Local Tests

CI Workflows

Smoke Tests

Developer Workflows

Working in Rosette Lane

Working in Adaptive Lab

Working in Relief Lab

Working in PipelineLab

How to Add New Art Studio Lanes

Common Troubleshooting

Next Major Roadmap Items

🔰 Introduction

Welcome to the Luthier’s ToolBox development ecosystem — a full-stack guitar-focused CAD/CAM suite including:

🌀 Art Studio

🌀 Rosette Designer + Compare Mode

🌀 Relief Carving

🌀 Adaptive Pocketing Lab

🌀 Unified CAM Pipeline

🌀 Cross-lab risk analytics

This guide is written so that any new developer can:

Set up their local environment

Run backend + frontend

Understand the folder structure

Build features in Art Studio or CAM Pipeline

Contribute new lanes

Debug, test, and run labs

Everything in this onboarding guide is derived from your actual repo, bundles, and architecture.

🏗 Project Architecture Overview
Backend (FastAPI)

Located at:

services/api/app/


Key directories:

routers/          → API endpoint definitions
models/           → Pydantic request/response models
db/               → SQLite wrappers & job stores
services/         → CAM kernels, geometry analyzers
utils/            → shared helper modules


Major API families:

Art Studio

art_studio_rosette_router.py

art_studio_relief_router.py

art_studio_compare_router.py

CAM Engines

cam_vcarve_router.py

cam_pocket_adaptive_router.py

cam_sim_router.py

Metrics

cam_metrics_router.py

Unified Pipeline

cam_pipeline_router.py (grows in future phases)

The backend is designed to be modular, so new “lanes” (Rosette, Relief, Adaptive) plug in cleanly.

Frontend (Vue 3 + Vite)

Located at:

packages/client/src/


Key areas:

views/          → Full-page screens (Labs, Art Studio)
components/     → Reusable UI widgets (sparklines, toolbars)
router/         → Route definitions
stores/         → Pinia stores (optional)
utils/          → math, geometry, api helpers


Primary views:

ArtStudioRosette.vue

ArtStudioRosetteCompare.vue

AdaptiveKernelLab.vue

ReliefKernelLab.vue

PipelineLab.vue

Vue pages rely heavily on:

Query params (lane, preset, jobA, jobB)

Deep linking between labs

Shared risk analytics spine

Database Layer

Current default: SQLite, via lightweight helper modules.

Stores:

Rosette jobs

Rosette compare snapshots

Risk timeline

Adaptive + Pipeline jobs (future expansions)

Later upgrades can migrate this to Timescale/Postgres without affecting API shape.

Labs and Art Studio Lanes

You now have 3 active lanes:

✔ Rosette Lane

Preview engine

Save/load jobs

Compare Mode

Risk pipeline

Preset scorecards

Cross-lab deep linking

✔ Adaptive Lab

Query-consuming

Preset-aware job selection

Ready for AdaptiveKernel v2 drop

✔ PipelineLab

Context banners

Auto-load jobs for given preset

Rosette ↔ Pipeline deep linking

⧗ Relief Lab (Stubbed)

Heightfield → toolpath mapper

Needs ReliefKernelCore implementation

🖥 Local Development Setup
Clone the repo:
git clone https://github.com/<your-org>/luthiers-toolbox.git
cd luthiers-toolbox

Backend Environment Setup

From project root:

make venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows

make install
make api-verify                  # runs temporary uvicorn + health check


If you prefer PowerShell:

.\scripts\install.ps1
.\scripts\verify_api.ps1


Backend will run at:

http://127.0.0.1:8000

Frontend Environment Setup
cd packages/client
npm install
npm run dev


Frontend runs at:

http://localhost:5173

Running Everything Together

Backend:

make api


Frontend:

npm run dev


Open your browser to:

👉 http://localhost:5173

🧩 Backend Guide
Router Layout

Located in:

services/api/app/routers/


Key patterns:

@router.post("/path")

Uses Pydantic for request/response models

Returns structured JSON for Vue components

Example: art_studio_rosette_router.py

Contains:

/preview

/save

/jobs

/compare

/compare/snapshot

/compare/export_csv

Adding New API Endpoints

Create a new file in routers/your_router.py

Add to api.py import list

Write Pydantic models in /models

Return JSON-friendly dicts

Add tests in services/api/tests/

Backend philosophy:

Small, explicit routers.
No massive monolithic files.

Art Studio Backend Responsibilities

Each lane router (Rosette, Relief, Adaptive) must provide:

A preview endpoint

A save job endpoint

A list jobs endpoint

A compare or risk endpoint

Ability to generate snapshots

These mirror the 3-lane architecture of the UI.

Risk & Snapshot Database Models

Schema includes:

id

timestamp

jobA_name

jobB_name

presetA, presetB

risk_score

diff_summary

notes (optional)

Risk snapshots support analytics across lanes via shared columns.

🎨 Frontend Guide
Views & Labs Structure
ArtStudioRosette.vue
ArtStudioRosetteCompare.vue
AdaptiveKernelLab.vue
PipelineLab.vue
ReliefKernelLab.vue


Each lab:

Runs its own preview engine

Has context from query params

Allows “send to x” deep linking

Uses shared sparklines

Can store risk snapshots

Global Navigation & Deep Links

Rosette Compare generates links like:

/lab/pipeline?lane=rosette&preset=Safe
/lab/adaptive?lane=rosette&preset=Aggressive


Pipeline and Adaptive Labs:

Read preset from route

Apply to dropdowns

Auto-load last job matching that preset

Show banner:

Preset loaded from Rosette: Safe (from job XYZ)

Compare Mode Architecture

Rosette Compare Mode:

Dual canvas

Shared viewBox and union bounding box

Diffs computed server-side

Sparkline trend

Filter chips

Preset scorecards

History panel

Snapshot → risk pipeline integration

Compare Mode for other lanes will reuse this same architecture.

Preset Filtering & Cross-Lab State

Preset selection state is passed between labs via:

?lane=rosette&preset=Safe


All labs understand this scheme.

🧪 Testing & CI
Local Tests

Backend:

pytest services/api/tests


Frontend:

Vite dev mode reactivity

Additional test suite planned

CI Workflows

Your repo includes:

Nightly API health checks

Smoke tests:

V-carve preview

Adaptive plan (stub)

Artifact uploads (health.json)

These confirm that CAM endpoints never silently break.

Smoke Tests

make api-verify:

Spins up uvicorn on ephemeral port

Hits /api/cam_vcarve/preview_infill

Ensures engine is healthy

Returns JSON badge for CI

🛠 Developer Workflows
Working in Rosette Lane

Use ArtStudioRosette.vue for design

Test compare mode via:

/api/art/rosette/compare

ArtStudioRosetteCompare.vue

Add new risk features in:

Snapshot router

Compare Mode UI

Working in Adaptive Lab

Preset awareness via query params

Needs AdaptiveKernel v2 (future bundle)

Work inside:

AdaptiveKernelLab.vue

cam_pocket_adaptive_router.py

Working in Relief Lab

ReliefKernelCore pending

Heightfield planning → slope → toolpath → risk

Files:

art_studio_relief_router.py

ReliefKernelLab.vue

Working in PipelineLab

Handles full multi-op orchestration

Reads deep links

Auto-selects preset & job

Shows context banner

Ideal place to add:

Lead-in/out

Post preset selection

Multi-stage pipelines

🌱 How to Add New Art Studio Lanes

Each new lane follows this formula:

Backend requirements:

router.py

/preview

/save

/jobs

/compare or /risk

/snapshot

Frontend requirements:

LaneName.vue

Query param consumption

Banner support

“Send to” buttons

Risk snapshot UI

Sparkline panels

This architecture was intentionally built to support unlimited lanes.

🐞 Common Troubleshooting

Backend won't start:

Activate venv

Run make install

Ensure no stray Python 3.13.7 conflicts

Frontend fails with missing modules:

Run npm install

Delete node_modules and reinstall

V-carve preview 500 error:

Missing Pyclipper or Shapely

Run make install to rebuild

Compare Mode canvas misaligned:

Reset to union bounding box

Confirm viewBox="{{bboxMerged.join(' ')}}"

🚀 Next Major Roadmap Items

These are your top 5 future bundles:

1. Rosette → CAM Toolpath Bridge

Transform rosette geometry into CNC-ready toolpaths.

2. Unified Job Detail View

Inspect individual jobs across all lanes.

3. Adaptive Kernel v2

True adaptive pocketing engine.

4. ReliefKernelCore

Heightmap → toolpath → analytics.

5. Cross-Lab Preset Risk Dashboard

Unified view of Safe / Aggressive / Custom behavior across the entire system.

🏁 Final Notes

This guide is intended to onboard:

New developers

Collaborators

Future maintainers

Yourself (after long breaks)