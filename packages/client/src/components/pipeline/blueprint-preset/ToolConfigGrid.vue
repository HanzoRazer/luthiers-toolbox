<script setup lang="ts">
/**
 * ToolConfigGrid.vue - Tool configuration form grid
 * Extracted from BlueprintPresetPanel.vue
 */

export interface ToolConfig {
  tool_d: number
  stepover: number
  stepdown: number
  margin: number
  safe_z: number
  z_rough: number
  feed_xy: number
}

const props = defineProps<{
  config: ToolConfig
}>()

const emit = defineEmits<{
  'update:config': [config: ToolConfig]
}>()

function updateField<K extends keyof ToolConfig>(key: K, value: ToolConfig[K]) {
  emit('update:config', { ...props.config, [key]: value })
}
</script>

<template>
  <div>
    <h3 class="section-title">🔧 Tool Configuration</h3>
    <div class="tool-grid">
      <label class="input-label">
        <span>Tool Ø (mm)</span>
        <input
          :value="config.tool_d"
          type="number"
          step="0.1"
          class="input-field"
          @input="updateField('tool_d', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
      <label class="input-label">
        <span>Stepover</span>
        <input
          :value="config.stepover"
          type="number"
          step="0.05"
          class="input-field"
          @input="updateField('stepover', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
      <label class="input-label">
        <span>Stepdown</span>
        <input
          :value="config.stepdown"
          type="number"
          step="0.1"
          class="input-field"
          @input="updateField('stepdown', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
      <label class="input-label">
        <span>Margin</span>
        <input
          :value="config.margin"
          type="number"
          step="0.1"
          class="input-field"
          @input="updateField('margin', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
      <label class="input-label">
        <span>Safe Z</span>
        <input
          :value="config.safe_z"
          type="number"
          step="0.1"
          class="input-field"
          @input="updateField('safe_z', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
      <label class="input-label">
        <span>Z Rough</span>
        <input
          :value="config.z_rough"
          type="number"
          step="0.1"
          class="input-field"
          @input="updateField('z_rough', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
      <label class="input-label span-2">
        <span>Feed XY</span>
        <input
          :value="config.feed_xy"
          type="number"
          step="10"
          class="input-field"
          @input="updateField('feed_xy', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  font-size: 1.1em;
  margin-bottom: 10px;
}

.tool-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.input-label {
  display: flex;
  flex-direction: column;
}

.input-label span {
  font-size: 0.9em;
  color: #666;
}

.input-field {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.span-2 {
  grid-column: span 2;
}
</style>
