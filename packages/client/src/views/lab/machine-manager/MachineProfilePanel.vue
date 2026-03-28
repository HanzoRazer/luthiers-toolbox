<script setup lang="ts">
/**
 * Machine profiles: orchestrates list, editor, and CAM connection (default post).
 */
import { useConfirm } from '@/composables/useConfirm'
import { ref, computed, onMounted, watch } from 'vue'
import MachineListPanel from './MachineListPanel.vue'
import MachineProfileEditor from './MachineProfileEditor.vue'
import MachineConnectionPanel from './MachineConnectionPanel.vue'
import {
  MACHINES_API,
  machineProfileFromNewDraft,
  type MachineProfile,
  type NewMachineDraft,
} from './machineManagerTypes'

const { confirm } = useConfirm()

const props = defineProps<{
  modelValue: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [id: string | null]
  error: [message: string]
  success: [message: string]
}>()

const selectedMachineId = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const machines = ref<MachineProfile[]>([])
const isLoadingMachines = ref(false)
const isSaving = ref(false)
const editingProfile = ref<MachineProfile | null>(null)
const listPanelRef = ref<InstanceType<typeof MachineListPanel> | null>(null)

const selectedMachine = computed(
  () => machines.value.find(m => m.id === selectedMachineId.value) || null,
)

onMounted(() => {
  void loadMachines()
})

watch(
  () => props.modelValue,
  (newId) => {
    if (newId) {
      const machine = machines.value.find(m => m.id === newId)
      if (machine) {
        editingProfile.value = JSON.parse(JSON.stringify(machine))
      }
    } else {
      editingProfile.value = null
    }
  },
)

watch(machines, () => {
  const id = props.modelValue
  if (id) {
    const machine = machines.value.find(m => m.id === id)
    if (machine) {
      editingProfile.value = JSON.parse(JSON.stringify(machine))
    }
  }
})

async function loadMachines() {
  isLoadingMachines.value = true
  emit('error', '')

  try {
    const response = await fetch(`${MACHINES_API}/profiles`)
    if (!response.ok) throw new Error('Failed to load machines')
    machines.value = await response.json()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to load machines'
    emit('error', msg)
  } finally {
    isLoadingMachines.value = false
  }
}

async function saveMachine() {
  if (!editingProfile.value) return

  isSaving.value = true
  emit('error', '')

  try {
    const response = await fetch(`${MACHINES_API}/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editingProfile.value),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to save machine')
    }

    const result = await response.json()
    emit('success', `Machine ${result.status}: ${result.id}`)
    await loadMachines()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to save machine'
    emit('error', msg)
  } finally {
    isSaving.value = false
  }
}

async function createMachine(draft: NewMachineDraft) {
  isSaving.value = true
  emit('error', '')

  try {
    const profile = machineProfileFromNewDraft(draft)

    const response = await fetch(`${MACHINES_API}/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to create machine')
    }

    listPanelRef.value?.resetAddModal()
    await loadMachines()
    emit('success', 'Machine created successfully')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to create machine'
    emit('error', msg)
  } finally {
    isSaving.value = false
  }
}

async function deleteMachine(id: string) {
  if (!(await confirm(`Delete machine "${id}"? This cannot be undone.`))) return

  try {
    const response = await fetch(`${MACHINES_API}/profiles/${id}`, {
      method: 'DELETE',
    })

    if (!response.ok) throw new Error('Failed to delete machine')

    if (selectedMachineId.value === id) {
      selectedMachineId.value = null
    }
    await loadMachines()
    emit('success', 'Machine deleted')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to delete machine'
    emit('error', msg)
  }
}

function resetEditor() {
  if (selectedMachine.value) {
    editingProfile.value = JSON.parse(JSON.stringify(selectedMachine.value))
  }
}
</script>

<template>
  <div class="profile-panels-row">
    <MachineListPanel
      ref="listPanelRef"
      v-model="selectedMachineId"
      :machines="machines"
      :is-loading-machines="isLoadingMachines"
      :is-saving="isSaving"
      @delete="deleteMachine"
      @create="createMachine"
    />
    <div class="profile-right-stack">
      <MachineProfileEditor
        v-model="editingProfile"
        :selected-machine="selectedMachine"
        :is-saving="isSaving"
        @save="saveMachine"
        @reset="resetEditor"
      />
      <MachineConnectionPanel
        v-model="editingProfile"
        @error="emit('error', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.profile-panels-row {
  display: contents;
}

.profile-right-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
}
</style>
