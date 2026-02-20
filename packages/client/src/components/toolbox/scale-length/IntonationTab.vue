<template>
  <div :class="styles.tabContent">
    <div :class="styles.sectionHeader">
      <h2>Intonation Compensation</h2>
      <p>Understanding the "dead zone" and why bridges aren't placed at the exact scale length</p>
    </div>

    <div :class="styles.intonationEducation">
      <div :class="styles.criticalConcept">
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

      <div :class="styles.compensationTable">
        <div :class="styles.compHeader">
          <div :class="styles.compTitle">Intonation Compensation Chart</div>
          <div :class="styles.compSubtitle">For 25.5" scale (Fender) with standard .010-.046 gauges</div>
        </div>

        <div :class="styles.compGrid">
          <div :class="styles.compHeaderRow">
            <div>String</div>
            <div>Gauge</div>
            <div>Design Length</div>
            <div>Actual Length</div>
            <div>Compensation</div>
          </div>
          <div
            v-for="row in compensationData"
            :key="row.string"
            :class="highlightClass(row.highlight)"
          >
            <div>{{ row.string }}</div>
            <div>{{ row.gauge }}</div>
            <div>{{ row.design }}</div>
            <div>{{ row.actual }}</div>
            <div>{{ row.compensation }}</div>
          </div>
        </div>
      </div>

      <div :class="styles.bridgePlacement">
        <h3>Bridge Placement Formula</h3>
        <div :class="styles.placementBox">
          <div :class="styles.formula">
            Bridge Center = Scale Length + (Low E Compensation ÷ 2)
          </div>
          <div :class="styles.formulaExample">
            Example: 25.5" + (0.25" ÷ 2) = <strong>25.625"</strong> from nut to bridge center
          </div>
        </div>
        <div :class="styles.placementNoteWarning">
          <strong>Common Mistake:</strong> Placing the bridge at exactly 25.5" from the nut.
          This forces all saddles backward, limiting adjustment range and causing intonation issues.
        </div>
        <div :class="styles.placementNoteSuccess">
          <strong>Correct Approach:</strong> Place bridge center at scale + (max_comp ÷ 2), allowing
          saddles to move both forward (high E, B) and backward (low E) for perfect intonation.
        </div>
      </div>

      <div :class="styles.compensationFactors">
        <h3>5 Physical Factors Affecting Compensation</h3>
        <div :class="styles.factorList">
          <div v-for="factor in factors" :key="factor.title" :class="styles.factorItem">
            <strong>{{ factor.title }}</strong>
            <div>{{ factor.description }}</div>
          </div>
        </div>
      </div>

      <div :class="styles.innovationConnection">
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
import styles from "./IntonationTab.module.css";

/**
 * Helper for dynamic highlight classes
 */
function highlightClass(highlight: string): string {
  const classMap: Record<string, string> = {
    "highlight-reference": styles.highlightReference,
    "highlight-max": styles.highlightMax,
  };
  return highlight ? classMap[highlight] || styles.compRow : styles.compRow;
}

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

