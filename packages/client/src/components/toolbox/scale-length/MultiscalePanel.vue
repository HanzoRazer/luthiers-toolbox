<script setup lang="ts">
/**
 * MultiscalePanel - Multi-scale/fanned fret education
 * Extracted from ScaleLengthDesigner.vue
 */
import styles from "./MultiscalePanel.module.css";

const emit = defineEmits<{
  'goToTension': []
}>()
</script>

<template>
  <div :class="styles.multiscalePanel">
    <div :class="styles.sectionHeader">
      <h2>Multi-Scale (Fanned Fret) Innovation</h2>
      <p>Why modern guitars are moving beyond single scale lengths</p>
    </div>

    <div :class="styles.multiscaleEducation">
      <div :class="styles.problemSolution">
        <div :class="styles.problemCard">
          <h3>The Single-Scale Compromise</h3>
          <p>Traditional guitars force all strings to use the same scale length:</p>
          <ul>
            <li><strong>Treble strings:</strong> Higher tension than ideal (harder to bend)</li>
            <li><strong>Bass strings:</strong> Lower tension than ideal (less definition)</li>
            <li><strong>Result:</strong> Every string is a compromise</li>
          </ul>
          <div :class="styles.example">
            <strong>Example: Baritone at 25.5" scale</strong>
            <div :class="styles.calcResultProblem">Low B string: 12.8 lbs (too floppy!)</div>
          </div>
        </div>

        <div :class="styles.solutionCard">
          <h3>The Multi-Scale Solution</h3>
          <p>Different scale length for each string, optimized independently:</p>
          <ul>
            <li><strong>Treble E:</strong> 25.5" (comfortable tension, easy bending)</li>
            <li><strong>Bass E:</strong> 27.0" (tight, defined, no flop)</li>
            <li><strong>Middle strings:</strong> Smoothly interpolated</li>
          </ul>
          <div :class="styles.example">
            <strong>Same baritone with multi-scale:</strong>
            <div :class="styles.calcResultSolution">Low B string: 14.3 lbs (perfect!)</div>
          </div>
        </div>
      </div>

      <div :class="styles.multiscaleDiagram">
        <h3>Visual: How Fanned Frets Work</h3>
        <div :class="styles.fretVisualization">
          <div :class="styles.fretLine">
            <div :class="styles.fretLabel">Treble Side (High E)</div>
            <div :class="styles.fretVisual">|———————————————————| 25.5" scale</div>
            <div :class="styles.fretTension">15.1 lbs tension</div>
          </div>
          <div :class="styles.fretLine">
            <div :class="styles.fretLabel">Bass Side (Low E)</div>
            <div :class="styles.fretVisual">|—————————————————————————| 27.0" scale</div>
            <div :class="styles.fretTension">14.8 lbs tension (with .046" gauge)</div>
          </div>
        </div>
        <p :class="styles.diagramNote">
          Notice how the bass side is longer. Frets are angled (fanned) to accommodate different
          scale lengths. The 12th fret is typically placed at the ergonomic "neutral" position.
        </p>
      </div>

      <div :class="styles.tensionComparison">
        <h3>Tension Comparison: Single vs Multi-Scale</h3>
        <div :class="styles.comparisonTable">
          <div :class="styles.comparisonHeader">
            <div>String</div>
            <div>Single 25.5"</div>
            <div>Multi (25.5"-27")</div>
            <div>Improvement</div>
          </div>
          <div :class="styles.comparisonRow">
            <div>High E (.010")</div>
            <div>15.1 lbs</div>
            <div>15.1 lbs</div>
            <div :class="styles.neutral">Same</div>
          </div>
          <div :class="styles.comparisonRow">
            <div>B (.013")</div>
            <div>15.2 lbs</div>
            <div>15.4 lbs</div>
            <div :class="styles.slight">+1.3%</div>
          </div>
          <div :class="styles.comparisonRow">
            <div>G (.017")</div>
            <div>15.0 lbs</div>
            <div>15.6 lbs</div>
            <div :class="styles.good">+4%</div>
          </div>
          <div :class="styles.comparisonRow">
            <div>D (.026")</div>
            <div>14.9 lbs</div>
            <div>16.0 lbs</div>
            <div :class="styles.good">+7.4%</div>
          </div>
          <div :class="styles.comparisonRow">
            <div>A (.036")</div>
            <div>14.3 lbs</div>
            <div>15.8 lbs</div>
            <div :class="styles.excellent">+10.5%</div>
          </div>
          <div :class="styles.comparisonRow">
            <div>Low E (.046")</div>
            <div>13.8 lbs</div>
            <div>15.7 lbs</div>
            <div :class="styles.excellent">+13.8%</div>
          </div>
        </div>
        <p :class="styles.comparisonNote">
          Multi-scale dramatically improves bass string tension while keeping treble strings comfortable.
          This is why extended-range guitars (7, 8, 9 strings) almost always use fanned frets.
        </p>
      </div>

      <div :class="styles.ergonomicBenefits">
        <h3>Ergonomic Benefits</h3>
        <div :class="styles.benefitGrid">
          <div :class="styles.benefitCard">
            <div :class="styles.benefitIcon">🤚</div>
            <div :class="styles.benefitTitle">Natural Hand Position</div>
            <div :class="styles.benefitText">
              Fanned frets follow the natural angle of your hand/wrist, reducing strain during
              extended playing sessions.
            </div>
          </div>
          <div :class="styles.benefitCard">
            <div :class="styles.benefitIcon">🎯</div>
            <div :class="styles.benefitTitle">Better Intonation</div>
            <div :class="styles.benefitText">
              Longer bass scales reduce compensation percentage, making intonation more accurate
              across the entire fretboard.
            </div>
          </div>
          <div :class="styles.benefitCard">
            <div :class="styles.benefitIcon">🔊</div>
            <div :class="styles.benefitTitle">Balanced Tone</div>
            <div :class="styles.benefitText">
              Each string has optimal tension for its frequency range, creating a more balanced
              and articulate sound across all strings.
            </div>
          </div>
          <div :class="styles.benefitCard">
            <div :class="styles.benefitIcon">⚡</div>
            <div :class="styles.benefitTitle">Extended Range</div>
            <div :class="styles.benefitText">
              Makes 7, 8, and 9-string guitars playable by ensuring low strings have enough tension
              for clarity and definition.
            </div>
          </div>
        </div>
      </div>

      <div :class="styles.customScaleExploration">
        <h3>Custom Scale Exploration</h3>
        <p>
          Want to innovate? Consider a 24.9" hybrid scale:
          <strong>slightly easier bending than Fender, slightly brighter than Gibson.</strong>
        </p>
        <p>
          Or go extreme: 28" baritone for drop G# tuning, 22" travel guitar for portability.
          The math is your guide!
        </p>
        <button :class="styles.btnExplore" @click="emit('goToTension')">
          Explore Custom Scales in Tension Calculator →
        </button>
      </div>
    </div>
  </div>
</template>

