<template>
  <div :class="styles.tabContent">
    <div :class="styles.sectionHeader">
      <h2>Standard Scale Lengths</h2>
      <p>Click a card to explore how scale length affects string tension and tone</p>
    </div>

    <div :class="styles.scaleGrid">
      <div
        v-for="preset in presets"
        :key="preset.id"
        :class="styles.scaleCard"
        @click="$emit('select', preset.id)"
      >
        <div :class="styles.scaleName">{{ preset.name }}</div>
        <div :class="styles.scaleValue">{{ preset.value }}</div>
        <div :class="styles.scaleInfo">
          <div v-for="trait in preset.traits" :key="trait" :class="styles.scaleTrait">
            • {{ trait }}
          </div>
        </div>
      </div>
    </div>

    <!-- Why Scale Length Matters -->
    <div :class="styles.educationSection">
      <div :class="styles.eduTitle">
        💡 Why Scale Length Matters for Innovation
      </div>

      <div :class="styles.eduCard">
        <h3>The Physics: Mersenne's Law</h3>
        <p>String tension is determined by a precise mathematical relationship:</p>
        <div :class="styles.formulaBox">
          <div :class="styles.formula">
            T = (μ × (2 × L × f)²) ÷ 4
          </div>
          <div :class="styles.formulaLegend">
            <div><strong>T</strong> = Tension (lbs)</div>
            <div><strong>μ</strong> = Linear mass density (lb/in)</div>
            <div><strong>L</strong> = Scale length (in)</div>
            <div><strong>f</strong> = Frequency (Hz)</div>
          </div>
        </div>
        <p :class="styles.eduNote">
          <strong>Key insight:</strong> Tension increases with the <em>square</em> of scale length.
          Every 0.75" longer scale = ~6% more tension!
        </p>
      </div>

      <div :class="styles.eduCard">
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
        <p :class="styles.eduNote">
          That 0.75" difference between Gibson and Fender creates noticeable feel and tone differences!
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from "./ScalePresetsTab.module.css";

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

