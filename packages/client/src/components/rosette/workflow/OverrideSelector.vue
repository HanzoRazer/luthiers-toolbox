<template>
  <div class="overrides">
    <div class="ovTitle">Download overrides</div>

    <select
      :value="toolId"
      class="sel"
      title="Override tool_id"
      @change="$emit('update:toolId', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="o in toolOptions" :key="o.id" :value="o.id">
        {{ o.label }}
      </option>
    </select>

    <select
      :value="materialId"
      class="sel"
      title="Override material_id"
      @change="$emit('update:materialId', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="o in materialOptions" :key="o.id" :value="o.id">
        {{ o.label }}
      </option>
    </select>

    <select
      :value="machineProfileId"
      class="sel"
      title="Override machine_profile_id"
      @change="$emit('update:machineProfileId', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="o in machineOptions" :key="o.id" :value="o.id">
        {{ o.label }}
      </option>
    </select>

    <select
      :value="camProfileId"
      class="sel"
      title="Override requested_cam_profile_id"
      @change="$emit('update:camProfileId', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="o in camProfileOptions" :key="o.id" :value="o.id">
        {{ o.label }}
      </option>
    </select>

    <select
      :value="riskTolerance"
      class="sel"
      title="Override risk_tolerance"
      @change="$emit('update:riskTolerance', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="o in riskToleranceOptions" :key="o.id" :value="o.id">
        {{ o.label }}
      </option>
    </select>

    <button class="btn ghost" title="Clear overrides" @click="$emit('clear')">
      Clear
    </button>
  </div>
</template>

<script setup lang="ts">
import type { OverrideOption } from '../composables/useWorkflowOverrides'

defineProps<{
  toolId: string
  materialId: string
  machineProfileId: string
  camProfileId: string
  riskTolerance: string
  toolOptions: OverrideOption[]
  materialOptions: OverrideOption[]
  machineOptions: OverrideOption[]
  camProfileOptions: OverrideOption[]
  riskToleranceOptions: OverrideOption[]
}>()

defineEmits<{
  'update:toolId': [value: string]
  'update:materialId': [value: string]
  'update:machineProfileId': [value: string]
  'update:camProfileId': [value: string]
  'update:riskTolerance': [value: string]
  clear: []
}>()
</script>

<style scoped>
.overrides {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.ovTitle {
  font-size: 12px;
  font-weight: 800;
  opacity: 0.85;
  margin-right: 4px;
}

.sel {
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  padding: 6px 8px;
  font-size: 12px;
  background: white;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  background: #fff;
  transition: background 0.1s;
}

.btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
}

.btn.ghost {
  background: transparent;
}
</style>
