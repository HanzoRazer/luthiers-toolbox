/**
 * Data Registry Store
 *
 * Pinia store for managing edition-based data from the registry API.
 * Handles caching, loading states, and entitlement errors gracefully.
 *
 * @module stores/useRegistryStore
 */

import { defineStore } from "pinia";
import { ref, computed, readonly } from "vue";
import {
  type Edition,
  type RegistryInfo,
  type ScaleLengthResponse,
  type WoodSpeciesResponse,
  type EmpiricalLimitsResponse,
  type FretFormulasResponse,
  type RegistryHealth,
  type EntitlementError,
  getCurrentEdition,
  setCurrentEdition,
  getRegistryInfo,
  getScaleLengths,
  getWoodSpecies,
  getEmpiricalLimits,
  getFretFormulas,
  getRegistryHealth,
  isEntitlementError,
} from "@/api/registry";

export const useRegistryStore = defineStore("registry", () => {
  // ============================================================================
  // State
  // ============================================================================

  // Current edition
  const edition = ref<Edition>(getCurrentEdition());

  // Registry metadata
  const registryInfo = ref<RegistryInfo | null>(null);
  const registryHealth = ref<RegistryHealth | null>(null);

  // Data cache
  const scaleLengths = ref<ScaleLengthResponse | null>(null);
  const woodSpecies = ref<WoodSpeciesResponse | null>(null);
  const empiricalLimits = ref<EmpiricalLimitsResponse | null>(null);
  const fretFormulas = ref<FretFormulasResponse | null>(null);

  // Loading states
  const loadingInfo = ref(false);
  const loadingScales = ref(false);
  const loadingWoods = ref(false);
  const loadingLimits = ref(false);
  const loadingFormulas = ref(false);

  // Error states
  const lastError = ref<string | null>(null);
  const entitlementError = ref<EntitlementError | null>(null);

  // ============================================================================
  // Getters
  // ============================================================================

  const isExpress = computed(() => edition.value === "express");
  const isPro = computed(() => ["pro", "enterprise"].includes(edition.value));
  const isEnterprise = computed(() => edition.value === "enterprise");

  const isStandalone = computed(() =>
    [
      "parametric",
      "neck_designer",
      "headstock_designer",
      "bridge_designer",
      "fingerboard_designer",
      "cnc_blueprints",
    ].includes(edition.value)
  );

  const canAccessEmpiricalLimits = computed(() => isPro.value);
  const canAccessTools = computed(() => isPro.value);
  const canAccessMachines = computed(() => isPro.value);
  const canAccessFleet = computed(() => isEnterprise.value);

  const isLoading = computed(
    () =>
      loadingInfo.value ||
      loadingScales.value ||
      loadingWoods.value ||
      loadingLimits.value ||
      loadingFormulas.value
  );

  const hasEntitlementError = computed(() => entitlementError.value !== null);

  // Data counts
  const scaleCount = computed(() => scaleLengths.value?.count ?? 0);
  const woodCount = computed(() => woodSpecies.value?.count ?? 0);
  const limitsCount = computed(() => empiricalLimits.value?.count ?? 0);
  const formulaCount = computed(() => fretFormulas.value?.count ?? 0);

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Set the current edition and persist to localStorage
   */
  function setEdition(newEdition: Edition) {
    edition.value = newEdition;
    setCurrentEdition(newEdition);
    // Clear cached edition-specific data
    empiricalLimits.value = null;
    entitlementError.value = null;
    lastError.value = null;
  }

  /**
   * Load registry metadata
   */
  async function loadRegistryInfo(): Promise<void> {
    loadingInfo.value = true;
    lastError.value = null;
    try {
      registryInfo.value = await getRegistryInfo(edition.value);
    } catch (err) {
      lastError.value =
        err instanceof Error ? err.message : "Failed to load registry info";
      console.error("[Registry] Failed to load info:", err);
    } finally {
      loadingInfo.value = false;
    }
  }

  /**
   * Load scale lengths (System tier - all editions)
   */
  async function loadScaleLengths(): Promise<void> {
    if (scaleLengths.value) return; // Already loaded
    loadingScales.value = true;
    lastError.value = null;
    try {
      scaleLengths.value = await getScaleLengths(edition.value);
    } catch (err) {
      lastError.value =
        err instanceof Error ? err.message : "Failed to load scale lengths";
      console.error("[Registry] Failed to load scales:", err);
    } finally {
      loadingScales.value = false;
    }
  }

  /**
   * Load wood species (System tier - all editions)
   */
  async function loadWoodSpecies(): Promise<void> {
    if (woodSpecies.value) return; // Already loaded
    loadingWoods.value = true;
    lastError.value = null;
    try {
      woodSpecies.value = await getWoodSpecies(edition.value);
    } catch (err) {
      lastError.value =
        err instanceof Error ? err.message : "Failed to load wood species";
      console.error("[Registry] Failed to load woods:", err);
    } finally {
      loadingWoods.value = false;
    }
  }

  /**
   * Load empirical limits (Edition tier - Pro/Enterprise only)
   * Sets entitlementError if Express user attempts access
   */
  async function loadEmpiricalLimits(): Promise<void> {
    if (empiricalLimits.value) return; // Already loaded
    loadingLimits.value = true;
    lastError.value = null;
    entitlementError.value = null;
    try {
      empiricalLimits.value = await getEmpiricalLimits(edition.value);
    } catch (err) {
      if (isEntitlementError(err)) {
        entitlementError.value = err;
        console.warn("[Registry] Entitlement required:", err.message);
      } else {
        lastError.value =
          err instanceof Error
            ? err.message
            : "Failed to load empirical limits";
        console.error("[Registry] Failed to load limits:", err);
      }
    } finally {
      loadingLimits.value = false;
    }
  }

  /**
   * Load fret formulas (System tier - all editions)
   */
  async function loadFretFormulas(): Promise<void> {
    if (fretFormulas.value) return; // Already loaded
    loadingFormulas.value = true;
    lastError.value = null;
    try {
      fretFormulas.value = await getFretFormulas(edition.value);
    } catch (err) {
      lastError.value =
        err instanceof Error ? err.message : "Failed to load fret formulas";
      console.error("[Registry] Failed to load formulas:", err);
    } finally {
      loadingFormulas.value = false;
    }
  }

  /**
   * Load registry health status
   */
  async function loadHealth(): Promise<void> {
    try {
      registryHealth.value = await getRegistryHealth();
    } catch (err) {
      console.error("[Registry] Health check failed:", err);
    }
  }

  /**
   * Load all system-tier data (for initial app load)
   */
  async function loadSystemData(): Promise<void> {
    await Promise.all([
      loadRegistryInfo(),
      loadScaleLengths(),
      loadWoodSpecies(),
      loadFretFormulas(),
    ]);
  }

  /**
   * Load edition-tier data (if entitled)
   */
  async function loadEditionData(): Promise<void> {
    if (canAccessEmpiricalLimits.value) {
      await loadEmpiricalLimits();
    }
  }

  /**
   * Initialize store - load all available data
   */
  async function initialize(): Promise<void> {
    await loadSystemData();
    await loadEditionData();
    await loadHealth();
  }

  /**
   * Clear entitlement error (for UI dismiss)
   */
  function clearEntitlementError(): void {
    entitlementError.value = null;
  }

  /**
   * Force refresh all data
   */
  async function refresh(): Promise<void> {
    // Clear cache
    scaleLengths.value = null;
    woodSpecies.value = null;
    empiricalLimits.value = null;
    fretFormulas.value = null;
    registryInfo.value = null;
    registryHealth.value = null;
    // Reload
    await initialize();
  }

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State (readonly externally)
    edition: readonly(edition),
    registryInfo: readonly(registryInfo),
    registryHealth: readonly(registryHealth),
    scaleLengths: readonly(scaleLengths),
    woodSpecies: readonly(woodSpecies),
    empiricalLimits: readonly(empiricalLimits),
    fretFormulas: readonly(fretFormulas),
    lastError: readonly(lastError),
    entitlementError: readonly(entitlementError),

    // Loading states
    loadingInfo: readonly(loadingInfo),
    loadingScales: readonly(loadingScales),
    loadingWoods: readonly(loadingWoods),
    loadingLimits: readonly(loadingLimits),
    loadingFormulas: readonly(loadingFormulas),
    isLoading,

    // Computed
    isExpress,
    isPro,
    isEnterprise,
    isStandalone,
    canAccessEmpiricalLimits,
    canAccessTools,
    canAccessMachines,
    canAccessFleet,
    hasEntitlementError,
    scaleCount,
    woodCount,
    limitsCount,
    formulaCount,

    // Actions
    setEdition,
    loadRegistryInfo,
    loadScaleLengths,
    loadWoodSpecies,
    loadEmpiricalLimits,
    loadFretFormulas,
    loadHealth,
    loadSystemData,
    loadEditionData,
    initialize,
    clearEntitlementError,
    refresh,
  };
});
