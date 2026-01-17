<template>
  <div class="business-calculator">
    <div class="header">
      <h1>💼 Business Calculator</h1>
      <p>Advanced financial planning for lutherie business</p>
    </div>

    <!-- Tab Navigation -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 1: Startup Planning -->
    <div v-if="activeTab === 'startup'" class="tab-content">
      <h2>🚀 Startup Planning</h2>
      
      <div class="section">
        <h3>Equipment & Tools</h3>
        <div class="input-row">
          <label>CNC Router:</label>
          <input v-model.number="startup.cncCost" type="number" step="1000">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Hand Tools:</label>
          <input v-model.number="startup.handTools" type="number" step="100">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Workbenches:</label>
          <input v-model.number="startup.workbenches" type="number" step="100">
          <span class="unit">$</span>
        </div>
      </div>

      <div class="section">
        <h3>Facilities</h3>
        <div class="input-row">
          <label>Workshop Rent (monthly):</label>
          <input v-model.number="startup.rent" type="number" step="100">
          <span class="unit">$/mo</span>
        </div>
        <div class="input-row">
          <label>Utilities (monthly):</label>
          <input v-model.number="startup.utilities" type="number" step="50">
          <span class="unit">$/mo</span>
        </div>
      </div>

      <div class="section">
        <h3>Equipment Financing</h3>
        <div class="input-row">
          <label>Loan Amount:</label>
          <input v-model.number="startup.loanAmount" type="number" step="1000">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Interest Rate (APR):</label>
          <input v-model.number="startup.interestRate" type="number" step="0.1" min="0">
          <span class="unit">%</span>
        </div>
        <div class="input-row">
          <label>Loan Term:</label>
          <input v-model.number="startup.loanTermYears" type="number" step="1" min="1">
          <span class="unit">years</span>
        </div>
        <div class="input-row">
          <label>Start Date:</label>
          <input v-model="startup.loanStartDate" type="month">
        </div>
      </div>

      <div class="results">
        <h3>Loan Summary</h3>
        <div class="result-item">
          <span>Monthly Payment:</span>
          <strong>${{ monthlyPayment.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong>
        </div>
        <div class="result-item">
          <span>Total Interest:</span>
          <strong>${{ totalInterest.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong>
        </div>
        <div class="result-item total">
          <span>Total Payment:</span>
          <strong>${{ totalLoanPayment.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong>
        </div>
      </div>

      <div class="results" style="margin-top: 20px;">
        <h3>Startup Summary</h3>
        <div class="result-item">
          <span>Total Equipment:</span>
          <strong>${{ totalEquipment.toLocaleString() }}</strong>
        </div>
        <div class="result-item">
          <span>Monthly Overhead:</span>
          <strong>${{ monthlyOverhead.toLocaleString() }}</strong>
        </div>
        <div class="result-item">
          <span>Monthly Loan Payment:</span>
          <strong>${{ monthlyPayment.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong>
        </div>
        <div class="result-item total">
          <span>Total Monthly Costs:</span>
          <strong>${{ (monthlyOverhead + monthlyPayment).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong>
        </div>
      </div>

      <div class="amortization-section" v-if="showAmortization">
        <button @click="showAmortization = !showAmortization" class="toggle-btn">
          {{ showAmortization ? '▼' : '▶' }} Hide Amortization Schedule
        </button>
        <div class="amortization-table">
          <div class="table-header">
            <div>Payment #</div>
            <div>Date</div>
            <div>Principal</div>
            <div>Interest</div>
            <div>Balance</div>
          </div>
          <div v-for="payment in amortizationSchedule.slice(0, 12)" :key="payment.number" class="table-row">
            <div>{{ payment.number }}</div>
            <div>{{ payment.date }}</div>
            <div>${{ payment.principal.toFixed(2) }}</div>
            <div>${{ payment.interest.toFixed(2) }}</div>
            <div>${{ payment.balance.toFixed(2) }}</div>
          </div>
          <div v-if="amortizationSchedule.length > 12" class="table-row summary">
            <div colspan="5">... {{ amortizationSchedule.length - 12 }} more payments ...</div>
          </div>
        </div>
      </div>
      <button v-else @click="showAmortization = true" class="toggle-btn">
        ▶ Show Amortization Schedule ({{ amortizationSchedule.length }} payments)
      </button>
    </div>

    <!-- Tab 2: Instrument Costing -->
    <div v-if="activeTab === 'costing'" class="tab-content">
      <h2>🎸 Instrument Cost Calculator</h2>
      
      <div class="section">
        <h3>Materials</h3>
        <div class="input-row">
          <label>Wood (body, neck):</label>
          <input v-model.number="costing.wood" type="number" step="10">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Hardware (tuners, bridge, etc):</label>
          <input v-model.number="costing.hardware" type="number" step="10">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Electronics (pickups, pots):</label>
          <input v-model.number="costing.electronics" type="number" step="10">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Finishing (paint, lacquer):</label>
          <input v-model.number="costing.finishing" type="number" step="5">
          <span class="unit">$</span>
        </div>
      </div>

      <div class="section">
        <h3>Labor</h3>
        <div class="input-row">
          <label>Your Hourly Rate:</label>
          <input v-model.number="costing.hourlyRate" type="number" step="5">
          <span class="unit">$/hr</span>
        </div>
        <div class="input-row">
          <label>Build Hours:</label>
          <input v-model.number="costing.buildHours" type="number" step="1">
          <span class="unit">hrs</span>
        </div>
        <div class="input-row">
          <label>Finishing Hours:</label>
          <input v-model.number="costing.finishHours" type="number" step="1">
          <span class="unit">hrs</span>
        </div>
        <div class="input-row">
          <label>Setup Hours:</label>
          <input v-model.number="costing.setupHours" type="number" step="0.5">
          <span class="unit">hrs</span>
        </div>
      </div>

      <div class="results">
        <h3>Cost Breakdown</h3>
        <div class="result-item">
          <span>Total Materials:</span>
          <strong>${{ totalMaterials.toFixed(2) }}</strong>
        </div>
        <div class="result-item">
          <span>Total Labor ({{ totalHours }}hrs):</span>
          <strong>${{ totalLabor.toFixed(2) }}</strong>
        </div>
        <div class="result-item">
          <span>Overhead Allocation:</span>
          <strong>${{ overheadAllocation.toFixed(2) }}</strong>
        </div>
        <div class="result-item total">
          <span>Total Cost:</span>
          <strong>${{ totalCost.toFixed(2) }}</strong>
        </div>
        <div class="insight">
          💡 Add profit margin: 30% → ${{ (totalCost * 1.3).toFixed(2) }} | 50% → ${{ (totalCost * 1.5).toFixed(2) }}
        </div>
      </div>
    </div>

    <!-- Tab 3: Pricing Strategy -->
    <div v-if="activeTab === 'pricing'" class="tab-content">
      <h2>🏷️ Pricing Strategy</h2>
      
      <div class="section">
        <h3>Target Pricing</h3>
        <div class="input-row">
          <label>Build Cost:</label>
          <input v-model.number="pricing.buildCost" type="number" step="10">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Desired Margin (%):</label>
          <input v-model.number="pricing.margin" type="number" step="5" min="10" max="200">
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

    <!-- Tab 4: Cash Flow -->
    <div v-if="activeTab === 'cashflow'" class="tab-content">
      <h2>💰 Cash Flow Projection</h2>
      
      <div class="section">
        <h3>Monthly Projections</h3>
        <div class="input-row">
          <label>Instruments Sold/Month:</label>
          <input v-model.number="cashflow.unitsSold" type="number" step="1" min="0">
          <span class="unit">units</span>
        </div>
        <div class="input-row">
          <label>Average Sale Price:</label>
          <input v-model.number="cashflow.avgPrice" type="number" step="100">
          <span class="unit">$</span>
        </div>
        <div class="input-row">
          <label>Monthly Fixed Costs:</label>
          <input v-model.number="cashflow.fixedCosts" type="number" step="100">
          <span class="unit">$</span>
        </div>
      </div>

      <div class="results">
        <h3>Monthly Cash Flow</h3>
        <div class="result-item">
          <span>Revenue:</span>
          <strong>${{ monthlyRevenue.toLocaleString() }}</strong>
        </div>
        <div class="result-item">
          <span>Fixed Costs:</span>
          <strong>${{ cashflow.fixedCosts.toLocaleString() }}</strong>
        </div>
        <div class="result-item" :class="{ profit: netIncome > 0, loss: netIncome < 0 }">
          <span>Net Income:</span>
          <strong>${{ netIncome.toLocaleString() }}</strong>
        </div>
      </div>
    </div>

    <!-- Tab 5: Growth Planning -->
    <div v-if="activeTab === 'growth'" class="tab-content">
      <h2>📈 Growth Planning</h2>
      
      <div class="section">
        <h3>Scaling Scenarios</h3>
        <div class="input-row">
          <label>Current Monthly Output:</label>
          <input v-model.number="growth.currentOutput" type="number" step="1">
          <span class="unit">instruments</span>
        </div>
        <div class="input-row">
          <label>Target Monthly Output:</label>
          <input v-model.number="growth.targetOutput" type="number" step="1">
          <span class="unit">instruments</span>
        </div>
        <div class="input-row">
          <label>Hours per Instrument:</label>
          <input v-model.number="growth.hoursPerUnit" type="number" step="1">
          <span class="unit">hrs</span>
        </div>
      </div>

      <div class="results">
        <h3>Growth Analysis</h3>
        <div class="result-item">
          <span>Current Monthly Hours:</span>
          <strong>{{ currentMonthlyHours }} hrs</strong>
        </div>
        <div class="result-item">
          <span>Target Monthly Hours:</span>
          <strong>{{ targetMonthlyHours }} hrs</strong>
        </div>
        <div class="insight">
          {{ growthInsight }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const tabs = [
  { id: 'startup', label: '🚀 Startup' },
  { id: 'costing', label: '🎸 Costing' },
  { id: 'pricing', label: '🏷️ Pricing' },
  { id: 'cashflow', label: '💰 Cash Flow' },
  { id: 'growth', label: '📈 Growth' }
]

const activeTab = ref('startup')
const showAmortization = ref(false)

// Startup data
const startup = ref({
  cncCost: 15000,
  handTools: 2000,
  workbenches: 1500,
  rent: 800,
  utilities: 200,
  loanAmount: 15000,
  interestRate: 7.5,
  loanTermYears: 5,
  loanStartDate: new Date().toISOString().slice(0, 7) // YYYY-MM format
})

const totalEquipment = computed(() => 
  startup.value.cncCost + startup.value.handTools + startup.value.workbenches
)

const monthlyOverhead = computed(() => 
  startup.value.rent + startup.value.utilities
)

const firstYearCost = computed(() => 
  totalEquipment.value + (monthlyOverhead.value * 12)
)

// Loan amortization calculations
const monthlyPayment = computed(() => {
  const P = startup.value.loanAmount
  const r = startup.value.interestRate / 100 / 12 // Monthly interest rate
  const n = startup.value.loanTermYears * 12 // Total payments
  
  if (r === 0) return P / n // No interest case
  
  // Standard amortization formula: P * [r(1+r)^n] / [(1+r)^n - 1]
  const payment = P * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1)
  return payment
})

const totalLoanPayment = computed(() => 
  monthlyPayment.value * startup.value.loanTermYears * 12
)

const totalInterest = computed(() => 
  totalLoanPayment.value - startup.value.loanAmount
)

const amortizationSchedule = computed(() => {
  const schedule: { number: number; date: string; principal: number; interest: number; balance: number }[] = []
  let balance = startup.value.loanAmount
  const monthlyRate = startup.value.interestRate / 100 / 12
  const totalPayments = startup.value.loanTermYears * 12
  const payment = monthlyPayment.value
  
  // Parse start date
  const [year, month] = startup.value.loanStartDate.split('-').map(Number)
  let currentDate = new Date(year, month - 1, 1)
  
  for (let i = 1; i <= totalPayments; i++) {
    const interestPayment = balance * monthlyRate
    const principalPayment = payment - interestPayment
    balance -= principalPayment
    
    schedule.push({
      number: i,
      date: currentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'short' }),
      principal: principalPayment,
      interest: interestPayment,
      balance: Math.max(0, balance) // Prevent negative due to rounding
    })
    
    // Increment month
    currentDate.setMonth(currentDate.getMonth() + 1)
  }
  
  return schedule
})

// Costing data
const costing = ref({
  wood: 150,
  hardware: 120,
  electronics: 200,
  finishing: 75,
  hourlyRate: 50,
  buildHours: 40,
  finishHours: 20,
  setupHours: 3
})

const totalMaterials = computed(() => 
  costing.value.wood + costing.value.hardware + costing.value.electronics + costing.value.finishing
)

const totalHours = computed(() => 
  costing.value.buildHours + costing.value.finishHours + costing.value.setupHours
)

const totalLabor = computed(() => 
  totalHours.value * costing.value.hourlyRate
)

const overheadAllocation = computed(() => 
  monthlyOverhead.value / 4 // Assuming 4 instruments per month
)

const totalCost = computed(() => 
  totalMaterials.value + totalLabor.value + overheadAllocation.value
)

// Pricing data
const pricing = ref({
  buildCost: 3500,
  margin: 50
})

const sellingPrice = computed(() => 
  pricing.value.buildCost * (1 + pricing.value.margin / 100)
)

const profit = computed(() => 
  sellingPrice.value - pricing.value.buildCost
)

const breakEvenUnits = computed(() => 
  Math.ceil(firstYearCost.value / profit.value)
)

// Cash flow data
const cashflow = ref({
  unitsSold: 4,
  avgPrice: 5000,
  fixedCosts: 1200
})

const monthlyRevenue = computed(() => 
  cashflow.value.unitsSold * cashflow.value.avgPrice
)

const netIncome = computed(() => 
  monthlyRevenue.value - cashflow.value.fixedCosts
)

// Growth data
const growth = ref({
  currentOutput: 4,
  targetOutput: 8,
  hoursPerUnit: 60
})

const currentMonthlyHours = computed(() => 
  growth.value.currentOutput * growth.value.hoursPerUnit
)

const targetMonthlyHours = computed(() => 
  growth.value.targetOutput * growth.value.hoursPerUnit
)

const growthInsight = computed(() => {
  const workableHours = 160 // 40 hrs/week
  if (targetMonthlyHours.value <= workableHours) {
    return `✅ Achievable solo (${targetMonthlyHours.value}hrs < ${workableHours}hrs/month)`
  } else {
    const additionalPeople = Math.ceil((targetMonthlyHours.value - workableHours) / workableHours)
    return `⚠️ Need to hire ${additionalPeople} person(s) or reduce hours per unit`
  }
})
</script>

<style scoped>
.business-calculator {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  font-family: system-ui, -apple-system, sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  color: #1a73e8;
  margin-bottom: 8px;
}

.header p {
  color: #666;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid #e0e0e0;
  overflow-x: auto;
}

.tabs button {
  padding: 12px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
}

.tabs button:hover {
  color: #1a73e8;
}

.tabs button.active {
  color: #1a73e8;
  border-bottom-color: #1a73e8;
}

.tab-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.tab-content h2 {
  color: #333;
  margin-bottom: 24px;
}

.section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.section h3 {
  color: #555;
  margin-bottom: 16px;
  font-size: 16px;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.input-row label {
  flex: 1;
  color: #333;
  font-size: 14px;
}

.input-row input {
  width: 120px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.input-row .unit {
  color: #666;
  font-size: 13px;
  min-width: 40px;
}

.results {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
  border-radius: 8px;
}

.results h3 {
  margin-bottom: 16px;
  font-size: 18px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255,255,255,0.2);
}

.result-item:last-child {
  border-bottom: none;
}

.result-item.total {
  font-size: 18px;
  padding-top: 16px;
  margin-top: 8px;
  border-top: 2px solid rgba(255,255,255,0.4);
}

.result-item.profit strong {
  color: #4caf50;
}

.result-item.loss strong {
  color: #f44336;
}

.insight {
  margin-top: 16px;
  padding: 12px;
  background: rgba(255,255,255,0.2);
  border-radius: 4px;
  font-size: 14px;
}

.toggle-btn {
  width: 100%;
  padding: 12px;
  margin-top: 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #5568d3;
}

.amortization-section {
  margin-top: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  color: #333;
}

.amortization-table {
  margin-top: 16px;
  overflow-x: auto;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 80px 100px 120px 120px 120px;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #e0e0e0;
  font-size: 14px;
}

.table-header {
  font-weight: 600;
  background: #f5f5f5;
  border-radius: 4px;
}

.table-row:hover {
  background: #f9f9f9;
}

.table-row.summary {
  font-style: italic;
  color: #666;
  text-align: center;
  grid-template-columns: 1fr;
}

@media (max-width: 768px) {
  .tabs {
    overflow-x: auto;
  }
  
  .input-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .input-row input {
    width: 100%;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 60px 80px 100px 100px 100px;
    gap: 8px;
    font-size: 12px;
  }
}
</style>
