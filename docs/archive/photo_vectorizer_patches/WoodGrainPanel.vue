<script setup lang="ts">
/**
 * WoodGrainPanel.vue
 *
 * Drop into WorkspaceView's right panel (or as a drawer/tab).
 * Emits 'change' whenever species or params update so the parent
 * can call grain.applyToPath(hsPath, layer, OX, OY, SC).
 *
 * Usage in WorkspaceView:
 *   <WoodGrainPanel :grain="grain" @change="redrawHS" />
 *
 * where grain = useWoodGrain() from the parent.
 */
import { WOOD_SPECIES } from '@/composables/useWoodGrain'
import type { useWoodGrain } from '@/composables/useWoodGrain'

const props = defineProps<{ grain: ReturnType<typeof useWoodGrain> }>()
const emit  = defineEmits<{ change: [] }>()

function selectSpecies(name: string) {
  props.grain.setSpecies(name)
  emit('change')
}
function onSlider(key: string, val: string) {
  props.grain.setParam(key as any, parseFloat(val))
  emit('change')
}
function randomise() {
  props.grain.randomiseSeed()
  emit('change')
}

const SLIDER_DEFS = [
  { id:'freq',  label:'Frequency',  min:1,   max:40, step:1   },
  { id:'wave',  label:'Waviness',   min:0,   max:60, step:1   },
  { id:'con',   label:'Contrast',   min:0,   max:100,step:1   },
  { id:'ang',   label:'Angle',      min:-30, max:30, step:1,  unit:'°' },
  { id:'curl',  label:'Curl figure',min:0,   max:100,step:1   },
  { id:'ray',   label:'Ray fleck',  min:0,   max:100,step:1   },
  { id:'gloss', label:'Gloss',      min:0,   max:100,step:1   },
  { id:'pore',  label:'Pore fill',  min:0,   max:100,step:1   },
]
</script>

<template>
  <div class="grain-panel">

    <div class="sec">
      <div class="sec-lbl">Wood species</div>
      <div class="species-grid">
        <div
          v-for="(sp, name) in WOOD_SPECIES" :key="name"
          class="sp-btn" :class="{ on: grain.speciesKey === name }"
          @click="selectSpecies(name)"
        >
          <span class="sp-dot" :style="{
            background: `rgb(${sp.base[0]},${sp.base[1]},${sp.base[2]})`
          }"></span>
          {{ name }}
        </div>
      </div>
    </div>

    <div class="sec">
      <div class="sec-lbl">Grain parameters</div>
      <div v-for="def in SLIDER_DEFS" :key="def.id" class="param-row">
        <span class="param-name">{{ def.label }}</span>
        <input
          class="param-slider" type="range"
          :min="def.min" :max="def.max" :step="def.step"
          :value="(grain.params as any)[def.id]"
          @input="onSlider(def.id, ($event.target as HTMLInputElement).value)"
        >
        <span class="param-val">
          {{ (grain.params as any)[def.id] }}{{ def.unit ?? '' }}
        </span>
      </div>
    </div>

    <div class="sec" style="border-bottom:none">
      <button class="sbtn" style="width:100%" @click="randomise">⚄ Randomise grain</button>
    </div>

  </div>
</template>

<style scoped>
.grain-panel { display:flex; flex-direction:column; }
.species-grid { display:grid; grid-template-columns:1fr 1fr; gap:4px; }
.sp-btn {
  display:flex; align-items:center; gap:6px;
  padding:5px 7px; background:var(--w2); border:1px solid var(--w3);
  border-radius:3px; font-size:9px; color:var(--dim); cursor:pointer;
  transition:all .1s; font-family:var(--serif); font-style:italic;
}
.sp-btn:hover { border-color:var(--br3); color:var(--v1); }
.sp-btn.on    { border-color:var(--br); background:rgba(184,150,46,.07); color:var(--br2); }
.sp-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; border:1px solid rgba(0,0,0,.2); }
</style>
