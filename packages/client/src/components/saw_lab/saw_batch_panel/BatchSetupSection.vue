<template>
  <div :class="styles.batchSetupSection">
    <h3 :class="styles.sectionTitle">Batch Configuration</h3>

    <!-- Blade Selection -->
    <div :class="styles.formGroup">
      <label>Saw Blade</label>
      <select
        :value="selectedBladeId"
        @change="$emit('update:selectedBladeId', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">
          Select blade...
        </option>
        <option
          v-for="blade in blades"
          :key="blade.blade_id"
          :value="blade.blade_id"
        >
          {{ blade.vendor }} {{ blade.model_code }} ({{ blade.diameter_mm }}mm)
        </option>
      </select>
    </div>

    <!-- Machine & Material -->
    <div :class="styles.formGroup">
      <label>Machine Profile</label>
      <select
        :value="machineProfile"
        @change="$emit('update:machineProfile', ($event.target as HTMLSelectElement).value)"
      >
        <option value="bcam_router_2030">
          BCAM Router 2030
        </option>
        <option value="syil_x7">
          SYIL X7
        </option>
        <option value="tormach_1100mx">
          Tormach 1100MX
        </option>
      </select>
    </div>

    <div :class="styles.formGroup">
      <label>Material Family</label>
      <select
        :value="materialFamily"
        @change="$emit('update:materialFamily', ($event.target as HTMLSelectElement).value)"
      >
        <option value="hardwood">
          Hardwood
        </option>
        <option value="softwood">
          Softwood
        </option>
        <option value="plywood">
          Plywood
        </option>
        <option value="mdf">
          MDF
        </option>
      </select>
    </div>

    <!-- Batch Parameters -->
    <div :class="styles.formGroup">
      <label>Number of Slices</label>
      <input
        :value="numSlices"
        type="number"
        min="1"
        max="50"
        step="1"
        @input="$emit('update:numSlices', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Slice Spacing (mm)</label>
      <input
        :value="sliceSpacing"
        type="number"
        step="1"
        min="1"
        @input="$emit('update:sliceSpacing', Number(($event.target as HTMLInputElement).value))"
      >
      <div :class="styles.helpText">
        Distance between slice start points
      </div>
    </div>

    <div :class="styles.formGroup">
      <label>Slice Length (mm)</label>
      <input
        :value="sliceLength"
        type="number"
        step="1"
        min="10"
        @input="$emit('update:sliceLength', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Start Position X (mm)</label>
      <input
        :value="startX"
        type="number"
        step="0.1"
        @input="$emit('update:startX', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Start Position Y (mm)</label>
      <input
        :value="startY"
        type="number"
        step="0.1"
        @input="$emit('update:startY', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Slice Orientation</label>
      <select
        :value="orientation"
        @change="$emit('update:orientation', ($event.target as HTMLSelectElement).value)"
      >
        <option value="horizontal">
          Horizontal (along X)
        </option>
        <option value="vertical">
          Vertical (along Y)
        </option>
      </select>
    </div>

    <!-- Depth Parameters -->
    <div :class="styles.formGroup">
      <label>Total Depth (mm)</label>
      <input
        :value="totalDepth"
        type="number"
        step="0.5"
        min="0.5"
        @input="$emit('update:totalDepth', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Depth Per Pass (mm)</label>
      <input
        :value="depthPerPass"
        type="number"
        step="0.5"
        min="0.5"
        @input="$emit('update:depthPerPass', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <!-- Feeds & Speeds -->
    <div :class="styles.formGroup">
      <label>RPM</label>
      <input
        :value="rpm"
        type="number"
        step="100"
        min="2000"
        max="6000"
        @input="$emit('update:rpm', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Feed Rate (IPM)</label>
      <input
        :value="feedIpm"
        type="number"
        step="5"
        min="10"
        max="300"
        @input="$emit('update:feedIpm', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Safe Z (mm)</label>
      <input
        :value="safeZ"
        type="number"
        step="0.5"
        min="1"
        @input="$emit('update:safeZ', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <!-- Actions -->
    <div :class="styles.actions">
      <button
        :disabled="!canValidate"
        :class="styles.btnPrimary"
        @click="$emit('validate')"
      >
        Validate Batch
      </button>
      <button
        :disabled="!canMerge"
        :class="styles.btnSecondary"
        @click="$emit('mergeLearnedParams')"
      >
        Apply Learned Overrides
      </button>
      <button
        :disabled="!isValid"
        :class="styles.btnPrimary"
        @click="$emit('generateGcode')"
      >
        Generate Batch G-code
      </button>
      <button
        :disabled="!hasGcode"
        :class="styles.btnSuccess"
        @click="$emit('sendToJobLog')"
      >
        Send Batch to JobLog
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from '../SawBatchPanel.module.css'

interface Blade {
  blade_id: string
  vendor: string
  model_code: string
  diameter_mm: number
}

defineProps<{
  blades: Blade[]
  selectedBladeId: string
  machineProfile: string
  materialFamily: string
  numSlices: number
  sliceSpacing: number
  sliceLength: number
  startX: number
  startY: number
  orientation: 'horizontal' | 'vertical'
  totalDepth: number
  depthPerPass: number
  rpm: number
  feedIpm: number
  safeZ: number
  canValidate: boolean
  canMerge: boolean
  isValid: boolean
  hasGcode: boolean
}>()

defineEmits<{
  'update:selectedBladeId': [value: string]
  'update:machineProfile': [value: string]
  'update:materialFamily': [value: string]
  'update:numSlices': [value: number]
  'update:sliceSpacing': [value: number]
  'update:sliceLength': [value: number]
  'update:startX': [value: number]
  'update:startY': [value: number]
  'update:orientation': [value: string]
  'update:totalDepth': [value: number]
  'update:depthPerPass': [value: number]
  'update:rpm': [value: number]
  'update:feedIpm': [value: number]
  'update:safeZ': [value: number]
  validate: []
  mergeLearnedParams: []
  generateGcode: []
  sendToJobLog: []
}>()
</script>
