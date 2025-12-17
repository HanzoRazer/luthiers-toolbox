docs/RMOS/AI_Profile_Tuning_Handoff.md

RMOS AI Profile Edit / Save Pipeline — Handoff
0. Purpose & Scope

This document explains how to integrate the Profile Edit / Save pipeline into the Luthier’s ToolBox / RMOS stack.

This bundle adds:

A backend profile admin API to:

Edit constraint profiles in memory

Persist them back to the YAML config file

Frontend Profile Editor UI:

Select a profile

Adjust fields (rings, widths, flags)

Save → writes to YAML

Immediately re-test via the existing Snapshot Inspector + AI Ops Dashboard

This builds on the existing pieces already shipped:

rmos/constraint_profiles.py (registry + YAML loader)

Snapshot endpoint: /api/rmos/ai/snapshots

AI Ops Dashboard (RmosAiOpsDashboard.vue) with:

RmosAiLogViewer

RmosAiSnapshotInspector

RmosAiProfilePerformance

1. Backend Changes
1.1. Extend constraint_profiles.py

File: services/api/app/rmos/constraint_profiles.py

You should already have:

_BASE_PROFILES dict

RosetteGeneratorConstraints dataclass

load_profiles_from_yaml(path: str) function

Add the following near the bottom of the file (after the YAML loader section):

# -------------------------------------------------------------------
# Profile update + save helpers
# -------------------------------------------------------------------

from typing import Any


def profiles_to_dict() -> dict[str, dict[str, Any]]:
    """
    Export all current profiles (from _BASE_PROFILES) as plain dicts,
    suitable for YAML/JSON.
    """
    result: dict[str, dict[str, Any]] = {}
    for name, c in _BASE_PROFILES.items():
        result[name] = {
            "min_rings": c.min_rings,
            "max_rings": c.max_rings,
            "min_ring_width_mm": c.min_ring_width_mm,
            "max_ring_width_mm": c.max_ring_width_mm,
            "min_total_width_mm": c.min_total_width_mm,
            "max_total_width_mm": c.max_total_width_mm,
            "allow_mosaic": c.allow_mosaic,
            "allow_segmented": c.allow_segmented,
            "palette_key": c.palette_key,
            "bias_simple": c.bias_simple,
        }
    return result


def update_profile_from_data(name: str, data: dict[str, Any]) -> RosetteGeneratorConstraints:
    """
    Update (or create) a single profile by name using a partial dict of fields.

    - Unknown fields are ignored.
    - Missing fields keep their existing values.
    """
    existing = _BASE_PROFILES.get(name, _BASE_PROFILES["default"])
    c = replace(existing)

    if "min_rings" in data:
        c.min_rings = int(data["min_rings"])
    if "max_rings" in data:
        c.max_rings = int(data["max_rings"])
    if "min_ring_width_mm" in data:
        c.min_ring_width_mm = float(data["min_ring_width_mm"])
    if "max_ring_width_mm" in data:
        c.max_ring_width_mm = float(data["max_ring_width_mm"])
    if "min_total_width_mm" in data:
        c.min_total_width_mm = float(data["min_total_width_mm"])
    if "max_total_width_mm" in data:
        c.max_total_width_mm = float(data["max_total_width_mm"])
    if "allow_mosaic" in data:
        c.allow_mosaic = bool(data["allow_mosaic"])
    if "allow_segmented" in data:
        c.allow_segmented = bool(data["allow_segmented"])
    if "palette_key" in data:
        c.palette_key = str(data["palette_key"])
    if "bias_simple" in data:
        c.bias_simple = bool(data["bias_simple"])

    # Sanity clamps
    if c.min_rings > c.max_rings:
        c.min_rings = c.max_rings
    if c.min_ring_width_mm > c.max_ring_width_mm:
        c.min_ring_width_mm = c.max_ring_width_mm
    if c.min_total_width_mm > c.max_total_width_mm:
        c.min_total_width_mm = c.max_total_width_mm

    _BASE_PROFILES[name] = c
    return c


def save_profiles_to_yaml(path: str) -> None:
    """
    Persist all profiles to a YAML file at the given path.

    This overwrites the file; in dev usage, you'll check it into git.
    """
    if not _YAML_AVAILABLE:
        raise ProfileLoaderError(
            "PyYAML is not installed. Install 'pyyaml' to save YAML profiles."
        )

    data = profiles_to_dict()

    # Create directory if needed
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=True)  # type: ignore[union-attr]


Notes:

This uses the same _YAML_AVAILABLE, ProfileLoaderError, and yaml import you already have.

The YAML file path is configured via the admin router (next section).

1.2. Add Profile Admin API Router

File: services/api/app/rmos/api_profile_admin.py

Create this new file with the following content:

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from .constraint_profiles import (
    RosetteGeneratorConstraints,
    list_profile_names,
    get_profile,
    update_profile_from_data,
    save_profiles_to_yaml,
)


# IMPORTANT:
# This is a DEV-ONLY API. Protect it with:
# - env flags
# - auth
# - IP whitelisting
# or only expose it on a dev server.
DEV_PROFILE_YAML_PATH = os.getenv(
    "RMOS_PROFILE_YAML_PATH",
    "services/api/app/config/rmos_constraint_profiles.yaml",
)

router = APIRouter(
    prefix="/rmos/ai/profile-admin",
    tags=["rmos-profile-admin"],
)


class RosetteProfileModel(BaseModel):
    min_rings: int
    max_rings: int
    min_ring_width_mm: float
    max_ring_width_mm: float
    min_total_width_mm: float
    max_total_width_mm: float
    allow_mosaic: bool
    allow_segmented: bool
    palette_key: str
    bias_simple: bool

    @classmethod
    def from_constraints(cls, c: RosetteGeneratorConstraints) -> "RosetteProfileModel":
        return cls(
            min_rings=c.min_rings,
            max_rings=c.max_rings,
            min_ring_width_mm=c.min_ring_width_mm,
            max_ring_width_mm=c.max_ring_width_mm,
            min_total_width_mm=c.min_total_width_mm,
            max_total_width_mm=c.max_total_width_mm,
            allow_mosaic=c.allow_mosaic,
            allow_segmented=c.allow_segmented,
            palette_key=c.palette_key,
            bias_simple=c.bias_simple,
        )


class ProfileListItem(BaseModel):
    name: str
    profile: RosetteProfileModel


class UpdateProfileRequest(BaseModel):
    # All fields optional – partial updates allowed
    min_rings: Optional[int] = None
    max_rings: Optional[int] = None
    min_ring_width_mm: Optional[float] = None
    max_ring_width_mm: Optional[float] = None
    min_total_width_mm: Optional[float] = None
    max_total_width_mm: Optional[float] = None
    allow_mosaic: Optional[bool] = None
    allow_segmented: Optional[bool] = None
    palette_key: Optional[str] = None
    bias_simple: Optional[bool] = None


@router.get(
    "/list",
    response_model=list[ProfileListItem],
    summary="List all constraint profiles and their current values (DEV-ONLY).",
)
def list_profiles() -> list[ProfileListItem]:
    names = list_profile_names()
    items: list[ProfileListItem] = []
    for name in names:
        c = get_profile(name)
        items.append(
            ProfileListItem(
                name=name,
                profile=RosetteProfileModel.from_constraints(c),
            )
        )
    return items


@router.get(
    "/{name}",
    response_model=RosetteProfileModel,
    summary="Get a specific profile by name (DEV-ONLY).",
)
def get_profile_detail(name: str) -> RosetteProfileModel:
    names = list_profile_names()
    if name not in names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{name}' not found.",
        )
    c = get_profile(name)
    return RosetteProfileModel.from_constraints(c)


@router.put(
    "/{name}",
    response_model=RosetteProfileModel,
    summary="Update a profile and persist to YAML (DEV-ONLY).",
)
def update_profile(
    name: str,
    payload: UpdateProfileRequest,
) -> RosetteProfileModel:
    # Convert payload to dict ignoring None fields.
    data = {k: v for k, v in payload.model_dump().items() if v is not None}

    try:
        c = update_profile_from_data(name, data)
        # Persist to YAML
        save_profiles_to_yaml(DEV_PROFILE_YAML_PATH)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update/save profile '{name}': {exc}",
        ) from exc

    return RosetteProfileModel.from_constraints(c)

1.2.1. Wire router into FastAPI

In your main FastAPI app (likely services/api/app/main.py or similar), add:

from rmos.api_profile_admin import router as rmos_profile_admin_router

app.include_router(rmos_profile_admin_router, prefix="/api")


Dev-only note:
Consider guarding this with an environment flag, e.g.:

import os

if os.getenv("ENABLE_RMOS_PROFILE_ADMIN", "false").lower() == "true":
    app.include_router(rmos_profile_admin_router, prefix="/api")


Then only enable it on your dev environment.

2. YAML File Path & Startup Behavior
2.1. YAML File Path

By default, the admin API writes to:

services/api/app/config/rmos_constraint_profiles.yaml


You can override this path with the environment variable:

RMOS_PROFILE_YAML_PATH=/absolute/or/relative/path/to/rmos_constraint_profiles.yaml

2.2. Recommended Startup Pattern

Ensure your app loads profiles from YAML at startup, before serving requests. For example, in main.py or an on_startup handler:

from rmos.constraint_profiles import load_profiles_from_yaml, ProfileLoaderError

PROFILE_YAML_PATH = os.getenv(
    "RMOS_PROFILE_YAML_PATH",
    "services/api/app/config/rmos_constraint_profiles.yaml",
)

@app.on_event("startup")
async def load_rmos_profiles() -> None:
    try:
        load_profiles_from_yaml(PROFILE_YAML_PATH)
        logger.info("Loaded RMOS constraint profiles from %s", PROFILE_YAML_PATH)
    except ProfileLoaderError as exc:
        logger.warning("Could not load RMOS profiles from %s: %s", PROFILE_YAML_PATH, exc)

3. Frontend Integration
3.1. Add RmosAiProfileEditor.vue

File: frontend/src/components/RmosAiProfileEditor.vue

Add the component exactly as defined in the previous message (it:

Calls GET /api/rmos/ai/profile-admin/list

Calls GET /api/rmos/ai/profile-admin/{name}

Sends PUT /api/rmos/ai/profile-admin/{name} on save

Shows a simple YAML preview of the selected profile)

Drop the code in as-is and adjust the API_BASE if your API prefix differs:

const API_BASE = '/api/rmos/ai/profile-admin'

3.2. Update AI Ops Dashboard

File: frontend/src/views/RmosAiOpsDashboard.vue

Make sure this view:

Already shows:

RmosAiLogViewer

RmosAiSnapshotInspector

RmosAiProfilePerformance

Now also includes the editor:

<script setup lang="ts">
import { ref } from 'vue'
import RmosAiLogViewer from '@/components/RmosAiLogViewer.vue'
import RmosAiSnapshotInspector from '@/components/RmosAiSnapshotInspector.vue'
import RmosAiProfilePerformance from '@/components/RmosAiProfilePerformance.vue'
import RmosAiProfileEditor from '@/components/RmosAiProfileEditor.vue'

type SelectedContext = {
  toolId: string | null
  materialId: string | null
  machineId: string | null
} | null

const selectedContext = ref<SelectedContext>(null)

function onSelectContext(ctx: SelectedContext) {
  selectedContext.value = ctx
}
</script>

<template>
  <div class="rmos-ai-ops-dashboard max-w-7xl mx-auto p-4 space-y-4">
    <header class="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
      <div>
        <h1 class="text-2xl font-bold">
          RMOS AI Ops Dashboard
        </h1>
        <p class="text-sm text-gray-600">
          Monitor AI runs, inspect generator behavior, and tune profiles per tool/material/machine.
        </p>
      </div>
    </header>

    <!-- Row 1: Logs + Snapshot -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
      <section>
        <RmosAiLogViewer @select-context="onSelectContext" />
      </section>
      <section>
        <RmosAiSnapshotInspector :selected-context="selectedContext" />
      </section>
    </div>

    <!-- Row 2: Performance analytics -->
    <div>
      <RmosAiProfilePerformance @select-context="onSelectContext" />
    </div>

    <!-- Row 3: Profile editor (DEV) -->
    <div>
      <RmosAiProfileEditor />
    </div>
  </div>
</template>


Make sure the corresponding route exists (earlier we used /dev/rmos-ai-ops):

{
  path: '/dev/rmos-ai-ops',
  name: 'RmosAiOpsDashboard',
  component: () => import('@/views/RmosAiOpsDashboard.vue'),
}

4. End-to-End Usage Flow
4.1. Tuning Loop

Run AI searches (constraint-first / ai_assisted) via your existing APIs.

Open /dev/rmos-ai-ops:

AI Log Viewer → examine individual runs & attempts.

Profile Performance → identify contexts with:

Low success rate

High RED ratio

Click a row in Performance or Logs → Snapshot Inspector auto-loads that context.

Examine Snapshot Inspector:

Check ring count distribution vs. profile bounds.

Check total radial width distribution vs. bounds.

Open Profile Editor:

Select the relevant profile (e.g. thin_saw, premium_shell).

Adjust:

min_rings, max_rings

min/max_ring_width_mm

min/max_total_width_mm

allow_mosaic, allow_segmented, bias_simple, palette_key

Click Save Profile (YAML):

Backend updates the in-memory profile.

Backend writes the entire profile set back to rmos_constraint_profiles.yaml.

Re-run Snapshot for the context:

Confirm generator behavior is now closer to desired.

Re-run AI searches, monitor performance, iterate.

4.2. Git / Deployment Considerations

The YAML file is now a source of truth that the editor writes to.

Recommended workflow:

Treat rmos_constraint_profiles.yaml as a versioned config in git.

After a tuning session, commit the updated YAML.

In production, you can:

Deploy with the tuned YAML, but disable the profile-admin API (ENABLE_RMOS_PROFILE_ADMIN=false).

Or keep it enabled only on an internal/staging deployment.

5. Verification Checklist

Backend

 pip install pyyaml (if not already installed).

 constraint_profiles.py extended with:

profiles_to_dict

update_profile_from_data

save_profiles_to_yaml

 api_profile_admin.py present and imported.

 App includes router with /api/rmos/ai/profile-admin prefix (dev-only).

 On startup, profiles load from YAML without error (or log a warning).

Sanity test (CLI/curl):

# List profiles
curl http://localhost:8000/api/rmos/ai/profile-admin/list

# Get a specific profile
curl http://localhost:8000/api/rmos/ai/profile-admin/thin_saw

# Update a profile
curl -X PUT http://localhost:8000/api/rmos/ai/profile-admin/thin_saw \
  -H "Content-Type: application/json" \
  -d '{"max_rings": 5, "max_total_width_mm": 7.5}'


Then inspect rmos_constraint_profiles.yaml to confirm values changed.

Frontend

 RmosAiProfileEditor.vue compiles with no TS errors.

 RmosAiOpsDashboard.vue imports and renders the editor.

 /dev/rmos-ai-ops loads and:

Profile list populates.

Selecting a profile fills in the form.

Saving shows a success message.

YAML preview matches edited values.