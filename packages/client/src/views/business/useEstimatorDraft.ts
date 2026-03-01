// views/business/useEstimatorDraft.ts
/**
 * Composable for persistent estimator draft state.
 *
 * Features:
 * - Auto-saves form state to localStorage on every change
 * - Restores draft on component mount
 * - Provides reset to defaults
 * - Tracks "dirty" state for unsaved changes indicator
 */

import { ref, watch, computed } from "vue";
import type { EstimateRequest, BodyComplexity } from "@/types/businessEstimator";

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEY = "ltb:estimator:draft:v2";
const ADVANCED_TOGGLE_KEY = "ltb:estimator:showAdvanced:v1";

export const DEFAULT_REQUEST: EstimateRequest = {
  instrument_type: "acoustic_dreadnought",
  builder_experience: "intermediate",
  body_complexity: ["standard"],
  binding_body_complexity: "none",
  neck_complexity: "standard",
  fretboard_inlay: "dots",
  finish_type: "nitro_solid",
  rosette_complexity: "simple_rings",
  batch_size: 1,
  hourly_rate: 45,
  include_materials: true,
};

// ============================================================================
// COMPOSABLE
// ============================================================================

export function useEstimatorDraft() {
  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------

  const form = ref<EstimateRequest>(loadDraft());
  const showAdvanced = ref(loadAdvancedToggle());
  const savedSnapshot = ref<string>(JSON.stringify(form.value));

  // ---------------------------------------------------------------------------
  // COMPUTED
  // ---------------------------------------------------------------------------

  const isDirty = computed(() => {
    return JSON.stringify(form.value) !== savedSnapshot.value;
  });

  const bodyComplexityArray = computed<BodyComplexity[]>({
    get: (): BodyComplexity[] => {
      const bc = form.value.body_complexity;
      if (Array.isArray(bc)) return bc as BodyComplexity[];
      return bc ? [bc] : ["standard" as BodyComplexity];
    },
    set: (val: BodyComplexity[]) => {
      form.value.body_complexity = val.length > 0 ? val : ["standard" as BodyComplexity];
    },
  });

  // ---------------------------------------------------------------------------
  // PERSISTENCE
  // ---------------------------------------------------------------------------

  function loadDraft(): EstimateRequest {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Migrate old single-value body_complexity to array
        if (parsed.body_complexity && !Array.isArray(parsed.body_complexity)) {
          parsed.body_complexity = [parsed.body_complexity];
        }
        return { ...DEFAULT_REQUEST, ...parsed };
      }
    } catch (e) {
      console.warn("[useEstimatorDraft] Failed to load draft:", e);
    }
    return { ...DEFAULT_REQUEST };
  }

  function saveDraft(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(form.value));
    } catch (e) {
      console.warn("[useEstimatorDraft] Failed to save draft:", e);
    }
  }

  function loadAdvancedToggle(): boolean {
    try {
      return localStorage.getItem(ADVANCED_TOGGLE_KEY) === "true";
    } catch {
      return false;
    }
  }

  function saveAdvancedToggle(): void {
    try {
      localStorage.setItem(ADVANCED_TOGGLE_KEY, String(showAdvanced.value));
    } catch {
      // Ignore
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIONS
  // ---------------------------------------------------------------------------

  function resetDraft(): void {
    form.value = { ...DEFAULT_REQUEST };
    savedSnapshot.value = JSON.stringify(form.value);
    saveDraft();
  }

  function markSaved(): void {
    savedSnapshot.value = JSON.stringify(form.value);
  }

  function toggleBodyComplexity(value: BodyComplexity): void {
    const current = bodyComplexityArray.value;
    const idx = current.indexOf(value);
    if (idx >= 0) {
      // Remove if already selected (but keep at least one)
      if (current.length > 1) {
        bodyComplexityArray.value = current.filter((v): v is BodyComplexity => v !== value);
      }
    } else {
      // Add to selection
      bodyComplexityArray.value = [...current, value] as BodyComplexity[];
    }
  }

  function isBodyComplexitySelected(value: BodyComplexity): boolean {
    return bodyComplexityArray.value.includes(value);
  }

  // ---------------------------------------------------------------------------
  // WATCHERS
  // ---------------------------------------------------------------------------

  // Auto-save on form changes
  watch(form, saveDraft, { deep: true });

  // Persist advanced toggle state
  watch(showAdvanced, saveAdvancedToggle);

  // ---------------------------------------------------------------------------
  // RETURN
  // ---------------------------------------------------------------------------

  return {
    // State
    form,
    showAdvanced,

    // Computed
    isDirty,
    bodyComplexityArray,

    // Actions
    resetDraft,
    markSaved,
    toggleBodyComplexity,
    isBodyComplexitySelected,

    // Constants
    DEFAULT_REQUEST,
  };
}
