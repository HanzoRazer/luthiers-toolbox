<script setup lang="ts">
import { ref, computed } from "vue";
import { useToast } from "primevue/usetoast";

const toast = useToast();

// Upload state
const selectedFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
const isUploading = ref(false);

// Conversion settings
const outputWidth = ref(100);
const fitToRing = ref(false);
const ringInner = ref(45);
const ringOuter = ref(55);
const simplify = ref(1.0);
const invert = ref(false);

// Results
const svgContent = ref<string | null>(null);
const dxfContent = ref<string | null>(null);
const stats = ref<any>(null);

// File input handling
function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];

    // Validate file type
    if (!file.type.startsWith("image/")) {
      toast.add({
        severity: "error",
        summary: "Invalid File",
        detail: "Please select an image file (JPG, PNG, etc.)",
        life: 3000,
      });
      return;
    }

    selectedFile.value = file;

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewUrl.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }
}

function clearFile() {
  selectedFile.value = null;
  previewUrl.value = null;
  svgContent.value = null;
  dxfContent.value = null;
  stats.value = null;
}

// Convert photo to SVG/DXF
async function convertPhoto() {
  if (!selectedFile.value) {
    toast.add({
      severity: "warn",
      summary: "No File Selected",
      detail: "Please select an image file first",
      life: 3000,
    });
    return;
  }

  isUploading.value = true;

  try {
    const formData = new FormData();
    formData.append("file", selectedFile.value);

    // Build query params
    const params = new URLSearchParams({
      output_width_mm: outputWidth.value.toString(),
      fit_to_ring: fitToRing.value.toString(),
      ring_inner_mm: ringInner.value.toString(),
      ring_outer_mm: ringOuter.value.toString(),
      simplify: simplify.value.toString(),
      invert: invert.value.toString(),
    });

    const response = await fetch(`/api/cam/rosette/import_photo?${params}`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Conversion failed");
    }

    const result = await response.json();

    svgContent.value = result.svg_content;
    dxfContent.value = result.dxf_content;
    stats.value = result.stats;

    toast.add({
      severity: "success",
      summary: "Conversion Complete",
      detail: `Found ${result.stats.contour_count} contours with ${result.stats.total_points} points`,
      life: 5000,
    });
  } catch (error: any) {
    toast.add({
      severity: "error",
      summary: "Conversion Failed",
      detail: error.message || "Unknown error occurred",
      life: 5000,
    });
  } finally {
    isUploading.value = false;
  }
}

// Download SVG
function downloadSVG() {
  if (!svgContent.value) return;

  const blob = new Blob([svgContent.value], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `rosette_converted_${Date.now()}.svg`;
  a.click();
  URL.revokeObjectURL(url);
}

// Download DXF
function downloadDXF() {
  if (!dxfContent.value) return;

  const blob = new Blob([dxfContent.value], { type: "application/dxf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `rosette_converted_${Date.now()}.dxf`;
  a.click();
  URL.revokeObjectURL(url);
}

// Computed
const hasResults = computed(() => svgContent.value !== null);
const canConvert = computed(
  () => selectedFile.value !== null && !isUploading.value
);
</script>

<template>
  <div class="rosette-photo-import">
    <Toast />

    <div class="p-card">
      <div class="p-card-header">
        <h2>📷 Rosette Photo Import</h2>
        <p class="subtitle">
          Convert photos, screenshots, or scans to CNC-ready vectors
        </p>
      </div>

      <div class="p-card-body">
        <!-- File Upload Section -->
        <div class="upload-section">
          <h3>1. Upload Image</h3>

          <div class="file-input-wrapper">
            <input
              type="file"
              id="photoInput"
              accept="image/*"
              @change="onFileSelected"
              style="display: none"
            />
            <Button
              label="Choose Image File"
              icon="pi pi-upload"
              @click="() => document.getElementById('photoInput')?.click()"
              :disabled="isUploading"
            />

            <span v-if="selectedFile" class="file-name">
              {{ selectedFile.name }}
            </span>

            <Button
              v-if="selectedFile"
              icon="pi pi-times"
              class="p-button-text p-button-danger"
              @click="clearFile"
              :disabled="isUploading"
            />
          </div>

          <!-- Image Preview -->
          <div v-if="previewUrl" class="image-preview">
            <img :src="previewUrl" alt="Preview" />
          </div>
        </div>

        <!-- Settings Section -->
        <div class="settings-section">
          <h3>2. Configure Settings</h3>

          <div class="settings-grid">
            <div class="field">
              <label for="outputWidth">Output Width (mm)</label>
              <InputNumber
                id="outputWidth"
                v-model="outputWidth"
                :min="10"
                :max="500"
                :disabled="isUploading"
              />
            </div>

            <div class="field">
              <label for="simplify">Simplification</label>
              <InputNumber
                id="simplify"
                v-model="simplify"
                :min="0.1"
                :max="10"
                :step="0.1"
                :disabled="isUploading"
              />
              <small>Higher = simpler paths</small>
            </div>

            <div class="field checkbox">
              <Checkbox
                id="fitToRing"
                v-model="fitToRing"
                :binary="true"
                :disabled="isUploading"
              />
              <label for="fitToRing">Fit to Circular Ring</label>
            </div>

            <div class="field checkbox">
              <Checkbox
                id="invert"
                v-model="invert"
                :binary="true"
                :disabled="isUploading"
              />
              <label for="invert">Invert Colors</label>
            </div>
          </div>

          <!-- Ring Dimensions (conditional) -->
          <div v-if="fitToRing" class="ring-settings">
            <h4>Ring Dimensions</h4>
            <div class="settings-grid">
              <div class="field">
                <label for="ringInner">Inner Diameter (mm)</label>
                <InputNumber
                  id="ringInner"
                  v-model="ringInner"
                  :min="10"
                  :max="200"
                  :disabled="isUploading"
                />
              </div>

              <div class="field">
                <label for="ringOuter">Outer Diameter (mm)</label>
                <InputNumber
                  id="ringOuter"
                  v-model="ringOuter"
                  :min="20"
                  :max="300"
                  :disabled="isUploading"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Convert Button -->
        <div class="action-section">
          <h3>3. Convert</h3>
          <Button
            label="Convert to SVG + DXF"
            icon="pi pi-cog"
            :loading="isUploading"
            :disabled="!canConvert"
            @click="convertPhoto"
            class="p-button-lg"
          />
        </div>

        <!-- Results Section -->
        <div v-if="hasResults" class="results-section">
          <h3>4. Results</h3>

          <!-- Stats -->
          <div v-if="stats" class="stats-grid">
            <div class="stat-card">
              <i class="pi pi-chart-line"></i>
              <div class="stat-value">{{ stats.contour_count }}</div>
              <div class="stat-label">Contours</div>
            </div>

            <div class="stat-card">
              <i class="pi pi-circle"></i>
              <div class="stat-value">{{ stats.total_points }}</div>
              <div class="stat-label">Points</div>
            </div>

            <div class="stat-card">
              <i class="pi pi-arrows-h"></i>
              <div class="stat-value">{{ stats.output_width_mm }}mm</div>
              <div class="stat-label">Width</div>
            </div>
          </div>

          <!-- SVG Preview -->
          <div class="svg-preview">
            <h4>SVG Preview</h4>
            <div class="preview-box" v-html="svgContent"></div>
          </div>

          <!-- Download Buttons -->
          <div class="download-actions">
            <Button
              label="Download SVG"
              icon="pi pi-download"
              @click="downloadSVG"
              class="p-button-success"
            />
            <Button
              label="Download DXF"
              icon="pi pi-download"
              @click="downloadDXF"
              class="p-button-success"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rosette-photo-import {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.p-card-header {
  padding: 1.5rem;
  border-bottom: 1px solid #dee2e6;
}

.p-card-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.75rem;
}

.subtitle {
  color: #6c757d;
  margin: 0;
}

.p-card-body {
  padding: 1.5rem;
}

.upload-section,
.settings-section,
.action-section,
.results-section {
  margin-bottom: 2rem;
}

.upload-section h3,
.settings-section h3,
.action-section h3,
.results-section h3 {
  margin-bottom: 1rem;
  color: #495057;
  font-size: 1.25rem;
}

.file-input-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.file-name {
  color: #495057;
  font-size: 0.9rem;
}

.image-preview {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  text-align: center;
}

.image-preview img {
  max-width: 100%;
  max-height: 400px;
  border-radius: 4px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field.checkbox {
  flex-direction: row;
  align-items: center;
}

.field.checkbox label {
  margin-left: 0.5rem;
}

.field label {
  font-weight: 500;
  color: #495057;
}

.field small {
  color: #6c757d;
  font-size: 0.85rem;
}

.ring-settings {
  margin-top: 1rem;
  padding: 1rem;
  background: #e9ecef;
  border-radius: 4px;
}

.ring-settings h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  text-align: center;
}

.stat-card i {
  font-size: 2rem;
  color: #007bff;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #495057;
}

.stat-label {
  color: #6c757d;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.svg-preview {
  margin-bottom: 1.5rem;
}

.svg-preview h4 {
  margin-bottom: 0.5rem;
}

.preview-box {
  padding: 1rem;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.download-actions {
  display: flex;
  gap: 1rem;
}
</style>
