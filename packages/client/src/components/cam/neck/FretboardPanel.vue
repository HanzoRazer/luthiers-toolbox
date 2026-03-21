<script setup lang="ts">
import { useNeckStore } from '@/stores/neck'

const store = useNeckStore()
const { fretboard } = store

function set<K extends keyof typeof fretboard.spec>(k: K, v: any) {
  fretboard.setSpec(k, v)
  if (k === 'nutWidthMm')    store.syncNutWidth(v)
  if (k === 'scaleLengthMm') store.syncScaleLength(v)
  if (k === 'fretCount')     store.syncFretCount(v)
}

// Key frets to display in the station table
const KEY_FRETS = [0, 1, 3, 5, 7, 9, 12, 15, 17, 19, 22]
</script>

<template>
  <div class="panel-body">

    <div class="sec">
      <div class="sec-lbl">Radius type</div>
      <div class="opt-grid">
        <div class="opt" :class="{ on: fretboard.spec.radiusType === 'single' }"
          @click="set('radiusType', 'single')">
          Single<br><span class="opt-sub">Constant</span>
        </div>
        <div class="opt" :class="{ on: fretboard.spec.radiusType === 'compound' }"
          @click="set('radiusType', 'compound')">
          Compound<br><span class="opt-sub">Conical</span>
        </div>
      </div>
      <div class="param-row">
        <span class="param-name">Nut radius</span>
        <input class="param-slider" type="range" min="7.25" max="20" step=".25"
          :value="fretboard.spec.r1Inch"
          @input="set('r1Inch', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ fretboard.spec.r1Inch }}"</span>
      </div>
      <div class="param-row" :class="{ muted: fretboard.spec.radiusType === 'single' }">
        <span class="param-name">Body radius</span>
        <input class="param-slider" type="range" min="12" max="20" step=".25"
          :value="fretboard.spec.r2Inch"
          :disabled="fretboard.spec.radiusType === 'single'"
          @input="set('r2Inch', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ fretboard.spec.r2Inch }}"</span>
      </div>
    </div>

    <div class="sec">
      <div class="sec-lbl">Board geometry</div>
      <div class="param-row">
        <span class="param-name">Board thickness</span>
        <input class="param-slider" type="range" min="4" max="8" step=".25"
          :value="fretboard.spec.thicknessMm"
          @input="set('thicknessMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ fretboard.spec.thicknessMm.toFixed(2) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Width @ 12th</span>
        <input class="param-slider" type="range" min="48" max="68" step=".5"
          :value="fretboard.spec.width12Mm"
          @input="set('width12Mm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ fretboard.spec.width12Mm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
    </div>

    <div class="sec">
      <div class="sec-lbl">CNC toolpath</div>
      <div class="param-row">
        <span class="param-name">Ball-nose Ø</span>
        <input class="param-slider" type="range" min="3" max="12" step=".5"
          :value="fretboard.spec.ballNoseMm"
          @input="set('ballNoseMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ fretboard.spec.ballNoseMm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Step-over</span>
        <input class="param-slider" type="range" min="5" max="40" step="1"
          :value="fretboard.spec.stepoverPct"
          @input="set('stepoverPct', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ fretboard.spec.stepoverPct }}</span>
        <span class="param-unit">%</span>
      </div>
    </div>

    <!-- Derived -->
    <div class="sec">
      <div class="sec-lbl">Derived</div>
      <div class="info-row"><span class="info-k">Crown @ nut</span><span class="info-v">{{ fretboard.derived.crownNut }} mm</span></div>
      <div class="info-row"><span class="info-k">Crown @ 12th</span><span class="info-v">{{ fretboard.derived.crown12 }} mm</span></div>
      <div class="info-row"><span class="info-k">Crown @ last</span><span class="info-v">{{ fretboard.derived.crownLast }} mm</span></div>
      <div class="info-row"><span class="info-k">Passes @ last</span><span class="info-v">{{ fretboard.derived.totalPasses }}</span></div>
      <div class="info-row"><span class="info-k">Step-over</span><span class="info-v">{{ fretboard.derived.stepoverMm }} mm</span></div>
      <div class="info-row"><span class="info-k">Nut slot E1</span><span class="info-v">{{ fretboard.derived.nutSlotDepthE1 }} mm</span></div>
      <div class="info-row"><span class="info-k">Nut slot E6</span><span class="info-v">{{ fretboard.derived.nutSlotDepthE6 }} mm</span></div>
    </div>

    <!-- Fret station table -->
    <div class="sec">
      <div class="sec-lbl">Fret stations</div>
      <table class="fret-table">
        <thead>
          <tr><th>Fret</th><th>r"</th><th>Crown</th><th>Width</th></tr>
        </thead>
        <tbody>
          <tr v-for="st in fretboard.fretStations.filter(s => KEY_FRETS.includes(s.fret))" :key="st.fret">
            <td>{{ st.fret === 0 ? 'Nut' : st.fret }}</td>
            <td>{{ st.radiusInch.toFixed(2) }}"</td>
            <td>{{ st.crownMm.toFixed(3) }}</td>
            <td>{{ st.widthMm.toFixed(1) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Gates -->
    <div class="sec" style="border-bottom:none">
      <div class="sec-lbl">Gates</div>
      <div v-for="g in fretboard.gates" :key="g.key" class="gate-item" :class="g.status">
        <span class="gate-dot"></span><span class="gate-txt">{{ g.label }}</span>
      </div>
    </div>

  </div>
</template>

<style scoped>
.panel-body { display:flex; flex-direction:column; }
.opt-grid   { display:grid; grid-template-columns:1fr 1fr; gap:3px; margin-bottom:7px; }
.opt-sub    { font-size:7px; color:var(--dim3); }
.muted      { opacity:.4; pointer-events:none; }
.info-row   { display:flex; justify-content:space-between; margin-bottom:3px; }
.info-k     { font-size:9px; color:var(--dim); }
.info-v     { font-size:9px; color:var(--v1); }
.fret-table { width:100%; border-collapse:collapse; font-size:8px; }
.fret-table th { text-align:right; color:var(--dim3); font-weight:normal; padding:2px 4px; border-bottom:1px solid var(--w2); }
.fret-table td { text-align:right; padding:2px 4px; color:var(--dim); border-bottom:1px solid var(--w1); }
.fret-table td:first-child { color:var(--br2); text-align:left; }
.fret-table tr:hover td { background:var(--w2); }
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
