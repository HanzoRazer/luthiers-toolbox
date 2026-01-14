<template>
  <div class="panel">
    <div class="hdr">
      <div class="title">Placement Preview</div>
      <div class="sub">Host-agnostic ornament placement</div>
    </div>

    <!-- PRESETS -->
    <div class="presets">
      <label>Presets</label>
      <div class="presetRow">
        <select v-model="selectedPresetId" @change="applySelectedPreset">
          <option disabled value="">— Select preset —</option>
          <option v-for="p in presets" :key="p.id" :value="p.id">
            {{ p.name }}
          </option>
        </select>

        <!-- ★ quick save from current selection -->
        <button
          class="ghost star"
          :title="starTitle"
          @click="savePresetFromCurrent"
        >
          ★
        </button>

        <button class="ghost" @click="savePreset">
          Save
        </button>

        <button
          class="ghost danger"
          :disabled="!canDeletePreset"
          @click="deletePreset"
        >
          Delete
        </button>
      </div>
    </div>

    <div class="grid">
      <!-- CONTROLS -->
      <div class="controls">
        <div class="row">
          <label>Host surface</label>
          <select v-model="host.kind">
            <option value="rect">Rect</option>
            <option value="circle">Circle</option>
            <option value="polygon">Polygon</option>
          </select>
        </div>

        <div v-if="host.kind === 'rect'" class="row2">
          <div>
            <label>Width (mm)</label>
            <input type="number" v-model.number="host.width_mm" />
          </div>
          <div>
            <label>Height (mm)</label>
            <input type="number" v-model.number="host.height_mm" />
          </div>
        </div>

        <div v-if="host.kind === 'circle'" class="row">
          <label>Radius (mm)</label>
          <input type="number" v-model.number="host.radius_mm" />
        </div>

        <div v-if="host.kind === 'polygon'" class="row">
          <label>Polygon (mm)</label>
          <textarea
            v-model="polygonText"
            rows="4"
            spellcheck="false"
          />
        </div>

        <div class="sep"></div>

        <div class="row2">
          <div>
            <label>Scale</label>
            <input type="number" step="0.05" v-model.number="placement.scale" />
          </div>
          <div>
            <label>Rotate (deg)</label>
            <input type="number" v-model.number="placement.rotate_deg" />
          </div>
        </div>

        <div class="row2">
          <div>
            <label>Offset X</label>
            <input type="number" v-model.number="placement.translate_x_mm" />
          </div>
          <div>
            <label>Offset Y</label>
            <input type="number" v-model.number="placement.translate_y_mm" />
          </div>
        </div>

        <div class="row checkbox">
          <input id="clip" type="checkbox" v-model="placement.clip_to_host" />
          <label for="clip">Clip to host</label>
        </div>

        <div class="row actions">
          <button @click="runPreview" :disabled="loading">
            {{ loading ? "Rendering…" : "Render Preview" }}
          </button>
          <button class="ghost" @click="resetDefaults">
            Reset
          </button>
        </div>

        <div v-if="err" class="err">{{ err }}</div>
      </div>

      <!-- PREVIEW -->
      <div class="preview">
        <div class="previewHdr">
          <div class="k">SVG Preview</div>
          <div class="v" v-if="lastUpdated">
            Updated {{ lastUpdated }}
          </div>
        </div>
        <div class="svgBox" v-html="svg"></div>
      </div>
    </div>

    <!-- Preset Save Modal -->
    <PresetSaveModal
      :open="showSaveModal"
      :preset-name="selectedUserPreset?.name ?? ''"
      :suggested-name="defaultPresetName()"
      :is-dirty="isDirty"
      @close="showSaveModal = false"
      @overwrite="handleOverwrite"
      @save-new="handleSaveNew"
    />

    <!-- Delete Confirmation Modal (32.6.5) -->
    <SmallModal
      :open="showDeleteModal"
      mode="confirm"
      title="Delete Preset"
      :message="`Delete preset &quot;${selectedUserPreset?.name ?? 'preset'}&quot;? This cannot be undone.`"
      ok-text="Delete"
      cancel-text="Cancel"
      @ok="confirmDelete"
      @cancel="showDeleteModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { previewPlacementSvg } from "@/sdk/endpoints/artPlacement";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";
import PresetSaveModal from "./PresetSaveModal.vue";
import SmallModal from "@/components/ui/SmallModal.vue";

/* -------------------------
   Types
-------------------------- */
type PlacementPreset = {
  id: string;
  name: string;
  host: any;
  placement: any;
  polygonText?: string;
};

/* -------------------------
   Constants
-------------------------- */
const PRESETS_KEY = "artstudio.placementPresets.v1";

/* -------------------------
   State
-------------------------- */
const store = useRosetteStore();
const toast = useToastStore();

const showSaveModal = ref(false);
const showDeleteModal = ref(false);

const host = ref<any>({
  kind: "rect",
  width_mm: 220,
  height_mm: 220,
});

const placement = ref<any>({
  translate_x_mm: 0,
  translate_y_mm: 0,
  rotate_deg: 0,
  scale: 1,
  clip_to_host: true,
});

const polygonText = ref("0,0\n220,0\n220,220\n0,220");

const loading = ref(false);
const err = ref<string | null>(null);
const svg = ref("");
const lastUpdated = ref("");

const selectedPresetId = ref("");

/* -------------------------
   Presets
-------------------------- */
const builtinPresets: PlacementPreset[] = [
  {
    id: "builtin_rect",
    name: "Square panel",
    host: { kind: "rect", width_mm: 220, height_mm: 220 },
    placement: { translate_x_mm: 0, translate_y_mm: 0, rotate_deg: 0, scale: 1, clip_to_host: true },
  },
  {
    id: "builtin_circle",
    name: "Circular panel",
    host: { kind: "circle", radius_mm: 110 },
    placement: { translate_x_mm: 0, translate_y_mm: 0, rotate_deg: 0, scale: 1, clip_to_host: true },
  },
  {
    id: "builtin_strip",
    name: "Wide strip",
    host: { kind: "rect", width_mm: 300, height_mm: 80 },
    placement: { translate_x_mm: 0, translate_y_mm: 0, rotate_deg: 0, scale: 1, clip_to_host: true },
  },
];

function loadUserPresets(): PlacementPreset[] {
  try {
    return JSON.parse(localStorage.getItem(PRESETS_KEY) || "[]");
  } catch {
    return [];
  }
}

const userPresets = ref<PlacementPreset[]>(loadUserPresets());

const presets = computed(() => [
  ...builtinPresets,
  ...userPresets.value,
]);

const canDeletePreset = computed(() =>
  userPresets.value.some((p) => p.id === selectedPresetId.value)
);

const selectedUserPreset = computed(() =>
  userPresets.value.find((p) => p.id === selectedPresetId.value) ?? null
);

const isDirty = computed(() => {
  const p = presets.value.find((x) => x.id === selectedPresetId.value);
  if (!p) return false;
  // Compare current values to preset values
  if (JSON.stringify(host.value) !== JSON.stringify(p.host)) return true;
  if (JSON.stringify(placement.value) !== JSON.stringify(p.placement)) return true;
  if (p.polygonText !== undefined && polygonText.value !== p.polygonText) return true;
  return false;
});

const starTitle = computed(() => {
  if (!selectedUserPreset.value) return "Save current host + placement as a new preset";
  if (isDirty.value) return `Unsaved changes (●). Click to overwrite or save as new: ${selectedUserPreset.value.name}`;
  return `Update preset: ${selectedUserPreset.value.name}`;
});

/* -------------------------
   Preset Actions
-------------------------- */
function applyPreset(p: PlacementPreset) {
  host.value = { ...p.host };
  placement.value = { ...p.placement };
  polygonText.value = p.polygonText ?? polygonText.value;
}

function applySelectedPreset() {
  const p = presets.value.find((x) => x.id === selectedPresetId.value);
  if (p) applyPreset(p);
}

function savePreset() {
  // Use the modal for saving new presets
  showSaveModal.value = true;
}

function deletePreset() {
  // Open confirmation modal instead of browser confirm() (32.6.5)
  showDeleteModal.value = true;
}

function confirmDelete() {
  // Called when user confirms deletion in modal
  const presetName = selectedUserPreset.value?.name ?? "preset";
  userPresets.value = userPresets.value.filter(
    (p) => p.id !== selectedPresetId.value
  );
  localStorage.setItem(PRESETS_KEY, JSON.stringify(userPresets.value));
  selectedPresetId.value = "";
  showDeleteModal.value = false;
  toast.info(`Preset "${presetName}" deleted`);
}

function defaultPresetName(): string {
  const k = host.value?.kind ?? "host";
  if (k === "rect") return `Rect ${host.value.width_mm ?? "?"}×${host.value.height_mm ?? "?"}`;
  if (k === "circle") return `Circle r${host.value.radius_mm ?? "?"}`;
  if (k === "polygon") return "Polygon";
  return "Preset";
}

function savePresetFromCurrent() {
  // If a user preset is selected and not dirty, update silently (fast path)
  if (selectedUserPreset.value && !isDirty.value) {
    const updated = {
      ...selectedUserPreset.value,
      host: structuredClone(host.value),
      placement: structuredClone(placement.value),
      polygonText: polygonText.value,
    };
    userPresets.value = userPresets.value.map((p) => (p.id === updated.id ? updated : p));
    localStorage.setItem(PRESETS_KEY, JSON.stringify(userPresets.value));
    selectedPresetId.value = updated.id;
    toast.success(`Preset "${updated.name}" updated`);
    return;
  }

  // Otherwise open the modal (dirty preset or new preset)
  showSaveModal.value = true;
}

function handleOverwrite() {
  if (!selectedUserPreset.value) return;

  const updated = {
    ...selectedUserPreset.value,
    host: structuredClone(host.value),
    placement: structuredClone(placement.value),
    polygonText: polygonText.value,
  };
  userPresets.value = userPresets.value.map((p) => (p.id === updated.id ? updated : p));
  localStorage.setItem(PRESETS_KEY, JSON.stringify(userPresets.value));
  selectedPresetId.value = updated.id;
  toast.success(`Preset "${updated.name}" overwritten`);
}

function handleSaveNew(name: string) {
  const preset: PlacementPreset = {
    id: crypto.randomUUID(),
    name,
    host: structuredClone(host.value),
    placement: structuredClone(placement.value),
    polygonText: polygonText.value,
  };

  userPresets.value.push(preset);
  localStorage.setItem(PRESETS_KEY, JSON.stringify(userPresets.value));
  selectedPresetId.value = preset.id;
  toast.success(`Preset "${name}" saved`);
}

/* -------------------------
   Preview
-------------------------- */
async function runPreview() {
  loading.value = true;
  err.value = null;
  try {
    const res = await previewPlacementSvg({
      ornament: store.currentParams,
      host: host.value,
      placement: placement.value,
    });
    svg.value = res.svg;
    lastUpdated.value = new Date().toLocaleTimeString();
  } catch (e: any) {
    err.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

function resetDefaults() {
  applyPreset(builtinPresets[0]);
  svg.value = "";
  lastUpdated.value = "";
}

/* Auto preview once */
watch(
  () => store.currentParams,
  () => {
    if (!svg.value) runPreview();
  },
  { deep: true }
);
</script>

<style scoped>
.panel {
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 12px;
  padding: 12px;
}
.hdr .title { font-weight: 700; }
.hdr .sub { font-size: 12px; opacity: 0.7; }

.presets {
  margin: 10px 0;
}
.presetRow {
  display: flex;
  gap: 6px;
}
select {
  flex: 1;
}

.grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 12px;
}

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
  background: rgba(0,0,0,0.1);
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
button.danger {
  color: #b00020;
}
button.star {
  width: 40px;
  padding: 6px 0;
  font-weight: 800;
}

.preview {
  border: 1px dashed rgba(0,0,0,0.15);
  border-radius: 12px;
  padding: 10px;
}
.previewHdr {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.svgBox {
  background: rgba(0,0,0,0.02);
  border-radius: 10px;
  padding: 10px;
}
.err {
  color: #b00020;
  font-size: 12px;
}
</style>
