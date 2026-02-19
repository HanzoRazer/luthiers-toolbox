<template>
  <div class="calculator-grid basic-grid">
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
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  clear: []
  backspace: []
  number: [value: string]
  operator: [value: string]
  toggleSign: []
  calculate: []
}>()
</script>

<style scoped>
.basic-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
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

.btn-number {
  background: #3c4043;
}

.btn-operator {
  background: #5f6368;
}

.btn-clear {
  background: #ea4335;
  color: white;
}

.btn-equals {
  background: #34a853;
  color: white;
}
</style>
