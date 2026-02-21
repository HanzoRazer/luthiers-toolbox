<template>
  <div class="settings-grid">
    <div class="field">
      <label for="outputWidth">Output Width (mm)</label>
      <InputNumber
        id="outputWidth"
        :model-value="outputWidth"
        :min="10"
        :max="500"
        :disabled="disabled"
        @update:model-value="$emit('update:outputWidth', $event)"
      />
    </div>

    <div class="field">
      <label for="simplify">Simplification</label>
      <InputNumber
        id="simplify"
        :model-value="simplify"
        :min="0.1"
        :max="10"
        :step="0.1"
        :disabled="disabled"
        @update:model-value="$emit('update:simplify', $event)"
      />
      <small>Higher = simpler paths</small>
    </div>

    <div class="field checkbox">
      <Checkbox
        id="fitToRing"
        :model-value="fitToRing"
        :binary="true"
        :disabled="disabled"
        @update:model-value="$emit('update:fitToRing', $event)"
      />
      <label for="fitToRing">Fit to Circular Ring</label>
    </div>

    <div class="field checkbox">
      <Checkbox
        id="invert"
        :model-value="invert"
        :binary="true"
        :disabled="disabled"
        @update:model-value="$emit('update:invert', $event)"
      />
      <label for="invert">Invert Colors</label>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  outputWidth: number
  simplify: number
  fitToRing: boolean
  invert: boolean
  disabled: boolean
}>()

defineEmits<{
  'update:outputWidth': [value: number]
  'update:simplify': [value: number]
  'update:fitToRing': [value: boolean]
  'update:invert': [value: boolean]
}>()
</script>

<style scoped>
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field.checkbox {
  flex-direction: row;
  align-items: center;
}

.field.checkbox label {
  margin-left: 0.5rem;
}

.field label {
  font-weight: 500;
  color: #495057;
}

.field small {
  color: #6c757d;
  font-size: 0.85rem;
}
</style>
