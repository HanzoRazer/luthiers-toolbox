<script setup lang="ts">
import { useNeckStore } from '@/stores/neck'
import type { ProfileShape } from '@/composables/useNeckProfile'

const store = useNeckStore()
const { profile } = store

function set<K extends keyof typeof profile.spec>(k: K, v: any) {
  profile.setSpec(k, v)
  if (k === 'depth1mm') store.syncNeckDepth(v as number)
}

const SHAPES: { val: ProfileShape; label: string; sub: string }[] = [
  { val: 'C',      label: 'C shape',    sub: 'Modern standard' },
  { val: 'C-soft', label: 'Soft C',     sub: 'Slim / boat neck' },
  { val: 'D',      label: 'D shape',    sub: 'Vintage / 50s' },
  { val: 'D-flat', label: 'Flat D',     sub: 'Modern thin' },
  { val: 'U',      label: 'U shape',    sub: 'Baseball' },
  { val: 'U-deep', label: 'Deep U',     sub: 'Early Fender' },
  { val: 'V-hard', label: 'Hard V',     sub: '40s sharp keel' },
  { val: 'V-soft', label: 'Soft V',     sub: '50s Fender' },
  { val: 'slim',   label: 'Slim / Wiz', sub: 'Ibanez Wizard' },
  { val: 'asymC',  label: 'Asym C',     sub: 'Bass-heavy' },
  { val: 'asymV',  label: 'Asym V',     sub: 'Treble keel' },
]

const COMPOUND_SHAPES: { val: ProfileShape; label: string; sub: string }[] = [
  { val: 'C→V',  label: 'C → V',  sub: 'Modern to vintage' },
  { val: 'U→C',  label: 'U → C',  sub: 'Chunky to modern' },
  { val: 'V→C',  label: 'V → C',  sub: 'Vintage to modern' },
  { val: 'C→D',  label: 'C → D',  sub: 'Round to flat' },
  { val: 'D→U',  label: 'D → U',  sub: 'Flat to chunky' },
]

const COMPOUND_KEYS = new Set(COMPOUND_SHAPES.map(s => s.val))
const isCompound = () => COMPOUND_KEYS.has(profile.spec.shape as any)

// Coupling breakdown at the preview fret
const breakdown = () => profile.couplingBreakdown(store.previewFret)
</script>

<template>
  <div class="panel-body">

    <div class="sec">
      <div class="sec-lbl">Back profile shape</div>
      <div class="shape-grid">
        <div v-for="s in SHAPES" :key="s.val"
          class="opt" :class="{ on: profile.spec.shape === s.val }"
          @click="set('shape', s.val)">
          {{ s.label }}<br><span class="opt-sub">{{ s.sub }}</span>
        </div>
      </div>
      <div class="sec-lbl" style="margin-top:6px">Compound taper</div>
      <div class="cmp-grid">
        <div v-for="s in COMPOUND_SHAPES" :key="s.val"
          class="opt" :class="{ on: profile.spec.shape === s.val }"
          @click="set('shape', s.val)">
          {{ s.label }}<br><span class="opt-sub">{{ s.sub }}</span>
        </div>
      </div>
    </div>

    <!-- Blend window — only shown for compound taper shapes -->
    <div v-if="isCompound()" class="sec">
      <div class="sec-lbl">Blend window</div>
      <div class="blend-note">
        Shape morphs continuously between nut and body shapes across this fret range.
      </div>
      <div class="param-row">
        <span class="param-name">Blend start</span>
        <input class="param-slider" type="range" min="0" max="9" step="1"
          :value="profile.spec.blendStartFret"
          @input="set('blendStartFret', +($event.target as HTMLInputElement).value)">
        <span class="param-val">Fret {{ profile.spec.blendStartFret }}</span>
      </div>
      <div class="param-row">
        <span class="param-name">Blend end</span>
        <input class="param-slider" type="range" min="5" max="22" step="1"
          :value="profile.spec.blendEndFret"
          @input="set('blendEndFret', +($event.target as HTMLInputElement).value)">
        <span class="param-val">Fret {{ profile.spec.blendEndFret }}</span>
      </div>
      <div class="param-row">
        <span class="param-name">Tension</span>
        <input class="param-slider" type="range" min="0" max="100" step="5"
          :value="profile.spec.blendTension"
          @input="set('blendTension', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ profile.spec.blendTension }}</span>
      </div>
    </div>

    <div class="sec">
      <div class="sec-lbl">Target neck depths</div>
      <div class="param-row">
        <span class="param-name">1st fret total</span>
        <input class="param-slider" type="range" min="18" max="26" step=".25"
          :value="profile.spec.depth1mm"
          @input="set('depth1mm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ profile.spec.depth1mm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">12th fret total</span>
        <input class="param-slider" type="range" min="20" max="28" step=".25"
          :value="profile.spec.depth12mm"
          @input="set('depth12mm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ profile.spec.depth12mm.toFixed(1) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Asym bass add</span>
        <input class="param-slider" type="range" min="0" max="3" step=".25"
          :value="profile.spec.asymBassAddMm"
          @input="set('asymBassAddMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ profile.spec.asymBassAddMm.toFixed(2) }}</span>
        <span class="param-unit">mm</span>
      </div>
    </div>

    <div class="sec">
      <div class="sec-lbl">Fretboard coupling</div>
      <div class="coupling-note">
        back = target − fret wire − FB thickness − crown comp
      </div>
      <div class="param-row">
        <span class="param-name">FB thickness</span>
        <input class="param-slider" type="range" min="4" max="8" step=".25"
          :value="profile.spec.fbThicknessMm"
          @input="set('fbThicknessMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ profile.spec.fbThicknessMm.toFixed(2) }}</span>
        <span class="param-unit">mm</span>
      </div>
      <div class="param-row">
        <span class="param-name">Fret wire h</span>
        <input class="param-slider" type="range" min="0.8" max="1.5" step=".05"
          :value="profile.spec.fretWireHeightMm"
          @input="set('fretWireHeightMm', +($event.target as HTMLInputElement).value)">
        <span class="param-val">{{ profile.spec.fretWireHeightMm.toFixed(2) }}</span>
        <span class="param-unit">mm</span>
      </div>
    </div>

    <!-- Coupling breakdown at preview fret -->
    <div class="sec">
      <div class="sec-lbl">Coupling @ fret {{ store.previewFret }}</div>
      <div class="info-row eq">
        <span class="info-k">Target total</span>
        <span class="info-v">{{ breakdown().targetTotal.toFixed(2) }} mm</span>
      </div>
      <div class="info-row">
        <span class="info-k">− Fret wire</span>
        <span class="info-v minus">{{ breakdown().minusFretWire.toFixed(2) }} mm</span>
      </div>
      <div class="info-row">
        <span class="info-k">− FB thickness</span>
        <span class="info-v minus">{{ breakdown().minusFBThickness.toFixed(2) }} mm</span>
      </div>
      <div class="info-row">
        <span class="info-k">− Crown comp</span>
        <span class="info-v minus">{{ breakdown().minusCrownComp.toFixed(4) }} mm</span>
      </div>
      <div class="info-row result">
        <span class="info-k">= Back depth</span>
        <span class="info-v ok">{{ breakdown().equalsBackDepth.toFixed(4) }} mm</span>
      </div>
    </div>

    <!-- Gates -->
    <div class="sec" style="border-bottom:none">
      <div class="sec-lbl">Gates</div>
      <div v-for="g in profile.gates" :key="g.key" class="gate-item" :class="g.status">
        <span class="gate-dot"></span><span class="gate-txt">{{ g.label }}</span>
      </div>
    </div>

  </div>
</template>

<style scoped>
.panel-body { display:flex; flex-direction:column; }
.shape-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:3px; margin-bottom:4px; }
.cmp-grid   { display:grid; grid-template-columns:1fr 1fr 1fr; gap:3px; margin-bottom:7px; }
.opt-sub    { font-size:7px; color:var(--dim3); }
.blend-note { font-size:8px; color:var(--blue2); background:rgba(91,143,168,.07); border:1px solid rgba(91,143,168,.18); border-radius:2px; padding:4px 7px; margin-bottom:6px; line-height:1.5; }
.coupling-note { font-size:8px; color:var(--blue2); background:rgba(91,143,168,.07); border:1px solid rgba(91,143,168,.18); border-radius:2px; padding:4px 7px; margin-bottom:6px; font-family:var(--mono); }
.info-row   { display:flex; justify-content:space-between; margin-bottom:3px; padding:0 2px; }
.info-row.result { border-top:1px solid var(--w3); margin-top:3px; padding-top:4px; }
.info-k     { font-size:9px; color:var(--dim); }
.info-v     { font-size:9px; color:var(--v1); }
.info-v.minus { color:var(--amber); }
.info-v.ok    { color:var(--green2); font-size:10px; }
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
