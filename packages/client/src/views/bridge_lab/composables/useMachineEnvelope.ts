/**
 * Composable for machine envelope state management.
 */
import { ref, type Ref } from 'vue'
import type { Machine, MachineLimits, MachineCamDefaults, AdaptiveParams } from './bridgeLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface MachineEnvelopeState {
  machine: Ref<Machine | null>
  machineLimits: Ref<MachineLimits | null>
  machineCamDefaults: Ref<MachineCamDefaults | null>
  onMachineSelected: (m: Machine | null) => void
  onLimitsChanged: (limits: MachineLimits | null) => void
  onCamDefaultsChanged: (defaults: MachineCamDefaults | null) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useMachineEnvelope(
  adaptiveParams: Ref<AdaptiveParams>
): MachineEnvelopeState {
  const machine = ref<Machine | null>(null)
  const machineLimits = ref<MachineLimits | null>(null)
  const machineCamDefaults = ref<MachineCamDefaults | null>(null)

  function onMachineSelected(m: Machine | null): void {
    machine.value = m
  }

  function onLimitsChanged(limits: MachineLimits | null): void {
    machineLimits.value = limits
  }

  function onCamDefaultsChanged(defaults: MachineCamDefaults | null): void {
    machineCamDefaults.value = defaults
    if (!defaults) return

    // Auto-fill adaptive params from machine CAM defaults
    if (defaults.tool_d != null) {
      adaptiveParams.value.tool_d = defaults.tool_d
    }
    if (defaults.stepover != null) {
      adaptiveParams.value.stepover = defaults.stepover
    }
    if (defaults.stepdown != null) {
      adaptiveParams.value.stepdown = defaults.stepdown
    }
    if (defaults.feed_xy != null) {
      adaptiveParams.value.feed_xy = defaults.feed_xy
    }
    if (defaults.safe_z != null) {
      adaptiveParams.value.safe_z = defaults.safe_z
    }
    if (defaults.z_rough != null) {
      adaptiveParams.value.z_rough = defaults.z_rough
    }
  }

  return {
    machine,
    machineLimits,
    machineCamDefaults,
    onMachineSelected,
    onLimitsChanged,
    onCamDefaultsChanged
  }
}
