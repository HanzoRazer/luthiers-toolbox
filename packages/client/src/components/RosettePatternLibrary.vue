<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, onMounted, computed } from "vue";
import { useToastStore } from "@/stores/toastStore";
import TraditionalPanel from './rosette_library/TraditionalPanel.vue';
import ModernPanel from './rosette_library/ModernPanel.vue';

// Adapter for PrimeVue-style toast API
const _toastStore = useToastStore();
const toast = {
  add(opts: { severity: string; summary?: string; detail?: string; life?: number }) {
    const msg = opts.detail || opts.summary || "Notification";
    const method = opts.severity as "success" | "error" | "warning" | "info";
    if (method in _toastStore) {
      (_toastStore as any)[method](msg, opts.life);
    } else {
      _toastStore.info(msg, opts.life);
    }
  }
};

// State
const patterns = ref<any[]>([]);
const selectedPattern = ref<any | null>(null);
const selectedCategory = ref<string | null>(null);
const categories = ref<string[]>([]);
const isLoading = ref(false);
const generationMode = ref<"traditional" | "modern">("traditional");

// Traditional method state
const traditionalResult = ref<any | null>(null);
const chipLength = ref(2.0);
const wasteFactor = ref(0.15);

// Modern method state
const modernResult = ref<any | null>(null);
const patternName = ref("Custom Rosette");
const soundholeDiameter = ref(90);
const rings = ref<any[]>([
  {
    inner_diameter_mm: 90,
    outer_diameter_mm: 94,
    pattern_type: "solid",
    primary_color: "black",
    secondary_color: "white",
    segment_count: null,
  },
]);

// Computed
const filteredPatterns = computed(() => {
  if (!selectedCategory.value) return patterns.value;
  return patterns.value.filter((p) => p.category === selectedCategory.value);
});

// Load patterns on mount
onMounted(async () => {
  await loadPatterns();
});

async function loadPatterns() {
  isLoading.value = true;
  try {
    const response = await api("/api/cam/rosette/patterns/patterns");
    if (!response.ok) {
      throw new Error("Failed to load patterns");
    }

    const data = await response.json();
    patterns.value = data.patterns;
    categories.value = data.categories;

    toast.add({
      severity: "success",
      summary: "Patterns Loaded",
      detail: `${data.total_patterns} patterns available`,
      life: 3000,
    });
  } catch (error: any) {
    toast.add({
      severity: "error",
      summary: "Load Failed",
      detail: error.message || "Could not load pattern catalog",
      life: 5000,
    });
  } finally {
    isLoading.value = false;
  }
}

function selectPattern(pattern: any) {
  selectedPattern.value = pattern;
  traditionalResult.value = null;
  modernResult.value = null;
}

async function generateTraditional() {
  if (!selectedPattern.value) {
    toast.add({
      severity: "warn",
      summary: "No Pattern Selected",
      detail: "Please select a pattern first",
      life: 3000,
    });
    return;
  }

  isLoading.value = true;
  try {
    const response = await api("/api/cam/rosette/patterns/generate_traditional",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_id: selectedPattern.value.id,
          chip_length_mm: chipLength.value,
          waste_factor: wasteFactor.value,
        }),
      }
    );

    if (!response.ok) {
      throw new Error("Generation failed");
    }

    traditionalResult.value = await response.json();

    toast.add({
      severity: "success",
      summary: "Pattern Generated",
      detail: `${selectedPattern.value.name} generated successfully`,
      life: 3000,
    });
  } catch (error: any) {
    toast.add({
      severity: "error",
      summary: "Generation Failed",
      detail: error.message,
      life: 5000,
    });
  } finally {
    isLoading.value = false;
  }
}

async function generateModern() {
  isLoading.value = true;
  try {
    const response = await api("/api/cam/rosette/patterns/generate_modern", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: patternName.value,
        rings: rings.value,
        soundhole_diameter_mm: soundholeDiameter.value,
        chip_length_mm: chipLength.value,
      }),
    });

    if (!response.ok) {
      throw new Error("Generation failed");
    }

    modernResult.value = await response.json();

    toast.add({
      severity: "success",
      summary: "Pattern Generated",
      detail: `${patternName.value} generated successfully`,
      life: 3000,
    });
  } catch (error: any) {
    toast.add({
      severity: "error",
      summary: "Generation Failed",
      detail: error.message,
      life: 5000,
    });
  } finally {
    isLoading.value = false;
  }
}

function addRing() {
  const lastRing = rings.value[rings.value.length - 1];
  rings.value.push({
    inner_diameter_mm: lastRing.outer_diameter_mm,
    outer_diameter_mm: lastRing.outer_diameter_mm + 4,
    pattern_type: "solid",
    primary_color: "black",
    secondary_color: "white",
    segment_count: null,
  });
}

function removeRing(index: number) {
  if (rings.value.length > 1) {
    rings.value.splice(index, 1);
  }
}

function downloadDXF(content: string, filename: string) {
  const blob = new Blob([content], { type: "application/dxf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadSVG(content: string, filename: string) {
  const blob = new Blob([content], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadJSON(data: any, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="rosette-pattern-library">
    <Toast />

    <div class="header">
      <h1>🎸 Rosette Pattern Library</h1>
      <p class="subtitle">
        24 Historical Patterns - Traditional Matrix + Modern Parametric Methods
      </p>
    </div>

    <div class="mode-selector">
      <div class="p-buttonset">
        <Button
          label="Traditional Matrix"
          :class="{ 'p-button-primary': generationMode === 'traditional' }"
          @click="generationMode = 'traditional'"
        />
        <Button
          label="Modern Parametric"
          :class="{ 'p-button-primary': generationMode === 'modern' }"
          @click="generationMode = 'modern'"
        />
      </div>
    </div>

    <!-- Traditional Method -->
    <TraditionalPanel
      v-if="generationMode === 'traditional'"
      :selected-pattern="selectedPattern"
      v-model:selected-category="selectedCategory"
      :categories="categories"
      :filtered-patterns="filteredPatterns"
      v-model:chip-length="chipLength"
      v-model:waste-factor="wasteFactor"
      :result="traditionalResult"
      :is-loading="isLoading"
      @select-pattern="selectPattern"
      @generate="generateTraditional"
      @download-json="downloadJSON"
    />

    <!-- Modern Parametric Method -->
    <ModernPanel
      v-if="generationMode === 'modern'"
      v-model:pattern-name="patternName"
      v-model:soundhole-diameter="soundholeDiameter"
      :rings="rings"
      :result="modernResult"
      :is-loading="isLoading"
      @add-ring="addRing"
      @remove-ring="removeRing"
      @generate="generateModern"
      @download-dxf="downloadDXF"
      @download-svg="downloadSVG"
      @download-json="downloadJSON"
    />
  </div>
</template>

<style scoped>
.rosette-pattern-library {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 2rem;
  text-align: center;
}

.header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
}

.subtitle {
  color: #6c757d;
  margin: 0;
}

.mode-selector {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}
</style>
