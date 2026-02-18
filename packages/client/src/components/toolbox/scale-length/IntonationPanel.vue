<script setup lang="ts">
/**
 * IntonationPanel - Intonation compensation education
 * Extracted from ScaleLengthDesigner.vue
 */
</script>

<template>
  <div class="intonation-panel">
    <div class="section-header">
      <h2>Intonation Compensation</h2>
      <p>Understanding the "dead zone" and why bridges aren't placed at the exact scale length</p>
    </div>

    <div class="intonation-education">
      <div class="critical-concept">
        <h3>The Dead Zone Problem</h3>
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

          <div class="comp-row">
            <div>High E</div>
            <div>.010"</div>
            <div>25.500"</div>
            <div>25.500"</div>
            <div>0.000" (none)</div>
          </div>

          <div class="comp-row highlight-reference">
            <div>B</div>
            <div>.013"</div>
            <div>25.500"</div>
            <div>25.500"</div>
            <div>0.000" (reference)</div>
          </div>

          <div class="comp-row">
            <div>G</div>
            <div>.017"</div>
            <div>25.500"</div>
            <div>25.562"</div>
            <div>+0.062" (~1/16")</div>
          </div>

          <div class="comp-row">
            <div>D</div>
            <div>.026"</div>
            <div>25.500"</div>
            <div>25.625"</div>
            <div>+0.125" (1/8")</div>
          </div>

          <div class="comp-row">
            <div>A</div>
            <div>.036"</div>
            <div>25.500"</div>
            <div>25.687"</div>
            <div>+0.187" (3/16")</div>
          </div>

          <div class="comp-row highlight-max">
            <div>Low E</div>
            <div>.046"</div>
            <div>25.500"</div>
            <div>25.750"</div>
            <div>+0.250" (1/4")</div>
          </div>
        </div>
      </div>

      <div class="bridge-placement">
        <h3>Bridge Placement Formula</h3>
        <div class="placement-box">
          <div class="formula">Bridge Center = Scale Length + (Low E Compensation ÷ 2)</div>
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
          <div class="factor-item">
            <strong>1. String Diameter</strong>
            <div>
              Thicker strings have more stiffness, creating larger dead zones. Low E (.046") needs
              ~4× more compensation than High E (.010").
            </div>
          </div>
          <div class="factor-item">
            <strong>2. String Structure</strong>
            <div>
              Wound strings (G, D, A, Low E) have higher stiffness than plain strings (High E, B)
              due to the wrap wire adding rigidity.
            </div>
          </div>
          <div class="factor-item">
            <strong>3. Core Wire Composition</strong>
            <div>
              Stainless steel cores are stiffer than nickel or phosphor bronze, requiring more
              compensation. Material matters!
            </div>
          </div>
          <div class="factor-item">
            <strong>4. String Action Height</strong>
            <div>
              Higher action means more stretch when fretting, pulling the string sharper. Compensate
              by moving saddles back further.
            </div>
          </div>
          <div class="factor-item">
            <strong>5. Fret Height</strong>
            <div>
              Tall frets (like jumbos) require more stretch to fret cleanly, increasing effective
              length. Lower frets need less compensation.
            </div>
          </div>
        </div>
      </div>

      <div class="innovation-connection">
        <h3>Why Multi-Scale Guitars Excel at Intonation</h3>
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

<style scoped>
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

.critical-concept {
  background: linear-gradient(135deg, rgba(234, 67, 53, 0.2), rgba(234, 67, 53, 0.1));
  padding: 24px;
  border-radius: 12px;
  border-left: 4px solid #ea4335;
  margin-bottom: 24px;
}

.critical-concept h3 {
  color: #ff6b6b;
  margin-bottom: 12px;
}

.critical-concept p {
  line-height: 1.6;
  color: #bdc1c6;
  margin-bottom: 12px;
}

.compensation-table {
  background: #292a2d;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
}

.comp-header {
  padding: 20px;
  background: #35363a;
}

.comp-title {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 4px;
}

.comp-subtitle {
  font-size: 13px;
  color: #9aa0a6;
}

.comp-grid {
  padding: 0 20px 20px;
}

.comp-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1.5fr 1.5fr 1.5fr;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #3c4043;
  font-size: 14px;
  color: #bdc1c6;
}

.comp-row:last-child {
  border-bottom: none;
}

.comp-header-row {
  font-weight: 600;
  color: #8ab4f8;
}

.highlight-reference {
  background: rgba(52, 168, 83, 0.15);
  margin: 0 -20px;
  padding: 12px 20px;
  color: #51cf66;
}

.highlight-max {
  background: rgba(251, 188, 5, 0.15);
  margin: 0 -20px;
  padding: 12px 20px;
  color: #ffc107;
}

.bridge-placement {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.bridge-placement h3 {
  color: #e8eaed;
  margin-bottom: 16px;
}

.placement-box {
  background: #1e1e1e;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.formula {
  font-family: 'Courier New', monospace;
  font-size: 16px;
  color: #8ab4f8;
  margin-bottom: 12px;
}

.formula-example {
  font-size: 14px;
  color: #9aa0a6;
}

.placement-note {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.placement-note.warning {
  background: rgba(251, 188, 5, 0.1);
  border-left: 3px solid #ffc107;
  color: #ffc107;
}

.placement-note.success {
  background: rgba(52, 168, 83, 0.1);
  border-left: 3px solid #51cf66;
  color: #51cf66;
}

.compensation-factors {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.compensation-factors h3 {
  color: #e8eaed;
  margin-bottom: 20px;
}

.factor-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.factor-item {
  padding: 16px;
  background: #1e1e1e;
  border-radius: 8px;
}

.factor-item strong {
  display: block;
  color: #8ab4f8;
  margin-bottom: 8px;
}

.factor-item div {
  font-size: 14px;
  line-height: 1.5;
  color: #9aa0a6;
}

.innovation-connection {
  background: linear-gradient(135deg, rgba(138, 180, 248, 0.2), rgba(138, 180, 248, 0.1));
  padding: 24px;
  border-radius: 12px;
  border-left: 4px solid #8ab4f8;
}

.innovation-connection h3 {
  color: #8ab4f8;
  margin-bottom: 12px;
}

.innovation-connection p {
  font-size: 14px;
  line-height: 1.6;
  color: #bdc1c6;
  margin-bottom: 12px;
}
</style>
