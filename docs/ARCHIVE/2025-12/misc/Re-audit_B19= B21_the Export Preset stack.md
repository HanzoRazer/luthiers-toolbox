UNIFIED_PRESETS_DESIGN.md
Luthier’s Tool Box – Unified Preset Architecture
Version: 2025-11-25
Status: Draft for Integration – Ready for Developer Implementation
________________________________________
1. Overview
The Luthier’s Tool Box now supports three different preset domains:
1.	CAM Presets
(Adaptive Plan parameters, machine/post selection, strategy settings)
2.	Export Presets
(Export format, filename template, include flags, default directories)
3.	Neck Presets
(Neck profile family, section defaults, scale length settings)
Historically these systems have lived in separate routers, stores, and UI surfaces, making cross-feature operations (Compare Mode → Export → NeckLab → PipelineLab) difficult and error-prone.
The Unified Preset System merges these into a single schema, single storage file, single router, and a unified frontend manager, while preserving existing behaviors for each domain.
This document defines:
•	Unified preset data model
•	Backend storage and router structure
•	Integrations with PipelineLab, CompareLab, NeckLab
•	Export naming pipeline upgrade
•	UI integration (Preset Hub)
This is the canonical design reference for all future work on presets.
________________________________________
2. Goals
✔ Unify CAM + Export + Neck presets
All three types share a common envelope, with optional sub-sections.
✔ Centralize storage in /server/data/presets.json
Instead of three different JSON files.
✔ Support advanced actions
•	Clone CAM preset from JobInt (B19)
•	Tooltips for lineage (B20)
•	Multi-run comparison (B21)
•	Neck diff comparisons saved as preset context
•	Export naming referencing neck profile & section
✔ Backend + Frontend consistency
Every preset is a single object with a single ID.
________________________________________
3. Unified Preset Schema
{
  "id": "uuid",
  "kind": "cam" | "export" | "neck" | "combo",
  "name": "Strat Modern C – Roughing Pass",
  "description": "Adaptive roughing preset for Strat neck work.",
  "tags": ["neck", "strat", "roughing"],
  "created_at": "2025-11-25T15:00:00Z",
  "created_by": "user-or-system",
  "job_source_id": "run-id-or-null",    // used by B19, B20, B21
  "source": "manual | clone | import",  // provenance info

  // CAM PRESET DOMAIN -------------------------------
  "machine_id": "haas_vf2",
  "post_id": "haas_ngc",
  "units": "mm",

  "cam_params": {
    "stepover": 0.45,
    "stepdown": 2.0,
    "strategy": "Spiral",
    "margin": 0.5,
    "feed_xy": 1200,
    "safe_z": 5.0,
    "z_rough": -1.5
  },

  // EXPORT PRESET DOMAIN ----------------------------
  "export_params": {
    "default_format": "gcode",
    "include_flags": {
      "include_baseline": true,
      "include_candidate": true,
      "include_diff_only": false
    },
    "filename_template": "{preset}__{neck_profile}__{neck_section}__{date}.gcode",
    "default_directory": null
  },

  // NECK PRESET DOMAIN ------------------------------
  "neck_params": {
    "profile_id": "strat_modern_c",
    "profile_name": "Fender Stratocaster Modern C",
    "scale_length_mm": 647.7,
    "section_defaults": [
      { "name": "fret_1", "width_mm": 45.4, "thickness_mm": 21.3 }
    ]
  }
}
Notes:
•	A preset may contain one or multiple preset domains.
•	Kind "combo" indicates a full production preset containing CAM + Export + Neck settings.
________________________________________
4. Backend Architecture
4.1 Storage File
server/data/presets.json
A single JSON list:
[
  { ...preset1... },
  { ...preset2... }
]
Backend store utilities:
server/util/presets_store.py
Must implement:
•	list_presets(kind: Optional[str])
•	get_preset(id)
•	insert_preset(preset)
•	update_preset(id, patch)
•	delete_preset(id)
________________________________________
4.2 Unified Router
server/routers/presets_router.py
Endpoints:
GET    /presets
GET    /presets/{id}
POST   /presets
PATCH  /presets/{id}
DELETE /presets/{id}
Query parameters:
?kind=cam|export|neck|combo
?tag=neck,strat,etc
Required behaviors:
•	Filtering by kind
•	Filtering by tags
•	Enforcing immutable fields:
o	id
o	created_at
o	created_by (optional)
•	Return proper 404 when preset does not exist
________________________________________
5. Preset Integration Points
5.1 PipelineLab (CAM Presets)
PipelineLab consumes:
•	kind: "cam" or "combo"
•	machine_id, post_id
•	cam_params
Also supports B19:
•	Clone preset from JobInt run
•	Auto-fill parameters from cloned run
________________________________________
5.2 Export Drawer (Export Presets)
Export drawer consumes:
•	kind: "export" or "combo"
•	export_params domain
Upgrade:
Compare Mode (neck_diff) now includes:
•	{neck_profile}
•	{neck_section}
•	{compare_mode}
Filename template now works like:
{preset}__{neck_profile}__{neck_section}__{date}.svg
Safety features:
•	Extension mismatch warning
•	Auto-fix extension
•	“Disable unless confirmed” mode
•	Full state persistence:
o	template
o	override
o	selected export preset
o	include flags
________________________________________
5.3 NeckLab (Neck Presets)
NeckLab uses:
•	kind: "neck" or "combo"
•	neck_params
Supports:
•	Default section width/thickness profiles
•	Jumping directly from a neck preset into CompareLab
•	Using preset as a “neck family” definition
________________________________________
5.4 CompareLab (Unified Integration)
CompareLab is now capable of:
•	Loading baseline/candidate from:
o	DXF
o	Gcode
o	Neck profile sections
o	Export overlays
o	Saved neck diffs
•	Using export presets for naming & format
•	Saving comparisons as:
o	Neck diffs → stored in neck_diffs.jsonl
o	Full preset diffs → stored in unified preset store
________________________________________
6. Unified Preset Manager (Frontend)
6.1 Location
client/src/views/PresetHubView.vue
Accessible via:
/lab/presets
6.2 Features
•	Tabbed UI:
o	CAM | Export | Neck | Combo | All
•	Filters:
o	Tags
o	Kind
o	Source job
•	Quick actions:
o	Use in PipelineLab
o	Use in CompareLab
o	Use in NeckLab
•	Hover/tooltip:
o	B20 lineage info (job_source_id)
o	Creation date
o	Machine/post details
o	Neck profile summary
•	Buttons:
o	Clone (pipeline job clone)
o	Duplicate preset
o	Delete
________________________________________
7. Naming & Template Engine (Unified)
7.1 Supported tokens
{preset}
{machine}
{post}
{operation}
{date}
{timestamp}

Neck-specific:
{neck_profile}
{neck_section}

Compare-mode:
{compare_mode}

Fallback:
{raw}   (literal passthrough)
7.2 Token Resolution Rules
•	Unknown tokens must remain literal (not error)
•	compare_mode is derived from CompareLab state:
o	“neck_diff”
o	“geom_diff”
•	Neck tokens only resolve when CompareLab or NeckLab are active
________________________________________
8. Versioning & Migration
8.1 Migration Step
A migration script:
scripts/migrate_presets_unified.py
•	Reads:
o	pipeline_presets.json
o	export_presets.json (if existed)
o	neck presets (if existed)
•	Writes unified presets.json
•	Marks old stores as archived
8.2 Backward Compatibility
•	Existing job clones in B19 must still resolve preset_id.
•	Old export templates remain valid.
________________________________________
9. Developer Testing Checklist
✔ Preset creation
POST /presets creates correct schema for all kinds.
✔ Filtering
GET /presets?kind=neck returns only neck presets.
✔ UI selection
Preset Hub opens correct UI actions for each kind.
✔ Token expansion
Verify filename rendering:
{preset}__{neck_profile}__{neck_section}__{date}.svg
✔ Compare Mode integration
Baseline/candidate neck loads must populate:
•	profileName
•	sectionName
•	scaleLengthMm
•	widthMm, heightMm
✔ B19 compatibility
Cloning job → generates valid unified preset with kind: "cam".
✔ B20 tooltips
Preset Hub hover shows lineage properly.
✔ B21 integration
Run comparison panel can load presets derived from runs.
________________________________________
10. Future Extensions
The unified system anticipates:
•	Material presets
•	Saw presets (ToolBox SawLab)
•	Relief carving presets
•	Chord/Scale CAD presets (musical geometry engine)
•	Cloud preset sync
This design remains compatible with all future expansions.
________________________________________
End of Document
This file is ready for insert into your repo at:
/docs/UNIFIED_PRESETS_DESIGN.md

