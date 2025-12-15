📘 JobInt_Roadmap.md
Luthier’s Tool Box — CAM Pipeline & Job Intelligence Roadmap
Checkpoint: November 20, 2025
🎯 Purpose

This roadmap defines the current state, short-term milestones, and future development path for the Job Intelligence (JobInt) subsystem inside the Luthier’s Tool Box CAM Pipeline.

JobInt is the system responsible for:

Capturing every CAM/Pipeline run

Logging structured metadata (machine, post, material, helical, review gates)

Recording simulation issues

Visualizing historical performance

Supporting preset creation from real-world performance

Powering design notebooks through exports (CSV/Markdown)

This roadmap ensures the entire ecosystem evolves coherently across the backend, frontend, and pipeline layers.

1. ✅ System Overview (Current State)
1.1 Job Store

JSON-backed storage at:

data/job_intel/jobs.json


Each job contains:

job_id, job_name

machine_id, post_id

material, material_type

created_at

sim_issues

notes (freeform text)

(soon) tags, preset_id, job_source_id, job_source_summary

1.2 JobInt API

/cam/jobint/summary

/cam/jobint/history

/cam/jobint/jobs (list)

/cam/jobint/jobs/{job_id}/notes (B17)

Supports structured trend analysis and historical filtering.

1.3 JobInt UI
✔ CamJobLogTable.vue includes:

Severity chips (Error / Warning / Clean)

Colored sparkline (E/W count)

Token-based quick filters (#Haas, #Ebony…)

CSV/Markdown export of filtered view (B16)

Inline Notes editor + persistence (B17)

✔ Visualization:

Backplot issues colored by severity

PipelineLab receives sim issues

BridgeLab includes preflight + review-gate status

2. 📦 Completed Bundles (JobInt Track)
Bundle	Name	Status	Functionality
B3–B5	BridgePipeline gate series	✔	DXF preflight blocks invalid bridges
B8	SimSummary	✔	Adds simulation summary to PipelineLab
B9–B10	SimIssues stub + Backplot coloring	✔	Warnings/errors shown visually
B11	SimIssues → JobInt	✔	Logs sim issues per job
B12	SimIssues History Chart	✔	Time-series trend visualization
B13	Filtered history (machine/material)	✔	UI filtering for charts
B14	Sparkline in log table	✔	Visual per-job issue summary
B15	Quick filters (severity/material/machine)	✔	Instant segmenting of job history
B16	Export filtered jobs (CSV/MD)	✔	For design notebooks
B17	Notes editor per job	✔	Inline notes + PATCH endpoint
3. 🔮 Upcoming Bundles (High Value Targets)
B18 — Job Tags + Favorites

Adds user-defined “semantic” labels:

tags: ["favorite", "ebony", "production", ...]

⭐ favorite toggle

Filter chips: #favorite, #prod

Tag editor in row

Tags included in CSV/Markdown exports

Value: instantly retrieve your “best passes” for specific machines/materials.

B19 — Clone Run into Preset (PresetFromJob)

Adds:

preset_id and job_source_id to job entries

API route: /cam/preset/clone_from_job/{job_id}

Seeds a new preset with:

feed rates

stepover/stepdown

helical flag

machine + post

material

Value: turn great results into reusable, shareable presets.

B20 — Show Preset Source in UI

Adds:

In preset view: “Source job”

Hover tooltip with job metadata

Navigate back to original job log

Allows tracking lineage of presets

Value: traceability — know why a preset exists.

B21 — CompareRunsPanel

Adds:

Multi-select jobs (2–4)

Compare:

machine

material

time

predicted vs simulated

review %

issues

notes

Value: data-driven decisions for optimization.

B22 — Machine Self-Calibration Loop

Adds:

Record actual_time_s (later input)

Compute per-machine calibration factor:

factor = avg(actual_time_s / predicted_time_s)


Show in Machine Profile:

“Haas VF-2: typically 1.08× slower”

“ShopBot: typically 0.92× faster”

Value: smarter simulations and runtime predictions.

B23 — Material Intelligence (Hardwood/Softwood Model)

Material classification

Bridge-specific behavior

Track success metrics by:

Wood species

Grain density

Recommend feeds per material

Value: luthier-optimized CAM based on material performance.

4. 🚀 Long-Term Vision (2026)
4.1 Job-Based Optimization Engine

Feed-run history becomes a dataset

Suggests improved presets automatically:

“Reduce stepover 5% for ebony on ShopBot”

“Enable helical ramping for dense woods”

4.2 Machine Learning Loop

Trend-based:

Review % reduction

Energy/time benchmarks

Predictive presets per machine-material pairing.

4.3 Cloudless Local Personalization

All data stays on the user’s machine.

No external servers needed.

Auto-backup of job intelligence in data/cam_backups/.

5. 📌 Implementation Notes

All JobInt features are additive:
No breaking changes to pipeline or simulator.

JSON file format will remain stable.

Frontend and backend always use:

sim_issues: List[{severity, code, message}]


Machine + material hooks are consistent across:

BridgeLab

BackplotGcode

PipelineLab

JobLog

Sim reports

6. 🧭 Where to Put This File

Recommended repo location:

docs/cam/jobint/JobInt_Roadmap.md


or for direct developer onboarding:

DEVELOPER_GUIDES/JobInt_Roadmap.md
