/**
 * CAM Advisor Store (Wave 12)
 *
 * Pinia store for AI-CAM operations:
 * - Cut operation analysis
 * - G-code explanation
 * - Parameter optimization
 */
import { defineStore } from "pinia";
import { api } from '@/services/apiBase';

export type CamSeverity = "info" | "warning" | "error";

export interface CamAdvisory {
  message: string;
  severity: CamSeverity;
  context?: Record<string, unknown> | null;
}

export interface CamPhysicsResults {
  chipload?: Record<string, unknown> | null;
  heat?: Record<string, unknown> | null;
  deflection?: Record<string, unknown> | null;
  rim_speed?: Record<string, unknown> | null;
  kickback?: Record<string, unknown> | null;
  [key: string]: unknown;
}

export interface CamRecommendedChanges {
  feed_mm_min?: number | null;
  rpm?: number | null;
  depth_of_cut_mm?: number | null;
  width_of_cut_mm?: number | null;
  note?: string | null;
  [key: string]: unknown;
}

export interface CamAnalysisState {
  loading: boolean;
  advisories: CamAdvisory[];
  recommendedChanges: CamRecommendedChanges | null;
  physics: CamPhysicsResults | null;
  lastError: string | null;
}

export interface CutOperationPayload {
  tool_id: string;
  material_id: string;
  tool_kind: "router_bit" | "saw_blade";
  feed_mm_min: number;
  rpm: number;
  depth_of_cut_mm: number;
  width_of_cut_mm?: number | null;
  machine_id?: string | null;
}

export interface GCodeExplanationLine {
  line_number: number;
  raw: string;
  explanation: string;
  risk?: string | null;
}

export interface GCodeExplainerState {
  loading: boolean;
  lines: GCodeExplanationLine[];
  overallRisk: string | null;
  lastError: string | null;
}

export interface OptimizationCandidate {
  feed_mm_min: number;
  rpm: number;
  depth_of_cut_mm: number;
  width_of_cut_mm?: number | null;
  score: number;
  physics: CamPhysicsResults;
  notes: string[];
}

export interface OptimizationState {
  loading: boolean;
  candidates: OptimizationCandidate[];
  best: OptimizationCandidate | null;
  lastError: string | null;
}

export const useCamAdvisorStore = defineStore("camAdvisor", {
  state: (): CamAnalysisState & { gcode: GCodeExplainerState } & {
    optimization: OptimizationState;
  } => ({
    // Analysis state
    loading: false,
    advisories: [],
    recommendedChanges: null,
    physics: null,
    lastError: null,
    // G-code explainer state
    gcode: {
      loading: false,
      lines: [],
      overallRisk: null,
      lastError: null,
    },
    // Optimization state
    optimization: {
      loading: false,
      candidates: [],
      best: null,
      lastError: null,
    },
  }),

  getters: {
    hasErrors(state): boolean {
      return state.advisories.some((a) => a.severity === "error");
    },
    hasWarnings(state): boolean {
      return state.advisories.some((a) => a.severity === "warning");
    },
    hasHighRiskGcode(state): boolean {
      return state.gcode.overallRisk === "high";
    },
    errorCount(state): number {
      return state.advisories.filter((a) => a.severity === "error").length;
    },
    warningCount(state): number {
      return state.advisories.filter((a) => a.severity === "warning").length;
    },
  },

  actions: {
    /**
     * Analyze a cut operation for physics-based advisories.
     */
    async analyzeOperation(payload: CutOperationPayload): Promise<void> {
      this.loading = true;
      this.lastError = null;
      this.advisories = [];
      this.recommendedChanges = null;
      this.physics = null;

      try {
        const res = await api("/api/ai-cam/analyze-operation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Server error ${res.status}: ${errorText}`);
        }

        const data = await res.json();

        this.advisories = (data.advisories || []) as CamAdvisory[];
        this.recommendedChanges = (data.recommended_changes ||
          data.recommendedChanges ||
          null) as CamRecommendedChanges | null;
        this.physics = (data.physics || null) as CamPhysicsResults | null;
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Unknown error during analysis";
        this.lastError = msg;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Explain G-code line by line.
     */
    async explainGcode(gcodeText: string, safeZ: number = 5.0): Promise<void> {
      this.gcode.loading = true;
      this.gcode.lastError = null;
      this.gcode.lines = [];
      this.gcode.overallRisk = null;

      try {
        const res = await api("/api/ai-cam/explain-gcode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ gcode_text: gcodeText, safe_z: safeZ }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Server error ${res.status}: ${errorText}`);
        }

        const data = await res.json();
        this.gcode.overallRisk = data.overall_risk || data.overallRisk || null;
        this.gcode.lines = (data.explanations ||
          data.lines ||
          []) as GCodeExplanationLine[];
      } catch (err: unknown) {
        const msg =
          err instanceof Error
            ? err.message
            : "Unknown error during G-code explain";
        this.gcode.lastError = msg;
      } finally {
        this.gcode.loading = false;
      }
    },

    /**
     * Search for optimized parameters.
     */
    async optimizeParameters(
      payload: CutOperationPayload,
      searchPct: number = 0.1
    ): Promise<void> {
      this.optimization.loading = true;
      this.optimization.lastError = null;
      this.optimization.candidates = [];
      this.optimization.best = null;

      try {
        const res = await api("/api/ai-cam/optimize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...payload, search_pct: searchPct }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Server error ${res.status}: ${errorText}`);
        }

        const data = await res.json();
        this.optimization.candidates = (data.candidates ||
          []) as OptimizationCandidate[];
        this.optimization.best = (data.best ||
          null) as OptimizationCandidate | null;
      } catch (err: unknown) {
        const msg =
          err instanceof Error
            ? err.message
            : "Unknown error during optimization";
        this.optimization.lastError = msg;
      } finally {
        this.optimization.loading = false;
      }
    },

    /**
     * Clear all state.
     */
    clearAll(): void {
      this.loading = false;
      this.advisories = [];
      this.recommendedChanges = null;
      this.physics = null;
      this.lastError = null;
      this.gcode = {
        loading: false,
        lines: [],
        overallRisk: null,
        lastError: null,
      };
      this.optimization = {
        loading: false,
        candidates: [],
        best: null,
        lastError: null,
      };
    },
  },
});
