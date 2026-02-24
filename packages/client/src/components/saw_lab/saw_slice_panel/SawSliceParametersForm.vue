<script setup lang="ts">
/**
 * SawSliceParametersForm.vue - Blade, machine, material, geometry, feeds form
 * Extracted from SawSlicePanel.vue
 */
import styles from "../SawSlicePanel.module.css";

export interface BladeInfo {
  blade_id: string;
  vendor: string;
  model_code: string;
  diameter_mm: number;
  kerf_mm: number;
  teeth: number;
}

export interface SawSliceFormState {
  selectedBladeId: string;
  machineProfile: string;
  materialFamily: string;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  totalDepth: number;
  depthPerPass: number;
  rpm: number;
  feedIpm: number;
  safeZ: number;
}

const props = defineProps<{
  formState: SawSliceFormState;
  blades: BladeInfo[];
  selectedBlade: BladeInfo | null;
  canValidate: boolean;
  canMerge: boolean;
  isValid: boolean;
  hasGcode: boolean;
}>();

const emit = defineEmits<{
  "update:formState": [state: SawSliceFormState];
  bladeChange: [];
  validate: [];
  mergeLearnedParams: [];
  generateGcode: [];
  sendToJobLog: [];
}>();

function updateField<K extends keyof SawSliceFormState>(
  key: K,
  value: SawSliceFormState[K]
) {
  emit("update:formState", { ...props.formState, [key]: value });
}

function handleBladeChange(bladeId: string) {
  updateField("selectedBladeId", bladeId);
  emit("bladeChange");
}
</script>

<template>
  <div :class="styles.parametersSection">
    <h3>Cut Parameters</h3>

    <!-- Blade Selection -->
    <div :class="styles.formGroup">
      <label>Saw Blade</label>
      <select
        :value="formState.selectedBladeId"
        @change="handleBladeChange(($event.target as HTMLSelectElement).value)"
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
      <div
        v-if="selectedBlade"
        :class="styles.bladeInfo"
      >
        Kerf: {{ selectedBlade.kerf_mm }}mm | Teeth: {{ selectedBlade.teeth }}
      </div>
    </div>

    <!-- Machine Profile -->
    <div :class="styles.formGroup">
      <label>Machine Profile</label>
      <select
        :value="formState.machineProfile"
        @change="updateField('machineProfile', ($event.target as HTMLSelectElement).value)"
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

    <!-- Material -->
    <div :class="styles.formGroup">
      <label>Material Family</label>
      <select
        :value="formState.materialFamily"
        @change="updateField('materialFamily', ($event.target as HTMLSelectElement).value)"
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

    <!-- Geometry -->
    <div :class="styles.formGroup">
      <label>Start X (mm)</label>
      <input
        :value="formState.startX"
        type="number"
        step="0.1"
        @input="updateField('startX', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Start Y (mm)</label>
      <input
        :value="formState.startY"
        type="number"
        step="0.1"
        @input="updateField('startY', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>End X (mm)</label>
      <input
        :value="formState.endX"
        type="number"
        step="0.1"
        @input="updateField('endX', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>End Y (mm)</label>
      <input
        :value="formState.endY"
        type="number"
        step="0.1"
        @input="updateField('endY', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Total Depth (mm)</label>
      <input
        :value="formState.totalDepth"
        type="number"
        step="0.5"
        min="0.5"
        @input="updateField('totalDepth', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Depth Per Pass (mm)</label>
      <input
        :value="formState.depthPerPass"
        type="number"
        step="0.5"
        min="0.5"
        @input="updateField('depthPerPass', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <!-- Feeds & Speeds -->
    <div :class="styles.formGroup">
      <label>RPM</label>
      <input
        :value="formState.rpm"
        type="number"
        step="100"
        min="2000"
        max="6000"
        @input="updateField('rpm', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Feed Rate (IPM)</label>
      <input
        :value="formState.feedIpm"
        type="number"
        step="5"
        min="10"
        max="300"
        @input="updateField('feedIpm', parseInt(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div :class="styles.formGroup">
      <label>Safe Z (mm)</label>
      <input
        :value="formState.safeZ"
        type="number"
        step="0.5"
        min="1"
        @input="updateField('safeZ', parseFloat(($event.target as HTMLInputElement).value))"
      >
    </div>

    <!-- Actions -->
    <div :class="styles.actions">
      <button
        :disabled="!canValidate"
        :class="styles.btnPrimary"
        @click="emit('validate')"
      >
        Validate Parameters
      </button>
      <button
        :disabled="!canMerge"
        :class="styles.btnSecondary"
        @click="emit('mergeLearnedParams')"
      >
        Apply Learned Overrides
      </button>
      <button
        :disabled="!isValid"
        :class="styles.btnPrimary"
        @click="emit('generateGcode')"
      >
        Generate G-code
      </button>
      <button
        :disabled="!hasGcode"
        :class="styles.btnSuccess"
        @click="emit('sendToJobLog')"
      >
        Send to JobLog
      </button>
    </div>
  </div>
</template>
