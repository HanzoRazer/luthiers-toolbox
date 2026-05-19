<script setup lang="ts">
/**
 * TargetMatchingPanel — Target matching task workflow panel
 *
 * Dev Order 17: Structured task-detail panels for solver intents.
 * Organizes future acoustic solving around user goals, not equations.
 *
 * Does NOT implement solver math.
 */
import { GateBadge, SectionLabel, PrerequisiteNotice } from '@/components/shared/workflow'
import { TargetTaskCard } from '@/components/shared/acoustics'

const tasks = [
  {
    id: 'solve-area',
    question: 'What aperture area is required to achieve a target air resonance?',
    purpose: 'Given body volume and target air resonance frequency, calculate the required aperture area.',
    inputs: ['body volume', 'target Helmholtz frequency', 'effective neck length estimate'],
    output: 'required aperture area',
    uses: ['ApertureGeometry', 'AcousticState', 'future measured response data'],
    assumptions: [
      'first-order acoustic approximation',
      'no cavity coupling',
      'no modal interaction',
    ],
    confidenceCaveats: [
      'body-volume accuracy',
      'effective-length estimation',
      'measured calibration data',
    ],
  },
  {
    id: 'solve-length',
    question: 'What effective neck length does this aperture geometry imply?',
    purpose: 'Given aperture geometry and measured air resonance, estimate the effective acoustic neck length.',
    inputs: ['aperture geometry', 'measured Helmholtz frequency', 'body volume'],
    output: 'estimated effective length',
    uses: ['ApertureGeometry', 'AcousticState', 'measured response data'],
    assumptions: [
      'first-order acoustic approximation',
      'no end correction anomalies',
      'stable body volume',
    ],
    confidenceCaveats: [
      'measurement precision',
      'body-volume accuracy',
      'aperture geometry accuracy',
    ],
  },
  {
    id: 'estimate-loss',
    question: 'How much acoustic loss or resistance is implied by the measured response?',
    purpose: 'Given measured Q factor and resonance, estimate the acoustic resistance and energy loss.',
    inputs: ['measured Q', 'measured resonance', 'aperture geometry'],
    output: 'loss estimate / resistance estimate',
    uses: ['ApertureGeometry', 'AcousticState', 'measured Q data'],
    assumptions: [
      'single-mode dominance',
      'no parasitic losses',
      'stable environmental conditions',
    ],
    confidenceCaveats: [
      'Q measurement accuracy',
      'resonance stability',
      'aperture edge conditions',
    ],
  },
  {
    id: 'match-candidate',
    question: 'What geometry changes are required for a candidate aperture to match a reference response?',
    purpose: 'Given reference and candidate apertures, determine which parameter must change to match acoustic behavior.',
    inputs: ['reference geometry', 'candidate geometry', 'future measured response data'],
    output: 'recommended parameter deltas',
    uses: ['ApertureGeometry (both)', 'Comparison delta table', 'AcousticState (both)'],
    assumptions: [
      'geometry-only matching',
      'no material property differences',
      'comparable body volumes',
    ],
    confidenceCaveats: [
      'comparison accuracy',
      'geometry normalization',
      'target metric selection',
    ],
    note: 'Uses comparison infrastructure from the Comparison tab.',
  },
]

const workflowSteps = [
  { label: 'Geometry', description: 'Aperture shape and dimensions' },
  { label: 'Comparison', description: 'Cross-type delta analysis' },
  { label: 'Acoustic State', description: 'Estimated acoustic properties' },
  { label: 'Target Matching', description: 'Goal-oriented solving' },
]
</script>

<template>
  <div :class="$style.panel">
    <!-- Intro Section -->
    <section :class="$style.intro">
      <div :class="$style.introHeader">
        <SectionLabel text="What do you want to solve for?" />
        <GateBadge gate="yellow" label="Planned Capability" />
      </div>
      <p :class="$style.introText">
        Target Matching organizes future acoustic solving around design goals instead of raw equations.
      </p>
      <p :class="$style.introText">
        These tools will use aperture geometry, comparison data, acoustic state, and future measured
        response data to estimate design changes needed to achieve target acoustic behavior.
      </p>
    </section>

    <!-- Task Cards Grid -->
    <section :class="$style.tasksSection">
      <div :class="$style.taskGrid">
        <TargetTaskCard
          v-for="task in tasks"
          :key="task.id"
          :question="task.question"
          :purpose="task.purpose"
          :inputs="task.inputs"
          :output="task.output"
          :uses="task.uses"
          :assumptions="task.assumptions"
          :confidence-caveats="task.confidenceCaveats"
          :note="task.note"
        />
      </div>
    </section>

    <!-- Workflow Relationship -->
    <section :class="$style.workflowSection">
      <SectionLabel text="Workflow Relationship" />
      <div :class="$style.workflowDiagram">
        <template v-for="(step, i) in workflowSteps" :key="step.label">
          <div :class="$style.workflowStep">
            <span :class="$style.stepLabel">{{ step.label }}</span>
          </div>
          <span v-if="i < workflowSteps.length - 1" :class="$style.arrow">→</span>
        </template>
      </div>
      <p :class="$style.workflowDescription">
        Each layer builds on the previous. Target Matching consumes geometry, comparison results,
        and acoustic state to compute goal-oriented recommendations.
      </p>
    </section>

    <!-- Footer Notice -->
    <PrerequisiteNotice
      message="The inverse solver is an internal calculation service. These cards represent solver intents — the math engine will be implemented in a future order."
    />
  </div>
</template>

<style module>
.panel {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.intro {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.introHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.introText {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: #9ca3af;
  line-height: 1.6;
}

.introText:last-of-type {
  margin-bottom: 0;
}

.tasksSection {
  /* Container for task grid */
}

.taskGrid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.workflowSection {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.workflowDiagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin: 1rem 0;
  padding: 1rem;
  background: #111827;
  border-radius: 0.375rem;
}

.workflowStep {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  background: #374151;
  border: 1px solid #4b5563;
  border-radius: 0.375rem;
}

.stepLabel {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #f9fafb;
}

.arrow {
  font-size: 1.25rem;
  color: #6366f1;
  font-weight: 600;
}

.workflowDescription {
  margin: 0;
  font-size: 0.8125rem;
  color: #6b7280;
  text-align: center;
}
</style>
