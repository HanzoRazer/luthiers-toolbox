<script setup lang="ts">
/**
 * CamSpecPanel.vue
 *
 * Collapsible panel for the three critical CAM parameters.
 * Drops into WorkspaceView's right sidebar beneath the inlay properties.
 *
 * Usage in WorkspaceView.vue:
 *
 *   import CamSpecPanel from '@/components/CamSpecPanel.vue'
 *   import { useCamSpec } from '@/composables/useCamSpec'
 *
 *   // in setup — nut width comes from the active headstock model
 *   const camSpec = useCamSpec(currentHS().nw * MM, 175)
 *
 *   // in template
 *   <CamSpecPanel :cam="camSpec" @change="onCamChange" />
 *
 * onCamChange: merge camSpec.exportPayload into the ExportRequest before
 * calling useExportDxf.exportDxf()
 */

import type { useCamSpec } from '@/composables/useCamSpec'
import type { PitchStyle, RodAccess, RodType, TunerPattern } from '@/composables/useCamSpec'

const props = defineProps<{ cam: ReturnType<typeof useCamSpec> }>()
const emit  = defineEmits<{ change: [] }>()

function set<K extends keyof typeof props.cam.spec>(key: K, val: any) {
  props.cam.setSpec(key, val)
  emit('change')
}

const PITCH_OPTS:  {val: PitchStyle;  label: string; sub: string}[] = [
  { val:'angled', label:'Angled',  sub:'Gibson / PRS' },
  { val:'flat',   label:'Flat',    sub:'Fender style' },
]
const ACCESS_OPTS: {val: RodAccess;   label: string; sub: string}[] = [
  { val:'heel', label:'Heel access', sub:'Gibson' },
  { val:'head', label:'Head access', sub:'Fender' },
]
const TYPE_OPTS:   {val: RodType;     label: string}[] = [
  { val:'single', label:'Single action' },
  { val:'double', label:'Double action' },
]
const PAT_OPTS:    {val: TunerPattern; label: string}[] = [
  { val:'3+3', label:'3+3' },
  { val:'6L',  label:'6 inline L' },
  { val:'6R',  label:'6 inline R' },
  { val:'4+2', label:'4+2' },
]

const SLIDERS = [
  { group:'pitch',  key:'angle',       label:'Back angle',  min:0,   max:17,  step:0.5, unit:'°',  disabled: () => props.cam.spec.pitchStyle === 'flat' },
  { group:'pitch',  key:'nutHeightMm', label:'Nut height',  min:4,   max:12,  step:0.5, unit:'mm', disabled: () => false },
  { group:'rod',    key:'rodWidthMm',  label:'Rod width',   min:4,   max:8,   step:0.5, unit:'mm', disabled: () => false },
  { group:'rod',    key:'rodDepthMm',  label:'Rod depth',   min:8,   max:16,  step:0.5, unit:'mm', disabled: () => false },
  { group:'rod',    key:'rodLengthMm', label:'Channel len', min:380, max:520, step:5,   unit:'mm', disabled: () => false },
  { group:'rod',    key:'endMillMm',   label:'End mill Ø',  min:3,   max:8,   step:0.5, unit:'mm', disabled: () => false },
  { group:'tuner',  key:'postDiamMm',  label:'Post Ø',      min:6,   max:12,  step:0.5, unit:'mm', disabled: () => false },
  { group:'tuner',  key:'postCCmm',    label:'Post C-C',    min:32,  max:52,  step:0.5, unit:'mm', disabled: () => false },
  { group:'tuner',  key:'screwDiamMm', label:'Screw Ø',     min:2,   max:4,   step:0.5, unit:'mm', disabled: () => false },
  { group:'tuner',  key:'edgeClearMm', label:'Edge clear',  min:3,   max:10,  step:0.5, unit:'mm', disabled: () => false },
]

const open = { pitch: true, rod: true, tuner: true }
</script>

<template>
  <div class="cam-panel">

    <!-- Pitch angle -->
    <div class="cam-sec">
      <div class="cam-sec-hdr" @click="open.pitch = !open.pitch">
        <span class="cam-sec-lbl">Headstock pitch</span>
        <span class="cam-chevron">{{ open.pitch ? '▾' : '▸' }}</span>
      </div>
      <template v-if="open.pitch">
        <div class="opt-grid">
          <div v-for="o in PITCH_OPTS" :key="o.val"
            class="opt" :class="{ on: cam.spec.pitchStyle === o.val }"
            @click="set('pitchStyle', o.val)">
            {{ o.label }}<br><span class="opt-sub">{{ o.sub }}</span>
          </div>
        </div>
        <template v-for="sl in SLIDERS.filter(s => s.group === 'pitch')" :key="sl.key">
          <div class="param-row" :class="{ muted: sl.disabled() }">
            <span class="param-name">{{ sl.label }}</span>
            <input class="param-slider" type="range"
              :min="sl.min" :max="sl.max" :step="sl.step"
              :value="(cam.spec as any)[sl.key]"
              :disabled="sl.disabled()"
              @input="set(sl.key as any, +($event.target as HTMLInputElement).value)">
            <span class="param-val">{{ (cam.spec as any)[sl.key] }}{{ sl.unit }}</span>
          </div>
        </template>
        <!-- Fixture note -->
        <div class="fixture-note">{{ cam.derived.fixtureNote }}</div>
      </template>
    </div>

    <!-- Truss rod -->
    <div class="cam-sec">
      <div class="cam-sec-hdr" @click="open.rod = !open.rod">
        <span class="cam-sec-lbl">Truss rod</span>
        <span class="cam-chevron">{{ open.rod ? '▾' : '▸' }}</span>
      </div>
      <template v-if="open.rod">
        <div class="opt-grid">
          <div v-for="o in ACCESS_OPTS" :key="o.val"
            class="opt" :class="{ on: cam.spec.rodAccess === o.val }"
            @click="set('rodAccess', o.val)">
            {{ o.label }}<br><span class="opt-sub">{{ o.sub }}</span>
          </div>
        </div>
        <div class="opt-grid" style="margin-top:4px">
          <div v-for="o in TYPE_OPTS" :key="o.val"
            class="opt" :class="{ on: cam.spec.rodType === o.val }"
            @click="set('rodType', o.val)">
            {{ o.label }}
          </div>
        </div>
        <div v-for="sl in SLIDERS.filter(s => s.group === 'rod')" :key="sl.key" class="param-row">
          <span class="param-name">{{ sl.label }}</span>
          <input class="param-slider" type="range"
            :min="sl.min" :max="sl.max" :step="sl.step"
            :value="(cam.spec as any)[sl.key]"
            @input="set(sl.key as any, +($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ (cam.spec as any)[sl.key] }}{{ sl.unit }}</span>
        </div>
      </template>
    </div>

    <!-- Tuner layout -->
    <div class="cam-sec">
      <div class="cam-sec-hdr" @click="open.tuner = !open.tuner">
        <span class="cam-sec-lbl">Tuner layout</span>
        <span class="cam-chevron">{{ open.tuner ? '▾' : '▸' }}</span>
      </div>
      <template v-if="open.tuner">
        <div class="opt-grid" style="grid-template-columns:repeat(4,1fr)">
          <div v-for="o in PAT_OPTS" :key="o.val"
            class="opt" :class="{ on: cam.spec.tunerPattern === o.val }"
            @click="set('tunerPattern', o.val)">
            {{ o.label }}
          </div>
        </div>
        <div v-for="sl in SLIDERS.filter(s => s.group === 'tuner')" :key="sl.key" class="param-row">
          <span class="param-name">{{ sl.label }}</span>
          <input class="param-slider" type="range"
            :min="sl.min" :max="sl.max" :step="sl.step"
            :value="(cam.spec as any)[sl.key]"
            @input="set(sl.key as any, +($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ (cam.spec as any)[sl.key] }}{{ sl.unit }}</span>
        </div>
      </template>
    </div>

    <!-- Derived dimensions -->
    <div class="cam-sec">
      <div class="sec-lbl">Derived</div>
      <div class="info-row"><span class="info-k">Break angle</span><span class="info-v">{{ cam.derived.breakAngleDeg }}°</span></div>
      <div class="info-row"><span class="info-k">Wall thickness</span><span class="info-v">{{ cam.derived.wallThicknessMm.toFixed(1) }}mm</span></div>
      <div class="info-row"><span class="info-k">Post height</span><span class="info-v">{{ cam.derived.postHeightMm }}mm</span></div>
      <div class="info-row"><span class="info-k">Column height</span><span class="info-v">{{ cam.derived.columnHeightMm.toFixed(0) }}mm</span></div>
      <div class="info-row"><span class="info-k">Rod clearance</span><span class="info-v">{{ cam.derived.rodClearanceMm.toFixed(0) }}mm min</span></div>
    </div>

    <!-- CAM gates -->
    <div class="cam-sec" style="border-bottom:none">
      <div class="sec-lbl">CAM gates</div>
      <div v-for="g in cam.gates" :key="g.key" class="gate-item" :class="g.status">
        <span class="gate-dot"></span>
        <span class="gate-txt">{{ g.label }}</span>
      </div>
    </div>

  </div>
</template>

<style scoped>
.cam-panel { display:flex; flex-direction:column; }

.cam-sec {
  padding: 8px 12px 6px;
  border-bottom: 1px solid var(--w2);
}
.cam-sec-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  margin-bottom: 7px;
  user-select: none;
}
.cam-sec-lbl { font-size:8px; letter-spacing:1.6px; text-transform:uppercase; color:var(--br3); }
.cam-chevron { font-size:9px; color:var(--dim3); }

.sec-lbl { font-size:8px; letter-spacing:1.6px; text-transform:uppercase; color:var(--br3); margin-bottom:6px; }

.opt-grid { display:grid; grid-template-columns:1fr 1fr; gap:3px; margin-bottom:7px; }
.opt {
  padding:5px 5px;
  background:var(--w2); border:1px solid var(--w3); border-radius:2px;
  font-size:8px; color:var(--dim); cursor:pointer; text-align:center;
  transition:all .1s; line-height:1.4;
}
.opt:hover { border-color:var(--br3); color:var(--v1); }
.opt.on { border-color:var(--br); background:rgba(184,150,46,.07); color:var(--br2); }
.opt-sub { font-size:7px; color:var(--dim3); }

.fixture-note {
  font-size:8px; color:var(--amber); background:rgba(184,112,32,.08);
  border:1px solid rgba(184,112,32,.2); border-radius:2px;
  padding:4px 7px; margin-top:4px; line-height:1.5;
}

.muted { opacity:.4; pointer-events:none; }

.info-row { display:flex; justify-content:space-between; margin-bottom:3px; }
.info-k { font-size:9px; color:var(--dim); }
.info-v { font-size:9px; color:var(--v1); }

.gate-item {
  display:flex; align-items:flex-start; gap:6px;
  padding:4px 6px; border-radius:3px; margin-bottom:3px;
}
.gate-item.pass { background:rgba(90,184,106,.08); }
.gate-item.warn { background:rgba(184,112,32,.08); }
.gate-item.fail { background:rgba(200,64,48,.1); }
.gate-dot {
  width:7px; height:7px; border-radius:50%; flex-shrink:0; margin-top:2px;
}
.gate-item.pass .gate-dot { background:var(--green2); }
.gate-item.warn .gate-dot { background:var(--amber); }
.gate-item.fail .gate-dot { background:var(--red); }
.gate-txt { font-size:8px; line-height:1.5; color:var(--dim); }
.gate-item.pass .gate-txt { color:var(--green2); }
.gate-item.warn .gate-txt { color:var(--amber); }
.gate-item.fail .gate-txt { color:#c84030; }
</style>
