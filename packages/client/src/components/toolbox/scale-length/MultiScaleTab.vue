<template>
  <div class="tab-content">
    <div class="section-header">
      <h2>Multi-Scale (Fanned Fret) Innovation</h2>
      <p>Why modern guitars are moving beyond single scale lengths</p>
    </div>

    <div class="multiscale-education">
      <div class="problem-solution">
        <div class="problem-card">
          <h3>🔴 The Single-Scale Compromise</h3>
          <p>Traditional guitars force all strings to use the same scale length:</p>
          <ul>
            <li><strong>Treble strings:</strong> Higher tension than ideal (harder to bend)</li>
            <li><strong>Bass strings:</strong> Lower tension than ideal (less definition)</li>
            <li><strong>Result:</strong> Every string is a compromise</li>
          </ul>
          <div class="example">
            <strong>Example: Baritone at 25.5" scale</strong>
            <div class="calc-result problem">Low B string: 12.8 lbs (too floppy!)</div>
          </div>
        </div>

        <div class="solution-card">
          <h3>✅ The Multi-Scale Solution</h3>
          <p>Different scale length for each string, optimized independently:</p>
          <ul>
            <li><strong>Treble E:</strong> 25.5" (comfortable tension, easy bending)</li>
            <li><strong>Bass E:</strong> 27.0" (tight, defined, no flop)</li>
            <li><strong>Middle strings:</strong> Smoothly interpolated</li>
          </ul>
          <div class="example">
            <strong>Same baritone with multi-scale:</strong>
            <div class="calc-result solution">Low B string: 14.3 lbs (perfect!)</div>
          </div>
        </div>
      </div>

      <div class="multiscale-diagram">
        <h3>Visual: How Fanned Frets Work</h3>
        <div class="fret-visualization">
          <div class="fret-line treble">
            <div class="fret-label">Treble Side (High E)</div>
            <div class="fret-visual">|———————————————————| 25.5" scale</div>
            <div class="fret-tension">15.1 lbs tension</div>
          </div>
          <div class="fret-line bass">
            <div class="fret-label">Bass Side (Low E)</div>
            <div class="fret-visual">|—————————————————————————| 27.0" scale</div>
            <div class="fret-tension">14.8 lbs tension (with .046" gauge)</div>
          </div>
        </div>
        <p class="diagram-note">
          Notice how the bass side is longer. Frets are angled (fanned) to accommodate different
          scale lengths. The 12th fret is typically placed at the ergonomic "neutral" position.
        </p>
      </div>

      <div class="tension-comparison">
        <h3>Tension Comparison: Single vs Multi-Scale</h3>
        <div class="comparison-table">
          <div class="comparison-header">
            <div>String</div>
            <div>Single 25.5"</div>
            <div>Multi (25.5"-27")</div>
            <div>Improvement</div>
          </div>
          <div
            v-for="row in comparisonData"
            :key="row.string"
            class="comparison-row"
          >
            <div>{{ row.string }}</div>
            <div>{{ row.single }}</div>
            <div>{{ row.multi }}</div>
            <div :class="row.level">{{ row.improvement }}</div>
          </div>
        </div>
        <p class="comparison-note">
          Multi-scale dramatically improves bass string tension while keeping treble strings comfortable.
          This is why extended-range guitars (7, 8, 9 strings) almost always use fanned frets.
        </p>
      </div>

      <div class="ergonomic-benefits">
        <h3>Ergonomic Benefits</h3>
        <div class="benefit-grid">
          <div v-for="benefit in benefits" :key="benefit.title" class="benefit-card">
            <div class="benefit-icon">{{ benefit.icon }}</div>
            <div class="benefit-title">{{ benefit.title }}</div>
            <div class="benefit-text">{{ benefit.text }}</div>
          </div>
        </div>
      </div>

      <div class="custom-scale-exploration">
        <h3>Custom Scale Exploration</h3>
        <p>
          Want to innovate? Consider a 24.9" hybrid scale:
          <strong>slightly easier bending than Fender, slightly brighter than Gibson.</strong>
        </p>
        <p>
          Or go extreme: 28" baritone for drop G# tuning, 22" travel guitar for portability.
          The math is your guide!
        </p>
        <button class="btn-explore" @click="$emit('goToTension')">
          Explore Custom Scales in Tension Calculator →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  goToTension: []
}>()

const comparisonData = [
  { string: 'High E (.010")', single: '15.1 lbs', multi: '15.1 lbs', improvement: 'Same', level: 'neutral' },
  { string: 'B (.013")', single: '15.2 lbs', multi: '15.4 lbs', improvement: '+1.3%', level: 'slight' },
  { string: 'G (.017")', single: '15.0 lbs', multi: '15.6 lbs', improvement: '+4%', level: 'good' },
  { string: 'D (.026")', single: '14.9 lbs', multi: '16.0 lbs', improvement: '+7.4%', level: 'good' },
  { string: 'A (.036")', single: '14.3 lbs', multi: '15.8 lbs', improvement: '+10.5%', level: 'excellent' },
  { string: 'Low E (.046")', single: '13.8 lbs', multi: '15.7 lbs', improvement: '+13.8%', level: 'excellent' }
]

const benefits = [
  { icon: '🤚', title: 'Natural Hand Position', text: 'Fanned frets follow the natural angle of your hand/wrist, reducing strain during extended playing sessions.' },
  { icon: '🎯', title: 'Better Intonation', text: 'Longer bass scales reduce compensation percentage, making intonation more accurate across the entire fretboard.' },
  { icon: '🔊', title: 'Balanced Tone', text: 'Each string has optimal tension for its frequency range, creating a more balanced and articulate sound across all strings.' },
  { icon: '⚡', title: 'Extended Range', text: 'Makes 7, 8, and 9-string guitars playable by ensuring low strings have enough tension for clarity and definition.' }
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

.multiscale-education {
  max-width: 1000px;
}

.problem-solution {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.problem-card, .solution-card {
  padding: 24px;
  border-radius: 12px;
}

.problem-card {
  background: linear-gradient(135deg, rgba(234, 67, 53, 0.2) 0%, rgba(234, 67, 53, 0.1) 100%);
  border: 2px solid #ea4335;
}

.solution-card {
  background: linear-gradient(135deg, rgba(52, 168, 83, 0.2) 0%, rgba(52, 168, 83, 0.1) 100%);
  border: 2px solid #34a853;
}

.problem-card h3 { color: #ff6b6b; }
.solution-card h3 { color: #51cf66; }

.problem-card h3, .solution-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.problem-card p, .solution-card p {
  font-size: 14px;
  line-height: 1.6;
  color: #e8eaed;
  margin-bottom: 12px;
}

.problem-card ul, .solution-card ul {
  margin: 12px 0;
  padding-left: 20px;
}

.problem-card li, .solution-card li {
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.example {
  margin-top: 16px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.example strong {
  display: block;
  font-size: 13px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.calc-result {
  font-size: 16px;
  font-weight: 600;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
}

.calc-result.problem {
  background: rgba(234, 67, 53, 0.3);
  color: #ff6b6b;
}

.calc-result.solution {
  background: rgba(52, 168, 83, 0.3);
  color: #51cf66;
}

.multiscale-diagram {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 32px;
}

.multiscale-diagram h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.fret-visualization {
  background: rgba(0, 0, 0, 0.3);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.fret-line {
  margin-bottom: 20px;
  padding: 12px;
  border-radius: 6px;
}

.fret-line.treble { background: rgba(138, 180, 248, 0.2); }
.fret-line.bass { background: rgba(52, 168, 83, 0.2); }

.fret-label {
  font-size: 14px;
  font-weight: 500;
  color: #ffd700;
  margin-bottom: 6px;
}

.fret-visual {
  font-family: 'Courier New', monospace;
  font-size: 16px;
  margin-bottom: 6px;
  letter-spacing: 2px;
  color: #fff;
}

.fret-tension {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.diagram-note {
  font-size: 13px;
  line-height: 1.6;
  color: #9aa0a6;
  font-style: italic;
}

.tension-comparison {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 32px;
}

.tension-comparison h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.comparison-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.comparison-header {
  display: grid;
  grid-template-columns: 120px 110px 140px 110px;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  font-weight: 600;
  color: #ffd700;
  font-size: 12px;
  border-radius: 6px;
}

.comparison-row {
  display: grid;
  grid-template-columns: 120px 110px 140px 110px;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 13px;
  align-items: center;
}

.comparison-row div:last-child {
  text-align: center;
  font-weight: 600;
  padding: 4px;
  border-radius: 4px;
}

.neutral { color: #9aa0a6; }
.slight { background: rgba(138, 180, 248, 0.2); color: #8ab4f8; }
.good { background: rgba(52, 168, 83, 0.2); color: #51cf66; }
.excellent { background: rgba(52, 168, 83, 0.3); color: #51cf66; font-weight: bold; }

.comparison-note {
  font-size: 13px;
  line-height: 1.6;
  color: #e8eaed;
  font-style: italic;
}

.ergonomic-benefits {
  margin-bottom: 32px;
}

.ergonomic-benefits h3 {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 16px;
}

.benefit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.benefit-card {
  background: #292a2d;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.benefit-card:hover {
  border-color: #8ab4f8;
  transform: translateY(-4px);
}

.benefit-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.benefit-title {
  font-size: 15px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 8px;
}

.benefit-text {
  font-size: 13px;
  line-height: 1.6;
  color: #e8eaed;
}

.custom-scale-exploration {
  background: linear-gradient(135deg, rgba(138, 180, 248, 0.2) 0%, rgba(138, 180, 248, 0.1) 100%);
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #8ab4f8;
  text-align: center;
}

.custom-scale-exploration h3 {
  font-size: 18px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 12px;
}

.custom-scale-exploration p {
  font-size: 14px;
  line-height: 1.7;
  color: #e8eaed;
  margin-bottom: 12px;
}

.custom-scale-exploration strong {
  color: #ffd700;
}

.btn-explore {
  background: linear-gradient(135deg, #1a73e8 0%, #8ab4f8 100%);
  color: #fff;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 8px;
}

.btn-explore:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(138, 180, 248, 0.4);
}

@media (max-width: 768px) {
  .problem-solution {
    grid-template-columns: 1fr;
  }
  .comparison-header,
  .comparison-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
  .benefit-grid {
    grid-template-columns: 1fr;
  }
}
</style>
