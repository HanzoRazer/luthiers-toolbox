<script setup lang="ts">
/**
 * PocketSettingsPanel - CAM settings for adaptive pocket
 * Extracted from AdaptivePocketLab.vue
 */

defineProps<{
  toolD: number
  stepoverPct: number
  stepdown: number
  margin: number
  strategy: 'Spiral' | 'Lanes'
  cornerRadiusMin: number
  slowdownFeedPct: number
  climb: boolean
  feedXY: number
  units: 'mm' | 'inch'
  feedZ: number
  plungeRate: number
  safeZ: number
  depth: number
  spindleRpm: number
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:toolD': [value: number]
  'update:stepoverPct': [value: number]
  'update:stepdown': [value: number]
  'update:margin': [value: number]
  'update:strategy': [value: 'Spiral' | 'Lanes']
  'update:cornerRadiusMin': [value: number]
  'update:slowdownFeedPct': [value: number]
  'update:climb': [value: boolean]
  'update:feedXY': [value: number]
  'update:units': [value: 'mm' | 'inch']
  'update:feedZ': [value: number]
  'update:plungeRate': [value: number]
  'update:safeZ': [value: number]
  'update:depth': [value: number]
  'update:spindleRpm': [value: number]
}>()
</script>

<template>
  <div class="settings-panel">
    <h4 class="section-title">Tool Settings</h4>

    <div class="form-grid">
      <label class="form-label">
        Tool Ø (mm)
        <input
          :value="toolD"
          type="number"
          step="0.1"
          min="0.1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:toolD', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Step-over (%)
        <input
          :value="stepoverPct"
          type="number"
          step="1"
          min="5"
          max="95"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:stepoverPct', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Step-down (mm)
        <input
          :value="stepdown"
          type="number"
          step="0.1"
          min="0.1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:stepdown', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Margin (mm)
        <input
          :value="margin"
          type="number"
          step="0.1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:margin', Number(($event.target as HTMLInputElement).value))"
        >
      </label>
    </div>

    <h4 class="section-title">Strategy</h4>

    <div class="form-grid">
      <label class="form-label">
        Strategy
        <select
          :value="strategy"
          :disabled="disabled"
          class="form-input"
          @change="emit('update:strategy', ($event.target as HTMLSelectElement).value as 'Spiral' | 'Lanes')"
        >
          <option value="Spiral">Spiral</option>
          <option value="Lanes">Lanes</option>
        </select>
      </label>

      <label class="form-label">
        Corner Radius Min (mm)
        <input
          :value="cornerRadiusMin"
          type="number"
          step="0.1"
          min="0"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:cornerRadiusMin', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Slowdown Feed (%)
        <input
          :value="slowdownFeedPct"
          type="number"
          step="5"
          min="30"
          max="100"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:slowdownFeedPct', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-checkbox">
        <input
          :checked="climb"
          type="checkbox"
          :disabled="disabled"
          @change="emit('update:climb', ($event.target as HTMLInputElement).checked)"
        >
        <span>Climb milling</span>
      </label>
    </div>

    <h4 class="section-title">Feeds & Speeds</h4>

    <div class="form-grid">
      <label class="form-label">
        Feed XY (mm/min)
        <input
          :value="feedXY"
          type="number"
          step="100"
          min="1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:feedXY', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Feed Z (mm/min)
        <input
          :value="feedZ"
          type="number"
          step="50"
          min="1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:feedZ', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Plunge Rate (mm/min)
        <input
          :value="plungeRate"
          type="number"
          step="50"
          min="1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:plungeRate', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Spindle RPM
        <input
          :value="spindleRpm"
          type="number"
          step="1000"
          min="0"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:spindleRpm', Number(($event.target as HTMLInputElement).value))"
        >
      </label>
    </div>

    <h4 class="section-title">Geometry</h4>

    <div class="form-grid">
      <label class="form-label">
        Depth (mm)
        <input
          :value="depth"
          type="number"
          step="0.5"
          min="0.1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:depth', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Safe Z (mm)
        <input
          :value="safeZ"
          type="number"
          step="1"
          min="1"
          :disabled="disabled"
          class="form-input"
          @input="emit('update:safeZ', Number(($event.target as HTMLInputElement).value))"
        >
      </label>

      <label class="form-label">
        Units
        <select
          :value="units"
          :disabled="disabled"
          class="form-input"
          @change="emit('update:units', ($event.target as HTMLSelectElement).value as 'mm' | 'inch')"
        >
          <option value="mm">mm (G21)</option>
          <option value="inch">inch (G20)</option>
        </select>
      </label>
    </div>
  </div>
</template>

<style scoped>
.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text, #1f2937);
  margin: 0;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
}

.form-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-muted, #6b7280);
}

.form-input {
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.875rem;
  width: 100%;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary, #3b82f6);
  box-shadow: 0 0 0 2px var(--color-primary-light, #dbeafe);
}

.form-input:disabled {
  background: var(--color-surface-elevated, #f3f4f6);
  cursor: not-allowed;
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
}

.form-checkbox input {
  margin: 0;
}
</style>
