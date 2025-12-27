/**
 * CAM Endpoint Types (H8.3)
 *
 * Typed payload and return shapes for CAM endpoints.
 * Keep loose until schemas freeze, then tighten progressively.
 */

/** CAM summary metadata (from X-CAM-Summary header) */
export type CamSummary = Record<string, unknown> & {
  intent_issues?: unknown[]; // tighten to Issue[] when schema freezes
  metrics?: {
    gcode_lines?: number;
    toolpath_length_mm?: number;
    estimated_time_sec?: number;
  };
};

/** Legacy roughing G-code request */
export type RoughingGcodeRequest = {
  entities: unknown[]; // tighten when entity schema freezes
  tool_diameter: number;
  depth_per_pass: number;
  stock_thickness: number;
  feed_xy: number;
  feed_z: number;
  safe_z: number;
  tabs_count: number;
  tab_width: number;
  tab_height: number;
  post: string;
};

/** Roughing G-code result (legacy + intent-native) */
export type RoughingGcodeResult = {
  gcode: string;
  summary: CamSummary | null;
  requestId?: string;
};

/** Intent normalization result */
export type NormalizeCamIntentResult<TIntent = unknown> = {
  intent: TIntent;
  issues: unknown[]; // tighten to Issue[] when schema freezes
  requestId?: string;
};

/** CAM pipeline run result (FormData surface) */
export type PipelineRunResult = {
  result: unknown; // keep loose until backend response stabilizes
  requestId?: string;
};
