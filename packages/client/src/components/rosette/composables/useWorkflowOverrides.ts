/**
 * Composable for managing workflow export overrides with localStorage persistence.
 * Extracted from DesignFirstWorkflowPanel.vue
 */
import { ref, watch, computed, onMounted, type Ref, type ComputedRef } from 'vue'

export interface OverrideOption {
  id: string
  label: string
}

export interface ExportOverrides {
  tool_id: string
  material_id: string
  machine_profile_id: string
  requested_cam_profile_id: string
  risk_tolerance: string
}

export const TOOL_OPTIONS: OverrideOption[] = [
  { id: '', label: 'Tool (default)' },
  { id: 'vbit_60', label: 'V-bit 60°' },
  { id: 'downcut_2mm', label: 'Downcut 2mm' },
  { id: 'upcut_2mm', label: 'Upcut 2mm' },
]

export const MATERIAL_OPTIONS: OverrideOption[] = [
  { id: '', label: 'Material (default)' },
  { id: 'ebony', label: 'Ebony' },
  { id: 'rosewood', label: 'Rosewood' },
  { id: 'maple', label: 'Maple' },
  { id: 'spruce', label: 'Spruce' },
]

export const MACHINE_OPTIONS: OverrideOption[] = [
  { id: '', label: 'Machine (default)' },
  { id: 'shopbot_alpha', label: 'ShopBot Alpha' },
  { id: 'shapeoko_pro', label: 'Shapeoko Pro' },
]

export const CAM_PROFILE_OPTIONS: OverrideOption[] = [
  { id: '', label: 'CAM profile (default)' },
  { id: 'vbit_60_ebony_safe', label: 'V-bit 60 / Ebony / Safe' },
  { id: 'downcut_maple_fast', label: 'Downcut / Maple / Fast' },
]

export const RISK_TOLERANCE_OPTIONS: OverrideOption[] = [
  { id: '', label: 'Risk tolerance (default)' },
  { id: 'GREEN_ONLY', label: 'GREEN only' },
  { id: 'ALLOW_YELLOW', label: 'Allow YELLOW' },
]

const OVERRIDES_LS_KEY_PREFIX = 'artStudio.promotionIntentExport.overrides.v1'

function getStorageKey(mode: string | undefined | null): string {
  const m = (mode || 'unknown').trim() || 'unknown'
  return `${OVERRIDES_LS_KEY_PREFIX}:${m}`
}

function readFromStorage(key: string): ExportOverrides | null {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return null
    const j = JSON.parse(raw)
    if (!j || typeof j !== 'object') return null
    return {
      tool_id: String(j.tool_id ?? ''),
      material_id: String(j.material_id ?? ''),
      machine_profile_id: String(j.machine_profile_id ?? ''),
      requested_cam_profile_id: String(j.requested_cam_profile_id ?? ''),
      risk_tolerance: String(j.risk_tolerance ?? ''),
    }
  } catch {
    return null
  }
}

function writeToStorage(key: string, v: ExportOverrides) {
  try {
    localStorage.setItem(key, JSON.stringify(v))
  } catch {
    // ignore (private browsing / storage disabled)
  }
}

function clearStorage(key: string) {
  try {
    localStorage.removeItem(key)
  } catch {
    // ignore
  }
}

export interface WorkflowOverridesState {
  toolId: Ref<string>
  materialId: Ref<string>
  machineProfileId: Ref<string>
  camProfileId: Ref<string>
  riskTolerance: Ref<string>
  currentOverrides: ComputedRef<ExportOverrides>
  clearOverrides: () => void
  hydrateOverrides: () => void
}

export function useWorkflowOverrides(
  getCurrentMode: () => string | undefined | null,
  onModeChange?: (newMode: string) => void
): WorkflowOverridesState {
  const toolId = ref('')
  const materialId = ref('')
  const machineProfileId = ref('')
  const camProfileId = ref('')
  const riskTolerance = ref('')

  const storageKey = computed(() => getStorageKey(getCurrentMode()))

  const currentOverrides = computed<ExportOverrides>(() => ({
    tool_id: toolId.value,
    material_id: materialId.value,
    machine_profile_id: machineProfileId.value,
    requested_cam_profile_id: camProfileId.value,
    risk_tolerance: riskTolerance.value,
  }))

  function hydrateOverrides() {
    const saved = readFromStorage(storageKey.value)
    if (saved) {
      toolId.value = saved.tool_id
      materialId.value = saved.material_id
      machineProfileId.value = saved.machine_profile_id
      camProfileId.value = saved.requested_cam_profile_id
      riskTolerance.value = saved.risk_tolerance
    }
  }

  function clearOverrides() {
    toolId.value = ''
    materialId.value = ''
    machineProfileId.value = ''
    camProfileId.value = ''
    riskTolerance.value = ''
    clearStorage(storageKey.value)
  }

  // Watch for mode changes
  watch(storageKey, (newKey, oldKey) => {
    if (newKey === oldKey) return
    const saved = readFromStorage(newKey)
    if (saved) {
      toolId.value = saved.tool_id
      materialId.value = saved.material_id
      machineProfileId.value = saved.machine_profile_id
      camProfileId.value = saved.requested_cam_profile_id
      riskTolerance.value = saved.risk_tolerance
      onModeChange?.(getCurrentMode() || 'unknown')
    } else {
      clearOverrides()
    }
  })

  // Auto-save on change
  watch(
    [toolId, materialId, machineProfileId, camProfileId, riskTolerance],
    () => {
      writeToStorage(storageKey.value, currentOverrides.value)
    }
  )

  return {
    toolId,
    materialId,
    machineProfileId,
    camProfileId,
    riskTolerance,
    currentOverrides,
    clearOverrides,
    hydrateOverrides,
  }
}
