<script setup lang="ts">
import { useNeckStore } from '@/stores/neck'
import type { VoluteType } from '@/composables/useHeadstockTransition'

const store = useNeckStore()
const { transition } = store

function set<K extends keyof typeof transition.spec>(k: K, v: any) {
  transition.setSpec(k, v)
  if (k === 'pitchAngleDeg') store.syncPitchAngle(v as number)
  if (k === 'neckDepthMm')   store.syncNeckDepth(v as number)
}

const VOLUTE_OPTS: { val: VoluteType; label: string; sub: string }[] = [
  { val: 'none',    label: 'None',    sub: 'Flat / Fender' },
  { val: 'gibson',  label: 'Gibson',  sub: 'Smooth Gaussian' },
  { val: 'martin',  label: 'Martin',  sub: 'Diamond pyramid' },
  { val: 'custom',  label: 'Custom',  sub: 'User-defined' },
  { val: 'scallop', label: 'Scallop', sub: 'Concave hollow' },
]

const showMartinParams = () => transition.spec.voluteType === 'martin'
const showGaussianParams = () => ['gibson','custom','scallop'].includes(transition.spec.voluteType)
</script>

<template>
  <div class="panel-body">

    <!-- Headstock type -->
    <div class="sec">
      <div class="sec-lbl">Headstock type</div>
      <div class="opt-grid">
        <div class="opt" :class="{ on: transition.spec.headstockType === 'angled' }"
          @click="set('headstockType', 'angled')">
          Angled<br><span class="opt-sub">Gibson / PRS</span>
        </div>
        <div class="opt" :class="{ on: transition.spec.headstockType === 'flat' }"
          @click="set('headstockType', 'flat')">
          Flat<br><span class="opt-sub">Fender</span>
        </div>
      </div>
      <div class="param-row" :class="{ muted: transition.spec.headstockType === 'flat' }">
        <span class="param-name">Pitch angle</span>
        <input class="param-slider" type="range" min="0" max="17" step=".5"
          :value="transition.spec.pitchAngleDeg"
          :disabled="transition.spec.headstockType === 'flat'"
          @input="set('pitchAngleDeg', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.pitchAngleDeg }}°</span>
      </div>
      <div class="param-row">
        <span class="param-name">HS thickness</span>
        <input class="param-slider" type="range" min="10" max="18" step=".5"
          :value="transition.spec.hsThicknessMm"
          @input="set('hsThicknessMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.hsThicknessMm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Neck depth</span>
        <input class="param-slider" type="range" min="18" max="26" step=".25"
          :value="transition.spec.neckDepthMm"
          @input="set('neckDepthMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.neckDepthMm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
    </div>

    <!-- Blend zone -->
    <div class="sec">
      <div class="sec-lbl">Blend zone</div>
      <div class="param-row">
        <span class="param-name">Length</span>
        <input class="param-slider" type="range" min="10" max="40" step="1"
          :value="transition.spec.blendLengthMm"
          @input="set('blendLengthMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.blendLengthMm.toFixed(0) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Centre offset</span>
        <input class="param-slider" type="range" min="-15" max="15" step="1"
          :value="transition.spec.blendCentreMm"
          @input="set('blendCentreMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.blendCentreMm > 0 ? '+' : '' }}{{ transition.spec.blendCentreMm }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Tension</span>
        <input class="param-slider" type="range" min="0" max="100" step="5"
          :value="transition.spec.blendTension"
          @input="set('blendTension', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.blendTension }}</span>
      </div>
    </div>

    <!-- Volute type -->
    <div class="sec">
      <div class="sec-lbl">Volute</div>
      <div class="volute-grid">
        <div v-for="o in VOLUTE_OPTS" :key="o.val"
          class="opt" :class="{ on: transition.spec.voluteType === o.val }"
          @click="set('voluteType', o.val)">
          {{ o.label }}<br><span class="opt-sub">{{ o.sub }}</span>
        </div>
      </div>

      <!-- Shared params -->
      <div v-if="transition.spec.voluteType !== 'none'" class="param-row">
        <span class="param-name">Height</span>
        <input class="param-slider" type="range" min="0" max="8" step=".25"
          :value="transition.spec.voluteHeightMm"
          @input="set('voluteHeightMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.voluteHeightMm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div v-if="transition.spec.voluteType !== 'none'" class="param-row">
        <span class="param-name">Position</span>
        <input class="param-slider" type="range" min="-30" max="0" step="1"
          :value="transition.spec.volutePositionMm"
          @input="set('volutePositionMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ transition.spec.volutePositionMm }}</span>
        <span class="param-unit">mm</span>
      </div>

      <!-- Gaussian params (gibson / custom / scallop) -->
      <template v-if="showGaussianParams()">
        <div class="param-row">
          <span class="param-name">Width σ</span>
          <input class="param-slider" type="range" min="5" max="25" step="1"
            :value="transition.spec.volSigmaMm"
            @input="set('volSigmaMm', +($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ transition.spec.volSigmaMm }}</span>
          <span class="param-unit">mm</span>
        </div>
      </template>

      <!-- Martin tent params -->
      <template v-if="showMartinParams()">
        <div class="martin-badge">Diamond / pyramid shape</div>
        <div class="param-row">
          <span class="param-name">Half width</span>
          <input class="param-slider" type="range" min="6" max="22" step=".5"
            :value="(transition.spec as any).volHalfWidthMm"
            @input="set('volHalfWidthMm' as any, +($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ (transition.spec as any).volHalfWidthMm?.toFixed(1) }}</span>
          <span class="param-unit">mm</span>
        </div>
        <div class="param-row">
          <span class="param-name">Sharpness</span>
          <input class="param-slider" type="range" min=".4" max="2" step=".05"
            :value="(transition.spec as any).volSharpness"
            @input="set('volSharpness' as any, +($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ (transition.spec as any).volSharpness?.toFixed(2) }}</span>
        </div>
        <div class="sharpness-note">
          {{ (transition.spec as any).volSharpness < 0.9 ? 'Flared base — classic pre-war Martin' :
             (transition.spec as any).volSharpness > 1.1 ? 'Steep sides — narrow crown' :
             'True linear pyramid' }}
        </div>
      </template>
    </div>

    <!-- Presets -->
    <div class="sec">
      <div class="sec-lbl">Presets</div>
      <div class="preset-grid">
        <div v-for="name in store.transitionPresets" :key="name"
          class="preset-btn"
          @click="store.loadTransitionPreset(name)">
          {{ name }}
        </div>
      </div>
    </div>

    <!-- Derived -->
    <div class="sec">
      <div class="sec-lbl">Derived</div>
      <div class="info-row"><span class="info-k">Thin point</span>
        <span class="info-v" :class="{ warn: transition.derived.value.thinPointMm < 12 }">
          {{ transition.derived.value.thinPointMm }} mm
        </span>
      </div>
      <div class="info-row"><span class="info-k">HS drop @30mm</span><span class="info-v">{{ transition.derived.value.hsDropAt30mm }} mm</span></div>
      <div class="info-row"><span class="info-k">Blend Δ</span><span class="info-v">{{ transition.derived.value.blendDeltaMm }} mm</span></div>
    </div>

    <!-- Gates -->
    <div class="sec" style="border-bottom:none">
      <div class="sec-lbl">Gates</div>
      <div v-for="g in transition.gates.value" :key="g.key" class="gate-item" :class="g.status">
        <span class="gate-dot"></span><span class="gate-txt">{{ g.label }}</span>
      </div>
    </div>

  </div>
</template>

<style scoped>
.panel-body   { display:flex; flex-direction:column; }
.opt-grid     { display:grid; grid-template-columns:1fr 1fr; gap:3px; margin-bottom:7px; }
.volute-grid  { display:grid; grid-template-columns:1fr 1fr 1fr; gap:3px; margin-bottom:7px; }
.opt-sub      { font-size:7px; color:var(--dim3); }
.muted        { opacity:.4; pointer-events:none; }
.martin-badge {
  font-size:8px; color:var(--br2); background:rgba(184,150,46,.08);
  border:1px solid var(--br3); border-radius:2px; padding:3px 7px; margin-bottom:5px;
}
.sharpness-note { font-size:8px; color:var(--dim2); margin-bottom:5px; padding-left:2px; }
.preset-grid  { display:grid; grid-template-columns:1fr 1fr; gap:4px; }
.preset-btn   {
  padding:5px 4px; background:var(--w2); border:1px solid var(--w3); border-radius:3px;
  font-family:var(--serif); font-size:9px; font-style:italic; color:var(--dim);
  cursor:pointer; text-align:center; transition:all .1s;
}
.preset-btn:hover { border-color:var(--br3); color:var(--v1); }
.info-row   { display:flex; justify-content:space-between; margin-bottom:3px; }
.info-k     { font-size:9px; color:var(--dim); }
.info-v     { font-size:9px; color:var(--v1); }
.info-v.warn { color:var(--amber); }
.gate-item  { display:flex; align-items:flex-start; gap:5px; padding:4px 6px; border-radius:2px; margin-bottom:3px; }
.gate-item.pass { background:rgba(90,184,106,.08); }
.gate-item.warn { background:rgba(184,112,32,.08); }
.gate-item.fail { background:rgba(200,64,48,.1); }
.gate-dot   { width:7px; height:7px; border-radius:50%; flex-shrink:0; margin-top:2px; }
.gate-item.pass .gate-dot { background:var(--green2); }
.gate-item.warn .gate-dot { background:var(--amber); }
.gate-item.fail .gate-dot { background:var(--red); }
.gate-txt   { font-size:8px; line-height:1.5; }
.gate-item.pass .gate-txt { color:var(--green2); }
.gate-item.warn .gate-txt { color:var(--amber); }
.gate-item.fail .gate-txt { color:#c84030; }
</style>
