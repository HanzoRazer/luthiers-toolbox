/**
 * Instrument Geometry Store (Wave 15-16, updated Wave 20)
 *
 * Manages fretboard geometry, CAM preview, and feasibility scoring for instrument construction.
 * Integrates with backend Wave 17-18 endpoints for unified CAM + feasibility analysis.
 *
 * Wave 20 Migration:
 * - INSTRUMENT_MODELS now loaded from API (not hardcoded)
 * - Uses instrumentApi service for canonical paths
 * - Falls back to FALLBACK_MODELS on API failure
 */

import { defineStore } from "pinia";
import { ref, computed, onMounted } from "vue";
import { api } from '@/services/apiBase';
import {
  fetchInstrumentModels,
  FALLBACK_MODELS,
  type InstrumentModel as ApiInstrumentModel,
} from "@/services/instrumentApi";

// ============================================================================
// Types
// ============================================================================

// --- Setup Evaluation Types (Phase 0) ---
export interface SetupIssue {
  parameter: string;
  current_value: number;
  recommended_range: [number, number];
  gate: "GREEN" | "YELLOW" | "RED";
  fix: string;
}

export interface SetupCascadeResponse {
  state: Record<string, number>;
  issues: SetupIssue[];
  overall_gate: "GREEN" | "YELLOW" | "RED";
  summary: string;
  suggestions: string[];
}

export interface SetupStateRequest {
  neck_angle_deg: number;
  truss_rod_relief_mm: number;
  action_at_nut_mm: number;
  action_at_12th_treble_mm: number;
  action_at_12th_bass_mm: number;
  saddle_height_mm: number;
  saddle_projection_mm: number;
  scale_length_mm: number;
  fretboard_height_at_joint_mm: number;
  neck_joint_fret: number;
}

// --- String Tension Types (Phase 0) ---
export interface StringTensionResult {
  name: string;
  gauge_inch: number;
  gauge_mm: number;
  note: string;
  is_wound: boolean;
  tension_lb: number;
  tension_n: number;
}

export interface StringTensionResponse {
  scale_length_mm: number;
  set_name: string;
  strings: StringTensionResult[];
  total_tension_lb: number;
  total_tension_n: number;
}

export interface StringPresetsResponse {
  string_sets: string[];
  scale_lengths_mm: Record<string, number>;
}

// --- Bridge Types (Phase 0) ---
export interface BridgeSpec {
  body_style: string;
  string_spacing_mm: number;
  bridge_length_mm: number;
  bridge_width_mm: number;
  saddle_slot_width_mm: number;
  saddle_slot_depth_mm: number;
  pin_spacing_mm: number;
  bridge_plate_length_mm: number;
  bridge_plate_width_mm: number;
  material: string;
  gate: string;
  string_count: number;
  notes: string[];
}

// --- Saddle Compensation Types (Phase 0) ---
export interface StringCompensationResult {
  name: string;
  x_mm: number;
  compensation_mm: number;
  fitted_compensation_mm: number;
  residual_mm: number;
}

export interface StraightSaddleFit {
  slope: number;
  intercept_mm: number;
  slant_angle_deg: number;
  r_squared: number;
}

export interface DesignCompensationResponse {
  scale_length_mm: number;
  string_results: StringCompensationResult[];
  saddle_fit: StraightSaddleFit;
  max_residual_mm: number;
  avg_compensation_mm: number;
  recommendation: string;
}

export interface StringSetupResult {
  name: string;
  x_mm: number;
  current_comp_mm: number;
  cents_error: number;
  delta_L_mm: number;
  new_comp_mm: number;
}

export interface SetupCompensationResponse {
  scale_length_mm: number;
  string_results: StringSetupResult[];
  avg_adjustment_mm: number;
  max_adjustment_mm: number;
  recommendation: string;
}

// --- NECK-A Relief Workflow Types (Phase 3) ---
export type DiagnosticGate = "green" | "yellow" | "red";

export interface ReliefDiagnosticResult {
  id: string;
  gate: DiagnosticGate;
  message: string;
  measurement: number | null;
  target_min: number | null;
  target_max: number | null;
  probable_causes: string[];
  recommended_actions: string[];
}

export interface ReliefWorkflowRequest {
  relief_mm: number;
  target_min_mm?: number;
  target_max_mm?: number;
}

// --- NECK-A Action Workflow Types (Phase 4) ---
export interface ActionWorkflowResponse {
  current_step: string;
  overall_gate: DiagnosticGate;
  diagnostics: ReliefDiagnosticResult[];
}

export interface ActionWorkflowRequest {
  treble_action_mm: number;
  bass_action_mm: number;
  treble_target_min_mm?: number;
  treble_target_max_mm?: number;
  bass_target_min_mm?: number;
  bass_target_max_mm?: number;
}

// --- NECK-A Nut Slot Workflow Types (Phase 5) ---
export interface NutWorkflowResponse {
  current_step: string;
  overall_gate: DiagnosticGate;
  diagnostics: ReliefDiagnosticResult[];
}

export interface NutWorkflowRequest {
  clearances_mm: number[];
  treble_target_min_mm?: number;
  treble_target_max_mm?: number;
  bass_target_min_mm?: number;
  bass_target_max_mm?: number;
}

// --- NECK-A Combined Diagnostics Types (Phase 6) ---
export interface CombinedDiagnostic {
  id: string;
  gate: DiagnosticGate;
  message: string;
  contributing_factors: string[];
  recommendation: string;
}

export interface CombinedDiagnosticsResponse {
  overall_gate: DiagnosticGate;
  diagnostics: CombinedDiagnostic[];
}

export interface FretboardSpec {
  scale_length_mm: number;
  num_frets: number;
  nut_width_mm: number;
  bridge_width_mm: number;
  base_radius_inches: number;
  end_radius_inches: number;
  slot_width_mm: number;
  slot_depth_mm: number;
  material_id?: string;
}

export interface ToolpathSummary {
  fret_number: number;
  position_mm: number;
  width_mm: number;
  depth_mm: number;
  tool_id: string;
  feed_rate: number;
  spindle_rpm: number;
  cut_time_s: number;
  cost_usd: number;
}

export interface CAMStatistics {
  total_time_s: number;
  total_cost_usd: number;
  total_energy_kwh: number;
  slot_count: number;
  total_length_mm: number;
}

export interface FeasibilityReport {
  overall_score: number;
  overall_risk: "GREEN" | "YELLOW" | "RED" | "UNKNOWN";
  is_feasible: boolean;
  needs_review: boolean;
  recommendations: string[];
}

export interface FretSlotPreviewResponse {
  toolpaths: ToolpathSummary[];
  dxf_preview: string;
  gcode_preview: string;
  statistics: CAMStatistics;
  feasibility_score: number;
  feasibility_risk: "GREEN" | "YELLOW" | "RED" | "UNKNOWN";
  is_feasible: boolean;
  needs_review: boolean;
  recommendations: string[];
  dxf_download_url: string;
  gcode_download_url: string;
}

export interface InstrumentModel {
  id: string;
  display_name: string;
  scale_length_mm: number;
  num_frets: number;
  nut_width_mm: number;
  bridge_width_mm: number;
}

/**
 * LEGACY: Static fallback models.
 * Wave 20: Models now loaded from API via loadInstrumentModels().
 * This constant kept for backwards compatibility and offline fallback.
 * @deprecated Use loadInstrumentModels() action instead
 */
export const INSTRUMENT_MODELS: InstrumentModel[] = [
  {
    id: "strat_25_5",
    display_name: 'Fender Stratocaster (25.5")',
    scale_length_mm: 647.7,
    num_frets: 22,
    nut_width_mm: 42.0,
    bridge_width_mm: 56.0,
  },
  {
    id: "lp_24_75",
    display_name: 'Gibson Les Paul (24.75")',
    scale_length_mm: 628.65,
    num_frets: 22,
    nut_width_mm: 43.0,
    bridge_width_mm: 52.0,
  },
  {
    id: "tele_25_5",
    display_name: 'Fender Telecaster (25.5")',
    scale_length_mm: 647.7,
    num_frets: 22,
    nut_width_mm: 42.5,
    bridge_width_mm: 54.0,
  },
  {
    id: "prs_25",
    display_name: 'PRS Custom (25")',
    scale_length_mm: 635.0,
    num_frets: 22,
    nut_width_mm: 42.9,
    bridge_width_mm: 55.0,
  },
];

// ============================================================================
// Store Definition
// ============================================================================

export const useInstrumentGeometryStore = defineStore(
  "instrumentGeometry",
  () => {
    // ===== State =====

    // Selected model
    const selectedModelId = ref<string>("strat_25_5");

    // Dynamic model list (loaded from API)
    const instrumentModels = ref<InstrumentModel[]>(INSTRUMENT_MODELS);
    const isLoadingModels = ref(false);
    const modelsLoadError = ref<string | null>(null);
    const modelsLoadedFromApi = ref(false);

    // Fretboard specification
    const fretboardSpec = ref<FretboardSpec>({
      scale_length_mm: 647.7,
      num_frets: 22,
      nut_width_mm: 42.0,
      bridge_width_mm: 56.0,
      base_radius_inches: 9.5,
      end_radius_inches: 12.0,
      slot_width_mm: 0.6,
      slot_depth_mm: 3.0,
      material_id: "rosewood",
    });

    // CAM preview response
    const previewResponse = ref<FretSlotPreviewResponse | null>(null);

    // Loading states
    const isLoadingPreview = ref(false);
    const previewError = ref<string | null>(null);

    // Fan-fret mode (Wave 16 enhancement → Wave 19 implementation)
    const fanFretEnabled = ref(false);
    const trebleScaleLength = ref(647.7);
    const bassScaleLength = ref(660.4); // +0.5" typical
    const perpendicularFret = ref(7); // Default perpendicular fret

    // ===== Phase 0: Setup Evaluation State =====
    const setupEvaluation = ref<SetupCascadeResponse | null>(null);
    const setupLoading = ref(false);
    const setupError = ref<string | null>(null);
    const setupRequest = ref<SetupStateRequest>({
      neck_angle_deg: 1.5,
      truss_rod_relief_mm: 0.25,
      action_at_nut_mm: 0.5,
      action_at_12th_treble_mm: 1.9,
      action_at_12th_bass_mm: 2.4,
      saddle_height_mm: 3.0,
      saddle_projection_mm: 2.5,
      scale_length_mm: 647.7,
      fretboard_height_at_joint_mm: 5.0,
      neck_joint_fret: 14,
    });

    // ===== Phase 0: String Tension State =====
    const stringTensionResult = ref<StringTensionResponse | null>(null);
    const stringTensionLoading = ref(false);
    const stringTensionError = ref<string | null>(null);
    const selectedStringSet = ref<string>("light_012");
    const stringPresets = ref<string[]>([]);

    // ===== Phase 0: Bridge State =====
    const bridgeOptions = ref<string[]>([]);
    const selectedBridgeStyle = ref<string>("dreadnought");
    const bridgeSpec = ref<BridgeSpec | null>(null);
    const bridgeLoading = ref(false);
    const bridgeError = ref<string | null>(null);

    // ===== Phase 0: Saddle Compensation State =====
    const saddleCompensationMode = ref<"design" | "setup">("design");
    const saddleDesignResult = ref<DesignCompensationResponse | null>(null);
    const saddleSetupResult = ref<SetupCompensationResponse | null>(null);
    const saddleLoading = ref(false);
    const saddleError = ref<string | null>(null);

    // ===== NECK-A Phase 3: Relief Workflow State =====
    const reliefWorkflowResult = ref<ReliefDiagnosticResult | null>(null);
    const reliefWorkflowLoading = ref(false);
    const reliefWorkflowError = ref<string | null>(null);
    const reliefMeasurement = ref<number>(0.20);
    const reliefTargetMin = ref<number>(0.10);
    const reliefTargetMax = ref<number>(0.30);

    // ===== NECK-A Phase 4: Action Workflow State =====
    const actionWorkflowResult = ref<ActionWorkflowResponse | null>(null);
    const actionWorkflowLoading = ref(false);
    const actionWorkflowError = ref<string | null>(null);
    const trebleActionMeasurement = ref<number>(1.50);
    const bassActionMeasurement = ref<number>(2.00);
    const trebleActionTargetMin = ref<number>(1.25);
    const trebleActionTargetMax = ref<number>(1.75);
    const bassActionTargetMin = ref<number>(1.75);
    const bassActionTargetMax = ref<number>(2.25);

    // ===== NECK-A Phase 5: Nut Slot Workflow State =====
    const nutWorkflowResult = ref<NutWorkflowResponse | null>(null);
    const nutWorkflowLoading = ref(false);
    const nutWorkflowError = ref<string | null>(null);
    // Default clearances: [high E, B, G, D, A, low E]
    const nutClearancesMm = ref<number[]>([0.25, 0.25, 0.25, 0.30, 0.30, 0.30]);
    const nutTrebleTargetMin = ref<number>(0.20);
    const nutTrebleTargetMax = ref<number>(0.30);
    const nutBassTargetMin = ref<number>(0.25);
    const nutBassTargetMax = ref<number>(0.40);

    // NECK-A Phase 6: Combined Diagnostics State
    const combinedDiagnosticsResult = ref<CombinedDiagnosticsResponse | null>(null);
    const combinedDiagnosticsLoading = ref(false);
    const combinedDiagnosticsError = ref<string | null>(null);

    // ===== Computed =====

    const selectedModel = computed(() => {
      return (
        instrumentModels.value.find((m) => m.id === selectedModelId.value) ||
        instrumentModels.value[0]
      );
    });

    /** All available models (for UI selectors) */
    const availableModels = computed(() => instrumentModels.value);

    const toolpaths = computed(() => previewResponse.value?.toolpaths || []);

    const statistics = computed(
      () =>
        previewResponse.value?.statistics || {
          total_time_s: 0,
          total_cost_usd: 0,
          total_energy_kwh: 0,
          slot_count: 0,
          total_length_mm: 0,
        }
    );

    const feasibility = computed((): FeasibilityReport => {
      if (!previewResponse.value) {
        return {
          overall_score: 0,
          overall_risk: "UNKNOWN",
          is_feasible: false,
          needs_review: false,
          recommendations: [],
        };
      }

      return {
        overall_score: previewResponse.value.feasibility_score,
        overall_risk: previewResponse.value.feasibility_risk,
        is_feasible: previewResponse.value.is_feasible,
        needs_review: previewResponse.value.needs_review,
        recommendations: previewResponse.value.recommendations,
      };
    });

    const riskColor = computed(() => {
      switch (feasibility.value.overall_risk) {
        case "GREEN":
          return "#22c55e";
        case "YELLOW":
          return "#eab308";
        case "RED":
          return "#ef4444";
        default:
          return "#6b7280";
      }
    });

    const riskLabel = computed(() => {
      switch (feasibility.value.overall_risk) {
        case "GREEN":
          return "Safe";
        case "YELLOW":
          return "Caution";
        case "RED":
          return "Warning";
        default:
          return "Unknown";
      }
    });

    // ===== Actions =====

    /**
     * Load model by ID and update fretboard spec
     */
    function selectModel(modelId: string) {
      const model = instrumentModels.value.find((m) => m.id === modelId);
      if (!model) {
        console.warn(`Unknown model ID: ${modelId}`);
        return;
      }

      selectedModelId.value = modelId;

      // Update fretboard spec from model
      fretboardSpec.value.scale_length_mm = model.scale_length_mm;
      fretboardSpec.value.num_frets = model.num_frets;
      fretboardSpec.value.nut_width_mm = model.nut_width_mm;
      fretboardSpec.value.bridge_width_mm = model.bridge_width_mm;

      // Clear preview (will be regenerated on next generatePreview call)
      previewResponse.value = null;
    }

    /**
     * Generate CAM preview with feasibility scoring (Wave 17-18 Phase E endpoint)
     */
    async function generatePreview() {
      isLoadingPreview.value = true;
      previewError.value = null;

      try {
        const requestBody: any = {
          model_id: selectedModelId.value,
          mode: fanFretEnabled.value ? "fan" : "standard",
          fret_count: fretboardSpec.value.num_frets,
          nut_width_mm: fretboardSpec.value.nut_width_mm,
          heel_width_mm: fretboardSpec.value.bridge_width_mm,
          slot_width_mm: fretboardSpec.value.slot_width_mm,
          slot_depth_mm: fretboardSpec.value.slot_depth_mm,
          post_id: "GRBL",
        };

        // Add fan-fret specific parameters
        if (fanFretEnabled.value) {
          requestBody.treble_scale_mm = trebleScaleLength.value;
          requestBody.bass_scale_mm = bassScaleLength.value;
          requestBody.perpendicular_fret = perpendicularFret.value;
        } else {
          requestBody.scale_length_mm = fretboardSpec.value.scale_length_mm;
        }

        const response = await api("/api/cam/fret_slots/preview", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail ||
              `HTTP ${response.status}: ${response.statusText}`
          );
        }

        const data = await response.json();
        previewResponse.value = data;

        console.log("✓ CAM preview generated:", {
          toolpaths: data.toolpaths.length,
          feasibility: data.feasibility_risk,
          score: data.feasibility_score,
        });
      } catch (err: any) {
        console.error("Failed to generate CAM preview:", err);
        previewError.value = err.message || "Unknown error";
        previewResponse.value = null;
      } finally {
        isLoadingPreview.value = false;
      }
    }

    /**
     * Download DXF file
     */
    async function downloadDxf() {
      if (!previewResponse.value?.dxf_download_url) {
        console.warn("No DXF download URL available");
        return;
      }

      try {
        const response = await fetch(previewResponse.value.dxf_download_url);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `fretboard_${selectedModelId.value}.dxf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log("✓ DXF downloaded");
      } catch (err) {
        console.error("Failed to download DXF:", err);
      }
    }

    /**
     * Download G-code file
     */
    async function downloadGcode() {
      if (!previewResponse.value?.gcode_download_url) {
        console.warn("No G-code download URL available");
        return;
      }

      try {
        const response = await fetch(previewResponse.value.gcode_download_url);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `fretboard_${selectedModelId.value}.nc`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log("✓ G-code downloaded");
      } catch (err) {
        console.error("Failed to download G-code:", err);
      }
    }

    /**
     * Reset to defaults
     */
    function reset() {
      selectModel("strat_25_5");
      previewResponse.value = null;
      previewError.value = null;
      fanFretEnabled.value = false;
    }

    // =========================================================================
    // Phase 0 Actions: Setup Evaluation
    // =========================================================================

    /**
     * Evaluate instrument setup via cascade endpoint
     */
    async function evaluateSetup() {
      setupLoading.value = true;
      setupError.value = null;

      try {
        // Sync scale length from current fretboard spec
        setupRequest.value.scale_length_mm = fretboardSpec.value.scale_length_mm;

        const response = await api("/api/instrument/setup/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(setupRequest.value),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        setupEvaluation.value = await response.json();
        console.log("✓ Setup evaluated:", setupEvaluation.value?.overall_gate);
      } catch (err: any) {
        console.error("Setup evaluation failed:", err);
        setupError.value = err.message || "Unknown error";
        setupEvaluation.value = null;
      } finally {
        setupLoading.value = false;
      }
    }

    // =========================================================================
    // Phase 0 Actions: String Tension
    // =========================================================================

    /**
     * Load string tension presets from backend
     */
    async function loadStringPresets() {
      try {
        const response = await api("/api/instrument/string-tension/presets");
        if (response.ok) {
          const data: StringPresetsResponse = await response.json();
          stringPresets.value = data.string_sets;
        }
      } catch (err) {
        console.warn("Failed to load string presets:", err);
      }
    }

    /**
     * Calculate string tension for current scale length and string set
     */
    async function calculateStringTension() {
      stringTensionLoading.value = true;
      stringTensionError.value = null;

      try {
        const response = await api("/api/instrument/string-tension", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scale_length_mm: fretboardSpec.value.scale_length_mm,
            string_set: selectedStringSet.value,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        stringTensionResult.value = await response.json();
        console.log("✓ String tension calculated:", stringTensionResult.value?.total_tension_lb.toFixed(1), "lb");
      } catch (err: any) {
        console.error("String tension calculation failed:", err);
        stringTensionError.value = err.message || "Unknown error";
        stringTensionResult.value = null;
      } finally {
        stringTensionLoading.value = false;
      }
    }

    // =========================================================================
    // Phase 0 Actions: Bridge
    // =========================================================================

    /**
     * Load bridge body style options
     */
    async function loadBridgeOptions() {
      try {
        const response = await api("/api/instrument/bridge/options");
        if (response.ok) {
          const data = await response.json();
          bridgeOptions.value = data.body_styles;
        }
      } catch (err) {
        console.warn("Failed to load bridge options:", err);
      }
    }

    /**
     * Calculate bridge geometry for selected style
     */
    async function calculateBridge() {
      bridgeLoading.value = true;
      bridgeError.value = null;

      try {
        const response = await api("/api/instrument/bridge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            body_style: selectedBridgeStyle.value,
            scale_length_mm: fretboardSpec.value.scale_length_mm,
            string_count: 6,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        bridgeSpec.value = await response.json();
        console.log("✓ Bridge calculated:", bridgeSpec.value?.body_style);
      } catch (err: any) {
        console.error("Bridge calculation failed:", err);
        bridgeError.value = err.message || "Unknown error";
        bridgeSpec.value = null;
      } finally {
        bridgeLoading.value = false;
      }
    }

    // =========================================================================
    // Phase 0 Actions: Saddle Compensation
    // =========================================================================

    /**
     * Calculate saddle compensation (design mode)
     */
    async function calculateSaddleCompensationDesign() {
      saddleLoading.value = true;
      saddleError.value = null;

      try {
        // String spacing for x_mm calculation
        const bridgeWidth = bridgeSpec.value?.string_spacing_mm || 52.0;
        const stringSpacing = bridgeWidth / 5; // 6 strings, 5 gaps

        // Use string tension data if available, else defaults
        const stringSpecs = stringTensionResult.value?.strings.map((s, i) => ({
          name: s.name,
          gauge_in: s.gauge_inch,
          tension_lb: s.tension_lb,
          is_wound: s.is_wound,
          x_mm: i * stringSpacing,
        })) || [
          { name: "E6", gauge_in: 0.046, tension_lb: 17.5, is_wound: true, x_mm: 0 },
          { name: "A5", gauge_in: 0.036, tension_lb: 19.0, is_wound: true, x_mm: stringSpacing },
          { name: "D4", gauge_in: 0.026, tension_lb: 17.5, is_wound: true, x_mm: stringSpacing * 2 },
          { name: "G3", gauge_in: 0.017, tension_lb: 15.0, is_wound: false, x_mm: stringSpacing * 3 },
          { name: "B2", gauge_in: 0.013, tension_lb: 14.5, is_wound: false, x_mm: stringSpacing * 4 },
          { name: "E1", gauge_in: 0.010, tension_lb: 14.0, is_wound: false, x_mm: stringSpacing * 5 },
        ];

        const response = await api("/api/instrument/bridge/compensation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scale_length_mm: fretboardSpec.value.scale_length_mm,
            action_12th_treble_mm: setupRequest.value.action_at_12th_treble_mm,
            action_12th_bass_mm: setupRequest.value.action_at_12th_bass_mm,
            strings: stringSpecs,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        saddleDesignResult.value = await response.json();
        console.log("✓ Saddle compensation (design) calculated");
      } catch (err: any) {
        console.error("Saddle compensation failed:", err);
        saddleError.value = err.message || "Unknown error";
        saddleDesignResult.value = null;
      } finally {
        saddleLoading.value = false;
      }
    }

    /**
     * Calculate saddle adjustments (setup mode) from cents errors
     */
    async function calculateSaddleCompensationSetup(measurements: Array<{ current_compensation_mm: number; cents_error: number }>) {
      saddleLoading.value = true;
      saddleError.value = null;

      try {
        // String spacing for x_mm calculation
        const bridgeWidth = bridgeSpec.value?.string_spacing_mm || 52.0;
        const stringSpacing = bridgeWidth / 5;
        const stringNames = ["E6", "A5", "D4", "G3", "B2", "E1"];

        const strings = measurements.map((m, i) => ({
          name: stringNames[i] || `S${i + 1}`,
          x_mm: i * stringSpacing,
          current_comp_mm: m.current_compensation_mm,
          cents_error: m.cents_error,
          weight: 1.0,
        }));

        const response = await api("/api/instrument/bridge/setup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scale_length_mm: fretboardSpec.value.scale_length_mm,
            strings,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        saddleSetupResult.value = await response.json();
        console.log("✓ Saddle adjustments (setup) calculated");
      } catch (err: any) {
        console.error("Saddle setup calculation failed:", err);
        saddleError.value = err.message || "Unknown error";
        saddleSetupResult.value = null;
      } finally {
        saddleLoading.value = false;
      }
    }

    // =========================================================================
    // NECK-A Phase 3: Relief Workflow Actions
    // =========================================================================

    /**
     * Evaluate neck relief via NECK-A workflow endpoint
     */
    async function evaluateRelief() {
      reliefWorkflowLoading.value = true;
      reliefWorkflowError.value = null;

      try {
        const response = await api("/api/instrument/setup/workflow/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            relief_mm: reliefMeasurement.value,
            target_min_mm: reliefTargetMin.value,
            target_max_mm: reliefTargetMax.value,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        reliefWorkflowResult.value = await response.json();
        console.log("✓ Relief evaluated:", reliefWorkflowResult.value?.gate);
      } catch (err: any) {
        console.error("Relief evaluation failed:", err);
        reliefWorkflowError.value = err.message || "Unknown error";
        reliefWorkflowResult.value = null;
      } finally {
        reliefWorkflowLoading.value = false;
      }
    }

    // =========================================================================
    // NECK-A Phase 4: Action Workflow Actions
    // =========================================================================

    /**
     * Evaluate action height via NECK-A workflow endpoint
     */
    async function evaluateActionWorkflow() {
      actionWorkflowLoading.value = true;
      actionWorkflowError.value = null;

      try {
        const response = await api("/api/instrument/setup/workflow/action/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            treble_action_mm: trebleActionMeasurement.value,
            bass_action_mm: bassActionMeasurement.value,
            treble_target_min_mm: trebleActionTargetMin.value,
            treble_target_max_mm: trebleActionTargetMax.value,
            bass_target_min_mm: bassActionTargetMin.value,
            bass_target_max_mm: bassActionTargetMax.value,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        actionWorkflowResult.value = await response.json();
        console.log("✓ Action evaluated:", actionWorkflowResult.value?.overall_gate);
      } catch (err: any) {
        console.error("Action evaluation failed:", err);
        actionWorkflowError.value = err.message || "Unknown error";
        actionWorkflowResult.value = null;
      } finally {
        actionWorkflowLoading.value = false;
      }
    }

    // =========================================================================
    // NECK-A Phase 5: Nut Slot Workflow Actions
    // =========================================================================

    /**
     * Evaluate nut slot clearance via NECK-A workflow endpoint
     */
    async function evaluateNutWorkflow() {
      nutWorkflowLoading.value = true;
      nutWorkflowError.value = null;

      try {
        const response = await api("/api/instrument/setup/workflow/nut/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            clearances_mm: nutClearancesMm.value,
            treble_target_min_mm: nutTrebleTargetMin.value,
            treble_target_max_mm: nutTrebleTargetMax.value,
            bass_target_min_mm: nutBassTargetMin.value,
            bass_target_max_mm: nutBassTargetMax.value,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        nutWorkflowResult.value = await response.json();
        console.log("✓ Nut slots evaluated:", nutWorkflowResult.value?.overall_gate);
      } catch (err: any) {
        console.error("Nut slot evaluation failed:", err);
        nutWorkflowError.value = err.message || "Unknown error";
        nutWorkflowResult.value = null;
      } finally {
        nutWorkflowLoading.value = false;
      }
    }

    // =========================================================================
    // NECK-A Phase 6: Combined Diagnostics Actions
    // =========================================================================

    /**
     * Check if all three workflow results exist for combined evaluation
     */
    function canEvaluateCombined(): boolean {
      return (
        reliefWorkflowResult.value !== null &&
        actionWorkflowResult.value !== null &&
        nutWorkflowResult.value !== null
      );
    }

    /**
     * Evaluate combined setup diagnostics via NECK-A workflow endpoint
     */
    async function evaluateCombinedSetup() {
      if (!canEvaluateCombined()) {
        combinedDiagnosticsError.value = "Evaluate Relief, Action, and Nut first.";
        return;
      }

      combinedDiagnosticsLoading.value = true;
      combinedDiagnosticsError.value = null;

      try {
        // Extract gates and diagnostic IDs from existing results
        const reliefGate = reliefWorkflowResult.value!.gate;
        const reliefDiagnosticIds = [reliefWorkflowResult.value!.id];

        const actionGate = actionWorkflowResult.value!.overall_gate;
        const actionDiagnosticIds = actionWorkflowResult.value!.diagnostics.map((d) => d.id);

        const nutGate = nutWorkflowResult.value!.overall_gate;
        const nutDiagnosticIds = nutWorkflowResult.value!.diagnostics.map((d) => d.id);

        const response = await api("/api/instrument/setup/workflow/combined/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            relief_gate: reliefGate,
            relief_diagnostic_ids: reliefDiagnosticIds,
            action_gate: actionGate,
            action_diagnostic_ids: actionDiagnosticIds,
            nut_gate: nutGate,
            nut_diagnostic_ids: nutDiagnosticIds,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        combinedDiagnosticsResult.value = await response.json();
        console.log("✓ Combined setup evaluated:", combinedDiagnosticsResult.value?.overall_gate);
      } catch (err: any) {
        console.error("Combined evaluation failed:", err);
        combinedDiagnosticsError.value = err.message || "Unknown error";
        combinedDiagnosticsResult.value = null;
      } finally {
        combinedDiagnosticsLoading.value = false;
      }
    }

    /**
     * Load instrument models from API (Wave 20 migration).
     * Falls back to static INSTRUMENT_MODELS on error.
     */
    async function loadInstrumentModels() {
      if (modelsLoadedFromApi.value) {
        // Already loaded, skip
        return;
      }

      isLoadingModels.value = true;
      modelsLoadError.value = null;

      try {
        const response = await fetchInstrumentModels();
        
        if (response.ok && response.models.length > 0) {
          // Transform API models to store format
          instrumentModels.value = response.models.map((m) => ({
            id: m.model_id,
            display_name: m.display_name,
            // These will be fetched per-model when selected
            // For now, use reasonable defaults
            scale_length_mm: 647.7,
            num_frets: 22,
            nut_width_mm: 42.0,
            bridge_width_mm: 56.0,
          }));
          modelsLoadedFromApi.value = true;
          console.log(`✓ Loaded ${response.total_models} instrument models from API`);
        } else {
          throw new Error("Empty model list from API");
        }
      } catch (err: any) {
        console.warn("Failed to load models from API, using fallback:", err.message);
        modelsLoadError.value = err.message;
        // Keep using the static INSTRUMENT_MODELS as fallback
        instrumentModels.value = INSTRUMENT_MODELS;
      } finally {
        isLoadingModels.value = false;
      }
    }

    return {
      // State
      selectedModelId,
      fretboardSpec,
      previewResponse,
      isLoadingPreview,
      previewError,
      fanFretEnabled,
      trebleScaleLength,
      bassScaleLength,
      perpendicularFret,
      // Wave 20: Dynamic model loading state
      instrumentModels,
      isLoadingModels,
      modelsLoadError,
      modelsLoadedFromApi,

      // Phase 0: Setup Evaluation State
      setupEvaluation,
      setupLoading,
      setupError,
      setupRequest,

      // Phase 0: String Tension State
      stringTensionResult,
      stringTensionLoading,
      stringTensionError,
      selectedStringSet,
      stringPresets,

      // Phase 0: Bridge State
      bridgeOptions,
      selectedBridgeStyle,
      bridgeSpec,
      bridgeLoading,
      bridgeError,

      // Phase 0: Saddle Compensation State
      saddleCompensationMode,
      saddleDesignResult,
      saddleSetupResult,
      saddleLoading,
      saddleError,

      // NECK-A Phase 3: Relief Workflow State
      reliefWorkflowResult,
      reliefWorkflowLoading,
      reliefWorkflowError,
      reliefMeasurement,
      reliefTargetMin,
      reliefTargetMax,

      // NECK-A Phase 4: Action Workflow State
      actionWorkflowResult,
      actionWorkflowLoading,
      actionWorkflowError,
      trebleActionMeasurement,
      bassActionMeasurement,
      trebleActionTargetMin,
      trebleActionTargetMax,
      bassActionTargetMin,
      bassActionTargetMax,

      // NECK-A Phase 5: Nut Slot Workflow State
      nutWorkflowResult,
      nutWorkflowLoading,
      nutWorkflowError,
      nutClearancesMm,
      nutTrebleTargetMin,
      nutTrebleTargetMax,
      nutBassTargetMin,
      nutBassTargetMax,

      // NECK-A Phase 6: Combined Diagnostics State
      combinedDiagnosticsResult,
      combinedDiagnosticsLoading,
      combinedDiagnosticsError,
      canEvaluateCombined,

      // Computed
      selectedModel,
      availableModels,
      toolpaths,
      statistics,
      feasibility,
      riskColor,
      riskLabel,

      // Actions
      selectModel,
      generatePreview,
      downloadDxf,
      downloadGcode,
      reset,
      loadInstrumentModels,

      // Phase 0 Actions
      evaluateSetup,
      loadStringPresets,
      calculateStringTension,
      loadBridgeOptions,
      calculateBridge,
      calculateSaddleCompensationDesign,
      calculateSaddleCompensationSetup,

      // NECK-A Phase 3 Actions
      evaluateRelief,

      // NECK-A Phase 4 Actions
      evaluateActionWorkflow,

      // NECK-A Phase 5 Actions
      evaluateNutWorkflow,

      // NECK-A Phase 6 Actions
      evaluateCombinedSetup,
    };
  }
);
