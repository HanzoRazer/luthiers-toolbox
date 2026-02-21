<template>
  <div class="amortization-section">
    <button
      class="toggle-btn"
      @click="emit('update:show', false)"
    >
      ▼ Hide Amortization Schedule
    </button>
    <div class="amortization-table">
      <div class="table-header">
        <div>Payment #</div>
        <div>Date</div>
        <div>Principal</div>
        <div>Interest</div>
        <div>Balance</div>
      </div>
      <div
        v-for="payment in schedule.slice(0, 12)"
        :key="payment.number"
        class="table-row"
      >
        <div>{{ payment.number }}</div>
        <div>{{ payment.date }}</div>
        <div>${{ payment.principal.toFixed(2) }}</div>
        <div>${{ payment.interest.toFixed(2) }}</div>
        <div>${{ payment.balance.toFixed(2) }}</div>
      </div>
      <div
        v-if="schedule.length > 12"
        class="table-row summary"
      >
        <div colspan="5">
          ... {{ schedule.length - 12 }} more payments ...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface AmortizationPayment {
  number: number
  date: string
  principal: number
  interest: number
  balance: number
}

defineProps<{
  schedule: AmortizationPayment[]
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()
</script>

<style scoped>
.amortization-section {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.toggle-btn {
  background: none;
  border: none;
  color: #1a73e8;
  cursor: pointer;
  font-size: 14px;
  padding: 5px 0;
  margin-bottom: 10px;
}

.toggle-btn:hover {
  text-decoration: underline;
}

.amortization-table {
  font-size: 13px;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 80px 100px 1fr 1fr 1fr;
  gap: 10px;
  padding: 8px 0;
}

.table-header {
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
  color: #495057;
}

.table-row {
  border-bottom: 1px solid #e9ecef;
}

.table-row.summary {
  font-style: italic;
  color: #6c757d;
}
</style>
