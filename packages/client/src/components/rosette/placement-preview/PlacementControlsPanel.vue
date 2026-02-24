<script setup lang="ts">
/**
 * PlacementControlsPanel.vue - Host surface and placement controls
 * Extracted from PlacementPreviewPanel.vue
 */

export interface HostConfig {
  kind: "rect" | "circle" | "polygon";
  width_mm?: number;
  height_mm?: number;
  radius_mm?: number;
}

export interface PlacementConfig {
  translate_x_mm: number;
  translate_y_mm: number;
  rotate_deg: number;
  scale: number;
  clip_to_host: boolean;
}

const props = defineProps<{
  host: HostConfig;
  placement: PlacementConfig;
  polygonText: string;
  loading: boolean;
  err: string | null;
}>();

const emit = defineEmits<{
  "update:host": [value: HostConfig];
  "update:placement": [value: PlacementConfig];
  "update:polygonText": [value: string];
  runPreview: [];
  resetDefaults: [];
}>();

// Local proxies for v-model binding
function updateHostField<K extends keyof HostConfig>(field: K, value: HostConfig[K]) {
  emit("update:host", { ...props.host, [field]: value });
}

function updatePlacementField<K extends keyof PlacementConfig>(field: K, value: PlacementConfig[K]) {
  emit("update:placement", { ...props.placement, [field]: value });
}
</script>

<template>
  <div class="controls">
    <div class="row">
      <label>Host surface</label>
      <select
        :value="host.kind"
        @change="updateHostField('kind', ($event.target as HTMLSelectElement).value as HostConfig['kind'])"
      >
        <option value="rect">
          Rect
        </option>
        <option value="circle">
          Circle
        </option>
        <option value="polygon">
          Polygon
        </option>
      </select>
    </div>

    <div
      v-if="host.kind === 'rect'"
      class="row2"
    >
      <div>
        <label>Width (mm)</label>
        <input
          :value="host.width_mm"
          type="number"
          @input="updateHostField('width_mm', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div>
        <label>Height (mm)</label>
        <input
          :value="host.height_mm"
          type="number"
          @input="updateHostField('height_mm', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <div
      v-if="host.kind === 'circle'"
      class="row"
    >
      <label>Radius (mm)</label>
      <input
        :value="host.radius_mm"
        type="number"
        @input="updateHostField('radius_mm', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div
      v-if="host.kind === 'polygon'"
      class="row"
    >
      <label>Polygon (mm)</label>
      <textarea
        :value="polygonText"
        rows="4"
        spellcheck="false"
        @input="emit('update:polygonText', ($event.target as HTMLTextAreaElement).value)"
      />
    </div>

    <div class="sep" />

    <div class="row2">
      <div>
        <label>Scale</label>
        <input
          :value="placement.scale"
          type="number"
          step="0.05"
          @input="updatePlacementField('scale', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div>
        <label>Rotate (deg)</label>
        <input
          :value="placement.rotate_deg"
          type="number"
          @input="updatePlacementField('rotate_deg', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <div class="row2">
      <div>
        <label>Offset X</label>
        <input
          :value="placement.translate_x_mm"
          type="number"
          @input="updatePlacementField('translate_x_mm', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div>
        <label>Offset Y</label>
        <input
          :value="placement.translate_y_mm"
          type="number"
          @input="updatePlacementField('translate_y_mm', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <div class="row checkbox">
      <input
        id="clip"
        :checked="placement.clip_to_host"
        type="checkbox"
        @change="updatePlacementField('clip_to_host', ($event.target as HTMLInputElement).checked)"
      >
      <label for="clip">Clip to host</label>
    </div>

    <div class="row actions">
      <button
        :disabled="loading"
        @click="emit('runPreview')"
      >
        {{ loading ? "Rendering…" : "Render Preview" }}
      </button>
      <button
        class="ghost"
        @click="emit('resetDefaults')"
      >
        Reset
      </button>
    </div>

    <div
      v-if="err"
      class="err"
    >
      {{ err }}
    </div>
  </div>
</template>

<style scoped>
.controls .row,
.controls .row2 {
  margin-bottom: 8px;
}

.controls .row2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.sep {
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  margin: 10px 0;
}

.checkbox {
  display: flex;
  gap: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

button {
  border-radius: 10px;
  padding: 6px 10px;
}

button.ghost {
  background: transparent;
}

.err {
  color: #b00020;
  font-size: 12px;
}
</style>
