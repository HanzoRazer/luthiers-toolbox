<script setup lang="ts">
import type { WorkflowDiagnostic } from '@/types/workflow'
import GateBadge from './GateBadge.vue'
import SectionLabel from './SectionLabel.vue'
import styles from './workflow.module.css'

defineProps<{
  diagnostic: WorkflowDiagnostic
}>()
</script>

<template>
  <div :class="[styles.diagnosticCard, styles[diagnostic.gate]]">
    <div :class="styles.diagnosticCardHeader">
      <GateBadge :gate="diagnostic.gate" />
      <span v-if="diagnostic.confidence" :class="styles.diagnosticCardConfidence">
        {{ Math.round(diagnostic.confidence * 100) }}% confidence
      </span>
    </div>

    <p :class="styles.diagnosticCardMessage">{{ diagnostic.message }}</p>

    <template v-if="diagnostic.probable_causes?.length">
      <SectionLabel text="Probable Causes" />
      <ul :class="styles.causesList">
        <li v-for="cause in diagnostic.probable_causes" :key="cause">{{ cause }}</li>
      </ul>
    </template>

    <template v-if="diagnostic.recommended_checks?.length">
      <SectionLabel text="Recommended Checks" />
      <ul :class="styles.checksList">
        <li v-for="check in diagnostic.recommended_checks" :key="check">{{ check }}</li>
      </ul>
    </template>

    <template v-if="diagnostic.recommended_actions?.length">
      <SectionLabel text="Recommended Actions" />
      <ul :class="styles.actionsList">
        <li v-for="action in diagnostic.recommended_actions" :key="action">{{ action }}</li>
      </ul>
    </template>
  </div>
</template>
