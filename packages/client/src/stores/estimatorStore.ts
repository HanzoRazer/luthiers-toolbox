// packages/client/src/stores/estimatorStore.ts
/**
 * Engineering Estimator Store
 *
 * Centralized state management for estimates:
 * - Draft persistence (auto-save to localStorage)
 * - Estimate history (last 20)
 * - Comparison state (A vs B)
 * - Override audit log
 * - RMOS run linkage
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { EstimateRequest, EstimateResult } from "@/types/businessEstimator";

// ============================================================================
// TYPES
// ============================================================================

export interface EstimateHistoryItem {
  id: string;
  timestamp: string;
  request: EstimateRequest;
  result: EstimateResult;
  notes?: string;
  linkedRunId?: string; // RMOS run for actual comparison
}

export interface PriceOverride {
  estimateId: string;
  originalPrice: number;
  overridePrice: number;
  reason: string;
  timestamp: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEYS = {
  draft: "ltb:estimator:draft:v1",
  history: "ltb:estimator:history:v1",
  overrides: "ltb:estimator:overrides:v1",
} as const;

const MAX_HISTORY = 20;

const DEFAULT_REQUEST: EstimateRequest = {
  instrument_type: "acoustic_dreadnought",
  builder_experience: "intermediate",
  body_complexity: "standard",
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
// STORE
// ============================================================================

export const useEstimatorStore = defineStore("estimator", () => {
  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------

  const draft = ref<EstimateRequest | null>(null);
  const current = ref<EstimateResult | null>(null);
  const history = ref<EstimateHistoryItem[]>([]);
  const compareA = ref<EstimateHistoryItem | null>(null);
  const compareB = ref<EstimateHistoryItem | null>(null);
  const overrides = ref<PriceOverride[]>([]);
  const isLoading = ref(false);

  // ---------------------------------------------------------------------------
  // GETTERS
  // ---------------------------------------------------------------------------

  const hasDraft = computed(() => draft.value !== null);

  const recentEstimates = computed(() => history.value.slice(0, 5));

  const linkedEstimates = computed(() =>
    history.value.filter((h) => h.linkedRunId)
  );

  const isComparing = computed(() => compareA.value && compareB.value);

  const defaultRequest = computed(() => ({ ...DEFAULT_REQUEST }));

  // ---------------------------------------------------------------------------
  // PERSISTENCE HELPERS
  // ---------------------------------------------------------------------------

  function loadFromStorage() {
    try {
      const draftJson = localStorage.getItem(STORAGE_KEYS.draft);
      const historyJson = localStorage.getItem(STORAGE_KEYS.history);
      const overridesJson = localStorage.getItem(STORAGE_KEYS.overrides);

      if (draftJson) draft.value = JSON.parse(draftJson);
      if (historyJson) history.value = JSON.parse(historyJson);
      if (overridesJson) overrides.value = JSON.parse(overridesJson);
    } catch (e) {
      console.warn("[estimatorStore] Failed to load from localStorage:", e);
    }
  }

  function persistDraft() {
    try {
      if (draft.value) {
        localStorage.setItem(STORAGE_KEYS.draft, JSON.stringify(draft.value));
      } else {
        localStorage.removeItem(STORAGE_KEYS.draft);
      }
    } catch (e) {
      console.warn("[estimatorStore] Failed to persist draft:", e);
    }
  }

  function persistHistory() {
    try {
      localStorage.setItem(STORAGE_KEYS.history, JSON.stringify(history.value));
    } catch (e) {
      console.warn("[estimatorStore] Failed to persist history:", e);
    }
  }

  function persistOverrides() {
    try {
      localStorage.setItem(
        STORAGE_KEYS.overrides,
        JSON.stringify(overrides.value)
      );
    } catch (e) {
      console.warn("[estimatorStore] Failed to persist overrides:", e);
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIONS
  // ---------------------------------------------------------------------------

  /**
   * Save current form state as draft (auto-saves to localStorage).
   */
  function saveDraft(request: EstimateRequest) {
    draft.value = request;
    persistDraft();
  }

  /**
   * Clear the current draft.
   */
  function clearDraft() {
    draft.value = null;
    persistDraft();
  }

  /**
   * Get the draft or return default values.
   */
  function getDraftOrDefault(): EstimateRequest {
    return draft.value ? { ...draft.value } : { ...DEFAULT_REQUEST };
  }

  /**
   * Save a completed estimate to history.
   * @returns The new history item ID
   */
  function saveEstimate(
    request: EstimateRequest,
    result: EstimateResult,
    notes?: string
  ): string {
    const id = crypto.randomUUID();
    const item: EstimateHistoryItem = {
      id,
      timestamp: new Date().toISOString(),
      request,
      result,
      notes,
    };

    // Add to front of history
    history.value.unshift(item);

    // Trim to max size
    if (history.value.length > MAX_HISTORY) {
      history.value = history.value.slice(0, MAX_HISTORY);
    }

    persistHistory();

    // Clear draft after successful save
    clearDraft();

    return id;
  }

  /**
   * Get an estimate from history by ID.
   */
  function getEstimate(id: string): EstimateHistoryItem | undefined {
    return history.value.find((h) => h.id === id);
  }

  /**
   * Delete an estimate from history.
   */
  function deleteEstimate(id: string) {
    history.value = history.value.filter((h) => h.id !== id);
    persistHistory();
  }

  /**
   * Link an estimate to an RMOS run for actual vs estimated comparison.
   */
  function linkToRun(estimateId: string, runId: string) {
    const item = history.value.find((h) => h.id === estimateId);
    if (item) {
      item.linkedRunId = runId;
      persistHistory();
    }
  }

  /**
   * Unlink an estimate from its RMOS run.
   */
  function unlinkFromRun(estimateId: string) {
    const item = history.value.find((h) => h.id === estimateId);
    if (item) {
      delete item.linkedRunId;
      persistHistory();
    }
  }

  /**
   * Set estimates for comparison.
   */
  function setCompare(a: EstimateHistoryItem | null, b: EstimateHistoryItem | null) {
    compareA.value = a;
    compareB.value = b;
  }

  /**
   * Clear comparison state.
   */
  function clearCompare() {
    compareA.value = null;
    compareB.value = null;
  }

  /**
   * Record a price override (for audit trail).
   */
  function recordOverride(
    estimateId: string,
    originalPrice: number,
    overridePrice: number,
    reason: string
  ) {
    const override: PriceOverride = {
      estimateId,
      originalPrice,
      overridePrice,
      reason,
      timestamp: new Date().toISOString(),
    };
    overrides.value.push(override);
    persistOverrides();
  }

  /**
   * Get overrides for a specific estimate.
   */
  function getOverrides(estimateId: string): PriceOverride[] {
    return overrides.value.filter((o) => o.estimateId === estimateId);
  }

  /**
   * Set the current estimate result (from API).
   */
  function setCurrent(result: EstimateResult | null) {
    current.value = result;
  }

  /**
   * Set loading state.
   */
  function setLoading(loading: boolean) {
    isLoading.value = loading;
  }

  // ---------------------------------------------------------------------------
  // INITIALIZE
  // ---------------------------------------------------------------------------

  // Load from localStorage on store creation
  loadFromStorage();

  // ---------------------------------------------------------------------------
  // RETURN
  // ---------------------------------------------------------------------------

  return {
    // State
    draft,
    current,
    history,
    compareA,
    compareB,
    overrides,
    isLoading,

    // Getters
    hasDraft,
    recentEstimates,
    linkedEstimates,
    isComparing,
    defaultRequest,

    // Actions
    loadFromStorage,
    saveDraft,
    clearDraft,
    getDraftOrDefault,
    saveEstimate,
    getEstimate,
    deleteEstimate,
    linkToRun,
    unlinkFromRun,
    setCompare,
    clearCompare,
    recordOverride,
    getOverrides,
    setCurrent,
    setLoading,
  };
});
