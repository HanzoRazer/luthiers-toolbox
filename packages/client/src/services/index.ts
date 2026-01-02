/**
 * API Services Index
 * ==================
 *
 * Centralized re-exports for all API services.
 *
 * Wave 20: Option C API Restructuring
 * H7.2: Added RMOS CAM Intent API
 *
 * Usage:
 *   import { fetchInstrumentModels, generateRosetteGeometry } from '@/services';
 *   import { normalizeCamIntent } from '@/services';
 */

// RMOS CAM Intent API (H7.2)
export {
  normalizeCamIntent,
  type CamIntentV1,
  type CamIntentIssue,
  type CamUnitsV1,
  type CamModeV1,
  type NormalizeCamIntentRequest,
  type NormalizeCamIntentResult,
  RmosApiError,
} from "./rmosCamIntentApi";

// Base utilities
export {
  API_BASE,
  buildUrl,
  apiFetch,
  apiFetchWithFallback,
  ApiError,
} from './apiBase';

// Instrument API
export {
  // Functions
  fetchInstrumentModels,
  fetchInstrumentSpec,
  fetchInstrumentGeometry,
  fetchInstrumentInfo,
  fetchModelsWithAssets,
  calculateFretPositions,
  generateFretboard,
  // Path builders
  buildInstrumentUrl,
  buildLegacyInstrumentUrl,
  // Types
  type InstrumentModel,
  type InstrumentModelList,
  type InstrumentSpec,
  type InstrumentGeometry,
  type InstrumentInfo,
  type FretboardParams,
  type FretPosition,
  // Fallback data
  FALLBACK_MODELS,
} from './instrumentApi';

// Art Studio API
export {
  // Functions
  generateRosetteGeometry,
  exportRosette,
  renderRosettePreview,
  fetchRosettePatterns,
  fetchPatternInfo,
  generateRosetteCam,
  // Path builders
  buildRosetteUrl,
  buildLegacyRosetteUrl,
  // Types
  type PatternType,
  type RosetteParams,
  type RosetteGeometry,
  type RosetteExportResult,
  type RosettePreviewResult,
  type PatternInfo,
  type RosetteCamParams,
  type RosetteCamResult,
  // Defaults
  PATTERN_DEFAULTS,
} from './artStudioApi';
