<template>
  <div class="modern-section">
    <div class="content-grid">
      <!-- Ring Designer -->
      <div class="designer-panel">
        <h2>Ring Designer</h2>

        <div class="field">
          <label>Pattern Name</label>
          <InputText
            :model-value="patternName"
            @update:model-value="emit('update:patternName', $event)"
          />
        </div>

        <div class="field">
          <label>Soundhole Diameter (mm)</label>
          <InputNumber
            :model-value="soundholeDiameter"
            :min="50"
            :max="150"
            @update:model-value="emit('update:soundholeDiameter', $event)"
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
                @click="emit('remove-ring', idx)"
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
            @click="emit('add-ring')"
          />
        </div>

        <Button
          label="Generate Modern Pattern"
          icon="pi pi-cog"
          :loading="isLoading"
          class="w-full"
          @click="emit('generate')"
        />
      </div>

      <!-- Results Panel -->
      <div class="results-panel">
        <h2>Results</h2>

        <div v-if="result">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-label">
                Rings
              </div>
              <div class="stat-value">
                {{ result.spec.rings.length }}
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Path Segments
              </div>
              <div class="stat-value">
                {{ result.paths.length }}
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Est. Cut Time
              </div>
              <div class="stat-value">
                {{ result.estimated_cut_time_min.toFixed(1) }} min
              </div>
            </div>
          </div>

          <div class="bom-section">
            <h4>Bill of Materials (area mm²)</h4>
            <div
              v-for="(area, material) in result.bom"
              :key="material"
              class="bom-row"
            >
              <span>{{ material }}:</span>
              <strong>{{ area.toFixed(1) }} mm²</strong>
            </div>
          </div>

          <div
            v-if="result.svg_content"
            class="svg-preview"
          >
            <h4>SVG Preview</h4>
            <div
              class="preview-box"
              v-html="result.svg_content"
            />
          </div>

          <div class="download-actions">
            <Button
              v-if="result.dxf_content"
              label="Download DXF"
              icon="pi pi-download"
              class="p-button-success"
              @click="emit('download-dxf', result.dxf_content, `${patternName.replace(/\s+/g, '_')}.dxf`)"
            />
            <Button
              v-if="result.svg_content"
              label="Download SVG"
              icon="pi pi-download"
              class="p-button-success"
              @click="emit('download-svg', result.svg_content, `${patternName.replace(/\s+/g, '_')}.svg`)"
            />
            <Button
              label="Download JSON"
              icon="pi pi-download"
              @click="emit('download-json', result, `${patternName.replace(/\s+/g, '_')}.json`)"
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
</template>

<script setup lang="ts">
interface Ring {
  inner_diameter_mm: number
  outer_diameter_mm: number
  pattern_type: string
  primary_color: string
  secondary_color: string
  segment_count: number | null
}

defineProps<{
  patternName: string
  soundholeDiameter: number
  rings: Ring[]
  result: any | null
  isLoading: boolean
}>()

const emit = defineEmits<{
  'update:patternName': [value: string]
  'update:soundholeDiameter': [value: number]
  'add-ring': []
  'remove-ring': [index: number]
  'generate': []
  'download-dxf': [content: string, filename: string]
  'download-svg': [content: string, filename: string]
  'download-json': [data: any, filename: string]
}>()
</script>

<style scoped>
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.designer-panel,
.results-panel {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.designer-panel h2,
.results-panel h2 {
  margin-top: 0;
  font-size: 1.5rem;
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

.bom-section {
  margin: 1.5rem 0;
}

.bom-section h4 {
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.bom-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: #f8f9fa;
  margin-bottom: 0.25rem;
  border-radius: 4px;
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
