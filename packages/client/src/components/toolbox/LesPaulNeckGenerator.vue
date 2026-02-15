<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">
        Les Paul Neck Generator (C-Profile)
      </h1>
      
      <!-- Preset Selector -->
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-2">
          <span class="text-sm font-medium">Load Preset:</span>
          <select 
            v-model="selectedPresetId" 
            class="border rounded px-3 py-2 text-sm"
            @change="loadPresetParams"
          >
            <option value="">-- Select Preset --</option>
            <option
              v-for="preset in neckPresets"
              :key="preset.id"
              :value="preset.id"
            >
              {{ preset.name }}
            </option>
          </select>
        </label>
        <button 
          v-if="selectedPresetId"
          class="text-xs px-2 py-1 border rounded hover:bg-gray-50" 
          title="Clear preset selection"
          @click="clearPreset"
        >
          ✕
        </button>
      </div>
    </div>
    
    <!-- Preset Feedback -->
    <div
      v-if="presetLoadedMessage"
      class="p-3 bg-blue-50 border border-blue-200 rounded text-sm"
    >
      {{ presetLoadedMessage }}
    </div>

    <!-- Validation Warnings -->
    <div
      v-if="validationWarnings.length > 0"
      class="p-3 bg-yellow-50 border border-yellow-300 rounded text-sm"
    >
      <p class="font-semibold mb-2">
        ⚠️ Parameter Warnings:
      </p>
      <ul class="list-disc list-inside space-y-1">
        <li
          v-for="warning in validationWarnings"
          :key="warning.field"
          :class="{'text-red-600': warning.severity === 'error', 'text-yellow-700': warning.severity === 'warning'}"
        >
          {{ warning.message }}
        </li>
      </ul>
    </div>

    <!-- Modified Indicator -->
    <div
      v-if="isModifiedFromPreset"
      class="p-3 bg-purple-50 border border-purple-200 rounded text-sm flex items-center justify-between"
    >
      <span>✏️ Modified from preset</span>
      <button 
        :disabled="!selectedPresetId" 
        class="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs"
        @click="revertToPreset"
      >
        ↺ Revert to Original
      </button>
    </div>
    
    <div class="grid md:grid-cols-3 gap-4">
      <!-- Parameter Form -->
      <div class="md:col-span-2 space-y-4">
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Blank Dimensions
          </h3>
          <div class="grid grid-cols-3 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Length (in)</span>
              <input
                v-model.number="form.blank_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Width (in)</span>
              <input
                v-model.number="form.blank_width"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness (in)</span>
              <input
                v-model.number="form.blank_thickness"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Scale & Dimensions
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Scale Length (in)</span>
              <input
                v-model.number="form.scale_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Neck Length (in)</span>
              <input
                v-model.number="form.neck_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Nut Width (in)</span>
              <input
                v-model.number="form.nut_width"
                type="number"
                step="0.001"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Heel Width (in)</span>
              <input
                v-model.number="form.heel_width"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Neck Angle (°)</span>
              <input
                v-model.number="form.neck_angle"
                type="number"
                step="0.1"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Fretboard Radius (in)</span>
              <input
                v-model.number="form.fretboard_radius"
                type="number"
                step="0.5"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            C-Profile Shape
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness @ 1st Fret (in)</span>
              <input
                v-model.number="form.thickness_1st_fret"
                type="number"
                step="0.01"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness @ 12th Fret (in)</span>
              <input
                v-model.number="form.thickness_12th_fret"
                type="number"
                step="0.01"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Radius @ 1st Fret (in)</span>
              <input
                v-model.number="form.radius_at_1st"
                type="number"
                step="0.05"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Radius @ 12th Fret (in)</span>
              <input
                v-model.number="form.radius_at_12th"
                type="number"
                step="0.05"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Headstock
          </h3>
          <div class="grid grid-cols-3 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Angle (°)</span>
              <input
                v-model.number="form.headstock_angle"
                type="number"
                step="0.5"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Length (in)</span>
              <input
                v-model.number="form.headstock_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness (in)</span>
              <input
                v-model.number="form.headstock_thickness"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Tuner Layout (in)</span>
              <input
                v-model.number="form.tuner_layout"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Tuner Diameter (in)</span>
              <input
                v-model.number="form.tuner_diameter"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Options
          </h3>
          <div class="space-y-2">
            <label class="flex items-center gap-2">
              <input
                v-model="form.include_fretboard"
                type="checkbox"
                class="form-checkbox"
              >
              <span class="text-sm">Include Fretboard Geometry</span>
            </label>
            <label class="flex items-center gap-2">
              <input
                v-model="form.alignment_pin_holes"
                type="checkbox"
                class="form-checkbox"
              >
              <span class="text-sm">Add Alignment Pin Holes</span>
            </label>
          </div>
        </div>

        <div class="flex gap-2">
          <button 
            class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors" 
            @click="generateNeck"
          >
            Generate Neck
          </button>
          <button 
            class="px-4 py-2 rounded border hover:bg-gray-50 transition-colors" 
            @click="loadDefaults"
          >
            Load Defaults
          </button>
          <button 
            class="px-4 py-2 rounded border hover:bg-gray-50 transition-colors" 
            @click="exportJSON"
          >
            Export JSON
          </button>
          <button 
            :disabled="!generatedGeometry" 
            class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            @click="exportDXF"
          >
            Export DXF
          </button>
        </div>
      </div>

      <!-- Info Panel -->
      <div class="space-y-4">
        <div class="p-4 border rounded bg-gray-50">
          <h3 class="font-semibold mb-2">
            About C-Profile
          </h3>
          <p class="text-sm opacity-80">
            The C-profile is characterized by a rounded, comfortable back shape. 
            Les Paul necks typically have a medium C-profile with gradual thickness increase toward the heel.
          </p>
        </div>

        <div class="p-4 border rounded bg-blue-50">
          <h3 class="font-semibold mb-2">
            Standard Les Paul Specs
          </h3>
          <ul class="text-sm space-y-1 opacity-80">
            <li><strong>Scale:</strong> 24.75"</li>
            <li><strong>Nut Width:</strong> 1.695"</li>
            <li><strong>Headstock Angle:</strong> 13°-17°</li>
            <li><strong>Fretboard Radius:</strong> 12"</li>
            <li><strong>Neck Angle:</strong> 3.5°-4°</li>
          </ul>
        </div>

        <div
          v-if="generatedGeometry"
          class="p-4 border rounded bg-green-50"
        >
          <h3 class="font-semibold mb-2">
            ✅ Geometry Generated
          </h3>
          <ul class="text-sm space-y-1">
            <li>Profile points: {{ generatedGeometry.profile.length }}</li>
            <li>Headstock points: {{ generatedGeometry.headstock.length }}</li>
            <li>Tuner holes: {{ generatedGeometry.tuner_holes.length }}</li>
            <li v-if="generatedGeometry.fretboard">
              Fretboard points: {{ generatedGeometry.fretboard.length }}
            </li>
          </ul>
          <p class="text-xs opacity-70 mt-2">
            Geometry ready for export to CAM software or 3D modeling.
          </p>
        </div>

        <div class="p-4 border rounded bg-yellow-50">
          <h3 class="font-semibold mb-2">
            ⚠️ CNC Notes
          </h3>
          <ul class="text-xs space-y-1 opacity-80">
            <li>Profile requires 4-axis or duplicator carving</li>
            <li>Headstock angle cut on bandsaw before CNC</li>
            <li>Tuner holes drilled with drill press</li>
            <li>Fretboard slots cut separately</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { reactive, ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  generateLesPaulNeck, 
  getDefaultLesPaulParams, 
  exportNeckAsJSON,
  convertParameters,
  validateParameters,
  type NeckGeometry,
  type NeckParameters,
  type ValidationWarning
} from '../../utils/neck_generator'

const route = useRoute()
const form = reactive(getDefaultLesPaulParams())
const generatedGeometry = ref<NeckGeometry | null>(null)

// Preset loading state
const neckPresets = ref<any[]>([])
const selectedPresetId = ref<string>('')
const presetLoadedMessage = ref<string>('')
const originalPresetParams = ref<NeckParameters | null>(null)
const validationWarnings = ref<ValidationWarning[]>([])

// Computed: Check if form was modified from loaded preset
const isModifiedFromPreset = computed(() => {
  if (!originalPresetParams.value || !selectedPresetId.value) return false
  
  const original = originalPresetParams.value
  const current = form
  
  // Compare all numeric fields
  const numericFields: (keyof NeckParameters)[] = [
    'blank_length', 'blank_width', 'blank_thickness',
    'scale_length', 'nut_width', 'heel_width', 'neck_length', 'neck_angle',
    'fretboard_radius', 'fretboard_offset',
    'thickness_1st_fret', 'thickness_12th_fret', 'radius_at_1st', 'radius_at_12th',
    'headstock_angle', 'headstock_length', 'headstock_thickness', 
    'tuner_layout', 'tuner_diameter'
  ]
  
  return numericFields.some(field => {
    const originalVal = original[field]
    const currentVal = current[field]
    if (originalVal === undefined || currentVal === undefined) return false
    return Math.abs((originalVal as number) - (currentVal as number)) > 0.001
  })
})

function generateNeck() {
  try {
    const geometry = generateLesPaulNeck({ ...form })
    generatedGeometry.value = geometry
    alert('✅ Les Paul neck geometry generated successfully!')
  } catch (error) {
    console.error('Error generating neck:', error)
    alert('❌ Error generating neck. Check console for details.')
  }
}

function loadDefaults() {
  const defaults = getDefaultLesPaulParams()
  Object.assign(form, defaults)
  generatedGeometry.value = null
}

function exportJSON() {
  if (!generatedGeometry.value) {
    alert('Please generate neck geometry first')
    return
  }

  const json = exportNeckAsJSON(generatedGeometry.value)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'les_paul_neck_geometry.json'
  link.click()
  URL.revokeObjectURL(url)
}

async function exportDXF() {
  if (!generatedGeometry.value) {
    alert('Please generate neck geometry first')
    return
  }

  try {
    const response = await api('/api/neck/export_dxf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...form }),
    })

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `les_paul_neck_${form.scale_length}${form.units || 'in'}.dxf`
    link.click()
    URL.revokeObjectURL(url)
    
    alert('✅ DXF exported successfully!')
  } catch (error) {
    console.error('Error exporting DXF:', error)
    alert('❌ Error exporting DXF. Check console for details.')
  }
}

// Preset loading functions
async function fetchNeckPresets() {
  try {
    const response = await api('/api/presets?kind=neck')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const data = await response.json()
    neckPresets.value = data.presets || []
  } catch (error) {
    console.error('Failed to fetch neck presets:', error)
    neckPresets.value = []
  }
}

async function loadPresetParams() {
  if (!selectedPresetId.value) return
  
  try {
    const response = await api(`/api/presets/${selectedPresetId.value}`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const preset = await response.json()
    
    // Map neck_params to form fields
    if (preset.neck_params) {
      let params = preset.neck_params
      
      // Detect units and convert if necessary
      const presetUnits = params.units || 'inch'
      const formUnits = 'inch' // LesPaulNeckGenerator always uses inches
      
      if (presetUnits !== formUnits) {
        // Convert parameters from preset units to form units
        params = convertParameters(params, presetUnits, formUnits)
        presetLoadedMessage.value = `✅ Loaded preset: ${preset.name} (converted from ${presetUnits} to ${formUnits})`
      } else {
        presetLoadedMessage.value = `✅ Loaded preset: ${preset.name}`
      }
      
      // Store original params for revert functionality
      originalPresetParams.value = { ...params }
      
      // Map all available fields from neck_params to form
      if (params.blank_length !== undefined) form.blank_length = params.blank_length
      if (params.blank_width !== undefined) form.blank_width = params.blank_width
      if (params.blank_thickness !== undefined) form.blank_thickness = params.blank_thickness
      if (params.scale_length !== undefined) form.scale_length = params.scale_length
      if (params.nut_width !== undefined) form.nut_width = params.nut_width
      if (params.heel_width !== undefined) form.heel_width = params.heel_width
      if (params.neck_length !== undefined) form.neck_length = params.neck_length
      if (params.neck_angle !== undefined) form.neck_angle = params.neck_angle
      if (params.fretboard_radius !== undefined) form.fretboard_radius = params.fretboard_radius
      if (params.thickness_1st_fret !== undefined) form.thickness_1st_fret = params.thickness_1st_fret
      if (params.thickness_12th_fret !== undefined) form.thickness_12th_fret = params.thickness_12th_fret
      if (params.radius_at_1st !== undefined) form.radius_at_1st = params.radius_at_1st
      if (params.radius_at_12th !== undefined) form.radius_at_12th = params.radius_at_12th
      if (params.headstock_angle !== undefined) form.headstock_angle = params.headstock_angle
      if (params.headstock_length !== undefined) form.headstock_length = params.headstock_length
      if (params.headstock_thickness !== undefined) form.headstock_thickness = params.headstock_thickness
      if (params.tuner_layout !== undefined) form.tuner_layout = params.tuner_layout
      if (params.tuner_diameter !== undefined) form.tuner_diameter = params.tuner_diameter
      if (params.fretboard_offset !== undefined) form.fretboard_offset = params.fretboard_offset
      if (params.include_fretboard !== undefined) form.include_fretboard = params.include_fretboard
      if (params.alignment_pin_holes !== undefined) form.alignment_pin_holes = params.alignment_pin_holes
      
      // Validate parameters
      const validation = validateParameters(form)
      validationWarnings.value = validation.warnings
      
      setTimeout(() => { presetLoadedMessage.value = '' }, 3000)
      
      // Clear generated geometry when loading new preset
      generatedGeometry.value = null
    } else {
      presetLoadedMessage.value = '⚠️ Preset has no neck parameters'
      setTimeout(() => { presetLoadedMessage.value = '' }, 3000)
    }
  } catch (error) {
    console.error('Failed to load preset:', error)
    alert('❌ Failed to load preset. Check console for details.')
  }
}

function clearPreset() {
  selectedPresetId.value = ''
  presetLoadedMessage.value = ''
  originalPresetParams.value = null
  validationWarnings.value = []
}

function revertToPreset() {
  if (!originalPresetParams.value) return
  
  const original = originalPresetParams.value
  
  // Restore all parameters
  Object.keys(original).forEach(key => {
    const typedKey = key as keyof NeckParameters
    if (original[typedKey] !== undefined) {
      (form as any)[typedKey] = original[typedKey]
    }
  })
  
  // Re-validate
  const validation = validateParameters(form)
  validationWarnings.value = validation.warnings
  
  // Clear geometry since params changed
  generatedGeometry.value = null
  
  presetLoadedMessage.value = '✅ Reverted to original preset values'
  setTimeout(() => {
    presetLoadedMessage.value = ''
  }, 3000)
}

// Lifecycle - fetch presets and check for query parameter
onMounted(async () => {
  await fetchNeckPresets()
  
  // Check if preset_id was passed via query parameter (from PresetHub)
  const presetIdFromQuery = route.query.preset_id as string
  if (presetIdFromQuery) {
    selectedPresetId.value = presetIdFromQuery
    await loadPresetParams()
  }
})
</script>

<style scoped>
/* Component-specific styles */
</style>
