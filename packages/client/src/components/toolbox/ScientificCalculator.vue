<template>
  <div class="calculator">
    <!-- Tab Navigation -->
    <div class="tabs">
      <div
        v-for="tabName in tabs"
        :key="tabName"
        class="tab"
        :class="{ active: activeTab === tabName }"
        @click="activeTab = tabName"
      >
        {{ tabName }}
      </div>
    </div>

    <!-- Display (shared across Basic & Scientific tabs) -->
    <CalculatorDisplay
      v-if="activeTab === 'Basic' || activeTab === 'Scientific'"
      :expression="expression"
      :display="display"
    />

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- BASIC TAB -->
      <BasicCalculatorPad
        v-if="activeTab === 'Basic'"
        @clear="clear"
        @backspace="backspace"
        @number="appendNumber"
        @operator="appendOperator"
        @toggle-sign="toggleSign"
        @calculate="calculate"
      />

      <!-- SCIENTIFIC TAB -->
      <ScientificCalculatorPad
        v-else-if="activeTab === 'Scientific'"
        v-model:angle-mode="angleMode"
        :show-history="showHistory"
        :history="history"
        @toggle-history="showHistory = !showHistory"
        @clear="clear"
        @backspace="backspace"
        @number="appendNumber"
        @operator="appendOperator"
        @function="appendFunction"
        @toggle-sign="toggleSign"
        @calculate="calculate"
        @load-history="loadHistory"
      />

      <!-- CONVERTER TAB -->
      <UnitConverterPanel
        v-else-if="activeTab === 'Converter'"
        v-model:category="converterCategory"
        :categories="converterCategories"
        v-model:from-value="converterFromValue"
        v-model:from-unit="converterFromUnit"
        :to-value="converterToValue"
        v-model:to-unit="converterToUnit"
        :units="converterUnits"
        v-model:fraction="fraction"
        @swap="swapConverterUnits"
        @preset="applyPreset"
      />

      <!-- WOODWORK TAB -->
      <WoodworkPanel
        v-else-if="activeTab === 'Woodwork'"
        v-model:active-category="woodworkCategory"
        :categories="woodworkCategories"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  CalculatorDisplay,
  BasicCalculatorPad,
  ScientificCalculatorPad,
  UnitConverterPanel,
  WoodworkPanel
} from './calculator'
import { useCalculatorCore } from './composables/useCalculatorCore'
import { useUnitConverter, UNIT_CATEGORIES } from './composables/useUnitConverter'

// ============================================================================
// TAB STATE
// ============================================================================

const tabs = ['Basic', 'Scientific', 'Converter', 'Woodwork']
const activeTab = ref('Basic')

// ============================================================================
// CALCULATOR CORE (Basic & Scientific)
// ============================================================================

const {
  display,
  expression,
  angleMode,
  history,
  showHistory,
  clear,
  backspace,
  appendNumber,
  appendOperator,
  appendFunction,
  toggleSign,
  calculate,
  loadHistory
} = useCalculatorCore()

// ============================================================================
// UNIT CONVERTER
// ============================================================================

const converterCategories = [...UNIT_CATEGORIES]

const {
  category: converterCategory,
  fromValue: converterFromValue,
  fromUnit: converterFromUnit,
  toUnit: converterToUnit,
  toValue: converterToValue,
  availableUnits,
  swapUnits: swapConverterUnits
} = useUnitConverter()

const converterUnits = computed(() =>
  availableUnits.value.map(u => ({ key: u.key, label: u.label }))
)

// Fraction input for length conversions
const fraction = ref({ whole: 0, num: 0, denom: 1 })

// When fraction changes, update the converter
watch(fraction, (f) => {
  if (converterCategory.value === 'Length' && f.denom > 0) {
    const decimal = f.whole + (f.num / f.denom)
    converterFromValue.value = decimal
    converterFromUnit.value = 'in'
    converterToUnit.value = 'mm'
  }
}, { deep: true })

function applyPreset(value: string, unit: string) {
  const numValue = value.includes('/')
    ? eval(value.replace('/', ' / '))
    : parseFloat(value)

  converterFromValue.value = numValue
  converterFromUnit.value = unit
  converterToUnit.value = unit === 'in' ? 'mm' : 'in'
}

// ============================================================================
// WOODWORK
// ============================================================================

const woodworkCategories = ['Board Feet', 'Volume', 'Angles']
const woodworkCategory = ref('Board Feet')
</script>

<style scoped>
.calculator {
  max-width: 800px;
  margin: 0 auto;
  background: #202124;
  border-radius: 12px;
  padding: 20px;
  color: #e8eaed;
  font-family: 'Roboto', sans-serif;
}

/* Tab Navigation */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid #3c4043;
  padding-bottom: 8px;
}

.tab {
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 8px 8px 0 0;
  transition: all 0.2s;
  color: #9aa0a6;
  font-size: 14px;
  font-weight: 500;
}

.tab:hover {
  background: #3c4043;
  color: #e8eaed;
}

.tab.active {
  background: #8ab4f8;
  color: #202124;
}

/* Responsive */
@media (max-width: 768px) {
  .calculator {
    padding: 12px;
  }

  .tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
  }
}
</style>
