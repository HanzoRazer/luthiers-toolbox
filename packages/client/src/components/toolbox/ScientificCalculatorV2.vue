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

    <!-- Shared Display -->
    <CalculatorDisplay :expression="expression" :display="display" />

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Basic Tab -->
      <BasicCalculatorPad
        v-if="activeTab === 'Basic'"
        @clear="clear"
        @backspace="backspace"
        @number="appendNumber"
        @operator="appendOperator"
        @toggle-sign="toggleSign"
        @calculate="calculate"
      />

      <!-- Scientific Tab -->
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

      <!-- Converter Tab -->
      <UnitConverterPanel
        v-else-if="activeTab === 'Converter'"
        v-model:category="converterCategory"
        :categories="converterCategories"
        :from-value="fromValue"
        :from-unit="fromUnit"
        :to-value="toValue"
        :to-unit="toUnit"
        :units="availableUnits"
        :fraction="fraction"
        @update:from-value="fromValue = $event"
        @update:from-unit="fromUnit = $event"
        @update:to-unit="toUnit = $event"
        @update:fraction="handleFractionUpdate"
        @swap="swapUnits"
        @preset="applyPreset"
      />

      <!-- Woodwork Tab -->
      <WoodworkPanel
        v-else-if="activeTab === 'Woodwork'"
        v-model:active-category="woodworkCategory"
        :categories="woodworkCategories"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useCalculatorCore } from './composables/useCalculatorCore'
import { useUnitConverter, UNIT_CATEGORIES, UNITS } from './composables/useUnitConverter'
import {
  CalculatorDisplay,
  BasicCalculatorPad,
  ScientificCalculatorPad,
  UnitConverterPanel,
  WoodworkPanel
} from './calculator'

// ============================================================================
// TAB STATE
// ============================================================================

const tabs = ['Basic', 'Scientific', 'Converter', 'Woodwork']
const activeTab = ref('Basic')

// ============================================================================
// CALCULATOR CORE (via composable)
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
// UNIT CONVERTER (via composable)
// ============================================================================

const converterCategories = [...UNIT_CATEGORIES]
const {
  category: converterCategory,
  fromValue,
  fromUnit,
  toValue,
  toUnit,
  availableUnits,
  swapUnits
} = useUnitConverter()

// Fraction input state
const fraction = ref({ whole: 0, num: 0, denom: 1 })

function handleFractionUpdate(newFraction: { whole: number; num: number; denom: number }) {
  fraction.value = newFraction
  const decimal = newFraction.whole + (newFraction.denom > 0 ? newFraction.num / newFraction.denom : 0)
  fromValue.value = decimal
  fromUnit.value = 'in'
  toUnit.value = 'mm'
}

function applyPreset(value: string, unit: string) {
  let numValue: number
  if (value.includes('/')) {
    const [num, denom] = value.split('/')
    numValue = Number(num) / Number(denom)
  } else {
    numValue = parseFloat(value)
  }

  fromValue.value = numValue
  fromUnit.value = unit
  toUnit.value = unit === 'in' ? 'mm' : 'in'
}

// ============================================================================
// WOODWORK (panel handles its own state via composable)
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
