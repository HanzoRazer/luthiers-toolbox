<template>
  <div class="dimension-sections">
    <!-- Body Dimensions -->
    <section class="form-section">
      <h3>Body Dimensions</h3>
      <div class="form-grid">
        <div class="form-field">
          <label for="bodyLength">Body Length</label>
          <div class="input-with-unit">
            <input
              id="bodyLength"
              :value="dimensions.bodyLength"
              type="number"
              step="0.1"
              @input="updateField('bodyLength', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Tip to tail along centerline</span>
        </div>

        <div class="form-field">
          <label for="bodyWidthUpper">Upper Bout Width</label>
          <div class="input-with-unit">
            <input
              id="bodyWidthUpper"
              :value="dimensions.bodyWidthUpper"
              type="number"
              step="0.1"
              @input="updateField('bodyWidthUpper', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Widest point above waist</span>
        </div>

        <div class="form-field">
          <label for="bodyWidthLower">Lower Bout Width</label>
          <div class="input-with-unit">
            <input
              id="bodyWidthLower"
              :value="dimensions.bodyWidthLower"
              type="number"
              step="0.1"
              @input="updateField('bodyWidthLower', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Widest point below waist</span>
        </div>

        <div class="form-field">
          <label for="waistWidth">Waist Width</label>
          <div class="input-with-unit">
            <input
              id="waistWidth"
              :value="dimensions.waistWidth"
              type="number"
              step="0.1"
              @input="updateField('waistWidth', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Narrowest point (C-curves)</span>
        </div>

        <div class="form-field">
          <label for="bodyDepth">Body Depth</label>
          <div class="input-with-unit">
            <input
              id="bodyDepth"
              :value="dimensions.bodyDepth"
              type="number"
              step="0.1"
              @input="updateField('bodyDepth', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Including top and back arch (if any)</span>
        </div>

        <div class="form-field">
          <label for="scaleLength">Scale Length</label>
          <div class="input-with-unit">
            <input
              id="scaleLength"
              :value="dimensions.scaleLength"
              type="number"
              step="0.1"
              @input="updateField('scaleLength', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Nut to bridge saddle</span>
        </div>
      </div>
    </section>

    <!-- Neck Dimensions -->
    <section class="form-section">
      <h3>Neck Dimensions</h3>
      <div class="form-grid">
        <div class="form-field">
          <label for="nutWidth">Nut Width</label>
          <div class="input-with-unit">
            <input
              id="nutWidth"
              :value="dimensions.nutWidth"
              type="number"
              step="0.1"
              @input="updateField('nutWidth', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
        </div>

        <div class="form-field">
          <label for="bridgeSpacing">Bridge String Spacing</label>
          <div class="input-with-unit">
            <input
              id="bridgeSpacing"
              :value="dimensions.bridgeSpacing"
              type="number"
              step="0.1"
              @input="updateField('bridgeSpacing', $event)"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
        </div>

        <div class="form-field">
          <label for="fretCount">Fret Count</label>
          <div class="input-with-unit">
            <input
              id="fretCount"
              :value="dimensions.fretCount"
              type="number"
              step="1"
              @input="updateField('fretCount', $event)"
            >
            <span class="unit">frets</span>
          </div>
        </div>

        <div class="form-field">
          <label for="neckAngle">Neck Angle</label>
          <div class="input-with-unit">
            <input
              id="neckAngle"
              :value="dimensions.neckAngle"
              type="number"
              step="0.1"
              @input="updateField('neckAngle', $event)"
            >
            <span class="unit">degrees</span>
          </div>
          <span class="hint">Set-neck tilt (0° for bolt-on)</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { GuitarDimensions } from '../composables/useGuitarDimensions'

const props = defineProps<{
  dimensions: GuitarDimensions
  currentUnit: string
}>()

const emit = defineEmits<{
  'update:dimensions': [value: GuitarDimensions]
  change: []
}>()

function updateField(field: keyof GuitarDimensions, event: Event) {
  const target = event.target as HTMLInputElement
  const value = field === 'fretCount' ? parseInt(target.value) : parseFloat(target.value)
  emit('update:dimensions', { ...props.dimensions, [field]: value })
  emit('change')
}
</script>

<style scoped>
.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h3 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: #444;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 600;
  color: #555;
  font-size: 0.9rem;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-field input {
  flex: 1;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-field input:focus {
  outline: none;
  border-color: #667eea;
}

.unit {
  font-size: 0.85rem;
  color: #666;
  min-width: 40px;
}

.hint {
  font-size: 0.8rem;
  color: #999;
  font-style: italic;
}
</style>
