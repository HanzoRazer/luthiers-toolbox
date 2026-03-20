<script setup lang="ts">
/**
 * MachineManagerView — thin host for machine lab panels.
 * @see machine-manager/MachineProfilePanel.vue — profiles CRUD
 * @see machine-manager/MachineToolsPanel.vue — per-machine tools
 * @see machine-manager/MachinePostsPanel.vue — post-processors list
 */
import { ref } from 'vue'
import MachineProfilePanel from './machine-manager/MachineProfilePanel.vue'
import MachineToolsPanel from './machine-manager/MachineToolsPanel.vue'
import MachinePostsPanel from './machine-manager/MachinePostsPanel.vue'

const selectedMachineId = ref<string | null>(null)
const error = ref('')
const successMessage = ref('')

let successTimer: ReturnType<typeof setTimeout> | undefined

function onError(msg: string) {
  error.value = msg
}

function onSuccess(msg: string) {
  successMessage.value = msg
  if (successTimer) clearTimeout(successTimer)
  successTimer = setTimeout(() => {
    successMessage.value = ''
  }, 3000)
}
</script>

<template>
  <div class="machine-manager-view">
    <header class="view-header">
      <h1>Machine Manager</h1>
      <p class="subtitle">Configure and manage your CNC machines, tools, and post-processors</p>
    </header>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button type="button" class="dismiss-btn" @click="error = ''">&times;</button>
    </div>

    <div v-if="successMessage" class="success-banner">
      {{ successMessage }}
    </div>

    <div class="content-grid">
      <MachineProfilePanel
        v-model="selectedMachineId"
        @error="onError"
        @success="onSuccess"
      />
      <MachinePostsPanel @error="onError" />
      <MachineToolsPanel
        :selected-machine-id="selectedMachineId"
        @error="onError"
        @success="onSuccess"
      />
    </div>
  </div>
</template>

<style scoped>
.machine-manager-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.success-banner {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #059669;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: inherit;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
</style>
