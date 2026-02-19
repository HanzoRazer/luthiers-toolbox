<template>
  <div class="converter-content">
    <!-- Category tabs -->
    <div class="converter-tabs">
      <button
        v-for="cat in categories"
        :key="cat"
        class="converter-tab"
        :class="{ active: category === cat }"
        @click="$emit('update:category', cat)"
      >
        {{ cat }}
      </button>
    </div>

    <div class="converter-main">
      <!-- From input -->
      <div class="converter-input-group">
        <input
          :value="fromValue"
          type="number"
          class="converter-input"
          placeholder="0"
          @input="$emit('update:fromValue', Number(($event.target as HTMLInputElement).value))"
        >
        <select
          :value="fromUnit"
          class="converter-select"
          @change="$emit('update:fromUnit', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="unit in units" :key="unit.key" :value="unit.key">
            {{ unit.label }}
          </option>
        </select>
      </div>

      <!-- Swap button -->
      <div class="converter-swap">
        <button class="btn-swap" @click="$emit('swap')">↕</button>
      </div>

      <!-- To input (readonly) -->
      <div class="converter-input-group">
        <input :value="toValue.toFixed(6)" type="text" readonly class="converter-input">
        <select
          :value="toUnit"
          class="converter-select"
          @change="$emit('update:toUnit', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="unit in units" :key="unit.key" :value="unit.key">
            {{ unit.label }}
          </option>
        </select>
      </div>

      <!-- Fraction input (Length only) -->
      <div v-if="category === 'Length'" class="fraction-input">
        <div class="fraction-label">Fraction Input:</div>
        <div class="fraction-fields">
          <input
            :value="fraction.whole"
            type="number"
            class="fraction-field"
            placeholder="2"
            @input="updateFraction('whole', $event)"
          >
          <span class="fraction-sep">+</span>
          <input
            :value="fraction.num"
            type="number"
            class="fraction-field"
            placeholder="7"
            @input="updateFraction('num', $event)"
          >
          <span class="fraction-sep">/</span>
          <input
            :value="fraction.denom"
            type="number"
            class="fraction-field"
            placeholder="16"
            @input="updateFraction('denom', $event)"
          >
          <span class="fraction-unit">inches</span>
        </div>
        <div class="fraction-result">
          = {{ fractionDecimal }}" = {{ fractionMM }} mm
        </div>
      </div>

      <!-- Quick presets -->
      <div class="quick-presets">
        <div class="preset-label">Common Measurements:</div>
        <div class="preset-buttons">
          <button class="btn-preset" @click="$emit('preset', '1/16', 'in')">1/16"</button>
          <button class="btn-preset" @click="$emit('preset', '1/32', 'in')">1/32"</button>
          <button class="btn-preset" @click="$emit('preset', '1/64', 'in')">1/64"</button>
          <button class="btn-preset" @click="$emit('preset', '0.010', 'in')">.010"</button>
          <button class="btn-preset" @click="$emit('preset', '0.046', 'in')">.046"</button>
          <button class="btn-preset" @click="$emit('preset', '25.5', 'in')">25.5"</button>
          <button class="btn-preset" @click="$emit('preset', '24.75', 'in')">24.75"</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  category: string
  categories: string[]
  fromValue: number
  fromUnit: string
  toValue: number
  toUnit: string
  units: { key: string; label: string }[]
  fraction: { whole: number; num: number; denom: number }
}>()

const emit = defineEmits<{
  'update:category': [value: string]
  'update:fromValue': [value: number]
  'update:fromUnit': [value: string]
  'update:toUnit': [value: string]
  'update:fraction': [value: { whole: number; num: number; denom: number }]
  swap: []
  preset: [value: string, unit: string]
}>()

const fractionDecimal = computed(() => {
  const { whole, num, denom } = props.fraction
  return (whole + (denom > 0 ? num / denom : 0)).toFixed(4)
})

const fractionMM = computed(() => {
  return (parseFloat(fractionDecimal.value) * 25.4).toFixed(3)
})

function updateFraction(field: 'whole' | 'num' | 'denom', event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  emit('update:fraction', { ...props.fraction, [field]: value })
}
</script>

<style scoped>
.converter-content {
  background: #292a2d;
  border-radius: 8px;
  padding: 20px;
}

.converter-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.converter-tab {
  padding: 8px 16px;
  background: #3c4043;
  border: none;
  border-radius: 8px;
  color: #e8eaed;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.converter-tab:hover { background: #5f6368; }
.converter-tab.active { background: #8ab4f8; color: #202124; }

.converter-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.converter-input-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.converter-input {
  flex: 1;
  padding: 12px;
  background: #3c4043;
  border: 1px solid #5f6368;
  border-radius: 8px;
  color: #e8eaed;
  font-size: 18px;
}

.converter-select {
  flex: 1;
  padding: 12px;
  background: #3c4043;
  border: 1px solid #5f6368;
  border-radius: 8px;
  color: #e8eaed;
  font-size: 14px;
}

.converter-swap { display: flex; justify-content: center; }

.btn-swap {
  padding: 12px 24px;
  background: #1a73e8;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-size: 20px;
}

.btn-swap:hover { background: #2b7de9; }

.fraction-input {
  background: #3c4043;
  padding: 16px;
  border-radius: 8px;
}

.fraction-label {
  font-size: 14px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.fraction-fields {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.fraction-field {
  width: 60px;
  padding: 8px;
  background: #292a2d;
  border: 1px solid #5f6368;
  border-radius: 4px;
  color: #e8eaed;
  text-align: center;
}

.fraction-sep { color: #9aa0a6; font-size: 18px; }
.fraction-unit { color: #9aa0a6; font-size: 14px; }
.fraction-result { color: #8ab4f8; font-size: 14px; }

.quick-presets {
  background: #3c4043;
  padding: 16px;
  border-radius: 8px;
}

.preset-label {
  font-size: 14px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.preset-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-preset {
  padding: 8px 12px;
  background: #1a73e8;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-size: 12px;
}

.btn-preset:hover { background: #2b7de9; }

@media (max-width: 768px) {
  .converter-input-group { flex-direction: column; }
}
</style>
