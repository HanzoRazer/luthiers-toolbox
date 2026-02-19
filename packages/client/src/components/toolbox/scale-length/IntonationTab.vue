<template>
  <div class="tab-content">
    <div class="section-header">
      <h2>Intonation Compensation</h2>
      <p>Understanding the "dead zone" and why bridges aren't placed at the exact scale length</p>
    </div>

    <div class="intonation-education">
      <div class="critical-concept">
        <h3>🔴 The Dead Zone Problem</h3>
        <p>
          String stiffness creates a non-vibrating "dead zone" near the saddle. This zone doesn't
          contribute to pitch but adds effective length to the string, making it sharper than expected.
        </p>
        <p>
          <strong>The B string intonates closest to the design scale length</strong> because its
          diameter and composition create the smallest dead zone. This is why the B string saddle
          is used as the reference point for all other strings.
        </p>
      </div>

      <div class="compensation-table">
        <div class="comp-header">
          <div class="comp-title">Intonation Compensation Chart</div>
          <div class="comp-subtitle">For 25.5" scale (Fender) with standard .010-.046 gauges</div>
        </div>

        <div class="comp-grid">
          <div class="comp-row comp-header-row">
            <div>String</div>
            <div>Gauge</div>
            <div>Design Length</div>
            <div>Actual Length</div>
            <div>Compensation</div>
          </div>
          <div
            v-for="row in compensationData"
            :key="row.string"
            class="comp-row"
            :class="row.highlight"
          >
            <div>{{ row.string }}</div>
            <div>{{ row.gauge }}</div>
            <div>{{ row.design }}</div>
            <div>{{ row.actual }}</div>
            <div>{{ row.compensation }}</div>
          </div>
        </div>
      </div>

      <div class="bridge-placement">
        <h3>Bridge Placement Formula</h3>
        <div class="placement-box">
          <div class="formula">
            Bridge Center = Scale Length + (Low E Compensation ÷ 2)
          </div>
          <div class="formula-example">
            Example: 25.5" + (0.25" ÷ 2) = <strong>25.625"</strong> from nut to bridge center
          </div>
        </div>
        <div class="placement-note warning">
          <strong>Common Mistake:</strong> Placing the bridge at exactly 25.5" from the nut.
          This forces all saddles backward, limiting adjustment range and causing intonation issues.
        </div>
        <div class="placement-note success">
          <strong>Correct Approach:</strong> Place bridge center at scale + (max_comp ÷ 2), allowing
          saddles to move both forward (high E, B) and backward (low E) for perfect intonation.
        </div>
      </div>

      <div class="compensation-factors">
        <h3>5 Physical Factors Affecting Compensation</h3>
        <div class="factor-list">
          <div v-for="factor in factors" :key="factor.title" class="factor-item">
            <strong>{{ factor.title }}</strong>
            <div>{{ factor.description }}</div>
          </div>
        </div>
      </div>

      <div class="innovation-connection">
        <h3>🚀 Why Multi-Scale Guitars Excel at Intonation</h3>
        <p>
          Multi-scale (fanned fret) guitars optimize scale length independently for each string.
          Treble strings get shorter scales (less tension, easier bending) while bass strings get
          longer scales (more tension, better definition).
        </p>
        <p>
          <strong>Bonus:</strong> Longer bass scales reduce the percentage difference in compensation.
          A 27" Low E needs +0.25" compensation (0.9% of scale) vs 25.5" needing +0.25" (1.0% of scale).
          Tighter tolerances, better intonation!
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const compensationData = [
  { string: 'High E', gauge: '.010"', design: '25.500"', actual: '25.500"', compensation: '0.000" (none)', highlight: '' },
  { string: 'B', gauge: '.013"', design: '25.500"', actual: '25.500"', compensation: '0.000" (reference)', highlight: 'highlight-reference' },
  { string: 'G', gauge: '.017"', design: '25.500"', actual: '25.562"', compensation: '+0.062" (~1/16")', highlight: '' },
  { string: 'D', gauge: '.026"', design: '25.500"', actual: '25.625"', compensation: '+0.125" (1/8")', highlight: '' },
  { string: 'A', gauge: '.036"', design: '25.500"', actual: '25.687"', compensation: '+0.187" (3/16")', highlight: '' },
  { string: 'Low E', gauge: '.046"', design: '25.500"', actual: '25.750"', compensation: '+0.250" (1/4")', highlight: 'highlight-max' }
]

const factors = [
  { title: '1. String Diameter', description: 'Thicker strings have more stiffness, creating larger dead zones. Low E (.046") needs ~4× more compensation than High E (.010").' },
  { title: '2. String Structure', description: 'Wound strings (G, D, A, Low E) have higher stiffness than plain strings (High E, B) due to the wrap wire adding rigidity.' },
  { title: '3. Core Wire Composition', description: 'Stainless steel cores are stiffer than nickel or phosphor bronze, requiring more compensation. Material matters!' },
  { title: '4. String Action Height', description: 'Higher action means more stretch when fretting, pulling the string sharper. Compensate by moving saddles back further.' },
  { title: '5. Fret Height', description: 'Tall frets (like jumbos) require more stretch to fret cleanly, increasing effective length. Lower frets need less compensation.' }
]
</script>

<style scoped>
.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 8px;
}

.section-header p {
  font-size: 14px;
  color: #9aa0a6;
}

.intonation-education {
  max-width: 1000px;
}

.critical-concept {
  background: linear-gradient(135deg, rgba(234, 67, 53, 0.2) 0%, rgba(234, 67, 53, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #ea4335;
  margin-bottom: 24px;
}

.critical-concept h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ff6b6b;
  margin-bottom: 12px;
}

.critical-concept p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.critical-concept strong {
  color: #8ab4f8;
}

.compensation-table {
  background: #292a2d;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.comp-header {
  margin-bottom: 16px;
}

.comp-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffd700;
  margin-bottom: 6px;
}

.comp-subtitle {
  font-size: 13px;
  color: #9aa0a6;
  font-style: italic;
}

.comp-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.comp-row {
  display: grid;
  grid-template-columns: 100px 80px 120px 120px 1fr;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 13px;
  align-items: center;
}

.comp-header-row {
  background: rgba(0, 0, 0, 0.3);
  font-weight: 600;
  color: #ffd700;
  font-size: 12px;
}

.highlight-reference {
  background: rgba(138, 180, 248, 0.2);
  border: 2px solid #8ab4f8;
  font-weight: 500;
}

.highlight-max {
  background: rgba(234, 67, 53, 0.2);
  border: 2px solid #ea4335;
  font-weight: 600;
}

.bridge-placement {
  background: linear-gradient(135deg, rgba(52, 168, 83, 0.2) 0%, rgba(52, 168, 83, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #34a853;
  margin-bottom: 24px;
}

.bridge-placement h3 {
  font-size: 18px;
  font-weight: 600;
  color: #51cf66;
  margin-bottom: 16px;
}

.placement-box {
  background: rgba(0, 0, 0, 0.4);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.formula {
  font-family: 'Courier New', monospace;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  color: #ffd700;
}

.formula-example {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #51cf66;
  text-align: center;
  margin-top: 12px;
}

.formula-example strong {
  font-size: 18px;
}

.placement-note {
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.placement-note:last-child {
  margin-bottom: 0;
}

.placement-note.warning {
  background: rgba(234, 67, 53, 0.2);
  border-left: 4px solid #ea4335;
}

.placement-note.warning strong {
  color: #ff6b6b;
}

.placement-note.success {
  background: rgba(52, 168, 83, 0.2);
  border-left: 4px solid #34a853;
}

.placement-note.success strong {
  color: #51cf66;
}

.compensation-factors {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.compensation-factors h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffd700;
  margin-bottom: 16px;
}

.factor-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.factor-item {
  font-size: 13px;
  line-height: 1.6;
  padding-left: 16px;
  border-left: 3px solid rgba(138, 180, 248, 0.5);
}

.factor-item strong {
  color: #8ab4f8;
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
}

.innovation-connection {
  background: linear-gradient(135deg, rgba(138, 180, 248, 0.2) 0%, rgba(138, 180, 248, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #8ab4f8;
}

.innovation-connection h3 {
  font-size: 18px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 12px;
}

.innovation-connection p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.innovation-connection p:last-child {
  margin-bottom: 0;
}

.innovation-connection strong {
  color: #8ab4f8;
}

@media (max-width: 768px) {
  .comp-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
  .comp-row > div {
    padding: 4px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  .comp-row > div:last-child {
    border-bottom: none;
  }
}
</style>
