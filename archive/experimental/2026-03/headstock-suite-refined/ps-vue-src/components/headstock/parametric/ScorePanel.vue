<template>
  <div class="score-panel">

    <!-- Novelty -->
    <div class="sec">
      <div class="sec-ttl">Design score</div>
      <div class="nov-header">
        <span class="nov-val" :style="{ color: noveltyColor }">{{ result.novelty.score }}</span>
        <span class="nov-label">novelty</span>
      </div>
      <div class="nov-bar-bg">
        <div class="nov-bar-fg" :style="{ width: result.novelty.score + '%', background: noveltyColor }" />
      </div>
      <div class="nov-sub">{{ noveltySub }}</div>
    </div>

    <!-- Corpus proximity -->
    <div class="sec">
      <div class="sec-lbl">Corpus distance</div>
      <div v-for="[name, dist] in corpusEntries" :key="name" class="corpus-row">
        <span class="corp-name">{{ name }}</span>
        <div class="corp-bar-bg">
          <div class="corp-bar-fg" :style="{ width: corpusBarWidth(dist) + '%', background: CORPUS_COLORS[name] + '44' }" />
        </div>
        <span class="corp-val" :style="{ color: dist < 0.25 ? 'var(--ps-red)' : 'var(--ps-dim2)' }">
          {{ dist.toFixed(3) }}
        </span>
      </div>
    </div>

    <!-- Gates -->
    <div class="sec">
      <div class="sec-lbl">Manufacture gates</div>
      <div v-for="gate in result.gates" :key="gate.name" class="gate-item">
        <div class="gate-icon" :class="gate.pass">{{ GATE_ICONS[gate.pass] }}</div>
        <div class="gate-text">
          <div class="gate-name">{{ gate.name }}</div>
          <div class="gate-detail">{{ gate.detail }}</div>
        </div>
      </div>
    </div>

    <!-- Tool diameter -->
    <div class="sec">
      <div class="sec-lbl">Tool diameter</div>
      <div class="param-row">
        <input
          class="param-slider"
          type="range" min="0.5" max="6" step="0.5"
          :value="store.toolDia"
          @input="store.toolDia = +($event.target as HTMLInputElement).value"
        />
        <span class="param-val">{{ store.toolDia.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
    </div>

    <!-- Send button -->
    <div class="sec send-sec">
      <button class="send-btn" @click="emit('send')">Send to workspace →</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useHeadstockStore } from '@/stores/headstock'
import { useScoring } from '@/composables/useScoring'

const store = useHeadstockStore()
const { result, noveltyColor, gatesSummary } = useScoring(
  () => store.params,
  () => store.toolDia,
)

const CORPUS_COLORS: Record<string, string> = {
  'Les Paul':'#e8724a','Strat':'#5baae8','PRS':'#7a5ae8','Telecaster':'#5ec478','SG':'#e8c85a'
}
const GATE_ICONS = { pass:'✓', warn:'!', fail:'✗' }

const corpusEntries = computed(() =>
  Object.entries(result.value.novelty.corpusDists).sort((a, b) => a[1] - b[1])
)

const maxDist = computed(() => Math.max(...Object.values(result.value.novelty.corpusDists), 0.001))
const corpusBarWidth = (dist: number) => ((1 - dist / maxDist.value) * 100)

const noveltySub = computed(() => {
  const { minDist, closestTo } = result.value.novelty
  if (minDist < 0.15) return `Too close to ${closestTo} (d=${minDist.toFixed(3)})`
  if (minDist < 0.3)  return 'Derived — recognisable lineage'
  return 'Novel — clear distance from corpus'
})

const emit = defineEmits<{ send: [] }>()
</script>

<style scoped>
.score-panel { display: flex; flex-direction: column; overflow-y: auto; }
.sec { padding: 10px 13px 8px; border-bottom: 1px solid var(--ps-border2); }
.sec-lbl  { font-size: 8px; letter-spacing: 1.6px; text-transform: uppercase; color: var(--ps-brass3); margin-bottom: 6px; }
.sec-ttl  { font-family: var(--ps-serif); font-size: 11px; font-style: italic; color: var(--ps-brass2); margin-bottom: 8px; }

.nov-header { display: flex; align-items: baseline; gap: 8px; }
.nov-val    { font-size: 22px; font-family: var(--ps-serif); line-height: 1; transition: color .3s; }
.nov-label  { font-size: 9px; color: var(--ps-dim); }
.nov-bar-bg { height: 5px; background: var(--ps-surface2); border-radius: 3px; overflow: hidden; margin: 5px 0 3px; }
.nov-bar-fg { height: 100%; border-radius: 3px; transition: width .3s, background .3s; }
.nov-sub    { font-size: 9px; color: var(--ps-dim); }

.corpus-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.corp-name  { width: 70px; font-size: 9px; color: var(--ps-dim); }
.corp-bar-bg { flex: 1; height: 3px; background: var(--ps-surface2); border-radius: 2px; overflow: hidden; }
.corp-bar-fg { height: 100%; transition: width .25s; }
.corp-val   { width: 32px; text-align: right; font-size: 8px; }

.gate-item  { display: flex; align-items: flex-start; gap: 6px; margin-bottom: 5px; padding: 5px 6px; border-radius: 3px; background: var(--ps-surface2); }
.gate-icon  { width: 13px; height: 13px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 7px; flex-shrink: 0; margin-top: 1px; }
.gate-icon.pass { background: var(--ps-green); }
.gate-icon.warn { background: var(--ps-amber); }
.gate-icon.fail { background: var(--ps-red); }
.gate-name   { font-size: 9px; color: var(--ps-text); }
.gate-detail { font-size: 8px; color: var(--ps-dim); }

.param-row   { display: flex; align-items: center; gap: 6px; }
.param-slider { flex: 1; accent-color: var(--ps-brass); }
.param-val   { width: 30px; text-align: right; font-size: 10px; color: var(--ps-text); }
.param-unit  { font-size: 8px; color: var(--ps-dim2); }

.send-sec { margin-top: auto; border-bottom: none; }
.send-btn {
  width: 100%; padding: 8px 0; background: none;
  border: 1px solid var(--ps-brass3); border-radius: 3px;
  color: var(--ps-brass2); font-family: var(--ps-mono); font-size: 9px;
  letter-spacing: .5px; text-transform: uppercase; cursor: pointer;
  transition: all .12s;
}
.send-btn:hover { background: var(--ps-brass3); color: var(--ps-bg); }
</style>
