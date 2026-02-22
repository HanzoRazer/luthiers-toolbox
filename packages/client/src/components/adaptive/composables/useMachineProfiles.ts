/**
 * Composable for machine profile management.
 * Handles machine selection, persistence, editor modal, and profile comparison.
 */
import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'

export interface MachineProfile {
  id: string
  title: string
  limits: {
    feed_xy: number
    accel: number
    jerk: number
    rapid: number
  }
  post_id_default?: string
}

export interface MachineProfilesConfig {
  /** Callback when selected machine's default post should be applied */
  onPostIdChange?: (postId: string) => void
}

export interface MachineProfilesState {
  machines: Ref<MachineProfile[]>
  machineId: Ref<string>
  selMachine: ComputedRef<MachineProfile | undefined>
  machineEditorOpen: Ref<boolean>
  compareMachinesOpen: Ref<boolean>
  openMachineEditor: () => void
  onMachineSaved: (id: string) => Promise<void>
  compareMachinesFunc: () => void
  loadMachines: () => Promise<void>
}

export function useMachineProfiles(config: MachineProfilesConfig = {}): MachineProfilesState {
  // State
  const machines = ref<MachineProfile[]>([])
  const machineId = ref<string>(localStorage.getItem('toolbox.machine') || 'Mach4_Router_4x8')
  const machineEditorOpen = ref(false)
  const compareMachinesOpen = ref(false)

  // Computed
  const selMachine = computed(() => machines.value.find(m => m.id === machineId.value))

  // Persist machineId to localStorage and auto-select matching post
  watch(machineId, (v: string) => {
    localStorage.setItem('toolbox.machine', v || '')
    // Auto-select matching post if profile has default
    const m = selMachine.value
    if (m?.post_id_default && config.onPostIdChange) {
      config.onPostIdChange(m.post_id_default)
    }
  })

  // Functions
  function openMachineEditor() {
    machineEditorOpen.value = true
  }

  async function onMachineSaved(id: string) {
    machineId.value = id
    await loadMachines()
  }

  function compareMachinesFunc() {
    compareMachinesOpen.value = true
  }

  async function loadMachines() {
    try {
      const r = await api('/api/machine/profiles')
      machines.value = await r.json()
    } catch (e) {
      console.error('Failed to load machines:', e)
    }
  }

  return {
    machines,
    machineId,
    selMachine,
    machineEditorOpen,
    compareMachinesOpen,
    openMachineEditor,
    onMachineSaved,
    compareMachinesFunc,
    loadMachines,
  }
}
