/**
 * useToolpathMachine — M-code machine state tracking for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Tracks spindle, coolant, and other machine states per segment.
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue';
import { buildMachineStates, type MachineState } from '@/util/mcodeTracker';

export interface MachineConfig {
  currentSegmentIndex: ComputedRef<number>;
}

export interface ToolpathMachineState {
  machineStates: Ref<MachineState[]>;
  currentMachine: ComputedRef<MachineState | null>;
  buildStates: (segments: Parameters<typeof buildMachineStates>[0]) => void;
}

export function useToolpathMachine(config: MachineConfig): ToolpathMachineState {
  const machineStates = ref<MachineState[]>([]);

  const currentMachine = computed<MachineState | null>(() => {
    const idx = config.currentSegmentIndex.value;
    if (idx < 0 || idx >= machineStates.value.length) return null;
    return machineStates.value[idx];
  });

  function buildStates(segments: Parameters<typeof buildMachineStates>[0]): void {
    machineStates.value = buildMachineStates(segments);
  }

  return {
    machineStates,
    currentMachine,
    buildStates,
  };
}
