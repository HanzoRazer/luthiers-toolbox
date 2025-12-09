<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Wiring Workbench - Electronics layout and tone analysis tool

Part of Phase P2.3: Utility Tools Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Wiring analyzer (output impedance, RC cutoff frequency)
- Treble bleed calculator (capacitor/resistor values)
- Switch validator (pickup combination checking)
- Pickup selector configuration (3-way, 5-way, superswitch)
- Push/pull switch planning
- Mini-switch integration
- Tone capacitor calculator
- JSON import/export for wiring configurations
-->

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-2xl font-bold">Wiring Workbench</h1>
      <div class="flex items-center gap-2 text-sm">
        <span class="opacity-70">Help:</span>
        <a class="underline" :href="reportHtmlHref" target="_blank" rel="noopener">Community Report (HTML)</a>
        <span>·</span>
        <a class="underline" :href="reportPdfHref" target="_blank" rel="noopener">Community Report (PDF)</a>
      </div>
    </div>

    <div class="flex gap-2 flex-wrap">
      <button 
        v-for="t in tabs" 
        :key="t" 
        class="px-3 py-1 rounded border transition-colors"
        :class="tab === t ? 'bg-blue-100 border-blue-500' : 'hover:bg-gray-50'" 
        @click="tab = t"
      >
        {{ t }}
      </button>
    </div>

    <!-- Analyzer Tab -->
    <div v-if="tab === 'Analyzer'" class="space-y-2">
      <p class="opacity-80 text-sm">Load a wiring JSON to estimate output impedance and tone RC cutoff.</p>
      <input 
        type="file" 
        @change="onFile" 
        accept=".json" 
        class="border p-2 rounded w-full max-w-md" 
      />
      <div v-if="result" class="grid gap-1 p-4 bg-gray-50 rounded">
        <div><b>Output Impedance (Zout)</b>: {{ result.zout.toFixed(1) }} Ω</div>
        <div><b>RC Cutoff Frequency</b>: {{ result.fc ? result.fc.toFixed(1) + ' Hz' : 'n/a' }}</div>
      </div>
    </div>

    <!-- Treble Bleed Tab -->
    <div v-else-if="tab === 'Treble Bleed'" class="space-y-2">
      <p class="opacity-80 text-sm">Suggest capacitor and resistor values and estimate corner frequency.</p>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
        <label class="flex flex-col">
          <span class="text-sm font-medium mb-1">Pot Resistance (Ω)</span>
          <input 
            v-model.number="tb.pot" 
            type="number" 
            class="border p-2 rounded" 
          />
        </label>
        <label class="flex flex-col">
          <span class="text-sm font-medium mb-1">Cable Capacitance (pF)</span>
          <input 
            v-model.number="tb.cable" 
            type="number" 
            class="border p-2 rounded" 
          />
        </label>
        <label class="flex flex-col">
          <span class="text-sm font-medium mb-1">Circuit Style</span>
          <select v-model="tb.style" class="border p-2 rounded">
            <option value="parallel">Parallel (cap || resistor)</option>
            <option value="series">Series (cap + resistor)</option>
            <option value="cap-only">Cap only</option>
          </select>
        </label>
      </div>
      <button 
        class="px-4 py-2 rounded border bg-blue-500 text-white hover:bg-blue-600 transition-colors" 
        @click="calcTB"
      >
        Calculate
      </button>
      <div v-if="tbOut" class="space-y-1 p-4 bg-gray-50 rounded">
        <div><b>Capacitor</b>: {{ tbOut.cap_pf }} pF</div>
        <div><b>Resistor</b>: {{ tbOut.resistor_k ?? '—' }} kΩ</div>
        <div><b>Approx Corner Frequency</b>: {{ tbOut.approx_fc_hz ? tbOut.approx_fc_hz.toFixed(1) + ' Hz' : 'n/a' }}</div>
        <div class="opacity-70 text-sm italic mt-2">{{ tbOut.note }}</div>
      </div>
    </div>

    <!-- Switch Validator Tab -->
    <div v-else-if="tab === 'Switch Validator'" class="space-y-2">
      <p class="opacity-80 text-sm">Check if requested pickup combinations are supported by your hardware configuration.</p>
      <div class="grid md:grid-cols-2 gap-4">
        <div class="space-y-2">
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Selector Switch</span>
            <select v-model="hw.selector" class="border p-2 rounded">
              <option value="3-way">3-way</option>
              <option value="5-way">5-way</option>
              <option value="5-way-superswitch">5-way Superswitch</option>
            </select>
          </label>
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Push/Pull Switches</span>
            <input 
              v-model.number="hw.push_pull" 
              type="number" 
              min="0"
              class="border p-2 rounded"
            />
          </label>
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Mini Toggle Switches</span>
            <input 
              v-model.number="hw.mini_toggles" 
              type="number" 
              min="0"
              class="border p-2 rounded"
            />
          </label>
        </div>
        <label class="flex flex-col">
          <span class="text-sm font-medium mb-1">Requested Combinations (comma-separated)</span>
          <textarea
            v-model="comboText"
            placeholder="N,B,N+B,N+M+B,split neck,split bridge"
            class="border p-2 rounded h-32"
          />
        </label>
      </div>
      <button 
        class="px-4 py-2 rounded border bg-blue-500 text-white hover:bg-blue-600 transition-colors" 
        @click="doValidate"
      >
        Validate
      </button>
      <div v-if="valOut" class="mt-2 p-4 bg-gray-50 rounded">
        <div v-for="(v, k) in valOut" :key="k" class="text-sm py-1">
          <b>{{ k }}</b>: 
          <span :class="v.includes('not supported') ? 'text-red-600' : 'text-green-600'">
            {{ v }}
          </span>
        </div>
      </div>
    </div>

    <!-- Docs Tab -->
    <div v-else-if="tab === 'Docs'" class="space-y-2">
      <p class="opacity-80 text-sm">Embedded quick help. Use the Help links above for the full Community Report.</p>
      <iframe 
        :src="docsSrc" 
        class="w-full border rounded" 
        style="height:60vh;"
      ></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { recommendTrebleBleed } from '../../utils/treble_bleed'
import { validateSwitching, type HardwareConfig } from '../../utils/switch_validator'

const tabs = ['Analyzer', 'Treble Bleed', 'Switch Validator', 'Docs']
const tab = ref('Analyzer')

// Analyzer
const result = ref<{ zout: number; fc: number | null } | null>(null)

async function onFile(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const text = await file.text()
  const diagram = JSON.parse(text)
  
  let pots: number[] = []
  let picks: number[] = []
  
  for (const c of (diagram.components || [])) {
    if (c.type === 'pot') {
      let v = c.value || '500k'
      if (typeof v === 'string' && v.endsWith('k')) v = parseFloat(v) * 1e3
      pots.push(+v)
    }
    if ((c.type || '').startsWith('pickup')) picks.push(8000)
  }
  
  const comb = (a: number, b: number) => 1 / (1 / a + 1 / b)
  let Rp: number | null = null
  
  for (const v of [...pots, ...picks]) {
    Rp = Rp == null ? v : comb(Rp, v)
  }
  
  const zout = Rp ?? 10000
  let C: number | null = null
  let R: number | null = null
  
  for (const c of (diagram.components || [])) {
    if (c.type === 'capacitor' && C === null) {
      let v = c.value || '0.022uF'
      if (typeof v === 'string' && v.endsWith('uF')) v = parseFloat(v) * 1e-6
      C = +v
    }
    if (c.type === 'pot' && R === null) {
      let v = c.value || '500k'
      if (typeof v === 'string' && v.endsWith('k')) v = parseFloat(v) * 1e3
      R = +v
    }
  }
  
  const fc = (C && R) ? 1 / (2 * Math.PI * R * C) : null
  result.value = { zout, fc }
}

// Treble Bleed
const tb = ref({ pot: 500000, cable: 500, style: 'parallel' as 'cap-only' | 'parallel' | 'series' })
const tbOut = ref<ReturnType<typeof recommendTrebleBleed> | null>(null)

function calcTB() {
  tbOut.value = recommendTrebleBleed(tb.value.pot, tb.value.cable, tb.value.style)
}

// Switch Validator
const hw = ref<HardwareConfig>({ selector: '5-way', push_pull: 1, mini_toggles: 0 })
const comboText = ref('N,B,N+M,N+M+B,split neck')
const valOut = ref<Record<string, string> | null>(null)

function doValidate() {
  const combos = comboText.value.split(',').map(s => s.trim()).filter(Boolean)
  valOut.value = validateSwitching(hw.value, combos)
}

// Docs
const docsSrc = '/docs/wiring_help.html'
const reportHtmlHref = '/docs/Community_Wiring_Mod_Report.html'
const reportPdfHref = '/docs/Community_Wiring_Mod_Report.pdf'
</script>

<style scoped>
/* Additional component-specific styles can go here */
</style>
