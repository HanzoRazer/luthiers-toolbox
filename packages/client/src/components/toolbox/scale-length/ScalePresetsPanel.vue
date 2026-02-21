<script setup lang="ts">
/**
 * ScalePresetsPanel - Scale length presets and physics education
 * Extracted from ScaleLengthDesigner.vue
 */
import styles from "./ScalePresetsPanel.module.css";
import shared from "./scale-length-shared.module.css";

const emit = defineEmits<{
  'selectScale': [scaleType: string]
}>()
</script>

<template>
  <div :class="styles.scalePresetsPanel">
    <div :class="shared.sectionHeader">
      <h2>Standard Scale Lengths</h2>
      <p>Click a card to explore how scale length affects string tension and tone</p>
    </div>

    <div :class="styles.scaleGrid">
      <div :class="styles.scaleCard" @click="emit('selectScale', 'fender')">
        <div :class="styles.scaleName">Fender Scale</div>
        <div :class="styles.scaleValue">25.5" (648mm)</div>
        <div :class="styles.scaleInfo">
          <div :class="styles.scaleTrait">• Bright, snappy tone</div>
          <div :class="styles.scaleTrait">• Higher string tension</div>
          <div :class="styles.scaleTrait">• Strat, Tele, Jazzmaster</div>
        </div>
      </div>

      <div :class="styles.scaleCard" @click="emit('selectScale', 'gibson')">
        <div :class="styles.scaleName">Gibson Scale</div>
        <div :class="styles.scaleValue">24.75" (629mm)</div>
        <div :class="styles.scaleInfo">
          <div :class="styles.scaleTrait">• Warm, fat tone</div>
          <div :class="styles.scaleTrait">• Easier bending</div>
          <div :class="styles.scaleTrait">• Les Paul, SG, 335</div>
        </div>
      </div>

      <div :class="styles.scaleCard" @click="emit('selectScale', 'prs')">
        <div :class="styles.scaleName">PRS Scale</div>
        <div :class="styles.scaleValue">25.0" (635mm)</div>
        <div :class="styles.scaleInfo">
          <div :class="styles.scaleTrait">• Balanced compromise</div>
          <div :class="styles.scaleTrait">• Medium tension</div>
          <div :class="styles.scaleTrait">• PRS core models</div>
        </div>
      </div>

      <div :class="styles.scaleCard" @click="emit('selectScale', 'short')">
        <div :class="styles.scaleName">Short Scale</div>
        <div :class="styles.scaleValue">24.0" (610mm)</div>
        <div :class="styles.scaleInfo">
          <div :class="styles.scaleTrait">• Easy playability</div>
          <div :class="styles.scaleTrait">• Lower tension</div>
          <div :class="styles.scaleTrait">• Mustang, Jaguar</div>
        </div>
      </div>

      <div :class="styles.scaleCard" @click="emit('selectScale', 'baritone')">
        <div :class="styles.scaleName">Baritone Scale</div>
        <div :class="styles.scaleValue">27.0" (686mm)</div>
        <div :class="styles.scaleInfo">
          <div :class="styles.scaleTrait">• Extended low range</div>
          <div :class="styles.scaleTrait">• Tight low strings</div>
          <div :class="styles.scaleTrait">• Drop A, B tuning</div>
        </div>
      </div>

      <div :class="styles.scaleCard" @click="emit('selectScale', 'multiscale')">
        <div :class="styles.scaleName">Multi-Scale (Fanned)</div>
        <div :class="styles.scaleValue">25.5" - 27.0"</div>
        <div :class="styles.scaleInfo">
          <div :class="styles.scaleTrait">• Ergonomic fanned frets</div>
          <div :class="styles.scaleTrait">• Optimized per string</div>
          <div :class="styles.scaleTrait">• Modern innovation</div>
        </div>
      </div>
    </div>

    <!-- Why Scale Length Matters -->
    <div :class="styles.educationSection">
      <div :class="styles.eduTitle">Why Scale Length Matters for Innovation</div>

      <div :class="shared.card">
        <h3>The Physics: Mersenne's Law</h3>
        <p>String tension is determined by a precise mathematical relationship:</p>
        <div :class="shared.formulaBox">
          <div :class="shared.formula">T = (μ × (2 × L × f)²) ÷ 4</div>
          <div :class="styles.formulaLegend">
            <div><strong>T</strong> = Tension (lbs)</div>
            <div><strong>μ</strong> = Linear mass density (lb/in)</div>
            <div><strong>L</strong> = Scale length (in)</div>
            <div><strong>f</strong> = Frequency (Hz)</div>
          </div>
        </div>
        <p :class="shared.noteInfo">
          <strong>Key insight:</strong> Tension increases with the <em>square</em> of scale length.
          Every 0.75" longer scale = ~6% more tension!
        </p>
      </div>

      <div :class="shared.card">
        <h3>Real-World Examples</h3>
        <div :class="styles.exampleGrid">
          <div :class="styles.exampleItem">
            <div :class="styles.exampleScale">Gibson 24.75"</div>
            <div :class="styles.exampleTension">14.2 lbs</div>
            <div :class="styles.exampleNote">High E string (.010")</div>
          </div>
          <div :class="styles.exampleItem">
            <div :class="styles.exampleScale">PRS 25.0"</div>
            <div :class="styles.exampleTension">14.5 lbs</div>
            <div :class="styles.exampleNote">+2.1% tension</div>
          </div>
          <div :class="styles.exampleItem">
            <div :class="styles.exampleScale">Fender 25.5"</div>
            <div :class="styles.exampleTension">15.1 lbs</div>
            <div :class="styles.exampleNote">+6.3% tension</div>
          </div>
        </div>
        <p :class="shared.noteInfo">
          That 0.75" difference between Gibson and Fender creates noticeable feel and tone differences!
        </p>
      </div>
    </div>
  </div>
</template>

