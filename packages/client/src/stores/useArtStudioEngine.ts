/**
 * Wave 7: Art Studio Engine Composable (updated Wave 20)
 *
 * Central facade for all Art Studio operations:
 * - Tools & materials loading
 * - Geometry generation (VCarve, Relief, Rosette)
 * - RMOS feasibility evaluation
 * - Toolpath planning
 * - Instrument geometry calculations
 * - Calculator debug integration
 *
 * Wave 20 Migration:
 * - Uses centralized apiBase for URL construction
 * - Rosette uses canonical /api/art/rosette/* paths via artStudioApi
 * - Fallback to legacy paths on 404
 */
import { ref, computed, reactive } from "vue";
import { API_BASE, apiFetchWithFallback, buildUrl } from "@/services/apiBase";
import {
  buildRosetteUrl,
  buildLegacyRosetteUrl,
  generateRosetteGeometry as apiGenerateRosetteGeometry,
  exportRosette as apiExportRosette,
  renderRosettePreview as apiRenderRosettePreview,
  fetchRosettePatterns,
  fetchPatternInfo,
  generateRosetteCam,
  PATTERN_DEFAULTS,
  type RosetteParams,
  type RosetteGeometry,
  type RosetteExportResult,
  type RosettePreviewResult,
  type PatternInfo,
  type PatternType,
  type RosetteCamParams,
  type RosetteCamResult,
} from "@/services/artStudioApi";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MLPoint {
  x: number;
  y: number;
}

export interface MLPath {
  id?: string;
  points: MLPoint[];
  closed: boolean;
  layer?: string;
  meta?: Record<string, unknown>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Wave 9: Risk Types
// ─────────────────────────────────────────────────────────────────────────────
export type RiskLevel = "none" | "info" | "warn" | "fail";

export interface PathRiskAnnotation {
  pathId: string;
  risk: RiskLevel;
  messages: string[];
  tags?: string[];
}

export interface GlobalRiskSummary {
  risk: RiskLevel;
  messages: string[];
}

export interface FeasibilityResult {
  overallScore: number;
  warnings: string[];
  hardFailures: string[];
  globalRisk?: GlobalRiskSummary;
  pathRisks?: PathRiskAnnotation[];
}

export interface ToolSummary {
  tool_id: string;
  type: string;
  name: string;
  diameter_mm?: number | null;
  flutes?: number | null;
}

export interface MaterialSummary {
  material_id: string;
  name: string;
  heat_sensitivity?: string;
  chipload_mm?: { min?: number; max?: number };
}

export interface InstrumentConfig {
  scale_length_mm: number;
  fret_count: number;
  nut_width_mm: number;
  heel_width_mm: number;
  base_radius_mm?: number;
  end_radius_mm?: number;
  extension_mm?: number;
}

export interface FretSlot {
  fret_number: number;
  distance_from_nut_mm: number;
  left: MLPoint;
  right: MLPoint;
}

export interface ChiploadResult {
  chipload_mm: number | null;
  in_range: boolean;
  message: string;
}

export interface HeatResult {
  heat_risk: number;
  category: string;
  message: string;
}

export interface DeflectionResult {
  deflection_mm: number | null;
  risk: string;
  message: string;
}

export interface RimSpeedResult {
  surface_speed_m_per_min: number | null;
  within_limits: boolean;
  message: string;
}

export interface KickbackResult {
  risk_score: number;
  category: string;
  message: string;
}

export interface BitePerToothResult {
  bite_mm: number | null;
  in_range: boolean;
  message: string;
}

export interface CalculatorResult {
  tool_id: string;
  material_id: string;
  tool_kind: string;
  chipload?: ChiploadResult;
  heat?: HeatResult;
  deflection?: DeflectionResult;
  rim_speed?: RimSpeedResult;
  kickback?: KickbackResult;
  bite_per_tooth?: BitePerToothResult;
  warnings: string[];
  hard_failures: string[];
  overall_risk: "GREEN" | "YELLOW" | "RED";
}

export interface CutOperationSpec {
  tool_id: string;
  material_id: string;
  tool_kind: "router_bit" | "saw_blade";
  feed_mm_min: number;
  rpm: number;
  depth_of_cut_mm: number;
  width_of_cut_mm?: number;
  tool_diameter_mm?: number;
  flute_count?: number;
  machine_id?: string;
  profile_id?: string;
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

// Note: API_BASE now imported from @/services/apiBase

// Geometry state
const currentPaths = ref<MLPath[]>([]);
const toolpaths = ref<MLPath[]>([]);

// Tools & Materials
const tools = ref<ToolSummary[]>([]);
const materials = ref<MaterialSummary[]>([]);

// Instrument geometry
const fretPositions = ref<number[]>([]);
const fretSlots = ref<FretSlot[]>([]);
const fretboardOutline = ref<MLPoint[]>([]);
const radiusProfile = ref<number[]>([]);
const bridgeLocationMm = ref<number | null>(null);
const fretboardLengthMm = ref<number | null>(null);

// Feasibility
const feasibility = ref<FeasibilityResult | null>(null);

// Calculator results
const calculatorResult = ref<CalculatorResult | null>(null);

// Loading states
const loading = reactive({
  tools: false,
  materials: false,
  geometry: false,
  feasibility: false,
  toolpaths: false,
  instrument: false,
  calculator: false,
});

// Error state
const lastError = ref<string | null>(null);

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const isFeasible = computed(
  () => !!feasibility.value && feasibility.value.hardFailures.length === 0
);

const hasGeometry = computed(() => currentPaths.value.length > 0);

const hasToolpaths = computed(() => toolpaths.value.length > 0);

const isLoading = computed(() => Object.values(loading).some(Boolean));

// ---------------------------------------------------------------------------
// Wave 9: Risk Computed & Helpers
// ---------------------------------------------------------------------------

/**
 * Map from pathId → PathRiskAnnotation for O(1) lookups
 */
const pathRiskMap = computed(() => {
  const map = new Map<string, PathRiskAnnotation>();
  if (feasibility.value?.pathRisks) {
    for (const pr of feasibility.value.pathRisks) {
      map.set(pr.pathId, pr);
    }
  }
  return map;
});

/**
 * Get the risk level for a specific path (defaults to "none")
 */
function getPathRisk(pathId: string): RiskLevel {
  return pathRiskMap.value.get(pathId)?.risk ?? "none";
}

/**
 * Get all risk messages for a specific path
 */
function getPathRiskMessages(pathId: string): string[] {
  return pathRiskMap.value.get(pathId)?.messages ?? [];
}

/**
 * Get stroke color based on risk level for canvas rendering
 */
function getRiskColor(risk: RiskLevel): string {
  switch (risk) {
    case "fail":
      return "#d32f2f"; // Red
    case "warn":
      return "#f57c00"; // Orange
    case "info":
      return "#1976d2"; // Blue
    case "none":
    default:
      return "#333333"; // Dark gray
  }
}

/**
 * Get the global risk summary (or a safe default)
 */
function getGlobalRisk(): GlobalRiskSummary {
  return feasibility.value?.globalRisk ?? { risk: "none", messages: [] };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  lastError.value = null;

  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    const error = `Request failed (${res.status}): ${text}`;
    lastError.value = error;
    throw new Error(error);
  }

  return (await res.json()) as T;
}

// ---------------------------------------------------------------------------
// Tools & Materials
// ---------------------------------------------------------------------------

async function loadTools() {
  loading.tools = true;
  try {
    const data = await fetchJSON<ToolSummary[]>(`${API_BASE}/tooling/tools`);
    tools.value = data;
  } finally {
    loading.tools = false;
  }
}

async function loadMaterials() {
  loading.materials = true;
  try {
    const data = await fetchJSON<MaterialSummary[]>(
      `${API_BASE}/tooling/materials`
    );
    materials.value = data;
  } finally {
    loading.materials = false;
  }
}

// ---------------------------------------------------------------------------
// Geometry Generation
// ---------------------------------------------------------------------------

async function generateVCarveGeometry(requestBody: unknown) {
  loading.geometry = true;
  try {
    const data = await fetchJSON<{ paths: MLPath[] }>(
      `${API_BASE}/artstudio/geometry/vcarve`,
      {
        method: "POST",
        body: JSON.stringify(requestBody),
      }
    );
    currentPaths.value = data.paths;
  } finally {
    loading.geometry = false;
  }
}

async function generateReliefGeometry(requestBody: unknown) {
  loading.geometry = true;
  try {
    const data = await fetchJSON<{ paths: MLPath[] }>(
      `${API_BASE}/artstudio/geometry/relief`,
      {
        method: "POST",
        body: JSON.stringify(requestBody),
      }
    );
    currentPaths.value = data.paths;
  } finally {
    loading.geometry = false;
  }
}

/**
 * Generate rosette geometry.
 * Wave 20: Uses canonical /api/art/rosette/geometry via artStudioApi service.
 */
async function generateRosetteGeometry(params: RosetteParams) {
  loading.geometry = true;
  lastError.value = null;

  try {
    const data = await apiGenerateRosetteGeometry(params);
    // Convert RosetteGeometry paths to MLPath format
    currentPaths.value = data.paths.map((p) => ({
      id: p.id,
      points: p.points.map(([x, y]) => ({ x, y })),
      closed: p.closed,
      layer: p.layer,
    }));
    return data;
  } catch (err: any) {
    lastError.value = err.message || "Failed to generate rosette geometry";
    throw err;
  } finally {
    loading.geometry = false;
  }
}

/**
 * Export rosette to DXF/SVG/NC format.
 * Wave 20: Uses canonical /api/art/rosette/export via artStudioApi service.
 */
async function exportRosette(
  params: RosetteParams & { format: "dxf" | "svg" | "nc" }
): Promise<RosetteExportResult> {
  loading.geometry = true;
  lastError.value = null;

  try {
    return await apiExportRosette(params);
  } catch (err: any) {
    lastError.value = err.message || "Failed to export rosette";
    throw err;
  } finally {
    loading.geometry = false;
  }
}

/**
 * Render rosette preview as inline SVG.
 * Wave 20: Uses canonical /api/art/rosette/render via artStudioApi service.
 */
async function renderRosettePreview(
  params: RosetteParams
): Promise<RosettePreviewResult> {
  loading.geometry = true;
  lastError.value = null;

  try {
    return await apiRenderRosettePreview(params);
  } catch (err: any) {
    lastError.value = err.message || "Failed to render rosette preview";
    throw err;
  } finally {
    loading.geometry = false;
  }
}

/**
 * Load available rosette patterns.
 * Wave 20: Uses canonical /api/art/rosette/patterns via artStudioApi service.
 */
async function loadRosettePatterns(): Promise<PatternInfo[]> {
  loading.geometry = true;
  lastError.value = null;

  try {
    const result = await fetchRosettePatterns();
    return result.patterns;
  } catch (err: any) {
    lastError.value = err.message || "Failed to load rosette patterns";
    throw err;
  } finally {
    loading.geometry = false;
  }
}

/**
 * Generate CAM toolpath for rosette.
 * Wave 20: Uses canonical /api/cam/art/rosette/toolpath via artStudioApi service.
 */
async function generateRosetteCamToolpath(
  params: RosetteCamParams
): Promise<RosetteCamResult> {
  loading.toolpaths = true;
  lastError.value = null;

  try {
    return await generateRosetteCam(params);
  } catch (err: any) {
    lastError.value = err.message || "Failed to generate rosette CAM toolpath";
    throw err;
  } finally {
    loading.toolpaths = false;
  }
}

// ---------------------------------------------------------------------------
// RMOS Feasibility & Toolpath Planning
// ---------------------------------------------------------------------------

async function evaluateFeasibility(rmosContext: unknown) {
  loading.feasibility = true;
  try {
    const result = await fetchJSON<FeasibilityResult>(
      `${API_BASE}/rmos/feasibility`,
      {
        method: "POST",
        body: JSON.stringify(rmosContext),
      }
    );
    feasibility.value = result;
  } finally {
    loading.feasibility = false;
  }
}

async function planToolpathsForCurrentDesign(rmosContext: unknown) {
  loading.toolpaths = true;
  try {
    const result = await fetchJSON<{ toolpaths: MLPath[] }>(
      `${API_BASE}/rmos/toolpaths`,
      {
        method: "POST",
        body: JSON.stringify(rmosContext),
      }
    );
    toolpaths.value = result.toolpaths;
  } finally {
    loading.toolpaths = false;
  }
}

// ---------------------------------------------------------------------------
// Instrument Geometry
// ---------------------------------------------------------------------------

async function computeInstrumentGeometry(config: InstrumentConfig) {
  loading.instrument = true;
  try {
    // 1) Fret positions
    const fretData = await fetchJSON<{
      scale_length_mm: number;
      fret_count: number;
      frets_mm: number[];
    }>(`${API_BASE}/instrument/geometry/frets`, {
      method: "POST",
      body: JSON.stringify({
        scale_length_mm: config.scale_length_mm,
        fret_count: config.fret_count,
      }),
    });
    fretPositions.value = fretData.frets_mm;

    // 2) Fretboard outline
    const outlineData = await fetchJSON<{
      points: { x: number; y: number }[];
      fretboard_length_mm: number;
    }>(`${API_BASE}/instrument/geometry/fretboard`, {
      method: "POST",
      body: JSON.stringify({
        nut_width_mm: config.nut_width_mm,
        heel_width_mm: config.heel_width_mm,
        scale_length_mm: config.scale_length_mm,
        fret_count: config.fret_count,
        extension_mm: config.extension_mm || 0,
      }),
    });
    fretboardOutline.value = outlineData.points;
    fretboardLengthMm.value = outlineData.fretboard_length_mm;

    // 3) Fret slots
    const slotsData = await fetchJSON<{ slots: FretSlot[] }>(
      `${API_BASE}/instrument/geometry/fret-slots`,
      {
        method: "POST",
        body: JSON.stringify({
          scale_length_mm: config.scale_length_mm,
          fret_count: config.fret_count,
          nut_width_mm: config.nut_width_mm,
          heel_width_mm: config.heel_width_mm,
        }),
      }
    );
    fretSlots.value = slotsData.slots;

    // 4) Radius profile (if compound)
    if (
      typeof config.base_radius_mm === "number" &&
      typeof config.end_radius_mm === "number"
    ) {
      const radiusData = await fetchJSON<{ radii_mm: number[] }>(
        `${API_BASE}/instrument/geometry/radius-profile`,
        {
          method: "POST",
          body: JSON.stringify({
            fret_count: config.fret_count,
            base_radius_mm: config.base_radius_mm,
            end_radius_mm: config.end_radius_mm,
          }),
        }
      );
      radiusProfile.value = radiusData.radii_mm;
    } else {
      radiusProfile.value = [];
    }

    // 5) Bridge location
    const bridgeData = await fetchJSON<{
      scale_length_mm: number;
      bridge_location_mm: number;
    }>(`${API_BASE}/instrument/geometry/bridge`, {
      method: "POST",
      body: JSON.stringify({
        scale_length_mm: config.scale_length_mm,
      }),
    });
    bridgeLocationMm.value = bridgeData.bridge_location_mm;
  } finally {
    loading.instrument = false;
  }
}

async function loadStandardGuitarPreset(
  preset: string,
  fretCount: number = 22
) {
  loading.instrument = true;
  try {
    const data = await fetchJSON<{
      preset: string;
      scale_length_mm: number;
      fret_count: number;
      nut_width_mm: number;
      frets_mm: number[];
      bridge_location_mm: number;
    }>(`${API_BASE}/instrument/geometry/standard-guitar`, {
      method: "POST",
      body: JSON.stringify({
        preset,
        fret_count: fretCount,
      }),
    });

    fretPositions.value = data.frets_mm;
    bridgeLocationMm.value = data.bridge_location_mm;

    return data;
  } finally {
    loading.instrument = false;
  }
}

// ---------------------------------------------------------------------------
// Calculator Debug
// ---------------------------------------------------------------------------

async function evaluateCutOperation(spec: CutOperationSpec) {
  loading.calculator = true;
  try {
    const result = await fetchJSON<CalculatorResult>(
      `${API_BASE}/calculators/evaluate`,
      {
        method: "POST",
        body: JSON.stringify(spec),
      }
    );
    calculatorResult.value = result;
    return result;
  } finally {
    loading.calculator = false;
  }
}

// ---------------------------------------------------------------------------
// State Management
// ---------------------------------------------------------------------------

function clearGeometry() {
  currentPaths.value = [];
  toolpaths.value = [];
}

function clearFeasibility() {
  feasibility.value = null;
}

function clearInstrumentGeometry() {
  fretPositions.value = [];
  fretSlots.value = [];
  fretboardOutline.value = [];
  radiusProfile.value = [];
  bridgeLocationMm.value = null;
  fretboardLengthMm.value = null;
}

function clearCalculatorResult() {
  calculatorResult.value = null;
}

function clearAll() {
  clearGeometry();
  clearFeasibility();
  clearInstrumentGeometry();
  clearCalculatorResult();
  lastError.value = null;
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export function useArtStudioEngine() {
  return {
    // State
    currentPaths,
    toolpaths,
    tools,
    materials,
    fretPositions,
    fretSlots,
    fretboardOutline,
    radiusProfile,
    bridgeLocationMm,
    fretboardLengthMm,
    feasibility,
    calculatorResult,
    loading,
    lastError,

    // Computed
    isFeasible,
    hasGeometry,
    hasToolpaths,
    isLoading,

    // Wave 9: Risk computed & helpers
    pathRiskMap,
    getPathRisk,
    getPathRiskMessages,
    getRiskColor,
    getGlobalRisk,

    // Tools & Materials
    loadTools,
    loadMaterials,

    // Geometry
    generateVCarveGeometry,
    generateReliefGeometry,
    generateRosetteGeometry,
    exportRosette,
    renderRosettePreview,
    loadRosettePatterns,
    generateRosetteCamToolpath,

    // Rosette Utilities (re-exported from artStudioApi)
    PATTERN_DEFAULTS,
    fetchPatternInfo,

    // RMOS
    evaluateFeasibility,
    planToolpathsForCurrentDesign,

    // Instrument
    computeInstrumentGeometry,
    loadStandardGuitarPreset,

    // Calculator
    evaluateCutOperation,

    // State management
    clearGeometry,
    clearFeasibility,
    clearInstrumentGeometry,
    clearCalculatorResult,
    clearAll,
  };
}
