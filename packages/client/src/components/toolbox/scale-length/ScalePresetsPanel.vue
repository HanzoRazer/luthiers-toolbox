<script setup lang="ts">
/**
 * ScalePresetsPanel - Scale length presets and physics education
 * Extracted from ScaleLengthDesigner.vue
 */

const emit = defineEmits<{
  'selectScale': [scaleType: string]
}>()
</script>

<template>
  <div class="scale-presets-panel">
    <div class="section-header">
      <h2>Standard Scale Lengths</h2>
      <p>Click a card to explore how scale length affects string tension and tone</p>
    </div>

    <div class="scale-grid">
      <div class="scale-card" @click="emit('selectScale', 'fender')">
        <div class="scale-name">Fender Scale</div>
        <div class="scale-value">25.5" (648mm)</div>
        <div class="scale-info">
          <div class="scale-trait">• Bright, snappy tone</div>
          <div class="scale-trait">• Higher string tension</div>
          <div class="scale-trait">• Strat, Tele, Jazzmaster</div>
        </div>
      </div>

      <div class="scale-card" @click="emit('selectScale', 'gibson')">
        <div class="scale-name">Gibson Scale</div>
        <div class="scale-value">24.75" (629mm)</div>
        <div class="scale-info">
          <div class="scale-trait">• Warm, fat tone</div>
          <div class="scale-trait">• Easier bending</div>
          <div class="scale-trait">• Les Paul, SG, 335</div>
        </div>
      </div>

      <div class="scale-card" @click="emit('selectScale', 'prs')">
        <div class="scale-name">PRS Scale</div>
        <div class="scale-value">25.0" (635mm)</div>
        <div class="scale-info">
          <div class="scale-trait">• Balanced compromise</div>
          <div class="scale-trait">• Medium tension</div>
          <div class="scale-trait">• PRS core models</div>
        </div>
      </div>

      <div class="scale-card" @click="emit('selectScale', 'short')">
        <div class="scale-name">Short Scale</div>
        <div class="scale-value">24.0" (610mm)</div>
        <div class="scale-info">
          <div class="scale-trait">• Easy playability</div>
          <div class="scale-trait">• Lower tension</div>
          <div class="scale-trait">• Mustang, Jaguar</div>
        </div>
      </div>

      <div class="scale-card" @click="emit('selectScale', 'baritone')">
        <div class="scale-name">Baritone Scale</div>
        <div class="scale-value">27.0" (686mm)</div>
        <div class="scale-info">
          <div class="scale-trait">• Extended low range</div>
          <div class="scale-trait">• Tight low strings</div>
          <div class="scale-trait">• Drop A, B tuning</div>
        </div>
      </div>

      <div class="scale-card" @click="emit('selectScale', 'multiscale')">
        <div class="scale-name">Multi-Scale (Fanned)</div>
        <div class="scale-value">25.5" - 27.0"</div>
        <div class="scale-info">
          <div class="scale-trait">• Ergonomic fanned frets</div>
          <div class="scale-trait">• Optimized per string</div>
          <div class="scale-trait">• Modern innovation</div>
        </div>
      </div>
    </div>

    <!-- Why Scale Length Matters -->
    <div class="education-section">
      <div class="edu-title">Why Scale Length Matters for Innovation</div>

      <div class="edu-card">
        <h3>The Physics: Mersenne's Law</h3>
        <p>String tension is determined by a precise mathematical relationship:</p>
        <div class="formula-box">
          <div class="formula">T = (μ × (2 × L × f)²) ÷ 4</div>
          <div class="formula-legend">
            <div><strong>T</strong> = Tension (lbs)</div>
            <div><strong>μ</strong> = Linear mass density (lb/in)</div>
            <div><strong>L</strong> = Scale length (in)</div>
            <div><strong>f</strong> = Frequency (Hz)</div>
          </div>
        </div>
        <p class="edu-note">
          <strong>Key insight:</strong> Tension increases with the <em>square</em> of scale length.
          Every 0.75" longer scale = ~6% more tension!
        </p>
      </div>

      <div class="edu-card">
        <h3>Real-World Examples</h3>
        <div class="example-grid">
          <div class="example-item">
            <div class="example-scale">Gibson 24.75"</div>
            <div class="example-tension">14.2 lbs</div>
            <div class="example-note">High E string (.010")</div>
          </div>
          <div class="example-item">
            <div class="example-scale">PRS 25.0"</div>
            <div class="example-tension">14.5 lbs</div>
            <div class="example-note">+2.1% tension</div>
          </div>
          <div class="example-item">
            <div class="example-scale">Fender 25.5"</div>
            <div class="example-tension">15.1 lbs</div>
            <div class="example-note">+6.3% tension</div>
          </div>
        </div>
        <p class="edu-note">
          That 0.75" difference between Gibson and Fender creates noticeable feel and tone differences!
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

.scale-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.scale-card {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.scale-card:hover {
  border-color: #8ab4f8;
  background: #35363a;
}

.scale-name {
  font-size: 18px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 8px;
}

.scale-value {
  font-size: 28px;
  font-weight: bold;
  color: #e8eaed;
  margin-bottom: 16px;
}

.scale-info {
  font-size: 13px;
  color: #9aa0a6;
}

.scale-trait {
  margin-bottom: 4px;
}

.education-section {
  margin-top: 32px;
}

.edu-title {
  font-size: 20px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 24px;
}

.edu-card {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.edu-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 12px;
}

.edu-card p {
  font-size: 14px;
  line-height: 1.6;
  color: #bdc1c6;
  margin-bottom: 16px;
}

.formula-box {
  background: #1e1e1e;
  padding: 20px;
  border-radius: 8px;
  margin: 16px 0;
}

.formula {
  font-family: 'Courier New', monospace;
  font-size: 18px;
  color: #8ab4f8;
  margin-bottom: 16px;
  text-align: center;
}

.formula-legend {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  font-size: 13px;
  color: #9aa0a6;
}

.edu-note {
  background: rgba(138, 180, 248, 0.1);
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #8ab4f8;
  margin-top: 16px;
}

.example-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 16px 0;
}

.example-item {
  background: #1e1e1e;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.example-scale {
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 8px;
}

.example-tension {
  font-size: 24px;
  font-weight: bold;
  color: #e8eaed;
  margin-bottom: 4px;
}

.example-note {
  font-size: 12px;
  color: #9aa0a6;
}
</style>
