<script setup lang="ts">
/**
 * RmosTooltip.vue - Educational tooltips for RMOS concepts
 *
 * Provides consistent, educational tooltips for RMOS terminology.
 * Deterministic: no API calls, all content is static.
 */

type ConceptKey =
  | 'risk-green'
  | 'risk-yellow'
  | 'risk-red'
  | 'override'
  | 'audit-trail'
  | 'feasibility'
  | 'operator-pack'
  | 'run-id'
  | 'content-addressed'

const props = defineProps<{
  concept: ConceptKey
  inline?: boolean
}>()

const CONCEPTS: Record<ConceptKey, { title: string; body: string; learnMore?: string }> = {
  'risk-green': {
    title: 'GREEN - Safe to Run',
    body: 'All feasibility checks pass. The operation can proceed without review. G-code export is enabled.',
    learnMore: 'GREEN means the CAM parameters are within safe operating ranges for the tool and material.',
  },
  'risk-yellow': {
    title: 'YELLOW - Review Required',
    body: 'One or more warnings detected. Review the warnings before proceeding. Override is required to export.',
    learnMore:
      'YELLOW operations may succeed but carry additional risk. An operator must acknowledge the warnings.',
  },
  'risk-red': {
    title: 'RED - Blocked',
    body: 'Safety violation detected. The operation cannot proceed. Fix the parameters to continue.',
    learnMore:
      'RED blocks dangerous operations that could damage the tool, material, or machine. No override is possible.',
  },
  override: {
    title: 'Override',
    body: 'An operator has acknowledged YELLOW warnings and authorized the operation to proceed.',
    learnMore:
      'Overrides are logged in the audit trail with the reason provided. They do not bypass safety checks.',
  },
  'audit-trail': {
    title: 'Audit Trail',
    body: 'Immutable record of all decisions, overrides, and operations. Cannot be modified after creation.',
    learnMore:
      'Every run creates a permanent record. This enables post-incident analysis and accountability.',
  },
  feasibility: {
    title: 'Feasibility Check',
    body: 'Pre-CAM validation of parameters against 22 safety rules (F001-F029).',
    learnMore:
      'Feasibility runs before any G-code generation. Rules check tool geometry, feeds/speeds, and material constraints.',
  },
  'operator-pack': {
    title: 'Operator Pack',
    body: 'ZIP bundle containing all artifacts for a run: G-code, DXF, manifest, and feasibility report.',
    learnMore:
      'The Operator Pack is the deliverable for CNC operators. It includes everything needed to run the job.',
  },
  'run-id': {
    title: 'Run ID',
    body: 'Unique identifier for each manufacturing run. Format: run_{timestamp}_{hash}',
    learnMore:
      'Run IDs are deterministic and content-addressed. The same inputs will produce the same run ID.',
  },
  'content-addressed': {
    title: 'Content-Addressed Storage',
    body: 'Artifacts stored by SHA256 hash. Same content = same hash = same file.',
    learnMore: 'Content addressing ensures integrity and enables deduplication. Files are immutable once stored.',
  },
}

const content = computed(() => CONCEPTS[props.concept] || CONCEPTS['feasibility'])

import { computed } from 'vue'
</script>

<template>
  <span
    class="rmos-tooltip"
    :class="{ inline }"
  >
    <span
      class="tooltip-trigger"
      tabindex="0"
    >
      <slot>
        <span class="help-icon">?</span>
      </slot>
    </span>
    <span
      class="tooltip-content"
      role="tooltip"
    >
      <strong class="tooltip-title">{{ content.title }}</strong>
      <span class="tooltip-body">{{ content.body }}</span>
      <span
        v-if="content.learnMore"
        class="tooltip-learn"
      >{{ content.learnMore }}</span>
    </span>
  </span>
</template>

<style scoped>
.rmos-tooltip {
  position: relative;
  display: inline-block;
}

.rmos-tooltip.inline {
  display: inline;
}

.tooltip-trigger {
  cursor: help;
}

.help-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  font-size: 0.625rem;
  font-weight: 700;
  color: #6b7280;
  background: #e5e7eb;
  border-radius: 50%;
  vertical-align: middle;
}

.tooltip-content {
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  padding: 0.75rem;
  background: #1f2937;
  color: #f9fafb;
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.tooltip-content::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #1f2937;
}

.tooltip-trigger:hover + .tooltip-content,
.tooltip-trigger:focus + .tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tooltip-title {
  font-weight: 600;
  color: #f9fafb;
}

.tooltip-body {
  color: #d1d5db;
}

.tooltip-learn {
  font-size: 0.75rem;
  color: #9ca3af;
  padding-top: 0.5rem;
  border-top: 1px solid #374151;
}
</style>
