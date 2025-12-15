Here’s a drop-in markdown doc you can save as:
docs/SawLab/Saw_Physics_Debugger.md

Saw Physics Debugger – Developer Notes
Subsystem: Saw Lab 2.0
Audience: Developers working on RMOS / Saw Lab / Art Studio integration
Purpose: Explain how to use the Saw Physics Debug API + UI panel to inspect saw-specific physics (rim speed, bite, heat, kickback, deflection) for a given design + context.

1. What This Is
The Saw Physics Debugger is a read-only diagnostics tool wired into Saw Lab 2.0.
It lets you:


See what the physics layer thinks about a saw configuration.


Inspect individual risk channels:


Rim speed


Bite per tooth


Heat / burn


Kickback


Deflection




View an overall severity bucket (GREEN / YELLOW / RED) and dominant risk channel.


It is not used to generate toolpaths or make production decisions directly.
Instead, it surfaces the same signals RMOS feasibility uses, in a panel that humans can read.

2. Backend: /api/saw/physics-debug
2.1 Route
Method: POST
Path: /api/saw/physics-debug
Module: saw_lab/debug_router.py
Signature:
@router.post("/physics-debug", response_model=SawPhysicsDebugResponse)
def get_saw_physics_debug(
    design: RosetteParamSpec,
    context: RmosContext,
) -> SawPhysicsDebugResponse:
    ...

Precondition:


context.tool_id must start with "saw:", otherwise the endpoint returns 400.


2.2 Request payload


design: RosetteParamSpec


The same schema used for RMOS feasibility / toolpath planning (e.g. rosette params).




context: RmosContext


The same context object used by RMOS 2.0 (material_id, tool_id, search_budget, etc.).




2.3 Response model
Defined in saw_lab/debug_schemas.py:
class SawPhysicsDebugResponse(BaseModel):
    rim_speed: SawRimSpeedResult
    bite: SawBiteResult
    heat: SawHeatResult
    deflection: SawDeflectionResult
    kickback: SawKickbackResult
    summary: SawPhysicsSummary

    raw_tool_id: str
    raw_material_id: str
    raw_feed_mm_min: float
    raw_rpm: float

SawPhysicsSummary contains:


max_risk: float (0..1)


dominant_channel: str ("heat" | "kickback" | "deflection" | "rimspeed" | "bite" | "none")


severity_bucket: str ("GREEN" | "YELLOW" | "RED")



3. What It Actually Does
Internally, the debug router:


Builds a SawCutContext from design + context (blade + material + feed + rpm).


Calls the same calculators used elsewhere:


compute_rim_speed(cut_ctx)


compute_bite_per_tooth(cut_ctx)


compute_saw_heat_risk(cut_ctx, cfg)


compute_saw_deflection(cut_ctx)


compute_kickback_risk(cut_ctx, cfg)




Computes a summary:


Finds the highest risk among the five channels.


Tags that as the dominant_channel.


Maps the max risk to GREEN / YELLOW / RED.




There is no custom physics logic in the debugger.
It is just a caller + aggregator of existing Saw Lab calculators.

4. Frontend Contract (Art Studio / RMOS UI)
4.1 TypeScript types
Defined in something like src/api/types/sawPhysics.ts:
export interface SawPhysicsDebugResponse {
  rim_speed: SawRimSpeedResult;
  bite: SawBiteResult;
  heat: SawHeatResult;
  deflection: SawDeflectionResult;
  kickback: SawKickbackResult;
  summary: SawPhysicsSummary;

  raw_tool_id: string;
  raw_material_id: string;
  raw_feed_mm_min: number;
  raw_rpm: number;
}

And a small client helper:
export async function fetchSawPhysicsDebug(
  design: RosetteParamSpec,
  context: RmosContext
): Promise<SawPhysicsDebugResponse> {
  const resp = await fetch("/api/saw/physics-debug", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ design, context }),
  });
  if (!resp.ok) {
    throw new Error(`Saw physics debug failed: ${resp.status}`);
  }
  return resp.json();
}

4.2 UI component
The main UI element is a panel (e.g. SawPhysicsDebugPanel.vue) that:


Shows an overall severity chip (GREEN / YELLOW / RED).


Displays a dominant risk channel (Heat / Kickback / Deflection / Rim Speed / Bite).


Renders per-channel cards:


value (e.g. m/min, mm/tooth, mm deflection)


risk percentage (risk_score × 100)


warning message, if present.




Echoes raw context (tool, material, feed, rpm) for debugging.


Typical usage:


Render the panel when:


A design is loaded and


context.tool_id starts with "saw:".




Trigger a refresh when:


Tool selection changes,


Material changes,


Feed/RPM parameters change,


Or the user explicitly clicks a “Recompute Saw Physics” button.





5. How to Use It as a Developer
5.1 Tuning physics
When tweaking any of:


Rim speed model (saw_rimspeed.py)


Bite model (saw_bite_load.py)


Heat model (saw_heat.py)


Deflection model (saw_deflection.py)


Kickback model (saw_kickback.py)


you can:


Start the dev server.


Load an Art Studio / RMOS page using a saw tool.


Open the Saw Physics Debug Panel.


Adjust tuning constants and immediately see:


Risk scores change.


Warnings change.


Summary severity/bucket update.




This gives you fast feedback without running full feasibility or toolpath flows.
5.2 Debugging weird behavior
If RMOS marks a saw configuration as RED and you’re not sure why:


Call /api/saw/physics-debug with the same design + context.


Check which channel has the highest risk.


Inspect that specific calculator and its tuning.


The debugger makes it obvious whether the bottleneck is:


heat vs. kickback vs. deflection vs. rim speed vs. bite.



6. Safety / Policy Notes


This endpoint is read-only and does not commit any changes.


It should never:


Create or modify toolpaths


Alter stored projects


Change machine profiles




It is intended for:


Developer tuning,


Advanced operator diagnostics,


UI display only when a saw tool is active.




Downstream safety decisions still flow through RMOS feasibility and the broader policy system.

7. Future Extensions
Possible future enhancements:


Add blade + material IDs resolved from real libraries instead of placeholders.


Allow optional “what-if” overrides in the request (e.g. try different RPM/feed without changing the actual context).


Add history / logging of physics snapshots for a given project or job.


Hook into an AI assistant that can suggest parameter changes (e.g. “reduce RPM by 10% to move from RED to YELLOW on heat & kickback”).



TL;DR


Saw Physics Debugger = a window into Saw Lab 2.0 physics.


Endpoint: /api/saw/physics-debug, POST, RosetteParamSpec + RmosContext.


Returns per-channel risk + an overall severity summary.


Used in UI panels for tuning, debugging, and safety transparency.

