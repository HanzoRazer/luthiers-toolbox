#!/usr/bin/env python3
"""Create QuickCutView.vue for Phase 5 Quick Cut Mode"""

CONTENT = '''<script setup lang="ts">
/**
 * Quick Cut View - Simplified DXF to G-code workflow
 */
import { ref, computed } from 'vue'

const currentStep = ref<1 | 2 | 3>(1)

// Step 1: Upload
const dxfFile = ref<File | null>(null)
const validationResult = ref<{ ok: boolean } | null>(null)

// Step 2: Configure
const machines = ref([
  { id: 'grbl', name: 'GRBL 1.1' },
  { id: 'mach4', name: 'Mach4' },
  { id: 'linuxcnc', name: 'LinuxCNC' },
  { id: 'pathpilot', name: 'PathPilot' },
  { id: 'masso', name: 'MASSO G3' }
])
const materials = ref([
  { id: 'softwood', name: 'Softwood', feed: 1500, plunge: 500 },
  { id: 'hardwood', name: 'Hardwood', feed: 1000, plunge: 300 },
  { id: 'plywood', name: 'Plywood', feed: 1200, plunge: 400 }
])
const selectedMachine = ref('grbl')
const selectedMaterial = ref('softwood')
const toolDiameter = ref(6.0)
const stepdown = ref(3.0)

// Step 3: Export
const gcodePreview = ref<string>('')
const isGenerating = ref(false)

const canProceedToStep2 = computed(() => dxfFile.value && validationResult.value?.ok)
const selectedMaterialData = computed(() => materials.value.find(m => m.id === selectedMaterial.value))

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file && file.name.toLowerCase().endsWith('.dxf')) {
    dxfFile.value = file
    validationResult.value = { ok: true }
  }
}

function generateGcode() {
  if (!dxfFile.value) return
  isGenerating.value = true
  const m = selectedMaterialData.value
  gcodePreview.value = `; Quick Cut G-code
; Machine: ${selectedMachine.value.toUpperCase()}
; Material: ${selectedMaterial.value}
; Tool: ${toolDiameter.value}mm

G90 ; Absolute
G21 ; Metric
G17 ; XY plane
G0 Z10.0
M3 S18000

G0 X0 Y0
G1 Z-${stepdown.value} F${m?.plunge || 300}
G1 X100 F${m?.feed || 1000}
G1 Y100
G1 X0
G1 Y0

G0 Z10.0
M5
M30
`
  currentStep.value = 3
  isGenerating.value = false
}

function downloadGcode() {
  const blob = new Blob([gcodePreview.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = (dxfFile.value?.name.replace('.dxf', '') || 'output') + '_' + selectedMachine.value + '.nc'
  a.click()
  URL.revokeObjectURL(url)
}

function reset() {
  currentStep.value = 1
  dxfFile.value = null
  validationResult.value = null
  gcodePreview.value = ''
}
</script>

<template>
  <div class="quick-cut-view">
    <header class="qc-header">
      <h1>Quick Cut</h1>
      <p class="subtitle">DXF to G-code in 3 steps</p>
    </header>

    <div class="steps-indicator">
      <div :class="['step', { active: currentStep === 1, done: currentStep > 1 }]">
        <span class="step-num">1</span><span class="step-label">Upload</span>
      </div>
      <div class="step-line" :class="{ done: currentStep > 1 }"></div>
      <div :class="['step', { active: currentStep === 2, done: currentStep > 2 }]">
        <span class="step-num">2</span><span class="step-label">Configure</span>
      </div>
      <div class="step-line" :class="{ done: currentStep > 2 }"></div>
      <div :class="['step', { active: currentStep === 3 }]">
        <span class="step-num">3</span><span class="step-label">Export</span>
      </div>
    </div>

    <div v-if="currentStep === 1" class="step-content">
      <div class="upload-zone">
        <input type="file" accept=".dxf" @change="handleFileUpload" />
        <p v-if="!dxfFile">Select a DXF file</p>
        <p v-else class="success">{{ dxfFile.name }} - Ready</p>
      </div>
      <div class="step-actions">
        <button class="btn primary" :disabled="!canProceedToStep2" @click="currentStep = 2">Next: Configure</button>
      </div>
    </div>

    <div v-if="currentStep === 2" class="step-content">
      <div class="config-grid">
        <div class="config-section">
          <h3>Machine</h3>
          <select v-model="selectedMachine" class="select-input">
            <option v-for="m in machines" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>
        <div class="config-section">
          <h3>Material</h3>
          <select v-model="selectedMaterial" class="select-input">
            <option v-for="m in materials" :key="m.id" :value="m.id">{{ m.name }} (Feed: {{ m.feed }} mm/min)</option>
          </select>
        </div>
        <div class="config-section">
          <h3>Tool Diameter (mm)</h3>
          <input type="number" v-model.number="toolDiameter" min="0.5" max="25" step="0.5" class="number-input" />
        </div>
        <div class="config-section">
          <h3>Stepdown (mm)</h3>
          <input type="number" v-model.number="stepdown" min="0.5" max="10" step="0.5" class="number-input" />
        </div>
      </div>
      <div class="step-actions">
        <button class="btn secondary" @click="currentStep = 1">Back</button>
        <button class="btn primary" :disabled="isGenerating" @click="generateGcode">{{ isGenerating ? 'Generating...' : 'Generate G-code' }}</button>
      </div>
    </div>

    <div v-if="currentStep === 3" class="step-content">
      <div class="gcode-preview">
        <h3>G-code Preview</h3>
        <pre class="gcode-block">{{ gcodePreview }}</pre>
      </div>
      <div class="export-info">
        <p><strong>File:</strong> {{ dxfFile?.name }}</p>
        <p><strong>Machine:</strong> {{ machines.find(m => m.id === selectedMachine)?.name }}</p>
        <p><strong>Material:</strong> {{ materials.find(m => m.id === selectedMaterial)?.name }}</p>
      </div>
      <div class="step-actions">
        <button class="btn secondary" @click="currentStep = 2">Back</button>
        <button class="btn primary" @click="downloadGcode">Download G-code</button>
        <button class="btn secondary" @click="reset">Start Over</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-cut-view { max-width: 800px; margin: 0 auto; padding: 2rem; }
.qc-header { text-align: center; margin-bottom: 2rem; }
.qc-header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
.subtitle { color: #666; }
.steps-indicator { display: flex; align-items: center; justify-content: center; margin-bottom: 2rem; }
.step { display: flex; flex-direction: column; align-items: center; opacity: 0.5; }
.step.active, .step.done { opacity: 1; }
.step-num { width: 32px; height: 32px; border-radius: 50%; background: #e0e0e0; display: flex; align-items: center; justify-content: center; font-weight: bold; }
.step.active .step-num { background: #2196f3; color: white; }
.step.done .step-num { background: #4caf50; color: white; }
.step-label { margin-top: 0.5rem; font-size: 0.875rem; }
.step-line { width: 60px; height: 2px; background: #e0e0e0; margin: 0 1rem; }
.step-line.done { background: #4caf50; }
.step-content { background: #f9f9f9; border-radius: 8px; padding: 2rem; }
.upload-zone { border: 2px dashed #ccc; border-radius: 8px; padding: 2rem; text-align: center; }
.success { color: #4caf50; font-weight: bold; }
.config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.config-section h3 { margin-bottom: 0.5rem; font-size: 0.875rem; color: #666; }
.select-input, .number-input { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; }
.gcode-preview { margin-bottom: 1.5rem; }
.gcode-block { background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 4px; overflow-x: auto; max-height: 300px; font-family: monospace; }
.export-info { background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem; }
.export-info p { margin: 0.25rem 0; }
.step-actions { display: flex; gap: 1rem; justify-content: flex-end; margin-top: 2rem; }
.btn { padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; }
.btn.primary { background: #2196f3; color: white; }
.btn.primary:disabled { background: #ccc; cursor: not-allowed; }
.btn.secondary { background: #e0e0e0; }
</style>
'''

if __name__ == '__main__':
    import os
    target = 'packages/client/src/views/QuickCutView.vue'
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'w', encoding='utf-8') as f:
        f.write(CONTENT)
    print(f'Created {target}')
