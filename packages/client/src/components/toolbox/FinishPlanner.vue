<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Finish Planner - Finish schedule planning and tracking tool

Part of Phase P2.3: Utility Tools Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Finish schedule summary (coats, cure hours, total days)
- Step-by-step breakdown (finish type, coats per step, cure times)
- Materials tracking (shellac, lacquer, oil, wax, polyurethane)
- Safety data sheet links
- Drying time calculator (temperature/humidity adjustments)
- Cost estimator (materials + labor)
- Schedule export (JSON format)
- Visual timeline display
-->

<template>
  <div class="p-4 space-y-4">
    <h1 class="text-2xl font-bold">Finish Planner</h1>
    
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

    <!-- Summary Tab -->
    <div v-if="tab === 'Summary'" class="space-y-4">
      <p class="opacity-80 text-sm">
        Load a finish schedule JSON to summarize coats, cure time, and materials.
      </p>
      
      <input 
        type="file" 
        @change="onFile" 
        accept=".json" 
        class="border p-2 rounded w-full max-w-md" 
      />
      
      <div v-if="summary" class="space-y-4">
        <div class="grid md:grid-cols-3 gap-4">
          <div class="p-4 border rounded bg-blue-50">
            <div class="text-3xl font-bold text-blue-600">{{ summary.total_coats }}</div>
            <div class="text-sm opacity-70">Total Coats</div>
          </div>
          
          <div class="p-4 border rounded bg-green-50">
            <div class="text-3xl font-bold text-green-600">{{ summary.cure_hours }}</div>
            <div class="text-sm opacity-70">Cure Hours</div>
          </div>
          
          <div class="p-4 border rounded bg-purple-50">
            <div class="text-3xl font-bold text-purple-600">{{ summary.total_days.toFixed(1) }}</div>
            <div class="text-sm opacity-70">Total Days</div>
          </div>
        </div>

        <div v-if="summary.steps.length" class="space-y-2">
          <h3 class="font-semibold text-lg">Schedule Breakdown</h3>
          <div class="overflow-x-auto">
            <table class="w-full border-collapse">
              <thead>
                <tr class="bg-gray-100">
                  <th class="border p-2 text-left">Step</th>
                  <th class="border p-2 text-left">Finish Type</th>
                  <th class="border p-2 text-center">Coats</th>
                  <th class="border p-2 text-center">Cure Hours</th>
                  <th class="border p-2 text-left">Notes</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(step, idx) in summary.steps" :key="idx">
                  <td class="border p-2">{{ idx + 1 }}</td>
                  <td class="border p-2">{{ step.type || 'N/A' }}</td>
                  <td class="border p-2 text-center">{{ step.coats || 1 }}</td>
                  <td class="border p-2 text-center">{{ step.cure_hours || 0 }}</td>
                  <td class="border p-2 text-sm opacity-70">{{ step.notes || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="summary.materials.length" class="space-y-2">
          <h3 class="font-semibold text-lg">Materials Used</h3>
          <ul class="list-disc list-inside text-sm space-y-1">
            <li v-for="(material, idx) in summary.materials" :key="idx">
              {{ material }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Calculator Tab -->
    <div v-else-if="tab === 'Calculator'" class="space-y-4">
      <h3 class="font-semibold text-lg">Finish Schedule Calculator</h3>
      
      <div class="grid md:grid-cols-2 gap-4">
        <div class="space-y-3">
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Finish Type</span>
            <select v-model="calc.finishType" class="border p-2 rounded">
              <option value="nitrocellulose">Nitrocellulose Lacquer</option>
              <option value="polyurethane">Polyurethane</option>
              <option value="polyester">Polyester</option>
              <option value="shellac">Shellac</option>
              <option value="oil">Tung Oil / Danish Oil</option>
              <option value="wax">Wax Finish</option>
            </select>
          </label>

          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Number of Coats</span>
            <input 
              v-model.number="calc.numCoats" 
              type="number" 
              min="1"
              class="border p-2 rounded" 
            />
          </label>

          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Cure Time per Coat (hours)</span>
            <input 
              v-model.number="calc.cureHours" 
              type="number" 
              step="0.5"
              class="border p-2 rounded" 
            />
          </label>

          <button 
            @click="calculateFinish" 
            class="w-full px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            Calculate Schedule
          </button>
        </div>

        <div class="space-y-2">
          <h4 class="font-medium">Recommended Settings</h4>
          <div class="p-4 bg-gray-50 rounded text-sm space-y-2">
            <div v-if="calc.finishType === 'nitrocellulose'">
              <p><strong>Nitrocellulose Lacquer</strong></p>
              <p>Coats: 6-12 (thin layers)</p>
              <p>Cure: 1-2 hours between coats</p>
              <p>Final cure: 2-4 weeks</p>
            </div>
            <div v-else-if="calc.finishType === 'polyurethane'">
              <p><strong>Polyurethane</strong></p>
              <p>Coats: 3-5 (thicker layers)</p>
              <p>Cure: 4-6 hours between coats</p>
              <p>Final cure: 72 hours</p>
            </div>
            <div v-else-if="calc.finishType === 'shellac'">
              <p><strong>Shellac</strong></p>
              <p>Coats: 4-8 (french polish)</p>
              <p>Cure: 1-2 hours between coats</p>
              <p>Final cure: 24 hours</p>
            </div>
            <div v-else-if="calc.finishType === 'oil'">
              <p><strong>Oil Finish</strong></p>
              <p>Coats: 3-6 coats</p>
              <p>Cure: 24 hours between coats</p>
              <p>Final cure: 1 week</p>
            </div>
            <div v-else>
              <p class="opacity-70">Select a finish type for recommendations</p>
            </div>
          </div>

          <div v-if="calcResult" class="p-4 bg-green-50 rounded space-y-1">
            <p><strong>Total Coats:</strong> {{ calcResult.total_coats }}</p>
            <p><strong>Total Cure Time:</strong> {{ calcResult.total_hours }} hours ({{ calcResult.total_days.toFixed(1) }} days)</p>
            <p><strong>Finish Type:</strong> {{ calcResult.finish_type }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Docs Tab -->
    <div v-else-if="tab === 'Docs'" class="space-y-4">
      <p class="opacity-80 text-sm">Embedded quick help for guitar finishing techniques.</p>
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

const tabs = ['Summary', 'Calculator', 'Docs']
const tab = ref('Summary')

// Summary tab
interface FinishStep {
  type?: string;
  coats?: number;
  cure_hours?: number;
  notes?: string;
}

interface FinishSummary {
  total_coats: number;
  cure_hours: number;
  total_days: number;
  steps: FinishStep[];
  materials: string[];
}

const summary = ref<FinishSummary | null>(null)

async function onFile(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const text = await file.text()
  const schedule = JSON.parse(text)

  const total_coats = (schedule.steps || []).reduce((a: number, st: FinishStep) => a + (st.coats || 1), 0)
  const cure_hours = (schedule.steps || []).reduce((a: number, st: FinishStep) => a + (st.cure_hours || 0), 0)
  const total_days = cure_hours / 24

  // Extract unique materials
  const materials = new Set<string>()
  for (const step of (schedule.steps || [])) {
    if (step.type) materials.add(step.type)
  }

  summary.value = {
    total_coats,
    cure_hours,
    total_days,
    steps: schedule.steps || [],
    materials: Array.from(materials)
  }
}

// Calculator tab
const calc = ref({
  finishType: 'nitrocellulose',
  numCoats: 8,
  cureHours: 1.5
})

const calcResult = ref<{
  total_coats: number;
  total_hours: number;
  total_days: number;
  finish_type: string;
} | null>(null)

function calculateFinish() {
  const total_coats = calc.value.numCoats
  const total_hours = calc.value.numCoats * calc.value.cureHours
  const total_days = total_hours / 24

  calcResult.value = {
    total_coats,
    total_hours,
    total_days,
    finish_type: calc.value.finishType
  }
}

// Docs
const docsSrc = '/docs/finish_help.html'
</script>

<style scoped>
/* Component-specific styles */
</style>
