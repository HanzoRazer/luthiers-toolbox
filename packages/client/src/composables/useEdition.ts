/**
 * useEdition Composable
 *
 * Provides edition-aware feature gating for Vue components.
 * Wraps the registry store with convenient helpers for UI components.
 *
 * @module composables/useEdition
 *
 * @example
 * ```vue
 * <script setup>
 * import { useEdition } from '@/composables/useEdition'
 *
 * const { canAccess, showUpgradePrompt, edition } = useEdition()
 * </script>
 *
 * <template>
 *   <div v-if="canAccess('empirical_limits')">
 *     <!-- Pro feature content -->
 *   </div>
 *   <UpgradePrompt v-else @click="showUpgradePrompt('empirical_limits')" />
 * </template>
 * ```
 */

import { computed, ref } from "vue";
import { useRegistryStore } from "@/stores/useRegistryStore";
import type { Edition } from "@/api/registry";

// Feature to minimum edition mapping
const FEATURE_REQUIREMENTS: Record<string, Edition> = {
  // System tier (all editions)
  geometry: "express",
  scale_lengths: "express",
  fret_formulas: "express",
  wood_species: "express",
  basic_templates: "express",
  dxf_export: "express",

  // Pro tier
  empirical_limits: "pro",
  tools: "pro",
  machines: "pro",
  cam_presets: "pro",
  posts: "pro",
  adaptive_pocketing: "pro",
  gcode_export: "pro",
  simulation: "pro",

  // Enterprise tier
  fleet: "enterprise",
  scheduling: "enterprise",
  customers: "enterprise",
  orders: "enterprise",
  inventory: "enterprise",
  multi_machine: "enterprise",
  production_tracking: "enterprise",
  analytics: "enterprise",
};

// Edition hierarchy for comparison
const EDITION_RANK: Record<Edition, number> = {
  express: 1,
  parametric: 1,
  neck_designer: 1,
  headstock_designer: 1,
  bridge_designer: 1,
  fingerboard_designer: 1,
  cnc_blueprints: 1,
  pro: 2,
  enterprise: 3,
};

export function useEdition() {
  const store = useRegistryStore();

  // Upgrade modal state
  const showingUpgradeModal = ref(false);
  const upgradeFeature = ref<string | null>(null);
  const upgradeRequiredEdition = ref<Edition | null>(null);

  /**
   * Check if current edition can access a feature
   */
  function canAccess(feature: string): boolean {
    const required = FEATURE_REQUIREMENTS[feature];
    if (!required) {
      // Unknown feature - allow by default
      return true;
    }
    const currentRank = EDITION_RANK[store.edition] ?? 0;
    const requiredRank = EDITION_RANK[required] ?? 0;
    return currentRank >= requiredRank;
  }

  /**
   * Get the minimum edition required for a feature
   */
  function getRequiredEdition(feature: string): Edition {
    return FEATURE_REQUIREMENTS[feature] ?? "express";
  }

  /**
   * Show upgrade prompt for a feature
   */
  function showUpgradePrompt(feature: string): void {
    upgradeFeature.value = feature;
    upgradeRequiredEdition.value = getRequiredEdition(feature);
    showingUpgradeModal.value = true;
  }

  /**
   * Hide upgrade prompt
   */
  function hideUpgradePrompt(): void {
    showingUpgradeModal.value = false;
    upgradeFeature.value = null;
    upgradeRequiredEdition.value = null;
  }

  /**
   * Get upgrade URL
   */
  function getUpgradeUrl(edition?: Edition): string {
    const target = edition ?? upgradeRequiredEdition.value ?? "pro";
    return `https://luthierstoolbox.com/upgrade?to=${target}`;
  }

  /**
   * Get feature display name
   */
  function getFeatureDisplayName(feature: string): string {
    const names: Record<string, string> = {
      empirical_limits: "Empirical Feed/Speed Limits",
      tools: "Tool Library",
      machines: "Machine Profiles",
      cam_presets: "CAM Presets",
      posts: "Post Processors",
      adaptive_pocketing: "Adaptive Pocketing",
      gcode_export: "G-Code Export",
      simulation: "Toolpath Simulation",
      fleet: "Fleet Management",
      scheduling: "Production Scheduling",
      customers: "Customer Management",
      orders: "Order Tracking",
      inventory: "Inventory Management",
      multi_machine: "Multi-Machine Support",
      production_tracking: "Production Tracking",
      analytics: "Advanced Analytics",
    };
    return (
      names[feature] ??
      feature.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    );
  }

  /**
   * Get edition display name
   */
  function getEditionDisplayName(edition: Edition): string {
    const names: Record<Edition, string> = {
      express: "Express",
      pro: "Pro",
      enterprise: "Enterprise",
      parametric: "Parametric Guitar",
      neck_designer: "Neck Designer",
      headstock_designer: "Headstock Designer",
      bridge_designer: "Bridge Designer",
      fingerboard_designer: "Fingerboard Designer",
      cnc_blueprints: "CNC Blueprints",
    };
    return names[edition] ?? edition;
  }

  // Computed convenience getters
  const edition = computed(() => store.edition);
  const isExpress = computed(() => store.isExpress);
  const isPro = computed(() => store.isPro);
  const isEnterprise = computed(() => store.isEnterprise);
  const isStandalone = computed(() => store.isStandalone);

  // Common feature checks as computed
  const canAccessEmpiricalLimits = computed(() =>
    canAccess("empirical_limits")
  );
  const canAccessTools = computed(() => canAccess("tools"));
  const canAccessMachines = computed(() => canAccess("machines"));
  const canAccessGcode = computed(() => canAccess("gcode_export"));
  const canAccessSimulation = computed(() => canAccess("simulation"));
  const canAccessFleet = computed(() => canAccess("fleet"));
  const canAccessAnalytics = computed(() => canAccess("analytics"));

  return {
    // Store state
    edition,
    isExpress,
    isPro,
    isEnterprise,
    isStandalone,

    // Feature checks
    canAccess,
    getRequiredEdition,
    canAccessEmpiricalLimits,
    canAccessTools,
    canAccessMachines,
    canAccessGcode,
    canAccessSimulation,
    canAccessFleet,
    canAccessAnalytics,

    // Upgrade prompt
    showingUpgradeModal,
    upgradeFeature,
    upgradeRequiredEdition,
    showUpgradePrompt,
    hideUpgradePrompt,
    getUpgradeUrl,

    // Display helpers
    getFeatureDisplayName,
    getEditionDisplayName,

    // Store actions
    setEdition: store.setEdition,
    initialize: store.initialize,
  };
}
