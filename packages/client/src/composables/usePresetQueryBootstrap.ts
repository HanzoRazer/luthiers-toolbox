// client/src/composables/usePresetQueryBootstrap.ts
import { onMounted, watch } from "vue";
import { useRoute, type RouteLocationNormalizedLoaded } from "vue-router";

export interface PresetQueryBootstrapOptions {
  /**
   * Called when we detect a `tab` query param (string).
   */
  onTab?(tab: string): void;

  /**
   * Called when we detect a `preset` query param (string).
   */
  onPreset?(preset: string): void;

  /**
   * Called when we detect a `job_hint` query param (string).
   */
  onJobHint?(jobHint: string): void;

  /**
   * Called when we detect a `lane` query param (string).
   */
  onLane?(lane: string): void;
}

/**
 * Shared helper: consume common query params (tab, preset, job_hint, lane)
 * and push them into the caller's local state.
 *
 * Usage:
 *   usePresetQueryBootstrap({
 *     onTab: (tab) => { activeTab.value = tab; },
 *     onPreset: (p) => { selectedPreset.value = p; },
 *     onJobHint: (j) => { if (!jobId.value) jobId.value = j; },
 *     onLane: (lane) => { currentLane.value = lane; },
 *   });
 */
export function usePresetQueryBootstrap(options: PresetQueryBootstrapOptions) {
  const route = useRoute();

  function applyQuery(route: RouteLocationNormalizedLoaded) {
    const q = route.query;

    const tab = typeof q.tab === "string" ? q.tab : undefined;
    if (tab && options.onTab) {
      options.onTab(tab);
    }

    const preset = typeof q.preset === "string" ? q.preset : undefined;
    if (preset && options.onPreset) {
      options.onPreset(preset);
    }

    const jobHint = typeof q.job_hint === "string" ? q.job_hint : undefined;
    if (jobHint && options.onJobHint) {
      options.onJobHint(jobHint);
    }

    const lane = typeof q.lane === "string" ? q.lane : undefined;
    if (lane && options.onLane) {
      options.onLane(lane);
    }
  }

  onMounted(() => {
    applyQuery(route as RouteLocationNormalizedLoaded);
  });

  watch(
    () => route.query,
    () => {
      applyQuery(route as RouteLocationNormalizedLoaded);
    },
    { deep: true }
  );
}
