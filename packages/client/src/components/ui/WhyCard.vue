<script setup lang="ts">
/**
 * WhyCard.vue - "Why?" affordance for decisions
 *
 * Shows triggered feasibility rules with explanation.
 * Always visible if rules exist, toggleable for details.
 *
 * Data sources (already exist):
 * - decision
 * - feasibility.rules_triggered
 * - explainRule() from feasibilityRuleRegistry
 */

import { ref, computed } from 'vue'
import { explainRule } from '@/lib/feasibilityRuleRegistry'

export interface TriggeredRule {
  rule_id: string
  level: string
  summary: string
  operator_hint?: string
}

const props = defineProps<{
  riskLevel: string
  rulesTriggered?: string[]
  overrideReason?: string | null
}>()

const expanded = ref(true)

const rules = computed<TriggeredRule[]>(() => {
  if (!Array.isArray(props.rulesTriggered)) return []
  return props.rulesTriggered
    .map((id) => String(id).trim().toUpperCase())
    .filter(Boolean)
    .map((rid) => explainRule(rid))
})

const hasRules = computed(() => rules.value.length > 0)

const summaryText = computed(() => {
  const n = rules.value.length
  if (n === 0) return null
  return `${n} feasibility rule${n === 1 ? '' : 's'} triggered`
})
</script>

<template>
  <div v-if="hasRules" class="why-card">
    <button class="why-header" @click="expanded = !expanded" type="button">
      <span class="why-icon">{{ expanded ? '▾' : '▸' }}</span>
      <span class="why-title">Why {{ riskLevel }}?</span>
      <span v-if="summaryText" class="why-summary">{{ summaryText }}</span>
    </button>

    <div v-if="expanded" class="why-body">
      <ul class="rule-list">
        <li v-for="r in rules" :key="r.rule_id" class="rule-item">
          <span class="rule-pill" :data-level="r.level.toLowerCase()">{{ r.level }}</span>
          <span class="rule-id">{{ r.rule_id }}</span>
          <span class="rule-summary">{{ r.summary }}</span>
          <span v-if="r.operator_hint" class="rule-hint">💡 {{ r.operator_hint }}</span>
        </li>
      </ul>

      <div v-if="overrideReason" class="override-note">
        <strong>Override reason:</strong> {{ overrideReason }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.why-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  margin: 0.5rem 0;
  overflow: hidden;
}

.why-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.625rem 0.875rem;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  font-size: 0.875rem;
}

.why-header:hover {
  background: #f1f5f9;
}

.why-icon {
  color: #64748b;
  font-size: 0.75rem;
  width: 1rem;
}

.why-title {
  font-weight: 600;
  color: #334155;
}

.why-summary {
  color: #64748b;
  font-size: 0.8125rem;
}

.why-body {
  padding: 0 0.875rem 0.75rem;
}

.rule-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.rule-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0;
  border-top: 1px solid #e2e8f0;
  font-size: 0.8125rem;
}

.rule-pill {
  font-size: 0.625rem;
  font-weight: 700;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  text-transform: uppercase;
}

.rule-pill[data-level="yellow"] {
  background: #fef3c7;
  color: #92400e;
}

.rule-pill[data-level="red"] {
  background: #fee2e2;
  color: #991b1b;
}

.rule-pill[data-level="green"] {
  background: #d1fae5;
  color: #065f46;
}

.rule-id {
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
  color: #64748b;
}

.rule-summary {
  color: #334155;
}

.rule-hint {
  flex-basis: 100%;
  font-size: 0.75rem;
  color: #64748b;
  padding-left: 1.5rem;
}

.override-note {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fefce8;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
  color: #713f12;
}
</style>
