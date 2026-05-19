<script setup lang="ts">
/**
 * TargetTaskCard — Reusable card for target matching solver tasks
 *
 * Dev Order 17: Task-detail card for solver intents.
 * Displays problem statement, inputs, outputs, assumptions, and confidence caveats.
 * Does NOT implement solver math.
 */
import { GateBadge } from '@/components/shared/workflow'

interface Props {
  question: string
  purpose: string
  inputs: string[]
  output: string
  uses: string[]
  assumptions: string[]
  confidenceCaveats: string[]
  note?: string
}

defineProps<Props>()
</script>

<template>
  <div :class="$style.card">
    <!-- Header -->
    <div :class="$style.header">
      <h4 :class="$style.question">{{ question }}</h4>
      <GateBadge gate="yellow" label="Coming Soon" />
    </div>

    <!-- Purpose -->
    <p :class="$style.purpose">{{ purpose }}</p>

    <!-- Inputs / Output -->
    <div :class="$style.ioSection">
      <div :class="$style.inputs">
        <span :class="$style.ioLabel">Inputs Needed</span>
        <ul>
          <li v-for="(input, i) in inputs" :key="i">{{ input }}</li>
        </ul>
      </div>
      <div :class="$style.output">
        <span :class="$style.ioLabel">Solves For</span>
        <span :class="$style.outputValue">{{ output }}</span>
      </div>
    </div>

    <!-- Uses -->
    <div :class="$style.usesSection">
      <span :class="$style.sectionLabel">Uses</span>
      <ul>
        <li v-for="(use, i) in uses" :key="i">{{ use }}</li>
      </ul>
    </div>

    <!-- Assumptions -->
    <div :class="$style.assumptionsSection">
      <span :class="$style.sectionLabel">Assumptions</span>
      <ul>
        <li v-for="(assumption, i) in assumptions" :key="i">{{ assumption }}</li>
      </ul>
    </div>

    <!-- Confidence Caveats -->
    <div :class="$style.confidenceSection">
      <span :class="$style.sectionLabel">Confidence depends on</span>
      <ul>
        <li v-for="(caveat, i) in confidenceCaveats" :key="i">{{ caveat }}</li>
      </ul>
    </div>

    <!-- Optional Note -->
    <p v-if="note" :class="$style.note">{{ note }}</p>
  </div>
</template>

<style module>
.card {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.question {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f9fafb;
  line-height: 1.3;
}

.purpose {
  margin: 0;
  font-size: 0.8125rem;
  color: #9ca3af;
  line-height: 1.5;
}

.ioSection {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: #111827;
  border-radius: 0.375rem;
}

.inputs {
  flex: 1;
}

.inputs ul {
  margin: 0.25rem 0 0 0;
  padding-left: 1rem;
}

.inputs li {
  font-size: 0.75rem;
  color: #d1d5db;
  line-height: 1.5;
}

.output {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.ioLabel {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.outputValue {
  font-size: 0.875rem;
  font-weight: 600;
  color: #60a5fa;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.usesSection,
.assumptionsSection,
.confidenceSection {
  font-size: 0.75rem;
}

.sectionLabel {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 0.25rem;
}

.usesSection ul,
.assumptionsSection ul,
.confidenceSection ul {
  margin: 0;
  padding-left: 1rem;
}

.usesSection li {
  color: #a5b4fc;
  line-height: 1.5;
}

.assumptionsSection li {
  color: #9ca3af;
  line-height: 1.5;
}

.confidenceSection li {
  color: #fbbf24;
  line-height: 1.5;
}

.note {
  margin: 0;
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  padding-top: 0.5rem;
  border-top: 1px solid #374151;
}
</style>
