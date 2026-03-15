/**
 * useToolpathLoader — G-code loading and analysis orchestration for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles G-code loading, validation, machine state building, and analysis triggers.
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue';
import { validateGcode, type ValidationResult, type ValidationIssue } from '@/util/gcodeValidator';
import { buildMachineStates, type MachineState } from '@/util/mcodeTracker';
import { annotationManager } from '@/util/toolpathAnnotations';

export interface LoaderConfig {
  gcode: Ref<string | undefined>;
  autoPlay: boolean;
  enableCollisionDetection: boolean;
  enableOptimization: boolean;
  store: {
    loadGcode: (gcode: string, options?: { arc_resolution_deg?: number }) => Promise<void>;
    segments: { length: number }[];
    currentSegmentIndex: number;
    play: () => void;
  };
  runCollisionDetection: () => void;
  runOptimizationAnalysis: () => void;
}

export interface ToolpathLoaderState {
  validation: Ref<ValidationResult | null>;
  validationErrors: ComputedRef<ValidationIssue[]>;
  hasErrors: ComputedRef<boolean>;
  machineStates: Ref<MachineState[]>;
  currentMachine: ComputedRef<MachineState | null>;
  doLoad: () => Promise<void>;
}

export function useToolpathLoader(config: LoaderConfig): ToolpathLoaderState {
  const validation = ref<ValidationResult | null>(null);
  const machineStates = ref<MachineState[]>([]);

  const validationErrors = computed(
    () => validation.value?.issues.filter((i) => i.severity === 'error') ?? []
  );

  const hasErrors = computed(() => validationErrors.value.length > 0);

  const currentMachine = computed<MachineState | null>(() => {
    const idx = config.store.currentSegmentIndex;
    if (idx < 0 || idx >= machineStates.value.length) return null;
    return machineStates.value[idx];
  });

  async function doLoad(): Promise<void> {
    const gcode = config.gcode.value;
    if (!gcode) return;

    await config.store.loadGcode(gcode, { arc_resolution_deg: 5 });
    machineStates.value = buildMachineStates(config.store.segments as unknown as Parameters<typeof buildMachineStates>[0]);

    // Initialize annotations for this G-code
    annotationManager.init(gcode);

    // Run collision detection
    if (config.enableCollisionDetection && config.store.segments.length > 0) {
      config.runCollisionDetection();
    }

    // Run optimization analysis
    if (config.enableOptimization && config.store.segments.length > 0) {
      config.runOptimizationAnalysis();
    }

    if (config.autoPlay) config.store.play();
  }

  function runValidation(): void {
    const gcode = config.gcode.value;
    if (gcode) {
      validation.value = validateGcode(gcode);
    }
  }

  // Run validation immediately if gcode is available
  runValidation();

  return {
    validation,
    validationErrors,
    hasErrors,
    machineStates,
    currentMachine,
    doLoad,
  };
}
