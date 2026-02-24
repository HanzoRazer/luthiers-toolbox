<template>
  <div :class="styles.advisorySection">
    <div :class="styles.advisoryHead">
      <h3>Advisory Explanation</h3>
      <div :class="styles.advisoryActions">
        <button
          :class="buttons.btnSm"
          :disabled="isExplaining"
          @click="$emit('generate', false)"
        >
          {{ hasAttachment ? 'Refresh Advisory' : 'Generate Advisory' }}
        </button>
        <button
          :class="buttons.btnSm"
          :disabled="isExplaining"
          title="Regenerate even if one exists"
          @click="$emit('generate', true)"
        >
          Regenerate (force)
        </button>
      </div>
    </div>
    <div
      v-if="error"
      :class="styles.advisoryError"
    >
      {{ error }}
    </div>
    <div
      v-else-if="isExplaining"
      :class="styles.advisoryLoading"
    >
      Generating advisory explanation…
    </div>

    <div
      v-if="explanation"
      :class="styles.advisoryBox"
    >
      <div :class="styles.advisorySummary">
        {{ explanation.summary }}
      </div>
      <div
        v-if="explanation.operator_notes?.length"
        :class="styles.advisorySubsection"
      >
        <h4>Operator Notes</h4>
        <ul>
          <li
            v-for="(n, idx) in explanation.operator_notes"
            :key="idx"
          >
            {{ n }}
          </li>
        </ul>
      </div>
      <div
        v-if="explanation.suggested_actions?.length"
        :class="styles.advisorySubsection"
      >
        <h4>Suggested Actions</h4>
        <ul>
          <li
            v-for="(a, idx) in explanation.suggested_actions"
            :key="idx"
          >
            {{ a }}
          </li>
        </ul>
      </div>
      <div :class="styles.advisoryDisclaimer">
        {{ explanation.disclaimer }}
      </div>
    </div>
    <div
      v-else-if="hasAttachment"
      :class="styles.advisoryPlaceholder"
    >
      assistant_explanation.json attached (sha: <code>{{ attachmentSha?.slice(0, 12) }}</code>…)
      — click "Refresh Advisory" to load it.
    </div>
    <div
      v-else
      :class="styles.advisoryEmpty"
    >
      No advisory explanation generated for this run.
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from '../RmosRunViewerView.module.css'
import { buttons } from '@/styles/shared'

export interface AssistantExplanation {
  summary?: string | null
  operator_notes?: string[] | null
  suggested_actions?: string[] | null
  disclaimer?: string | null
}

defineProps<{
  isExplaining: boolean
  error: string | null
  explanation: AssistantExplanation | null
  hasAttachment: boolean
  attachmentSha?: string
}>()

defineEmits<{
  generate: [force: boolean]
}>()
</script>
