<template>
  <div class="tab-content">
    <div class="section-header">
      <h2>Standard Scale Lengths</h2>
      <p>Click a card to explore how scale length affects string tension and tone</p>
    </div>

    <div class="scale-grid">
      <div
        v-for="preset in presets"
        :key="preset.id"
        class="scale-card"
        @click="$emit('select', preset.id)"
      >
        <div class="scale-name">{{ preset.name }}</div>
        <div class="scale-value">{{ preset.value }}</div>
        <div class="scale-info">
          <div v-for="trait in preset.traits" :key="trait" class="scale-trait">
            • {{ trait }}
          </div>
        </div>
      </div>
    </div>

    <!-- Why Scale Length Matters -->
    <div class="education-section">
      <div class="edu-title">
        💡 Why Scale Length Matters for Innovation
      </div>

      <div class="edu-card">
        <h3>The Physics: Mersenne's Law</h3>
        <p>String tension is determined by a precise mathematical relationship:</p>
        <div class="formula-box">
          <div class="formula">
            T = (μ × (2 × L × f)²) ÷ 4
          </div>
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

<script setup lang="ts">
defineEmits<{
  select: [scaleType: string]
}>()

const presets = [
  {
    id: 'fender',
    name: 'Fender Scale',
    value: '25.5" (648mm)',
    traits: ['Bright, snappy tone', 'Higher string tension', 'Strat, Tele, Jazzmaster']
  },
  {
    id: 'gibson',
    name: 'Gibson Scale',
    value: '24.75" (629mm)',
    traits: ['Warm, fat tone', 'Easier bending', 'Les Paul, SG, 335']
  },
  {
    id: 'prs',
    name: 'PRS Scale',
    value: '25.0" (635mm)',
    traits: ['Balanced compromise', 'Medium tension', 'PRS core models']
  },
  {
    id: 'short',
    name: 'Short Scale',
    value: '24.0" (610mm)',
    traits: ['Easy playability', 'Lower tension', 'Mustang, Jaguar']
  },
  {
    id: 'baritone',
    name: 'Baritone Scale',
    value: '27.0" (686mm)',
    traits: ['Extended low range', 'Tight low strings', 'Drop A, B tuning']
  },
  {
    id: 'multiscale',
    name: 'Multi-Scale (Fanned)',
    value: '25.5" - 27.0"',
    traits: ['Ergonomic fanned frets', 'Optimized per string', 'Modern innovation']
  }
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

.scale-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.scale-card {
  background: #292a2d;
  padding: 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.scale-card:hover {
  border-color: #8ab4f8;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(138, 180, 248, 0.3);
}

.scale-name {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 6px;
}

.scale-value {
  font-size: 16px;
  color: #8ab4f8;
  margin-bottom: 12px;
  font-weight: 500;
}

.scale-info {
  font-size: 13px;
  color: #9aa0a6;
  line-height: 1.6;
}

.scale-trait {
  margin-bottom: 4px;
}

.education-section {
  margin-top: 32px;
}

.edu-title {
  font-size: 22px;
  font-weight: 600;
  color: #ffd700;
  margin-bottom: 20px;
}

.edu-card {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  border-left: 4px solid #8ab4f8;
}

.edu-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 16px;
}

.edu-card p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.formula-box {
  background: rgba(0, 0, 0, 0.4);
  padding: 20px;
  border-radius: 8px;
  margin: 16px 0;
}

.formula {
  font-family: 'Courier New', monospace;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 16px;
  color: #ffd700;
}

.formula-legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.formula-legend strong {
  color: #8ab4f8;
}

.edu-note {
  background: rgba(138, 180, 248, 0.1);
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  border-left: 3px solid #8ab4f8;
}

.edu-note strong {
  color: #8ab4f8;
}

.example-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin: 16px 0;
}

.example-item {
  background: rgba(0, 0, 0, 0.3);
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.example-scale {
  font-size: 14px;
  font-weight: 500;
  color: #ffd700;
  margin-bottom: 8px;
}

.example-tension {
  font-size: 22px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 4px;
}

.example-note {
  font-size: 12px;
  color: #9aa0a6;
}

@media (max-width: 768px) {
  .scale-grid {
    grid-template-columns: 1fr;
  }
  .example-grid {
    grid-template-columns: 1fr;
  }
}
</style>
