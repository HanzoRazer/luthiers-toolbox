<script setup lang="ts">
import { useNeckStore } from '@/stores/neck'
import type { TaperType, SpacingType } from '@/composables/useNeckTaper'

const store = useNeckStore()
const { taper } = store

function setTaper<K extends keyof typeof taper.spec>(k: K, v: any) {
  taper.setSpec(k, v)
  if (k === 'nutWidthMm')   store.syncNutWidth(v)
  if (k === 'scaleLengthMm') store.syncScaleLength(v)
  if (k === 'fretCount')     store.syncFretCount(v)
}

const TAPER_OPTS: { val: TaperType; label: string; sub: string }[] = [
  { val: 'linear',  label: 'Linear',  sub: 'Constant rate' },
  { val: 'convex',  label: 'Convex',  sub: 'Bell — wider mid' },
  { val: 'concave', label: 'Concave', sub: 'Slow → fast' },
  { val: 'stepped', label: 'Stepped', sub: 'Two-rate split' },
]

const SPACING_OPTS: { val: SpacingType; label: string; sub: string }[] = [
  { val: 'equal-edge',   label: 'Edge equal',   sub: 'String to edge' },
  { val: 'equal-centre', label: 'Centre equal',  sub: 'C-C constant' },
  { val: 'fan',          label: 'Fan spread',   sub: 'Bridge-proportional' },
  { val: 'compound',     label: 'Compound',     sub: 'TOM style' },
]
</script>

<template>
  <div class="panel-body">

    <div class="sec">
      <div class="sec-lbl">Scale &amp; frets</div>
      <div class="param-row">
        <span class="param-name">Scale length</span>
        <input class="param-slider" type="range" min="610" max="660" step="1"
          :value="taper.spec.scaleLengthMm"
          @input="setTaper('scaleLengthMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.scaleLengthMm.toFixed(0) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Fret count</span>
        <input class="param-slider" type="range" min="19" max="24" step="1"
          :value="taper.spec.fretCount"
          @input="setTaper('fretCount', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.fretCount }}</span>
        <span class="param-unit"></span>
      </div>
    </div>

    <div class="sec">
      <div class="sec-lbl">Neck width taper</div>
      <div class="opt-grid">
        <div v-for="o in TAPER_OPTS" :key="o.val"
          class="opt" :class="{ on: taper.spec.taperType === o.val }"
          @click="setTaper('taperType', o.val)">
          {{ o.label }}<br><span class="opt-sub">{{ o.sub }}</span>
        </div>
      </div>
      <div class="param-row">
        <span class="param-name">Nut width</span>
        <input class="param-slider" type="range" min="38" max="48" step=".5"
          :value="taper.spec.nutWidthMm"
          @input="setTaper('nutWidthMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.nutWidthMm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Width @ 12th</span>
        <input class="param-slider" type="range" min="48" max="68" step=".5"
          :value="taper.spec.width12Mm"
          @input="setTaper('width12Mm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.width12Mm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Width @ last</span>
        <input class="param-slider" type="range" min="54" max="80" step=".5"
          :value="taper.spec.lastFretWidthMm"
          @input="setTaper('lastFretWidthMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.lastFretWidthMm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
    </div>

    <div class="sec">
      <div class="sec-lbl">String spacing</div>
      <div class="opt-grid">
        <div v-for="o in SPACING_OPTS" :key="o.val"
          class="opt" :class="{ on: taper.spec.spacingType === o.val }"
          @click="setTaper('spacingType', o.val)">
          {{ o.label }}<br><span class="opt-sub">{{ o.sub }}</span>
        </div>
      </div>
      <div class="param-row">
        <span class="param-name">String count</span>
        <input class="param-slider" type="range" min="6" max="8" step="1"
          :value="taper.spec.stringCount"
          @input="setTaper('stringCount', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.stringCount }}</span>
        <span class="param-unit"></span>
      </div>
      <div class="param-row">
        <span class="param-name">Edge margin nut</span>
        <input class="param-slider" type="range" min="2" max="5" step=".25"
          :value="taper.spec.edgeMarginNutMm"
          @input="setTaper('edgeMarginNutMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.edgeMarginNutMm.toFixed(2) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Bridge spacing</span>
        <input class="param-slider" type="range" min="48" max="68" step=".5"
          :value="taper.spec.bridgeSpacingMm"
          @input="setTaper('bridgeSpacingMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ taper.spec.bridgeSpacingMm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
    </div>

    <!-- Derived -->
    <div class="sec">
      <div class="sec-lbl">Derived</div>
      <div class="info-row"><span class="info-k">Taper rate</span><span class="info-v">{{ taper.derived.value.taperRateMmPerM }} mm/m</span></div>
      <div class="info-row"><span class="info-k">C-C @ nut</span><span class="info-v">{{ taper.derived.value.ccAtNut }} mm</span></div>
      <div class="info-row"><span class="info-k">C-C @ 12th</span><span class="info-v">{{ taper.derived.value.ccAt12 }} mm</span></div>
      <div class="info-row"><span class="info-k">Edge margin L</span><span class="info-v">{{ taper.derived.value.nutEdgeLeft }} mm</span></div>
      <div class="info-row"><span class="info-k">String spread</span><span class="info-v">+{{ taper.derived.value.totalStringSpread }} mm</span></div>
    </div>

    <!-- Gates -->
    <div class="sec" style="border-bottom:none">
      <div class="sec-lbl">Gates</div>
      <div v-for="g in taper.gates.value" :key="g.key" class="gate-item" :class="g.status">
        <span class="gate-dot"></span><span class="gate-txt">{{ g.label }}</span>
      </div>
    </div>

  </div>
</template>

<style scoped>
.panel-body { display:flex; flex-direction:column; }
.opt-grid   { display:grid; grid-template-columns:1fr 1fr; gap:3px; margin-bottom:7px; }
.opt-sub    { font-size:7px; color:var(--dim3); }
.info-row   { display:flex; justify-content:space-between; margin-bottom:3px; }
.info-k     { font-size:9px; color:var(--dim); }
.info-v     { font-size:9px; color:var(--v1); }
.gate-item  { display:flex; align-items:flex-start; gap:5px; padding:4px 6px; border-radius:2px; margin-bottom:3px; }
.gate-item.pass { background:rgba(90,184,106,.08); }
.gate-item.warn { background:rgba(184,112,32,.08); }
.gate-item.fail { background:rgba(200,64,48,.1); }
.gate-dot   { width:7px; height:7px; border-radius:50%; flex-shrink:0; margin-top:2px; }
.gate-item.pass .gate-dot { background:var(--green2); }
.gate-item.warn .gate-dot { background:var(--amber); }
.gate-item.fail .gate-dot { background:var(--red); }
.gate-txt   { font-size:8px; line-height:1.5; color:var(--dim); }
.gate-item.pass .gate-txt { color:var(--green2); }
.gate-item.warn .gate-txt { color:var(--amber); }
.gate-item.fail .gate-txt { color:#c84030; }
</style>
