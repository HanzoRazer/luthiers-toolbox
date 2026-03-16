/**
 * useToolpathLifecycle — Lifecycle management for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles G-code loading, validation, collision detection, and optimization analysis.
 */

import { ref, computed, onMounted, onUnmounted, type Ref, type ComputedRef } from 'vue';
import { validateGcode, type ValidationResult, type ValidationIssue } from '@/util/gcodeValidator';
import { annotationManager } from '@/util/toolpathAnnotations';
import type { useToolpathPlayerStore } from '@/stores/useToolpathPlayerStore';
import type { useToolpathAnalysis } from './useToolpathAnalysis';
import type { useToolpathMachine } from './useToolpathMachine';

export interface LifecycleConfig {
  gcode: string | undefined;
  autoPlay: boolean;
  enableCollisionDetection: boolean;
  enableOptimization: boolean;
  store: ReturnType<typeof useToolpathPlayerStore>;
  analysis: ReturnType<typeof useToolpathAnalysis>;
  machine: ReturnType<typeof useToolpathMachine>;
}

export interface ToolpathLifecycleState {
  validation: Ref<ValidationResult | null>;
  validationErrors: ComputedRef<ValidationIssue[]>;
  hasErrors: ComputedRef<boolean>;
  doLoad: () => Promise<void>;
}

export function useToolpathLifecycle(config: LifecycleConfig): ToolpathLifecycleState {
  const validation = ref<ValidationResult | null>(null);

  const validationErrors = computed(
    () => validation.value?.issues.filter((i) => i.severity === 'error') ?? []
  );

  const hasErrors = computed(() => validationErrors.value.length > 0);

  async function doLoad(): Promise<void> {
    if (!config.gcode) return;

    await config.store.loadGcode(config.gcode, { arc_resolution_deg: 5 });
    config.machine.buildStates(config.store.segments);

    // Initialize annotations for this G-code
    annotationManager.init(config.gcode);

    // Run collision detection
    if (config.enableCollisionDetection && config.store.segments.length > 0) {
      config.analysis.runCollisionDetection(config.store.segments, config.store.bounds);
    }

    // Run optimization analysis
    if (config.enableOptimization && config.store.segments.length > 0) {
      config.analysis.runOptimizationAnalysis(config.store.segments, config.store.totalDurationMs);
    }

    if (config.autoPlay) config.store.play();
  }

  // Lifecycle hooks
  onMounted(async () => {
    if (config.gcode) {
      validation.value = validateGcode(config.gcode);
      if (!hasErrors.value) await doLoad();
    }
  });

  onUnmounted(() => {
    config.store.dispose();
  });

  return {
    validation,
    validationErrors,
    hasErrors,
    doLoad,
  };
}
