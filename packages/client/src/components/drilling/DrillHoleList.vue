<template>
  <section :class="[styles.panelSection, styles.holeList]">
    <h3>Holes ({{ holes.length }})</h3>
    <div :class="styles.holeItems">
      <div
        v-for="(hole, index) in holes"
        :key="index"
        :class="[styles.holeItem, { [styles.holeItemSelected]: selectedHole === index }]"
        @click="emit('select-hole', index)"
      >
        <input
          :checked="hole.enabled"
          type="checkbox"
          @click.stop
          @change="emit('toggle-hole', index, ($event.target as HTMLInputElement).checked)"
        >
        <div :class="styles.holeInfo">
          <strong>H{{ index + 1 }}</strong>
          <small>X{{ hole.x.toFixed(1) }} Y{{ hole.y.toFixed(1) }}</small>
        </div>
        <button
          :class="styles.btnRemove"
          @click.stop="emit('remove-hole', index)"
        >
          ✕
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface Hole {
  x: number
  y: number
  enabled: boolean
}

defineProps<{
  styles: Record<string, string>
  holes: Hole[]
  selectedHole: number | null
}>()

const emit = defineEmits<{
  'select-hole': [index: number]
  'remove-hole': [index: number]
  'toggle-hole': [index: number, enabled: boolean]
}>()
</script>
