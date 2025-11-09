/**
 * CAM Pipeline API Client
 * 
 * Unified CAM workflow: DXF → Preflight → Adaptive → Post → Sim
 * Part of Art Studio v16.1 integration.
 */

const base = (import.meta as any).env?.VITE_API_BASE || "/api";

export type Design = {
  source: "dxf" | "svg" | "blueprint";
  dxf_path?: string;
  svg_path?: string;
  blueprint_path?: string;
  units: "mm" | "inch";
};

export type PipelineContext = {
  machine_profile_id?: string | null;
  post_preset?: string | null;
  workspace_id?: string | null;
};

export type PipelineOp = {
  id: string;
  op: string;
  from_layer?: string;
  from_op?: string;
  input?: Record<string, any>;
};

export type PipelineRunIn = {
  design: Design;
  context: PipelineContext;
  ops: PipelineOp[];
};

export type PipelineRunOut = {
  results: Record<string, any>;
  gcode: string;
  summary?: Record<string, any>;
};

async function postJson<T>(url: string, body: any): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Run unified CAM pipeline
 * 
 * @param payload - Design, context, and operations
 * @returns Pipeline results with final G-code
 */
export const runPipeline = (payload: PipelineRunIn) =>
  postJson<PipelineRunOut>(`${base}/pipeline/run`, payload);
