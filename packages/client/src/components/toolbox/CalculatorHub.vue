<template>
  <div class="calculator-hub">
    <div class="hub-header">
      <h2>🧮 Calculator Hub</h2>
      <p>All lutherie calculators in one place - from structural analysis to business planning</p>
    </div>

    <!-- Calculator Selection Grid -->
    <div v-if="!activeCalculator" class="calculator-grid">
      <!-- Math & Precision Calculators -->
      <div class="calc-category">
        <h3>📐 Math & Precision</h3>
        <div class="calc-cards">
          <div class="calc-card placeholder" @click="selectCalculator('fractions')">
            <div class="calc-icon">🔢</div>
            <h4>Fraction Calculator</h4>
            <p>Decimal↔fraction for woodworking precision</p>
            <span class="status-badge">Coming Soon</span>
          </div>
          <div class="calc-card active" @click="selectCalculator('scientific')">
            <div class="calc-icon">🧮</div>
            <h4>Scientific Calculator</h4>
            <p>Trig, logarithms, and lutherie math</p>
            <span class="status-badge ready">✓ Ready</span>
          </div>
        </div>
      </div>

      <!-- Business Calculators -->
      <div class="calc-category">
        <h3>💼 Business & ROI</h3>
        <div class="calc-cards">
          <div class="calc-card placeholder" @click="selectCalculator('cnc-roi')">
            <div class="calc-icon">💰</div>
            <h4>CNC ROI Calculator</h4>
            <p>Financial analysis for CNC investment</p>
            <span class="status-badge">Coming Soon</span>
          </div>
          <div class="calc-card active" @click="selectCalculator('business-calc')">
            <div class="calc-icon">💼</div>
            <h4>Business Calculator</h4>
            <p>Costing, pricing, cash flow projections</p>
            <span class="status-badge ready">✓ Ready</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Calculator Display -->
    <div v-else class="active-calculator">
      <div class="calc-toolbar">
        <button @click="activeCalculator = null" class="back-btn">
          ← Back to Calculator Hub
        </button>
        <h3>{{ getCalculatorTitle(activeCalculator) }}</h3>
      </div>

      <FractionCalculator v-if="activeCalculator === 'fractions'" />
      <ScientificCalculator v-if="activeCalculator === 'scientific'" />
      <CNCROICalculator v-if="activeCalculator === 'cnc-roi'" />
      <BusinessCalculator v-if="activeCalculator === 'business-calc'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FractionCalculator from './FractionCalculator.vue'
import ScientificCalculator from './ScientificCalculator.vue'
import CNCROICalculator from './CNCROICalculator.vue'
import BusinessCalculator from './BusinessCalculator.vue'

const activeCalculator = ref<string | null>(null)

function selectCalculator(calcId: string) {
  activeCalculator.value = calcId
}

function getCalculatorTitle(calcId: string): string {
  const titles: Record<string, string> = {
    'fractions': '🔢 Fraction Calculator',
    'scientific': '🧮 Scientific Calculator',
    'cnc-roi': '💰 CNC ROI Calculator',
    'business-calc': '💼 Business Calculator'
  }
  return titles[calcId] || calcId
}
</script>

<style scoped>
.calculator-hub {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.hub-header {
  text-align: center;
  margin-bottom: 3rem;
}

.hub-header h2 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.hub-header p {
  font-size: 1.1rem;
  color: #666;
}

.calculator-grid {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.calc-category {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.calc-category h3 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  color: #2c3e50;
  border-bottom: 2px solid #3b82f6;
  padding-bottom: 0.5rem;
}

.calc-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.calc-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  position: relative;
}

.calc-card.placeholder {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  opacity: 0.7;
}

.calc-card.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.calc-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}

.calc-card.placeholder:hover {
  transform: translateY(-2px);
}

.status-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0,0,0,0.3);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.ready {
  background: rgba(255,255,255,0.3);
}

.calc-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  text-align: center;
}

.calc-card h4 {
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.calc-card p {
  font-size: 0.95rem;
  opacity: 0.9;
  text-align: center;
  line-height: 1.5;
}

.active-calculator {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.calc-toolbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-btn {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: rgba(255,255,255,0.3);
}

.calc-toolbar h3 {
  margin: 0;
  font-size: 1.5rem;
}

@media (max-width: 768px) {
  .calculator-hub {
    padding: 1rem;
  }

  .calc-cards {
    grid-template-columns: 1fr;
  }

  .hub-header h2 {
    font-size: 2rem;
  }
}
</style>
