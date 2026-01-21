<template>
  <div class="why-panel">
    <div class="why-header">
      <h3>Why this is {{ riskLevel }}</h3>
      <div
        v-if="summaryText"
        class="why-summary"
      >
        {{ summaryText }}
      </div>
    </div>

    <ul
      v-if="triggeredRules.length"
      class="why-list"
    >
      <li
        v-for="r in triggeredRules"
        :key="r.rule_id"
        class="why-item"
      >
        <span
          class="rule-pill"
          :data-level="r.level"
        >{{ r.level }}</span>
        <span class="rule-id">{{ r.rule_id }}</span>
        <span class="rule-summary">{{ r.summary }}</span>
        <span
          v-if="r.operator_hint"
          class="rule-hint"
        >{{ r.operator_hint }}</span>
      </li>
    </ul>

    <div
      v-if="explanation?.text"
      class="why-text"
    >
      {{ explanation.text }}
    </div>

    <div
      v-if="showOverrideHint && riskLevel === 'YELLOW'"
      class="why-hint"
    >
      Operator Pack requires an override for YELLOW runs.
    </div>
    <div
      v-if="hasOverride"
      class="why-hint why-hint-ok"
    >
      Override recorded.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { explainRule } from '@/lib/feasibilityRuleRegistry'

const props = defineProps<{
  explanation?: {
    text?: string
    override_reason?: string
    rules_triggered?: string[]
  } | null
  riskLevel?: string
  rulesTriggered?: string[]
  showOverrideHint?: boolean
  hasOverride?: boolean
}>()

const riskLevel = computed(() => (props.riskLevel || '').toUpperCase())

const ruleIds = computed<string[]>(() => {
  const fromExplanation = props.explanation?.rules_triggered
  const fromProps = props.rulesTriggered
  const ids = fromExplanation || fromProps || []
  if (!Array.isArray(ids)) return []
  return ids.map((x: any) => String(x).trim().toUpperCase()).filter(Boolean)
})

const triggeredRules = computed(() => {
  return ruleIds.value.map((rid) => explainRule(rid))
})

const summaryText = computed(() => {
  if (ruleIds.value.length === 0) return null
  const levels = triggeredRules.value.map((r) => r.level)
  const hasRed = levels.includes('RED')
  const hasYellow = levels.includes('YELLOW')
  if (hasRed) return `${ruleIds.value.length} rule(s) triggered including blocking constraints`
  if (hasYellow) return `${ruleIds.value.length} warning(s) require review`
  return `${ruleIds.value.length} rule(s) triggered`
})
</script>

<style scoped>
.why-panel {
  background: var(--color-bg-secondary, #f8f9fa);
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: 8px;
  padding: 1rem;
}

.why-header {
  margin-bottom: 0.75rem;
}

.why-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
}

.why-summary {
  color: var(--color-text-muted, #6c757d);
  font-size: 0.875rem;
}

.why-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.why-item {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.875rem;
}

.rule-pill {
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.rule-pill[data-level="RED"] {
  background: #f8d7da;
  color: #842029;
}

.rule-pill[data-level="YELLOW"] {
  background: #fff3cd;
  color: #664d03;
}

.rule-pill[data-level="GREEN"] {
  background: #d1e7dd;
  color: #0f5132;
}

.rule-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6c757d);
}

.rule-summary {
  flex: 1;
}

.rule-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted, #6c757d);
  font-style: italic;
}

.why-text {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #dee2e6);
  font-size: 0.875rem;
}

.why-hint {
  margin-top: 0.75rem;
  padding: 0.5rem;
  background: #fff3cd;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #664d03;
}

.why-hint-ok {
  background: #d1e7dd;
  color: #0f5132;
}
</style>
