<script setup lang="ts">
/**
 * RunCompareCard - Run-to-run comparison display
 * Extracted from DxfToGcodeView.vue
 */
import { computed, ref } from 'vue'

interface CompareResult {
  summary?: Record<string, boolean>
  decision_diff?: {
    before?: { risk_level?: string; block_reason?: string }
    after?: { risk_level?: string; block_reason?: string }
  }
  feasibility_diff?: {
    rules_added?: string[]
    rules_removed?: string[]
  }
  param_diff?: Record<string, [unknown, unknown]>
}

const props = defineProps<{
  compareResult: CompareResult | null
  compareError: string | null
  previousRunId: string | null
  currentRunId: string | null
}>()

const emit = defineEmits<{
  'clear': []
}>()

const showDeepCompare = ref(false)

const compareSummary = computed(() => props.compareResult?.summary ?? null)
const compareDecision = computed(() => props.compareResult?.decision_diff ?? null)
const compareFeasibility = computed(() => props.compareResult?.feasibility_diff ?? null)
const compareParamDiff = computed(() => props.compareResult?.param_diff ?? {})

const paramDiffRows = computed(() => {
  const obj = compareParamDiff.value || {}
  return Object.keys(obj).sort().map((k) => ({ key: k, a: obj[k]?.[0], b: obj[k]?.[1] }))
})

function pillLabel(k: string) {
  const map: Record<string, string> = {
    risk_changed: 'Risk changed',
    blocking_changed: 'Block reason changed',
    feasibility_changed: 'Feasibility changed',
    cam_changed: 'CAM changed',
    gcode_changed: 'G-code changed',
    attachments_changed: 'Attachments changed',
    override_changed: 'Override changed',
  }
  return map[k] ?? k
}
</script>

<template>
  <div class="compare-shell">
    <div class="compare-header-row">
      <h3>Compare with Previous Run</h3>
      <div class="muted">
        {{ previousRunId?.slice(0, 8) }}… → {{ currentRunId?.slice(0, 8) }}…
      </div>
      <button class="btn-clear" @click="emit('clear')">Clear</button>
    </div>

    <div v-if="compareError" class="compare-error">
      {{ compareError }}
    </div>

    <div v-else class="compare-content">
      <!-- Summary chips -->
      <div v-if="compareSummary" class="pill-row">
        <template v-for="(v, k) in compareSummary" :key="k">
          <span v-if="v" class="pill ok">{{ pillLabel(String(k)) }}</span>
        </template>
        <span
          v-if="Object.values(compareSummary).every((x: any) => !x)"
          class="pill muted"
        >
          No changes detected
        </span>
      </div>

      <!-- Decision -->
      <div v-if="compareDecision" class="compare-section">
        <div class="section-title">Decision</div>
        <div class="kv-row">
          <div class="kv-label">Risk</div>
          <div class="kv-value">
            <span class="pill">{{ compareDecision.before?.risk_level }}</span>
            <span class="arrow">→</span>
            <span class="pill">{{ compareDecision.after?.risk_level }}</span>
          </div>
        </div>
        <div
          v-if="compareDecision.before?.block_reason || compareDecision.after?.block_reason"
          class="kv-row"
        >
          <div class="kv-label">Block reason</div>
          <div class="kv-value muted">
            {{ compareDecision.before?.block_reason || '—' }}
            <span class="arrow">→</span>
            {{ compareDecision.after?.block_reason || '—' }}
          </div>
        </div>
      </div>

      <!-- Feasibility rules -->
      <div v-if="compareFeasibility" class="compare-section">
        <div class="section-title">Feasibility rules</div>
        <div class="kv-row">
          <div class="kv-label">Added</div>
          <div class="kv-value">
            <span v-if="(compareFeasibility.rules_added || []).length === 0" class="muted">—</span>
            <span
              v-for="rid in (compareFeasibility.rules_added || [])"
              :key="rid"
              class="pill ok"
            >{{ rid }}</span>
          </div>
        </div>
        <div class="kv-row">
          <div class="kv-label">Removed</div>
          <div class="kv-value">
            <span v-if="(compareFeasibility.rules_removed || []).length === 0" class="muted">—</span>
            <span
              v-for="rid in (compareFeasibility.rules_removed || [])"
              :key="rid"
              class="pill"
            >{{ rid }}</span>
          </div>
        </div>
      </div>

      <!-- Parameter changes -->
      <div class="compare-section">
        <div class="section-title">Parameter changes</div>
        <div v-if="paramDiffRows.length === 0" class="muted">
          No parameter changes detected.
        </div>
        <div v-else class="diff-grid">
          <div class="diff-row diff-head">
            <div>Field</div>
            <div>Previous</div>
            <div>Current</div>
          </div>
          <div v-for="row in paramDiffRows" :key="row.key" class="diff-row">
            <div class="k">{{ row.key }}</div>
            <div class="vcell">{{ row.a ?? '—' }}</div>
            <div class="vcell">{{ row.b ?? '—' }}</div>
          </div>
        </div>
      </div>

      <!-- Deep diff toggle -->
      <button class="compare-toggle" @click="showDeepCompare = !showDeepCompare">
        <span class="chev">{{ showDeepCompare ? '▾' : '▸' }}</span>
        <span>Show deep diffs</span>
        <span class="muted">(request/feasibility/decision/hashes/attachments)</span>
      </button>
      <pre v-if="showDeepCompare" class="code">{{ JSON.stringify(compareResult, null, 2) }}</pre>
    </div>
  </div>
</template>

<style scoped>
.compare-shell {
  margin-top: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  background: #fafafa;
  padding: 1rem;
}

.compare-header-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.compare-header-row h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.btn-clear {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.btn-clear:hover {
  background: #d1d5db;
}

.compare-error {
  color: #b91c1c;
  margin-top: 0.75rem;
}

.compare-content {
  margin-top: 0.75rem;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.pill {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: #e5e7eb;
  font-size: 0.75rem;
  font-weight: 500;
}

.pill.ok {
  background: #d1fae5;
  color: #065f46;
}

.pill.muted {
  background: #f3f4f6;
  color: #9ca3af;
}

.compare-section {
  margin-top: 1rem;
}

.section-title {
  font-weight: 700;
  font-size: 0.8125rem;
  margin-bottom: 0.5rem;
}

.kv-row {
  display: grid;
  grid-template-columns: 8rem 1fr;
  gap: 0.75rem;
  margin: 0.375rem 0;
  align-items: start;
}

.kv-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.kv-value {
  font-size: 0.8125rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.arrow {
  color: #9ca3af;
}

.muted {
  color: #9ca3af;
}

.diff-grid {
  display: grid;
  gap: 0.5rem;
}

.diff-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.75rem;
  align-items: start;
}

.diff-head {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.k {
  font-size: 0.75rem;
  font-weight: 500;
}

.vcell {
  font-size: 0.75rem;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 0.5rem;
  word-break: break-word;
}

.compare-toggle {
  width: 100%;
  text-align: left;
  margin-top: 1rem;
  padding: 0.625rem 0.875rem;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.875rem;
  cursor: pointer;
  display: flex;
  gap: 0.625rem;
  align-items: center;
  font-size: 0.8125rem;
}

.compare-toggle:hover {
  background: #f9fafb;
}

.chev {
  width: 1.125rem;
  display: inline-block;
}

.code {
  margin-top: 0.75rem;
  padding: 1rem;
  background: #1f2937;
  color: #f9fafb;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
