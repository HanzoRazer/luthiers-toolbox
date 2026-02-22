/**
 * BridgeCalculatorPanel state composable.
 */
import { ref, computed, reactive, type Ref, type ComputedRef } from 'vue'
import type {
  UnitMode,
  UiFieldKey,
  FamilyPreset,
  AdjustmentPreset
} from './bridgeCalculatorTypes'
import { FALLBACK_FAMILIES, FALLBACK_GAUGES, FALLBACK_ACTIONS } from './bridgeCalculatorTypes'

export interface BridgeStateReturn {
  // Units
  isMetric: Ref<boolean>
  unitLabel: ComputedRef<string>
  unitMode: ComputedRef<UnitMode>

  // Presets
  familyPresets: Ref<FamilyPreset[]>
  gaugePresets: Ref<AdjustmentPreset[]>
  actionPresets: Ref<AdjustmentPreset[]>
  presetFamily: Ref<string>
  gaugePresetId: Ref<string>
  actionPresetId: Ref<string>
  presetsLoading: Ref<boolean>
  presetError: Ref<string | null>

  // UI state
  ui: Record<UiFieldKey, number>
  exporting: Ref<boolean>
  statusMessage: Ref<string | null>

  // Field definitions
  geometryFields: ComputedRef<Array<{ key: UiFieldKey; label: string; step: number; unit: string }>>
}

export function useBridgeState(): BridgeStateReturn {
  // Units
  const isMetric = ref(true)
  const unitLabel = computed(() => (isMetric.value ? 'mm' : 'in'))
  const unitMode = computed<UnitMode>(() => (isMetric.value ? 'mm' : 'inch'))

  // Presets
  const familyPresets = ref<FamilyPreset[]>([...FALLBACK_FAMILIES])
  const gaugePresets = ref<AdjustmentPreset[]>([...FALLBACK_GAUGES])
  const actionPresets = ref<AdjustmentPreset[]>([...FALLBACK_ACTIONS])
  const presetFamily = ref<string>(familyPresets.value[1]?.id ?? 'strat_tele')
  const gaugePresetId = ref<string>('medium')
  const actionPresetId = ref<string>('standard')
  const presetsLoading = ref(false)
  const presetError = ref<string | null>(null)

  // UI state
  const exporting = ref(false)
  const statusMessage = ref<string | null>(null)

  const ui = reactive<Record<UiFieldKey, number>>({
    scale: familyPresets.value[1]?.scaleLength ?? 647.7,
    spread: familyPresets.value[1]?.stringSpread ?? 52.5,
    compTreble: 2.0,
    compBass: 3.5,
    slotWidth: 3.0,
    slotLength: 75.0
  })

  // Field definitions
  const geometryFields = computed<Array<{ key: UiFieldKey; label: string; step: number; unit: string }>>(() => [
    { key: 'scale', label: 'Scale length', step: 0.01, unit: unitLabel.value },
    { key: 'spread', label: 'Saddle string spread', step: 0.01, unit: unitLabel.value },
    { key: 'compTreble', label: 'Compensation — Treble', step: 0.01, unit: unitLabel.value },
    { key: 'compBass', label: 'Compensation — Bass', step: 0.01, unit: unitLabel.value },
    { key: 'slotWidth', label: 'Slot width', step: 0.01, unit: unitLabel.value },
    { key: 'slotLength', label: 'Slot length (visual)', step: 0.1, unit: unitLabel.value }
  ])

  return {
    isMetric,
    unitLabel,
    unitMode,
    familyPresets,
    gaugePresets,
    actionPresets,
    presetFamily,
    gaugePresetId,
    actionPresetId,
    presetsLoading,
    presetError,
    ui,
    exporting,
    statusMessage,
    geometryFields
  }
}
