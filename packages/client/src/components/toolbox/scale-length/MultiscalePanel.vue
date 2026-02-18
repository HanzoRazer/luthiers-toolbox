<script setup lang="ts">
/**
 * MultiscalePanel - Multi-scale/fanned fret education
 * Extracted from ScaleLengthDesigner.vue
 */

const emit = defineEmits<{
  'goToTension': []
}>()
</script>

<template>
  <div class="multiscale-panel">
    <div class="section-header">
      <h2>Multi-Scale (Fanned Fret) Innovation</h2>
      <p>Why modern guitars are moving beyond single scale lengths</p>
    </div>

    <div class="multiscale-education">
      <div class="problem-solution">
        <div class="problem-card">
          <h3>The Single-Scale Compromise</h3>
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
          <h3>The Multi-Scale Solution</h3>
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
          <div class="comparison-row">
            <div>High E (.010")</div>
            <div>15.1 lbs</div>
            <div>15.1 lbs</div>
            <div class="neutral">Same</div>
          </div>
          <div class="comparison-row">
            <div>B (.013")</div>
            <div>15.2 lbs</div>
            <div>15.4 lbs</div>
            <div class="slight">+1.3%</div>
          </div>
          <div class="comparison-row">
            <div>G (.017")</div>
            <div>15.0 lbs</div>
            <div>15.6 lbs</div>
            <div class="good">+4%</div>
          </div>
          <div class="comparison-row">
            <div>D (.026")</div>
            <div>14.9 lbs</div>
            <div>16.0 lbs</div>
            <div class="good">+7.4%</div>
          </div>
          <div class="comparison-row">
            <div>A (.036")</div>
            <div>14.3 lbs</div>
            <div>15.8 lbs</div>
            <div class="excellent">+10.5%</div>
          </div>
          <div class="comparison-row">
            <div>Low E (.046")</div>
            <div>13.8 lbs</div>
            <div>15.7 lbs</div>
            <div class="excellent">+13.8%</div>
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
          <div class="benefit-card">
            <div class="benefit-icon">🤚</div>
            <div class="benefit-title">Natural Hand Position</div>
            <div class="benefit-text">
              Fanned frets follow the natural angle of your hand/wrist, reducing strain during
              extended playing sessions.
            </div>
          </div>
          <div class="benefit-card">
            <div class="benefit-icon">🎯</div>
            <div class="benefit-title">Better Intonation</div>
            <div class="benefit-text">
              Longer bass scales reduce compensation percentage, making intonation more accurate
              across the entire fretboard.
            </div>
          </div>
          <div class="benefit-card">
            <div class="benefit-icon">🔊</div>
            <div class="benefit-title">Balanced Tone</div>
            <div class="benefit-text">
              Each string has optimal tension for its frequency range, creating a more balanced
              and articulate sound across all strings.
            </div>
          </div>
          <div class="benefit-card">
            <div class="benefit-icon">⚡</div>
            <div class="benefit-title">Extended Range</div>
            <div class="benefit-text">
              Makes 7, 8, and 9-string guitars playable by ensuring low strings have enough tension
              for clarity and definition.
            </div>
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
        <button class="btn-explore" @click="emit('goToTension')">
          Explore Custom Scales in Tension Calculator →
        </button>
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

.problem-solution {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

@media (max-width: 900px) {
  .problem-solution {
    grid-template-columns: 1fr;
  }
}

.problem-card, .solution-card {
  padding: 24px;
  border-radius: 12px;
}

.problem-card {
  background: rgba(234, 67, 53, 0.1);
  border-left: 4px solid #ea4335;
}

.solution-card {
  background: rgba(52, 168, 83, 0.1);
  border-left: 4px solid #34a853;
}

.problem-card h3 {
  color: #ff6b6b;
  margin-bottom: 12px;
}

.solution-card h3 {
  color: #51cf66;
  margin-bottom: 12px;
}

.problem-card p, .solution-card p {
  color: #bdc1c6;
  margin-bottom: 12px;
}

.problem-card ul, .solution-card ul {
  list-style: none;
  padding: 0;
  margin-bottom: 16px;
}

.problem-card li, .solution-card li {
  padding: 4px 0;
  color: #9aa0a6;
  font-size: 14px;
}

.example {
  margin-top: 16px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.example strong {
  display: block;
  font-size: 13px;
  color: #9aa0a6;
  margin-bottom: 8px;
}

.calc-result {
  font-size: 18px;
  font-weight: 600;
  padding: 8px;
  border-radius: 4px;
}

.calc-result.problem {
  color: #ff6b6b;
  background: rgba(234, 67, 53, 0.2);
}

.calc-result.solution {
  color: #51cf66;
  background: rgba(52, 168, 83, 0.2);
}

.multiscale-diagram {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.multiscale-diagram h3 {
  color: #e8eaed;
  margin-bottom: 20px;
}

.fret-visualization {
  font-family: 'Courier New', monospace;
  margin-bottom: 16px;
}

.fret-line {
  margin-bottom: 16px;
}

.fret-label {
  font-size: 12px;
  color: #8ab4f8;
  margin-bottom: 4px;
}

.fret-visual {
  font-size: 14px;
  color: #e8eaed;
  margin-bottom: 4px;
}

.fret-tension {
  font-size: 12px;
  color: #51cf66;
}

.diagram-note {
  font-size: 14px;
  color: #9aa0a6;
  line-height: 1.5;
}

.tension-comparison {
  background: #292a2d;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.tension-comparison h3 {
  color: #e8eaed;
  margin-bottom: 16px;
}

.comparison-table {
  margin-bottom: 16px;
}

.comparison-header, .comparison-row {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr 1.5fr;
  gap: 16px;
  padding: 12px;
  font-size: 14px;
}

.comparison-header {
  background: #35363a;
  border-radius: 8px 8px 0 0;
  font-weight: 600;
  color: #8ab4f8;
}

.comparison-row {
  border-bottom: 1px solid #3c4043;
  color: #bdc1c6;
}

.comparison-row:last-child {
  border-bottom: none;
}

.neutral { color: #9aa0a6; }
.slight { color: #ffc107; }
.good { color: #8ab4f8; }
.excellent { color: #51cf66; font-weight: 600; }

.comparison-note {
  font-size: 14px;
  color: #9aa0a6;
  line-height: 1.5;
}

.ergonomic-benefits {
  margin-bottom: 24px;
}

.ergonomic-benefits h3 {
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
}

.benefit-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.benefit-title {
  font-size: 16px;
  font-weight: 600;
  color: #8ab4f8;
  margin-bottom: 8px;
}

.benefit-text {
  font-size: 13px;
  line-height: 1.5;
  color: #9aa0a6;
}

.custom-scale-exploration {
  background: linear-gradient(135deg, rgba(138, 180, 248, 0.2), rgba(138, 180, 248, 0.1));
  padding: 24px;
  border-radius: 12px;
  border-left: 4px solid #8ab4f8;
}

.custom-scale-exploration h3 {
  color: #8ab4f8;
  margin-bottom: 12px;
}

.custom-scale-exploration p {
  font-size: 14px;
  line-height: 1.6;
  color: #bdc1c6;
  margin-bottom: 12px;
}

.btn-explore {
  padding: 12px 24px;
  background: #8ab4f8;
  color: #202124;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-explore:hover {
  background: #aecbfa;
}
</style>
