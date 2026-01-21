<script setup lang="ts">
/**
 * WhyPanel.vue - Reusable "Why this decision?" panel
 *
 * Takes the explanation data from the run and displays:
 * - Summary of the decision
 * - List of triggered rules with level and summary
 * - Override reason if present
 */
import { computed } from "vue"

type TriggeredRule = {
  rule_id: string
  level?: string
  summary?: string
  details?: Record<string, any>
}

const props = defineProps<{
  explanation?: {
    risk_level?: string
    summary?: string
    triggered_rules?: TriggeredRule[]
    override_reason?: string | null
  } | null
}>()

const rules = computed(() => props.explanation?.triggered_rules ?? [])
</script>

<template>
  <div class="why-panel">
    <div class="why-header">Why this decision?</div>
    <div class="why-summary">
      {{ explanation?.summary || "No explanation available." }}
    </div>

    <div v-if="rules.length" class="rules-list">
      <div
        v-for="r in rules"
        :key="r.rule_id"
        class="rule-row"
      >
        <div class="rule-header">
          <div class="rule-id">{{ r.rule_id }}</div>
          <div v-if="r.level" class="rule-level" :data-level="r.level?.toLowerCase()">
            {{ r.level }}
          </div>
        </div>
        <div class="rule-summary">{{ r.summary || "Rule triggered." }}</div>
      </div>
    </div>

    <div v-if="explanation?.override_reason" class="override-box">
      <div class="override-title">Override applied</div>
      <div class="override-reason">{{ explanation.override_reason }}</div>
    </div>
  </div>
</template>

<style scoped>
.why-panel {
  margin-top: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #fff;
  padding: 0.75rem;
}

.why-header {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
}

.why-summary {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #64748b;
}

.rules-list {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rule-row {
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  padding: 0.5rem;
}

.rule-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.rule-id {
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
  color: #64748b;
}

.rule-level {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.rule-level[data-level="red"] {
  background: #fee2e2;
  color: #991b1b;
}

.rule-level[data-level="yellow"] {
  background: #fef3c7;
  color: #92400e;
}

.rule-level[data-level="green"] {
  background: #d1fae5;
  color: #065f46;
}

.rule-summary {
  font-size: 0.875rem;
  color: #334155;
  margin-top: 0.25rem;
}

.override-box {
  margin-top: 0.75rem;
  border: 1px solid #fcd34d;
  background: #fefce8;
  border-radius: 0.375rem;
  padding: 0.5rem;
}

.override-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #92400e;
}

.override-reason {
  font-size: 0.8125rem;
  color: #713f12;
  margin-top: 0.25rem;
}
</style>
