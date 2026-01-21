<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useToastStore } from "@/stores/toastStore";

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
    const response = await fetch("/api/cam/rosette/patterns/patterns");
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
    const response = await fetch(
      "/api/cam/rosette/patterns/generate_traditional",
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
    const response = await fetch("/api/cam/rosette/patterns/generate_modern", {
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
    <div
      v-if="generationMode === 'traditional'"
      class="traditional-section"
    >
      <div class="content-grid">
        <!-- Pattern Catalog -->
        <div class="catalog-panel">
          <h2>Pattern Catalog</h2>

          <div class="category-filter">
            <Button
              label="All"
              :class="{ 'p-button-outlined': selectedCategory !== null }"
              size="small"
              @click="selectedCategory = null"
            />
            <Button
              v-for="cat in categories"
              :key="cat"
              :label="cat"
              :class="{ 'p-button-outlined': selectedCategory !== cat }"
              size="small"
              @click="selectedCategory = cat"
            />
          </div>

          <div class="pattern-list">
            <div
              v-for="pattern in filteredPatterns"
              :key="pattern.id"
              class="pattern-card"
              :class="{ selected: selectedPattern?.id === pattern.id }"
              @click="selectPattern(pattern)"
            >
              <div class="pattern-header">
                <strong>{{ pattern.name }}</strong>
                <span class="badge">{{ pattern.category }}</span>
              </div>
              <div class="pattern-info">
                <span>{{ pattern.rows }}×{{ pattern.columns }}</span>
                <span>{{ pattern.materials.join(", ") }}</span>
              </div>
              <div
                v-if="pattern.notes"
                class="pattern-notes"
              >
                {{ pattern.notes }}
              </div>
            </div>
          </div>
        </div>

        <!-- Generation Panel -->
        <div class="generation-panel">
          <h2>Generate Pattern</h2>

          <div
            v-if="selectedPattern"
            class="selected-pattern-info"
          >
            <h3>{{ selectedPattern.name }}</h3>
            <p>{{ selectedPattern.notes }}</p>
          </div>

          <div class="settings-group">
            <div class="field">
              <label>Chip Length (mm)</label>
              <InputNumber
                v-model="chipLength"
                :min="0.5"
                :max="5"
                :step="0.1"
              />
            </div>

            <div class="field">
              <label>Waste Factor (%)</label>
              <InputNumber
                v-model="wasteFactor"
                :min="0"
                :max="0.5"
                :step="0.05"
                :min-fraction-digits="2"
              />
            </div>
          </div>

          <Button
            label="Generate Traditional Pattern"
            icon="pi pi-cog"
            :disabled="!selectedPattern || isLoading"
            :loading="isLoading"
            class="w-full"
            @click="generateTraditional"
          />

          <!-- Results -->
          <div
            v-if="traditionalResult"
            class="results-section"
          >
            <h3>Results</h3>

            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-label">
                  Width
                </div>
                <div class="stat-value">
                  {{
                    traditionalResult.pattern_dimensions.width_mm.toFixed(1)
                  }}
                  mm
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-label">
                  Height
                </div>
                <div class="stat-value">
                  {{
                    traditionalResult.pattern_dimensions.height_mm.toFixed(1)
                  }}
                  mm
                </div>
              </div>
            </div>

            <div class="material-totals">
              <h4>Material Totals (strips needed)</h4>
              <div
                v-for="(count, material) in traditionalResult.material_totals"
                :key="material"
                class="material-row"
              >
                <span>{{ material }}:</span>
                <strong>{{ count }} strips</strong>
              </div>
            </div>

            <div class="cut-list">
              <h4>Cut List (with waste)</h4>
              <div
                v-for="(item, idx) in traditionalResult.cut_list"
                :key="idx"
                class="cut-item"
              >
                {{ item.material }}: {{ item.count }}× @ {{ item.width_mm }}×{{
                  item.length_mm
                }}
                mm
              </div>
            </div>

            <div class="assembly-instructions">
              <h4>Assembly Instructions</h4>
              <ol>
                <li
                  v-for="instr in traditionalResult.assembly_instructions"
                  :key="instr.step"
                >
                  {{ instr.action }}
                </li>
              </ol>
            </div>

            <Button
              label="Download JSON"
              icon="pi pi-download"
              class="w-full"
              @click="
                downloadJSON(
                  traditionalResult,
                  `${selectedPattern.id}_traditional.json`
                )
              "
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Modern Parametric Method -->
    <div
      v-if="generationMode === 'modern'"
      class="modern-section"
    >
      <div class="content-grid">
        <!-- Ring Designer -->
        <div class="designer-panel">
          <h2>Ring Designer</h2>

          <div class="field">
            <label>Pattern Name</label>
            <InputText v-model="patternName" />
          </div>

          <div class="field">
            <label>Soundhole Diameter (mm)</label>
            <InputNumber
              v-model="soundholeDiameter"
              :min="50"
              :max="150"
            />
          </div>

          <div class="rings-list">
            <h4>Rings (inner to outer)</h4>

            <div
              v-for="(ring, idx) in rings"
              :key="idx"
              class="ring-editor"
            >
              <div class="ring-header">
                <strong>Ring {{ idx + 1 }}</strong>
                <Button
                  icon="pi pi-times"
                  class="p-button-text p-button-danger p-button-sm"
                  :disabled="rings.length === 1"
                  @click="removeRing(idx)"
                />
              </div>

              <div class="ring-fields">
                <div class="field-inline">
                  <label>Inner (mm)</label>
                  <InputNumber
                    v-model="ring.inner_diameter_mm"
                    :min="0"
                  />
                </div>
                <div class="field-inline">
                  <label>Outer (mm)</label>
                  <InputNumber
                    v-model="ring.outer_diameter_mm"
                    :min="0"
                  />
                </div>
              </div>

              <div class="field">
                <label>Pattern Type</label>
                <Dropdown
                  v-model="ring.pattern_type"
                  :options="['solid', 'rope', 'herringbone', 'checkerboard']"
                />
              </div>

              <div class="field-inline">
                <div class="field">
                  <label>Primary Color</label>
                  <InputText v-model="ring.primary_color" />
                </div>
                <div class="field">
                  <label>Secondary Color</label>
                  <InputText v-model="ring.secondary_color" />
                </div>
              </div>

              <div
                v-if="ring.pattern_type !== 'solid'"
                class="field"
              >
                <label>Segments (optional)</label>
                <InputNumber
                  v-model="ring.segment_count"
                  :min="1"
                />
              </div>
            </div>

            <Button
              label="Add Ring"
              icon="pi pi-plus"
              class="w-full"
              size="small"
              @click="addRing"
            />
          </div>

          <Button
            label="Generate Modern Pattern"
            icon="pi pi-cog"
            :loading="isLoading"
            class="w-full"
            @click="generateModern"
          />
        </div>

        <!-- Results Panel -->
        <div class="results-panel">
          <h2>Results</h2>

          <div v-if="modernResult">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-label">
                  Rings
                </div>
                <div class="stat-value">
                  {{ modernResult.spec.rings.length }}
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-label">
                  Path Segments
                </div>
                <div class="stat-value">
                  {{ modernResult.paths.length }}
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-label">
                  Est. Cut Time
                </div>
                <div class="stat-value">
                  {{ modernResult.estimated_cut_time_min.toFixed(1) }} min
                </div>
              </div>
            </div>

            <div class="bom-section">
              <h4>Bill of Materials (area mm²)</h4>
              <div
                v-for="(area, material) in modernResult.bom"
                :key="material"
                class="bom-row"
              >
                <span>{{ material }}:</span>
                <strong>{{ area.toFixed(1) }} mm²</strong>
              </div>
            </div>

            <div
              v-if="modernResult.svg_content"
              class="svg-preview"
            >
              <h4>SVG Preview</h4>
              <div
                class="preview-box"
                v-html="modernResult.svg_content"
              />
            </div>

            <div class="download-actions">
              <Button
                v-if="modernResult.dxf_content"
                label="Download DXF"
                icon="pi pi-download"
                class="p-button-success"
                @click="
                  downloadDXF(
                    modernResult.dxf_content,
                    `${patternName.replace(/\s+/g, '_')}.dxf`
                  )
                "
              />
              <Button
                v-if="modernResult.svg_content"
                label="Download SVG"
                icon="pi pi-download"
                class="p-button-success"
                @click="
                  downloadSVG(
                    modernResult.svg_content,
                    `${patternName.replace(/\s+/g, '_')}.svg`
                  )
                "
              />
              <Button
                label="Download JSON"
                icon="pi pi-download"
                @click="
                  downloadJSON(
                    modernResult,
                    `${patternName.replace(/\s+/g, '_')}.json`
                  )
                "
              />
            </div>
          </div>

          <div
            v-else
            class="empty-state"
          >
            <i class="pi pi-info-circle" />
            <p>Configure rings and generate to see results</p>
          </div>
        </div>
      </div>
    </div>
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

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.catalog-panel,
.generation-panel,
.designer-panel,
.results-panel {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.catalog-panel h2,
.generation-panel h2,
.designer-panel h2,
.results-panel h2 {
  margin-top: 0;
  font-size: 1.5rem;
}

.category-filter {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.pattern-list {
  max-height: 600px;
  overflow-y: auto;
}

.pattern-card {
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.pattern-card:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.pattern-card.selected {
  background: #e7f3ff;
  border-color: #007bff;
}

.pattern-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.badge {
  background: #6c757d;
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  text-transform: capitalize;
}

.pattern-info {
  display: flex;
  gap: 1rem;
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.pattern-notes {
  font-size: 0.85rem;
  color: #495057;
  font-style: italic;
}

.settings-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
}

.field {
  margin-bottom: 1rem;
}

.field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #495057;
}

.field-inline {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

.stat-card {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  text-align: center;
}

.stat-label {
  font-size: 0.85rem;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #495057;
}

.material-totals,
.cut-list,
.assembly-instructions,
.bom-section {
  margin: 1.5rem 0;
}

.material-totals h4,
.cut-list h4,
.assembly-instructions h4,
.bom-section h4 {
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.material-row,
.cut-item,
.bom-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: #f8f9fa;
  margin-bottom: 0.25rem;
  border-radius: 4px;
}

.rings-list {
  margin: 1rem 0;
}

.ring-editor {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.ring-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.ring-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.svg-preview {
  margin: 1.5rem 0;
}

.preview-box {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.download-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.w-full {
  width: 100%;
}
</style>
