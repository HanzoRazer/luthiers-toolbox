from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.cam_sim_router import router as sim_router
from .routers.feeds_router import router as feeds_router
from .routers.geometry_router import router as geometry_router
from .routers.tooling_router import router as tooling_router
from .routers.adaptive_router import router as adaptive_router
from .routers.machine_router import router as machine_router
from .routers.cam_opt_router import router as cam_opt_router  # M.2
from .routers.material_router import router as material_router  # M.3
from .routers.cam_metrics_router import router as cam_metrics_router  # M.3
from .routers.cam_logs_router import router as cam_logs_router  # M.4
from .routers.cam_learn_router import router as cam_learn_router  # M.4

# Patch N.12 — Machine Tool Tables
try:
    from .routers.machines_tools_router import router as machines_tools_router
except Exception:
    machines_tools_router = None

# Patch N.14 — Unified CAM Settings (Post Templates + Adaptive Preview)
try:
    from .routers.posts_router import router as posts_router
except Exception:
    posts_router = None

try:
    from .routers.machines_router import router as machines_router
except Exception:
    machines_router = None

try:
    from .routers.adaptive_preview_router import router as adaptive_preview_router
except Exception:
    adaptive_preview_router = None

# Art Studio preview router (v13)
try:
    from .routers.cam_vcarve_router import router as cam_vcarve_router
except Exception as _e:
    cam_vcarve_router = None

# Art Studio v15.5 — Post-processor with CRC + Lead-in/out
try:
    from .routers.cam_post_v155_router import router as cam_post_v155_router
except Exception:
    cam_post_v155_router = None

# Art Studio v15.5 — Smoke test router
try:
    from .routers.cam_smoke_v155_router import router as cam_smoke_v155_router
except Exception:
    cam_smoke_v155_router = None

# Patch N.15 — G-code Backplot + Time Estimator
try:
    from .routers.gcode_backplot_router import router as gcode_backplot_router
except Exception:
    gcode_backplot_router = None

# Patch N.18 — G2/G3 Arc Linkers + Feed Floors
try:
    from .routers.adaptive_poly_gcode_router import router as adaptive_poly_gcode_router
except Exception:
    adaptive_poly_gcode_router = None

# Art Studio v16.0 — SVG Editor + Relief Mapper
try:
    from .routers.cam_svg_v160_router import router as cam_svg_v160_router
except Exception:
    cam_svg_v160_router = None

try:
    from .routers.cam_relief_v160_router import router as cam_relief_v160_router
except Exception:
    cam_relief_v160_router = None

# Art Studio v16.1 — Helical Z-Ramping
try:
    from .routers.cam_helical_v161_router import router as cam_helical_v161_router
except Exception:
    cam_helical_v161_router = None

# Blueprint Import — Phase 1 & 2 (AI Analysis + SVG/DXF Export)
try:
    from .routers.blueprint_router import router as blueprint_router
except Exception as e:
    print(f"Warning: Could not load blueprint_router: {e}")
    blueprint_router = None

# Blueprint → CAM Bridge (Phase 2 Integration)
try:
    from .routers.blueprint_cam_bridge import router as blueprint_cam_bridge_router
except Exception as e:
    print(f"Warning: Could not load blueprint_cam_bridge: {e}")
    blueprint_cam_bridge_router = None

# Unified CAM Pipeline Router (DXF → Preflight → Adaptive → Post → Sim)
try:
    from .routers.pipeline_router import router as pipeline_router
except Exception as e:
    print(f"Warning: Could not load pipeline_router: {e}")
    pipeline_router = None

# Pipeline Presets (Named machine/post recipes)
try:
    from .routers.pipeline_presets_router import router as pipeline_presets_router
except Exception as e:
    print(f"Warning: Could not load pipeline_presets_router: {e}")
    pipeline_presets_router = None

# DXF → Adaptive Plan (Direct DXF-to-loops conversion)
try:
    from .routers.dxf_plan_router import router as dxf_plan_router
except Exception as e:
    print(f"Warning: Could not load dxf_plan_router: {e}")
    dxf_plan_router = None

# Specialty Module Routers (Archtop, Stratocaster, Smart Guitar)
try:
    from .routers.archtop_router import router as archtop_router
except Exception as e:
    print(f"Warning: Could not load archtop_router: {e}")
    archtop_router = None

try:
    from .routers.stratocaster_router import router as stratocaster_router
except Exception as e:
    print(f"Warning: Could not load stratocaster_router: {e}")
    stratocaster_router = None

try:
    from .routers.smart_guitar_router import router as smart_guitar_router
except Exception as e:
    print(f"Warning: Could not load smart_guitar_router: {e}")
    smart_guitar_router = None

try:
    from .routers.om_router import router as om_router
except Exception as e:
    print(f"Warning: Could not load om_router: {e}")
    om_router = None

import os

app = FastAPI(title="ToolBox API", version="0.2.0")

# CORS configuration
origins = (os.getenv("CORS_ORIGINS") or "").split(",") if os.getenv("CORS_ORIGINS") else []
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(sim_router)
app.include_router(feeds_router)
app.include_router(geometry_router)
app.include_router(tooling_router)
app.include_router(adaptive_router)
app.include_router(machine_router)
app.include_router(cam_opt_router)  # M.2
app.include_router(material_router)  # M.3
app.include_router(cam_metrics_router)  # M.3
app.include_router(cam_logs_router)  # M.4
app.include_router(cam_learn_router)  # M.4

# Patch N.12: Machine Tool Tables
if machines_tools_router:
    app.include_router(machines_tools_router)

# Patch N.14: Unified CAM Settings
if posts_router:
    app.include_router(posts_router)
if machines_router:
    app.include_router(machines_router)
if adaptive_preview_router:
    app.include_router(adaptive_preview_router)

# v13: Art Studio preview infill endpoint
if cam_vcarve_router:
    app.include_router(cam_vcarve_router)

# v15.5: Art Studio post-processor (CRC + Lead-in/out + Corner smoothing)
if cam_post_v155_router:
    app.include_router(cam_post_v155_router)

# v15.5: Art Studio smoke test (validates all presets)
if cam_smoke_v155_router:
    app.include_router(cam_smoke_v155_router)

# Patch N.15: G-code backplot and time estimation
if gcode_backplot_router:
    app.include_router(gcode_backplot_router)

# Patch N.18: Adaptive poly offset-spiral with G2/G3 arcs + feed floors
if adaptive_poly_gcode_router:
    app.include_router(adaptive_poly_gcode_router)

# Art Studio v16.0: SVG Editor and Relief Mapper
if cam_svg_v160_router:
    app.include_router(cam_svg_v160_router)
if cam_relief_v160_router:
    app.include_router(cam_relief_v160_router)

# Art Studio v16.1: Helical Z-Ramping
if cam_helical_v161_router:
    app.include_router(cam_helical_v161_router)

# Blueprint Import: Phase 1 & 2 (AI analysis + SVG/DXF export)
if blueprint_router:
    app.include_router(blueprint_router)

# Blueprint → CAM Bridge: Phase 2 Integration (DXF → Adaptive pocket)
if blueprint_cam_bridge_router:
    app.include_router(blueprint_cam_bridge_router)

# Unified CAM Pipeline: Full workflow (DXF → Preflight → Adaptive → Post → Sim)
if pipeline_router:
    app.include_router(pipeline_router)

# Pipeline Presets: Named machine/post recipes for quick setup
if pipeline_presets_router:
    app.include_router(pipeline_presets_router)

# DXF → Adaptive Plan: Direct DXF-to-loops conversion endpoint
if dxf_plan_router:
    app.include_router(dxf_plan_router)

# Specialty Modules: Archtop, Stratocaster, Smart Guitar, OM
if archtop_router:
    app.include_router(archtop_router)

if stratocaster_router:
    app.include_router(stratocaster_router)

if smart_guitar_router:
    app.include_router(smart_guitar_router)

if om_router:
    app.include_router(om_router)
    app.include_router(smart_guitar_router)

@app.get("/health")
def health():
    return {"ok": True}
