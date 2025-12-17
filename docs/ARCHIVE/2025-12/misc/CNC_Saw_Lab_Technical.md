# CNC Saw Lab Technical Reference

This document consolidates all CNC-related engineering content from `CNC Saw Lab.md` into a single, non-conversational reference. It focuses on safe saw-blade use on CNC routers, the proof-of-concept (PoC) attachment, cross-stack implementation details, and the long-term roadmap captured in the original discussion.

---
## 1. Safe Circular-Saw Operation on CNC Routers
- **Spindle RPM vs. Blade Rating**: Keep spindle speed below the blade’s published max RPM. Router spindles (12–24k RPM) require CNC-rated slitting or veneer blades designed for high RPM.
- **Blade Selection**:
  - 2–3" slitting saws (kerf 1.5–2.0 mm) for binding/purfling channels.
  - 5–7" thin-kerf veneer blades (0.8–1.4 mm) for rosette sausage slicing and decorative laminations.
  - Use negative or neutral hook angles; avoid consumer table-saw blades and unbalanced hardware-store options.
- **Arbor Requirements**:
  - ER32 shank (16–20 mm) with dual clamping flanges ≥ 40 mm OD.
  - Pilot journal sized to blade bore −0.01 mm (sliding fit) with 4–5 mm engagement.
  - Keep spindle nose to blade center ≤ 50 mm to limit deflection.
- **Machine Rigidity**: Perform dial-indicator push tests (<0.15 mm lateral deflection at mid-span) and resonance checks (spin at 6k/9k/12k RPM without blade) before loading saw hardware on long gantries (BCAMCNC 2030CA spans 8'4").
- **Workholding**: Vacuum tables, screw-down fixtures, V-block jigs, and backers are mandatory. Edge clamps alone are prohibited.
- **Cut Strategy**:
  - Rim speed target 2,000–4,000 m/min (v = π·D·RPM).
  - Feed per tooth 0.01–0.03 mm for delicate veneers.
  - Depth of cut per pass 0.2–0.5 mm for veneer slicing; ≤1.0 mm for slitting saws.
  - Never plunge a saw blade into solid stock; enter via existing kerf or pre-cut pocket.

---
## 2. Saw Attachment Proof-of-Concept (PoC)
### 2.1 Goals
- Demonstrate that Luthier’s Tool Box can define saw tools, generate toolpaths, enforce risk checks, and log CNC jobs.
- Target operations: rosette sausage slicing, binding channels, purfling strips, veneer wafers.

### 2.2 Mechanical Stack
- **Blade Spec**: 63.5 mm (2.5") carbide slitting saw, 1.6 mm kerf, ≥18k RPM rating.
- **Arbor Stack**: ER collet → shank → upper flange → blade → lower flange; optional drive pin for heavier cuts.
- **Guard Concept**: L-shaped aluminum bracket plus polycarbonate shield protecting the top 120° of the blade; guard status stored as a boolean in tool metadata.

### 2.3 CAM Templates (Fusion 360)
- Tool definition `LTB_Saw_63p5x1p6_40T`.
- Operations: circular rosette contour, linear binding contour, future fret-slot template.
- Per-pass DOC 0.5–1.0 mm; climb cutting; tangential lead-in/out only.

### 2.4 Safety Checklist (for Risk Reports)
- Pre-run: verify blade rating, rim speed, arbor cleanliness, workholding, and dry-run at Z+10 mm.
- During run: start with 50% feed override, monitor vibration.
- Post-run: log overrides and subjective rating (Safe/Marginal/Problematic).

### 2.5 Data Model & Pipeline Hooks
- `SawTool` schema example with recommended rim-speed bands, guard requirements, and allowable workholding types.
- `SawSliceOp` pipeline node: geometry source (line/circle/DXF), slice thickness, passes, risk options.
- Outputs: G-code snippet, JSON risk report, job-log record.

---
## 3. Rosette & Veneer Production System (5–7" Blades)
### 3.1 Machine Constraints
- Limit blade diameter to 125–180 mm on long gantry routers.
- Run 6,000–9,000 RPM with shallow passes (≤0.5 mm) and feeds ≤800 mm/min.

### 3.2 Blade & Arbor Guidelines
- 160 mm thin-kerf (≈1.2 mm) blade, 96–120 teeth, neutral/negative hook, ≥18k RPM rating.
- ER32 arbor with 45 mm OD flanges, 8–10 mm thick, pilot fit to 20 mm bore.

### 3.3 Rosette Sausage Slicing Jig
- Base plate 400×200×18 mm with mounting holes.
- 90° V-block sized for 4–4.5" sausages; adjustable end-stop with 0.5–2.0 mm slice range.
- Backer board and dowel pins for repeatable fixturing.

### 3.4 Cutting Presets
- Gentle: 6,000 RPM, 300 mm/min, 0.25 mm DOC.
- Normal: 7,500 RPM, 500 mm/min, 0.35 mm DOC.
- Aggressive: 9,000 RPM, 800 mm/min, 0.5 mm DOC (soft woods only).
- Risk engine colors presets (Gentle = green, Aggressive = yellow).

### 3.5 Backend/Schema Artifacts
- `server/schemas/tool_saw.schema.json` and example `tool_saw_rosette_160mm.json` define saw tools.
- `server/schemas/op_saw_slice.schema.json` plus pipeline example `pipeline_saw_slice_rosette.json` capture slicing operations.

### 3.6 UI Specifications
- `SawToolPanel` component: diameter/kerf/bore inputs, preset table, workholding chips, risk hints reacting to gantry span.
- `SawSliceOpPanel`: tool selector, geometry controls, slice parameters, preset buttons, risk preview, G-code display.

---
## 4. Cross-Stack Implementation Details
### 4.1 Backend Schemas & Helpers
- `SawTool` Pydantic models with preset validation and workholding enums.
- `SawSliceOp` schema handling line/circle/DXF geometry plus risk options.
- `saw_risk.py`: rim-speed calculation, DOC grading, gantry-span heuristic, combined risk grade.
- `saw_gcode.py`: linear G-code stub (start/stop spindle, safe Z, feed moves). Multi-pass support planned.

### 4.2 FastAPI Routes
- `/saw-tools` CRUD endpoints expose in-memory store (swap in DB later).
- `/saw-ops/slice/preview` accepts `SawSliceOp`, returns risk summary + G-code snippet.

### 4.3 Frontend Components
- `SawToolPanel.vue` and `SawSliceOpPanel.vue` (Vue 3 + TypeScript) mirror backend schemas, emit updates, and call preview endpoint via Axios.
- Risk banners highlight long-gantry + large blade combos; presets update backend preview.

---
## 5. PipelineLab & Multi-Slice Model
- `NODE_REGISTRY` maps `op_type` to runner callables.
- `saw_slice` runner instantiates `SawSliceOp`, injects machine gantry span, evaluates risk, and emits G-code.
- `SawSliceBatchOp` schema describes multi-slice batches (base geometry, number of slices, step axis, thickness, passes).
- `run_saw_slice_batch` expands batches, accumulates per-slice risk, concatenates G-code, and reports worst-case grade.
- Example pipeline `rosette_sausage_slice_batch_v1` produces 24 wafers with 1.4 mm offsets.

---
## 6. Creative Rosette Manufacturing Workflow
- **Strip & Tile Modeling**: use `RosetteStrip` and `RosetteTile` primitives with cross-section and color metadata.
- **Strip Recipes**: derive stick dimensions, rotation angles, slice thickness, kerf allowance, and jig requirements.
- **StripSliceOp / StripSliceBatchOp**: extend saw batch logic into rotated coordinate systems for angled slices and ultra-thin veneers.
- **Risk Extensions**: enforce minimum slice thickness vs. kerf ratios and require carriers/backers for fragile parts.
- **Manufacturing Planner**: aggregates strip usage, computes required stick count, and populates JobLog entries per batch.

---
## 7. Job Logging & Diagnostics
- Each saw batch records operation ID, blade/tool ID, RPM/feed/DOC, number of slices, per-slice risk grades, yield metrics, and operator notes.
- Risk data (rim speed, DOC grade, gantry grade) is embedded in responses from `/saw-ops/slice/preview` and batch runners for downstream logging.
- The `/health` endpoint (see repo) now exposes dependency versions and queue/cache checks, ensuring saw pipelines run on known environments.

---
## 8. Roadmap Highlights from CNC Saw Lab
- Kerf compensation and deflection-aware cutting.
- In-cut blade dynamics (torque, vibration, thermal modeling).
- Adaptive pass scheduling and dual-direction climb/conventional passes.
- Dedicated CNC saw arbor hardware with dampers and guards.
- Advanced workholding (multi-zone vacuum, sacrificial carriers, magnetic fixtures).
- Horizontal slicing fixtures for billet-to-veneer workflows.
- Batch scheduler + production dashboard with material traceability.
- Recipe engine mapping sausage glue-ups to rosette templates.
- AI-driven rosette generator linking creative patterns to manufacturing plans.

---
## 9. LS-OS Manual (High-Level Operational Guidance)
The conversation also generated a 10-chunk **Long-Session Operating System (LS-OS)** manual covering:
1. **Executive Summary & Scope** – definition of LS-OS, assumptions, terminology.
2. **Four-Chat Architecture** – Master Index, Active Work, Deep Storage, Rapid Sandbox chats.
3. **Stability Protocol** – chunked output, file-based delivery, module isolation, MIL-SPEC requirements.
4. (Subsequent chunks in the source file continue with session recovery, diagnostics, UI failure handling, etc.).

The full manual text remains in `CNC Saw Lab.md` for reference; this summary highlights the sections relevant to keeping multi-module CNC/CAM work stable inside ChatGPT-driven workflows.

---
## 10. Where to Go Next
- Decide whether to prioritize kerf compensation, hardware attachments, AI pattern engines, or production scheduling.
- Promote the `SawSliceBatchOp` and future `StripSliceBatchOp` nodes into the live PipelineLab once persistence and UI editors are ready.
- Scope JobLog ingestion endpoints and dashboards so each saw batch feeds analytics automatically.
- If LS-OS practices resonate, mirror the Four-Chat model in your repo’s contributor guide to keep future CNC Saw Lab work organized.
