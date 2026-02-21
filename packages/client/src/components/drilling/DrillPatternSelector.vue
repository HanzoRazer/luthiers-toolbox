<template>
  <section :class="styles.panelSection">
    <h3>Pattern Generator</h3>
    <select
      :value="patternType"
      :class="styles.patternSelector"
      @change="emit('update:patternType', ($event.target as HTMLSelectElement).value)"
    >
      <option value="manual">
        Manual (Click Canvas)
      </option>
      <option value="linear">
        Linear Array
      </option>
      <option value="circular">
        Circular Pattern
      </option>
      <option value="grid">
        Grid Array
      </option>
      <option value="csv">
        CSV Import
      </option>
    </select>

    <!-- Linear Pattern -->
    <DrillPatternLinear
      v-if="patternType === 'linear'"
      v-model:direction="linearPatternLocal.direction"
      v-model:startX="linearPatternLocal.startX"
      v-model:startY="linearPatternLocal.startY"
      v-model:spacing="linearPatternLocal.spacing"
      v-model:count="linearPatternLocal.count"
      @generate="emit('generate-linear', linearPatternLocal)"
    />

    <!-- Circular Pattern -->
    <DrillPatternCircular
      v-if="patternType === 'circular'"
      v-model:centerX="circularPatternLocal.centerX"
      v-model:centerY="circularPatternLocal.centerY"
      v-model:radius="circularPatternLocal.radius"
      v-model:count="circularPatternLocal.count"
      v-model:startAngle="circularPatternLocal.startAngle"
      @generate="emit('generate-circular', circularPatternLocal)"
    />

    <!-- Grid Pattern -->
    <DrillPatternGrid
      v-if="patternType === 'grid'"
      v-model:startX="gridPatternLocal.startX"
      v-model:startY="gridPatternLocal.startY"
      v-model:spacingX="gridPatternLocal.spacingX"
      v-model:spacingY="gridPatternLocal.spacingY"
      v-model:countX="gridPatternLocal.countX"
      v-model:countY="gridPatternLocal.countY"
      @generate="emit('generate-grid', gridPatternLocal)"
    />

    <!-- CSV Import -->
    <div
      v-if="patternType === 'csv'"
      :class="styles.patternControls"
    >
      <textarea
        :value="csvInput"
        rows="6"
        placeholder="x,y&#10;10,10&#10;30,10&#10;50,10"
        :class="styles.csvInput"
        @input="emit('update:csvInput', ($event.target as HTMLTextAreaElement).value)"
      />
      <button
        :class="styles.btnGenerate"
        @click="emit('import-csv')"
      >
        Import CSV
      </button>
      <small :class="styles.hint">Format: x,y (one hole per line)</small>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import DrillPatternLinear from './DrillPatternLinear.vue'
import DrillPatternCircular from './DrillPatternCircular.vue'
import DrillPatternGrid from './DrillPatternGrid.vue'

interface LinearPattern {
  direction: string
  startX: number
  startY: number
  spacing: number
  count: number
}

interface CircularPattern {
  centerX: number
  centerY: number
  radius: number
  count: number
  startAngle: number
}

interface GridPattern {
  startX: number
  startY: number
  spacingX: number
  spacingY: number
  countX: number
  countY: number
}

const props = defineProps<{
  styles: Record<string, string>
  patternType: string
  linearPattern: LinearPattern
  circularPattern: CircularPattern
  gridPattern: GridPattern
  csvInput: string
}>()

const emit = defineEmits<{
  'update:patternType': [value: string]
  'update:csvInput': [value: string]
  'generate-linear': [pattern: LinearPattern]
  'generate-circular': [pattern: CircularPattern]
  'generate-grid': [pattern: GridPattern]
  'import-csv': []
}>()

// Local reactive copies for v-model binding with child components
const linearPatternLocal = reactive({ ...props.linearPattern })
const circularPatternLocal = reactive({ ...props.circularPattern })
const gridPatternLocal = reactive({ ...props.gridPattern })

// Sync from props when they change
watch(() => props.linearPattern, (val) => Object.assign(linearPatternLocal, val), { deep: true })
watch(() => props.circularPattern, (val) => Object.assign(circularPatternLocal, val), { deep: true })
watch(() => props.gridPattern, (val) => Object.assign(gridPatternLocal, val), { deep: true })
</script>
