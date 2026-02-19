<template>
  <div class="woodwork-content">
    <!-- Category tabs -->
    <div class="woodwork-tabs">
      <button
        v-for="cat in categories"
        :key="cat"
        class="woodwork-tab"
        :class="{ active: activeCategory === cat }"
        @click="$emit('update:activeCategory', cat)"
      >
        {{ cat }}
      </button>
    </div>

    <!-- Board Feet Calculator -->
    <div v-if="activeCategory === 'Board Feet'" class="woodwork-panel">
      <h3>📏 Board Feet Calculator</h3>
      <div class="input-row">
        <label>Length (in):</label>
        <input v-model.number="boardFeetLocal.length" type="number">
      </div>
      <div class="input-row">
        <label>Width (in):</label>
        <input v-model.number="boardFeetLocal.width" type="number">
      </div>
      <div class="input-row">
        <label>Thickness (in):</label>
        <input v-model.number="boardFeetLocal.thickness" type="number">
      </div>
      <div class="result-box">
        <div class="result-label">Board Feet:</div>
        <div class="result-value">{{ boardFeetResult.toFixed(2) }} BF</div>
      </div>
      <div class="input-row">
        <label>Price ($/BF):</label>
        <input v-model.number="boardFeetLocal.pricePerBF" type="number">
      </div>
      <div class="result-box">
        <div class="result-label">Total Cost:</div>
        <div class="result-value">${{ boardCostResult.toFixed(2) }}</div>
      </div>
    </div>

    <!-- Wood Volume/Weight -->
    <div v-if="activeCategory === 'Volume'" class="woodwork-panel">
      <h3>🌲 Wood Volume & Weight</h3>
      <div class="input-row">
        <label>Length (mm):</label>
        <input v-model.number="woodVolumeLocal.length" type="number">
      </div>
      <div class="input-row">
        <label>Width (mm):</label>
        <input v-model.number="woodVolumeLocal.width" type="number">
      </div>
      <div class="input-row">
        <label>Thickness (mm):</label>
        <input v-model.number="woodVolumeLocal.thickness" type="number">
      </div>
      <div class="input-row">
        <label>Species:</label>
        <select v-model="woodVolumeLocal.species">
          <option v-for="(spec, key) in woodSpecies" :key="key" :value="key">
            {{ spec.name }} (ρ={{ spec.density }} g/cm³)
          </option>
        </select>
      </div>
      <div class="result-box">
        <div class="result-label">Volume:</div>
        <div class="result-value">{{ volumeResult.toFixed(1) }} cm³</div>
      </div>
      <div class="result-box">
        <div class="result-label">Weight:</div>
        <div class="result-value">{{ weightResult.toFixed(1) }} g</div>
      </div>
    </div>

    <!-- Miter Angles -->
    <div v-if="activeCategory === 'Angles'" class="woodwork-panel">
      <h3>📐 Miter/Bevel Angle Calculator</h3>
      <div class="input-row">
        <label>Rise (mm):</label>
        <input v-model.number="miterLocal.rise" type="number">
      </div>
      <div class="input-row">
        <label>Run (mm):</label>
        <input v-model.number="miterLocal.run" type="number">
      </div>
      <div class="result-box">
        <div class="result-label">Angle:</div>
        <div class="result-value">{{ miterAngleResult.toFixed(2) }}°</div>
      </div>
      <div class="helper-text">
        Common uses: Neck angle (0.5-3°), Headstock angle (12-17°), Bridge ramp
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useWoodworkCalculator, WOOD_SPECIES } from '../composables/useWoodworkCalculator'

defineProps<{
  activeCategory: string
  categories: string[]
}>()

defineEmits<{
  'update:activeCategory': [value: string]
}>()

const {
  boardFeet,
  boardFeetResult,
  boardCostResult,
  woodVolume,
  volumeResult,
  weightResult,
  miter,
  miterAngle: miterAngleResult
} = useWoodworkCalculator()

// Local reactive bindings
const boardFeetLocal = boardFeet
const woodVolumeLocal = woodVolume
const miterLocal = miter
const woodSpecies = WOOD_SPECIES
</script>

<style scoped>
.woodwork-content {
  background: #292a2d;
  border-radius: 8px;
  padding: 20px;
}

.woodwork-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.woodwork-tab {
  padding: 8px 16px;
  background: #3c4043;
  border: none;
  border-radius: 8px;
  color: #e8eaed;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.woodwork-tab:hover { background: #5f6368; }
.woodwork-tab.active { background: #8ab4f8; color: #202124; }

.woodwork-panel {
  background: #3c4043;
  padding: 20px;
  border-radius: 8px;
}

.woodwork-panel h3 {
  margin: 0 0 16px 0;
  color: #8ab4f8;
  font-size: 18px;
}

.input-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.input-row label {
  flex: 0 0 150px;
  color: #9aa0a6;
  font-size: 14px;
}

.input-row input,
.input-row select {
  flex: 1;
  padding: 10px;
  background: #292a2d;
  border: 1px solid #5f6368;
  border-radius: 4px;
  color: #e8eaed;
  font-size: 14px;
}

.result-box {
  background: #292a2d;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-label {
  color: #9aa0a6;
  font-size: 14px;
}

.result-value {
  color: #34a853;
  font-size: 24px;
  font-weight: 500;
}

.helper-text {
  color: #9aa0a6;
  font-size: 12px;
  font-style: italic;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .input-row {
    flex-direction: column;
    align-items: stretch;
  }
  .input-row label {
    flex: 0 0 auto;
  }
}
</style>
