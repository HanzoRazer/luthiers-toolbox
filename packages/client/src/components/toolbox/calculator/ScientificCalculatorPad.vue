<template>
  <div class="calculator-grid scientific-grid">
    <!-- Mode toggles -->
    <div class="mode-toggles">
      <label class="toggle">
        <input v-model="angleModeLocal" type="radio" value="deg">
        <span>DEG</span>
      </label>
      <label class="toggle">
        <input v-model="angleModeLocal" type="radio" value="rad">
        <span>RAD</span>
      </label>
      <button class="btn-small" @click="$emit('toggleHistory')">History</button>
    </div>

    <!-- Scientific functions row 1 -->
    <button class="btn btn-function" @click="$emit('function', 'sin(')">sin</button>
    <button class="btn btn-function" @click="$emit('function', 'cos(')">cos</button>
    <button class="btn btn-function" @click="$emit('function', 'tan(')">tan</button>
    <button class="btn btn-function" @click="$emit('function', 'ln(')">ln</button>
    <button class="btn btn-function" @click="$emit('function', 'log(')">log</button>
    <button class="btn btn-function" @click="$emit('function', 'sqrt(')">√</button>

    <!-- Scientific functions row 2 -->
    <button class="btn btn-operator" @click="$emit('operator', '^')">^</button>
    <button class="btn btn-operator" @click="$emit('operator', '(')">(</button>
    <button class="btn btn-operator" @click="$emit('operator', ')')">)</button>
    <button class="btn btn-function" @click="$emit('number', 'π')">π</button>
    <button class="btn btn-function" @click="$emit('number', 'e')">e</button>
    <button class="btn btn-function" @click="$emit('function', '!')">!</button>

    <!-- Standard calculator buttons -->
    <button class="btn btn-clear" @click="$emit('clear')">C</button>
    <button class="btn btn-operator" @click="$emit('backspace')">⌫</button>
    <button class="btn btn-operator" @click="$emit('operator', '%')">%</button>
    <button class="btn btn-operator" @click="$emit('operator', '÷')">÷</button>
    <button class="btn btn-number" @click="$emit('number', '7')">7</button>
    <button class="btn btn-number" @click="$emit('number', '8')">8</button>

    <button class="btn btn-number" @click="$emit('number', '9')">9</button>
    <button class="btn btn-operator" @click="$emit('operator', '×')">×</button>
    <button class="btn btn-number" @click="$emit('number', '4')">4</button>
    <button class="btn btn-number" @click="$emit('number', '5')">5</button>
    <button class="btn btn-number" @click="$emit('number', '6')">6</button>
    <button class="btn btn-operator" @click="$emit('operator', '−')">−</button>

    <button class="btn btn-number" @click="$emit('number', '1')">1</button>
    <button class="btn btn-number" @click="$emit('number', '2')">2</button>
    <button class="btn btn-number" @click="$emit('number', '3')">3</button>
    <button class="btn btn-operator" @click="$emit('operator', '+')">+</button>
    <button class="btn btn-number" @click="$emit('toggleSign')">±</button>
    <button class="btn btn-number" @click="$emit('number', '0')">0</button>

    <button class="btn btn-number" @click="$emit('number', '.')">.</button>
    <button class="btn btn-equals" @click="$emit('calculate')">=</button>

    <!-- History dropdown -->
    <div v-if="showHistory" class="history-dropdown">
      <div class="history-title">History</div>
      <div
        v-for="(item, i) in history"
        :key="i"
        class="history-item"
        @click="$emit('loadHistory', item)"
      >
        {{ item }}
      </div>
      <div v-if="history.length === 0" class="history-empty">No history yet</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  angleMode: 'deg' | 'rad'
  showHistory: boolean
  history: string[]
}>()

const emit = defineEmits<{
  'update:angleMode': [value: 'deg' | 'rad']
  toggleHistory: []
  clear: []
  backspace: []
  number: [value: string]
  operator: [value: string]
  function: [value: string]
  toggleSign: []
  calculate: []
  loadHistory: [item: string]
}>()

const angleModeLocal = computed({
  get: () => props.angleMode,
  set: (v) => emit('update:angleMode', v)
})
</script>

<style scoped>
.scientific-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  position: relative;
}

.mode-toggles {
  grid-column: 1 / -1;
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px;
  background: #292a2d;
  border-radius: 8px;
  margin-bottom: 8px;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #e8eaed;
}

.toggle input[type="radio"] {
  accent-color: #8ab4f8;
}

.btn-small {
  padding: 4px 12px;
  background: #3c4043;
  border: none;
  border-radius: 4px;
  color: #e8eaed;
  cursor: pointer;
  font-size: 12px;
}

.btn-small:hover {
  background: #5f6368;
}

.btn {
  padding: 16px;
  border: none;
  border-radius: 50%;
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #3c4043;
  color: #e8eaed;
}

.btn:hover {
  background: #5f6368;
  transform: scale(1.05);
}

.btn:active {
  transform: scale(0.95);
}

.btn-number { background: #3c4043; }
.btn-operator { background: #5f6368; }
.btn-function { background: #1a73e8; color: white; }
.btn-clear { background: #ea4335; color: white; }
.btn-equals { background: #34a853; color: white; }

.history-dropdown {
  position: absolute;
  top: 60px;
  right: 0;
  background: #292a2d;
  border: 1px solid #3c4043;
  border-radius: 8px;
  padding: 8px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 10;
  min-width: 300px;
}

.history-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #8ab4f8;
}

.history-item {
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 4px;
  color: #e8eaed;
}

.history-item:hover {
  background: #3c4043;
}

.history-empty {
  color: #9aa0a6;
  font-size: 12px;
  padding: 8px;
}

@media (max-width: 768px) {
  .scientific-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
