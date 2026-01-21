<script setup lang="ts">
import { computed, ref, watch } from "vue"

type ComparePayload = any

const props = defineProps<{
  /** The run currently being viewed (typically from /rmos/runs/:id route) */
  currentRunId: string
  /** Optional default for the "other" run id */
  defaultOtherRunId?: string | null
}>()

const otherRunId = ref<string>((props.defaultOtherRunId || "").trim())
const isComparing = ref(false)
const error = ref<string | null>(null)
const compare = ref<ComparePayload | null>(null)
const showDeep = ref(false)

watch(
  () => props.defaultOtherRunId,
  (v) => {
    if (!otherRunId.value) otherRunId.value = String(v || "").trim()
  }
)

const canCompare = computed(() => {
  const a = String(props.currentRunId || "").trim()
  const b = String(otherRunId.value || "").trim()
  return !!a && !!b && !isComparing.value
})

const summary = computed(() => compare.value?.summary ?? null)
const decision = computed(() => compare.value?.decision_diff ?? null)
const feasibility = computed(() => compare.value?.feasibility_diff ?? null)
const paramDiff = computed<Record<string, [any, any]>>(() => compare.value?.param_diff ?? {})
const paramRows = computed(() => {
  const obj = paramDiff.value || {}
  return Object.keys(obj)
    .sort()
    .map((k) => ({ key: k, a: obj[k]?.[0], b: obj[k]?.[1] }))
})

function pillLabel(k: string) {
  const map: Record<string, string> = {
    risk_changed: "Risk changed",
    blocking_changed: "Block reason changed",
    feasibility_changed: "Feasibility changed",
    cam_changed: "CAM changed",
    gcode_changed: "G-code changed",
    attachments_changed: "Attachments changed",
    override_changed: "Override changed",
  }
  return map[k] ?? k
}

function clear() {
  compare.value = null
  error.value = null
  showDeep.value = false
}

function swapRuns() {
  const a = String(props.currentRunId || "").trim()
  const b = String(otherRunId.value || "").trim()
  otherRunId.value = a
  // swap meaningfully: caller typically "current" is fixed; this swap is just convenience
  // If you want true swap semantics, wire currentRunId from route param to a local ref.
}

async function runCompare() {
  const a = String(props.currentRunId || "").trim()
  const b = String(otherRunId.value || "").trim()
  if (!a || !b) return

  isComparing.value = true
  error.value = null
  compare.value = null
  showDeep.value = false

  try {
    const resp = await fetch(`/api/rmos/runs_v2/compare/${encodeURIComponent(a)}/${encodeURIComponent(b)}`)
    if (!resp.ok) {
      let msg = `Compare failed (HTTP ${resp.status})`
      try {
        const j = await resp.json()
        if (j?.detail) msg = String(j.detail)
      } catch {}
      throw new Error(msg)
    }
    compare.value = await resp.json()
  } catch (e: any) {
    error.value = e?.message || "Failed to compare runs."
  } finally {
    isComparing.value = false
  }
}
</script>

<template>
  <div class="card">
    <div class="head">
      <div>
        <h3>Compare runs</h3>
        <div class="muted">
          Compare the current run against any other run id.
        </div>
      </div>
    </div>

    <div class="row">
      <div class="field">
        <label>Current</label>
        <div class="mono pill">
          {{ currentRunId }}
        </div>
      </div>
      <div class="field grow">
        <label>Other run id</label>
        <input
          v-model="otherRunId"
          class="input mono"
          placeholder="run_..."
          spellcheck="false"
          autocomplete="off"
        >
      </div>
      <div class="btns">
        <button
          class="btn"
          :disabled="!canCompare"
          @click="runCompare"
        >
          {{ isComparing ? "Comparing…" : "Compare" }}
        </button>
        <button
          class="btn secondary"
          :disabled="!compare && !error"
          @click="clear"
        >
          Clear
        </button>
      </div>
    </div>

    <div
      v-if="error"
      class="error"
    >
      {{ error }}
    </div>

    <div
      v-else-if="compare"
      class="compare"
    >
      <div
        v-if="summary"
        class="pillbar"
      >
        <template
          v-for="(v, k) in summary"
          :key="k"
        >
          <span
            v-if="v"
            class="pill ok"
          >{{ pillLabel(String(k)) }}</span>
        </template>
        <span
          v-if="Object.values(summary).every((x:any)=>!x)"
          class="pill"
        >No changes detected</span>
      </div>

      <div
        v-if="decision"
        class="section"
      >
        <div class="title">
          Decision
        </div>
        <div class="kv">
          <div class="k">
            Risk
          </div>
          <div class="v">
            <span class="pill mono">{{ decision.before?.risk_level }}</span>
            <span class="muted">→</span>
            <span class="pill mono">{{ decision.after?.risk_level }}</span>
          </div>
        </div>
        <div
          v-if="decision.before?.block_reason || decision.after?.block_reason"
          class="kv"
        >
          <div class="k">
            Block reason
          </div>
          <div class="v mono">
            <span class="muted">{{ decision.before?.block_reason || "—" }}</span>
            <span class="muted">→</span>
            <span class="muted">{{ decision.after?.block_reason || "—" }}</span>
          </div>
        </div>
      </div>

      <div
        v-if="feasibility"
        class="section"
      >
        <div class="title">
          Feasibility rules
        </div>
        <div class="kv">
          <div class="k">
            Added
          </div>
          <div class="v">
            <span
              v-if="(feasibility.rules_added||[]).length===0"
              class="muted"
            >—</span>
            <span
              v-for="rid in (feasibility.rules_added||[])"
              :key="rid"
              class="pill ok mono"
            >{{ rid }}</span>
          </div>
        </div>
        <div class="kv">
          <div class="k">
            Removed
          </div>
          <div class="v">
            <span
              v-if="(feasibility.rules_removed||[]).length===0"
              class="muted"
            >—</span>
            <span
              v-for="rid in (feasibility.rules_removed||[])"
              :key="rid"
              class="pill mono"
            >{{ rid }}</span>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="title">
          Parameter changes
        </div>
        <div
          v-if="paramRows.length === 0"
          class="muted"
        >
          No parameter changes detected.
        </div>
        <div
          v-else
          class="table"
        >
          <div class="tr head">
            <div>Field</div><div>Previous</div><div>Current</div>
          </div>
          <div
            v-for="row in paramRows"
            :key="row.key"
            class="tr"
          >
            <div class="mono k">
              {{ row.key }}
            </div>
            <div class="cell mono">
              {{ row.a ?? "—" }}
            </div>
            <div class="cell mono">
              {{ row.b ?? "—" }}
            </div>
          </div>
        </div>
      </div>

      <button
        class="toggle"
        @click="showDeep = !showDeep"
      >
        <span class="chev">{{ showDeep ? "▾" : "▸" }}</span>
        <span>Show deep diffs</span>
        <span class="muted">(engineer)</span>
      </button>
      <pre
        v-if="showDeep"
        class="code"
      >{{ JSON.stringify(compare, null, 2) }}</pre>
    </div>
  </div>
</template>

<style scoped>
.card { border: 1px solid #eee; border-radius: 16px; padding: 14px; background: #fafafa; }
.head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
h3 { margin: 0; font-size: 16px; }
.muted { color: #666; font-size: 12px; }
.row { display: flex; gap: 12px; align-items: end; flex-wrap: wrap; margin-top: 10px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.grow { flex: 1; min-width: 260px; }
label { font-size: 12px; color: #666; }
.input { border: 1px solid #e6e6e6; border-radius: 12px; padding: 10px 12px; background: #fff; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.btns { display: flex; gap: 10px; }
.btn { border: 1px solid #dcdcdc; border-radius: 999px; padding: 8px 12px; background: #fff; cursor: pointer; font-size: 12px; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn.secondary { background: #f6f6f6; }
.error { margin-top: 10px; color: #b00020; }
.compare { margin-top: 12px; }
.pillbar { display: flex; flex-wrap: wrap; gap: 8px; }
.pill { padding: 4px 10px; border: 1px solid #eaeaea; border-radius: 999px; background: #fff; font-size: 12px; }
.pill.ok { border-color: #d7f0dc; background: #f2fbf4; }
.section { margin-top: 12px; }
.title { font-weight: 700; font-size: 13px; margin-bottom: 8px; }
.kv { display: grid; grid-template-columns: 130px 1fr; gap: 10px; margin: 6px 0; }
.k { font-weight: 600; }
.table { display: grid; gap: 8px; margin-top: 8px; }
.tr { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; align-items: start; }
.tr.head { color: #666; font-size: 12px; }
.cell { background: #fff; border: 1px solid #eee; border-radius: 12px; padding: 8px; word-break: break-word; font-size: 12px; }
.toggle { width: 100%; text-align: left; margin-top: 12px; padding: 10px 12px; background: #fff; border: 1px solid #eee; border-radius: 14px; cursor: pointer; display: flex; gap: 10px; align-items: center; }
.chev { width: 18px; display: inline-block; }
.code { margin-top: 10px; white-space: pre-wrap; word-break: break-word; font-size: 12px; background: #fff; border: 1px solid #eee; border-radius: 12px; padding: 10px; }
</style>
