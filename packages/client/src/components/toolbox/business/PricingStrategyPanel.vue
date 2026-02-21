<template>
  <div class="tab-content">
    <h2>🏷️ Pricing Strategy</h2>

    <div class="section">
      <h3>Target Pricing</h3>
      <div class="input-row">
        <label>Build Cost:</label>
        <input
          :value="buildCost"
          type="number"
          step="10"
          @input="emit('update:buildCost', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">$</span>
      </div>
      <div class="input-row">
        <label>Desired Margin (%):</label>
        <input
          :value="margin"
          type="number"
          step="5"
          min="10"
          max="200"
          @input="emit('update:margin', Number(($event.target as HTMLInputElement).value))"
        >
        <span class="unit">%</span>
      </div>
    </div>

    <div class="results">
      <h3>Recommended Pricing</h3>
      <div class="result-item">
        <span>Selling Price:</span>
        <strong>${{ sellingPrice.toFixed(2) }}</strong>
      </div>
      <div class="result-item">
        <span>Profit per Unit:</span>
        <strong>${{ profit.toFixed(2) }}</strong>
      </div>
      <div class="result-item">
        <span>Units to Break Even:</span>
        <strong>{{ breakEvenUnits }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  buildCost: number
  margin: number
  sellingPrice: number
  profit: number
  breakEvenUnits: number
}>()

const emit = defineEmits<{
  'update:buildCost': [value: number]
  'update:margin': [value: number]
}>()
</script>

<style scoped>
.tab-content {
  padding: 20px 0;
}

.tab-content h2 {
  margin-bottom: 20px;
  color: #333;
}

.section {
  margin-bottom: 25px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.section h3 {
  margin-bottom: 15px;
  color: #495057;
  font-size: 16px;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.input-row label {
  flex: 0 0 150px;
  color: #495057;
}

.input-row input {
  flex: 1;
  max-width: 150px;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.input-row .unit {
  color: #6c757d;
  font-size: 14px;
}

.results {
  padding: 15px;
  background: #e3f2fd;
  border-radius: 8px;
}

.results h3 {
  margin-bottom: 15px;
  color: #1565c0;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #bbdefb;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item span {
  color: #495057;
}

.result-item strong {
  color: #1a73e8;
}
</style>
