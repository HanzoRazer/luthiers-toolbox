<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import axios from 'axios';

type ArtPreset = {
  id: string;
  lane: string;
  name: string;
  params: Record<string, any>;
  created_at: number;
};

const props = defineProps<{
  lane: string;
  modelValue: string | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void;
  (e: 'presetLoaded', preset: ArtPreset | null): void;
}>();

const presets = ref<ArtPreset[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const selectedId = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

async function loadPresets() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await axios.get('/api/art/presets', {
      params: { lane: props.lane },
    });
    presets.value = data || [];
  } catch (err: any) {
    error.value = err?.message || 'Failed to load presets.';
  } finally {
    loading.value = false;
  }
}

function onSelect() {
  const preset = presets.value.find((p) => p.id === selectedId.value) || null;
  emit('presetLoaded', preset);
}

onMounted(loadPresets);

watch(
  () => props.lane,
  () => loadPresets(),
);
</script>

<template>
  <div class="flex flex-col gap-1 text-xs">
    <label class="text-[11px] text-gray-600">Preset</label>

    <div class="flex items-center gap-2">
      <select
        v-model="selectedId"
        class="border rounded px-2 py-1 text-xs bg-white"
        @change="onSelect"
      >
        <option :value="null">— none —</option>
        <option v-for="preset in presets" :key="preset.id" :value="preset.id">
          {{ preset.name }}
        </option>
      </select>

      <button
        type="button"
        class="rounded border px-2 py-1 bg-gray-50 hover:bg-gray-100 text-[11px]"
        :disabled="loading"
        @click="loadPresets"
      >
        Refresh
      </button>
    </div>

    <div v-if="error" class="text-[11px] text-red-600">
      {{ error }}
    </div>
  </div>
</template>
