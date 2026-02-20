<script setup lang="ts">
/**
 * IntonationPanel - Intonation compensation education
 * Extracted from ScaleLengthDesigner.vue
 */
import styles from "./IntonationPanel.module.css";
</script>

<template>
  <div :class="styles.intonationPanel">
    <div :class="styles.sectionHeader">
      <h2>Intonation Compensation</h2>
      <p>Understanding the "dead zone" and why bridges aren't placed at the exact scale length</p>
    </div>

    <div :class="styles.intonationEducation">
      <div :class="styles.criticalConcept">
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

      <div :class="styles.compensationTable">
        <div :class="styles.compHeader">
          <div :class="styles.compTitle">Intonation Compensation Chart</div>
          <div :class="styles.compSubtitle">For 25.5" scale (Fender) with standard .010-.046 gauges</div>
        </div>

        <div :class="styles.compGrid">
          <div :class="[styles.compRow, styles.compHeaderRow]">
            <div>String</div>
            <div>Gauge</div>
            <div>Design Length</div>
            <div>Actual Length</div>
            <div>Compensation</div>
          </div>

          <div :class="styles.compRow">
            <div>High E</div>
            <div>.010"</div>
            <div>25.500"</div>
            <div>25.500"</div>
            <div>0.000" (none)</div>
          </div>

          <div :class="[styles.compRow, styles.highlightReference]">
            <div>B</div>
            <div>.013"</div>
            <div>25.500"</div>
            <div>25.500"</div>
            <div>0.000" (reference)</div>
          </div>

          <div :class="styles.compRow">
            <div>G</div>
            <div>.017"</div>
            <div>25.500"</div>
            <div>25.562"</div>
            <div>+0.062" (~1/16")</div>
          </div>

          <div :class="styles.compRow">
            <div>D</div>
            <div>.026"</div>
            <div>25.500"</div>
            <div>25.625"</div>
            <div>+0.125" (1/8")</div>
          </div>

          <div :class="styles.compRow">
            <div>A</div>
            <div>.036"</div>
            <div>25.500"</div>
            <div>25.687"</div>
            <div>+0.187" (3/16")</div>
          </div>

          <div :class="[styles.compRow, styles.highlightMax]">
            <div>Low E</div>
            <div>.046"</div>
            <div>25.500"</div>
            <div>25.750"</div>
            <div>+0.250" (1/4")</div>
          </div>
        </div>
      </div>

      <div :class="styles.bridgePlacement">
        <h3>Bridge Placement Formula</h3>
        <div :class="styles.placementBox">
          <div :class="styles.formula">Bridge Center = Scale Length + (Low E Compensation ÷ 2)</div>
          <div :class="styles.formulaExample">
            Example: 25.5" + (0.25" ÷ 2) = <strong>25.625"</strong> from nut to bridge center
          </div>
        </div>
        <div :class="[styles.placementNote, styles.placementNoteWarning]">
          <strong>Common Mistake:</strong> Placing the bridge at exactly 25.5" from the nut.
          This forces all saddles backward, limiting adjustment range and causing intonation issues.
        </div>
        <div :class="[styles.placementNote, styles.placementNoteSuccess]">
          <strong>Correct Approach:</strong> Place bridge center at scale + (max_comp ÷ 2), allowing
          saddles to move both forward (high E, B) and backward (low E) for perfect intonation.
        </div>
      </div>

      <div :class="styles.compensationFactors">
        <h3>5 Physical Factors Affecting Compensation</h3>
        <div :class="styles.factorList">
          <div :class="styles.factorItem">
            <strong>1. String Diameter</strong>
            <div>
              Thicker strings have more stiffness, creating larger dead zones. Low E (.046") needs
              ~4× more compensation than High E (.010").
            </div>
          </div>
          <div :class="styles.factorItem">
            <strong>2. String Structure</strong>
            <div>
              Wound strings (G, D, A, Low E) have higher stiffness than plain strings (High E, B)
              due to the wrap wire adding rigidity.
            </div>
          </div>
          <div :class="styles.factorItem">
            <strong>3. Core Wire Composition</strong>
            <div>
              Stainless steel cores are stiffer than nickel or phosphor bronze, requiring more
              compensation. Material matters!
            </div>
          </div>
          <div :class="styles.factorItem">
            <strong>4. String Action Height</strong>
            <div>
              Higher action means more stretch when fretting, pulling the string sharper. Compensate
              by moving saddles back further.
            </div>
          </div>
          <div :class="styles.factorItem">
            <strong>5. Fret Height</strong>
            <div>
              Tall frets (like jumbos) require more stretch to fret cleanly, increasing effective
              length. Lower frets need less compensation.
            </div>
          </div>
        </div>
      </div>

      <div :class="styles.innovationConnection">
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

