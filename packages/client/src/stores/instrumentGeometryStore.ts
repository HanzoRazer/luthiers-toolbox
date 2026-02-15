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
    };
  }
);
