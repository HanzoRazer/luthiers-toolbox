<template>
  <section :class="styles.panelSection">
    <h3>Depth Settings</h3>
    <div :class="styles.formGroup">
      <label>Hole Depth (mm, negative)</label>
      <input
        :value="depth"
        type="number"
        step="1"
        max="0"
        @input="emit('update:depth', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Retract Plane (mm)</label>
      <input
        :value="retract"
        type="number"
        step="1"
        min="0"
        @input="emit('update:retract', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Safe Z (mm)</label>
      <input
        :value="safeZ"
        type="number"
        step="1"
        min="0"
        @input="emit('update:safeZ', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
  depth: number
  retract: number
  safeZ: number
}>()

const emit = defineEmits<{
  'update:depth': [value: number]
  'update:retract': [value: number]
  'update:safeZ': [value: number]
}>()
</script>
