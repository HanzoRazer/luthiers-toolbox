<template>
  <div class="mixed-material-editor">
    <!-- Header -->
    <div class="editor-header">
      <h2>Mixed-Material Strip Family Lab</h2>
      <p class="subtitle">
        Create rosette strip families from curated templates or design custom combinations
      </p>
    </div>

    <!-- Error Display -->
    <div
      v-if="store.error"
      class="error-banner"
    >
      {{ store.error }}
    </div>

    <!-- Loading Overlay -->
    <div
      v-if="store.loading"
      class="loading-overlay"
    >
      <div class="spinner" />
      <span>Loading...</span>
    </div>

    <div class="editor-layout">
      <!-- Left Panel: Template Library -->
      <div class="template-library">
        <h3>Template Library</h3>
        <p class="library-hint">
          Click "Apply" to instantiate a template into your workspace
        </p>
        
        <div
          v-if="store.templates.length === 0 && !store.loading"
          class="empty-state"
        >
          <button
            class="btn-primary"
            @click="store.fetchTemplates()"
          >
            Load Templates
          </button>
        </div>

        <div class="template-grid">
          <div 
            v-for="tpl in store.templates" 
            :key="tpl.id"
            class="template-card"
          >
            <div class="template-header">
              <h4>{{ tpl.name }}</h4>
              <span class="template-badge">{{ tpl.materials?.length || 0 }} materials</span>
            </div>
            
            <div class="template-materials">
              <div 
                v-for="(mat, idx) in tpl.materials?.slice(0, 3)" 
                :key="idx"
                class="material-preview"
                :style="{ backgroundColor: mat.visual?.base_color || '#ccc' }"
              >
                <span class="material-label">{{ mat.species || mat.type }}</span>
              </div>
            </div>

            <div class="template-meta">
              <span>Width: {{ tpl.default_width_mm || 0 }}mm</span>
              <span>Seq: {{ tpl.sequence || 0 }}</span>
              <span>Lane: {{ tpl.lane || 'experimental' }}</span>
            </div>

            <button 
              class="btn-apply" 
              :disabled="store.loading"
              @click="applyTemplate(tpl.id)"
            >
              Apply Template
            </button>
          </div>
        </div>
      </div>

      <!-- Right Panel: Selected Family Editor -->
      <div class="family-editor">
        <div
          v-if="!store.selected"
          class="editor-placeholder"
        >
          <p>Select a template to begin editing</p>
        </div>

        <div
          v-else
          class="editor-content"
        >
          <h3>Editing: {{ workingFamily.name }}</h3>

          <!-- Basic Properties -->
          <div class="editor-section">
            <label>Name</label>
            <input
              v-model="workingFamily.name"
              type="text"
              class="input-text"
            >

            <label>Default Width (mm)</label>
            <input
              v-model.number="workingFamily.default_width_mm"
              type="number"
              step="0.1"
              class="input-text"
            >

            <label>Sequence</label>
            <input
              v-model.number="workingFamily.sequence"
              type="number"
              class="input-text"
            >

            <label>Quality Lane</label>
            <select
              v-model="workingFamily.lane"
              class="input-select"
            >
              <option value="experimental">
                Experimental
              </option>
              <option value="tuned_v1">
                Tuned v1
              </option>
              <option value="tuned_v2">
                Tuned v2
              </option>
              <option value="safe">
                Safe
              </option>
              <option value="archived">
                Archived
              </option>
            </select>

            <label>Description</label>
            <textarea
              v-model="workingFamily.description"
              class="input-textarea"
              rows="3"
            />
          </div>

          <!-- Materials Editor -->
          <div class="editor-section">
            <div class="section-header">
              <h4>Materials ({{ workingFamily.materials?.length || 0 }})</h4>
              <button
                class="btn-secondary"
                @click="addMaterial"
              >
                + Add Material
              </button>
            </div>

            <div 
              v-for="(mat, idx) in workingFamily.materials" 
              :key="idx"
              class="material-editor"
            >
              <div class="material-header">
                <span class="material-index">#{{ idx + 1 }}</span>
                <button
                  class="btn-remove"
                  @click="removeMaterial(idx)"
                >
                  ×
                </button>
              </div>

              <div class="material-fields">
                <label>Material Type</label>
                <select
                  v-model="mat.type"
                  class="input-select"
                >
                  <option value="wood">
                    Wood
                  </option>
                  <option value="metal">
                    Metal
                  </option>
                  <option value="shell">
                    Shell
                  </option>
                  <option value="paper">
                    Paper
                  </option>
                  <option value="foil">
                    Foil
                  </option>
                  <option value="charred">
                    Charred
                  </option>
                  <option value="resin">
                    Resin
                  </option>
                  <option value="composite">
                    Composite
                  </option>
                </select>

                <label>Species / Name</label>
                <input
                  v-model="mat.species"
                  type="text"
                  class="input-text"
                  placeholder="e.g. Rosewood, Abalone, Copper"
                >

                <label>Thickness (mm)</label>
                <input
                  v-model.number="mat.thickness_mm"
                  type="number"
                  step="0.01"
                  class="input-text"
                >

                <label>Finish</label>
                <input
                  v-model="mat.finish"
                  type="text"
                  class="input-text"
                  placeholder="e.g. polished, matte, oxidized"
                >

                <label>CAM Profile (optional)</label>
                <input
                  v-model="mat.cam_profile"
                  type="text"
                  class="input-text"
                  placeholder="e.g. hardwood_fast, metal_slow"
                >

                <!-- Visual Properties -->
                <details
                  v-if="mat.visual"
                  class="visual-details"
                >
                  <summary>Visual Properties</summary>
                  <label>Base Color</label>
                  <input
                    v-model="mat.visual.base_color"
                    type="color"
                    class="input-color"
                  >

                  <label>Reflectivity (0-1)</label>
                  <input
                    v-model.number="mat.visual.reflectivity"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    class="input-text"
                  >

                  <label>Iridescence (0-1)</label>
                  <input
                    v-model.number="mat.visual.iridescence"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    class="input-text"
                  >

                  <label>Texture Map URL</label>
                  <input
                    v-model="mat.visual.texture_map"
                    type="text"
                    class="input-text"
                    placeholder="Optional texture URL"
                  >

                  <label>Burn Gradient (optional JSON)</label>
                  <textarea
                    v-model="(mat.visual as any).burn_gradient"
                    class="input-textarea"
                    rows="2"
                    placeholder="{&quot;start&quot;:&quot;#000&quot;,&quot;end&quot;:&quot;#8b4513&quot;}"
                  />
                </details>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="editor-actions">
            <button
              class="btn-primary"
              :disabled="store.loading"
              @click="saveChanges"
            >
              Save Changes
            </button>
            <button
              class="btn-secondary"
              @click="cancelEdit"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Panel: Existing Families -->
    <div class="existing-families">
      <h3>Existing Strip Families ({{ store.families.length }})</h3>
      <div class="families-list">
        <div 
          v-for="family in store.families" 
          :key="family.id"
          class="family-item"
          :class="{ selected: store.selected?.id === family.id }"
          @click="selectFamily(family)"
        >
          <span class="family-name">{{ family.name }}</span>
          <span class="family-badge">{{ family.materials?.length || 0 }} mats</span>
          <span class="family-lane">{{ family.lane }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { useStripFamilyStore } from '@/stores/useStripFamilyStore'
import type { StripFamily, MaterialSpec } from '@/models/strip_family'

const store = useStripFamilyStore()

const workingFamily = reactive<Partial<StripFamily>>({
  name: '',
  default_width_mm: 3.0,
  sequence: [],
  lane: 'experimental',
  description: '',
  materials: [],
})

onMounted(() => {
  store.fetchTemplates()
  store.fetchFamilies()
})

watch(() => store.selected, (selected) => {
  if (selected) {
    Object.assign(workingFamily, JSON.parse(JSON.stringify(selected)))
  }
})

function applyTemplate(templateId: string) {
  store.createFromTemplate(templateId)
}

function selectFamily(family: StripFamily) {
  store.select(family)
}

function addMaterial() {
  if (!workingFamily.materials) workingFamily.materials = []
  workingFamily.materials.push({
    key: `mat_${Date.now()}`,
    type: 'wood',
    species: '',
    thickness_mm: 0.5,
    finish: 'polished',
    cam_profile: undefined,
    visual: {
      base_color: '#8b4513',
      reflectivity: 0.3,
      iridescence: false,
      texture_map: undefined,
      burn_gradient: undefined,
    },
  })
}

function removeMaterial(idx: number) {
  if (workingFamily.materials) {
    workingFamily.materials.splice(idx, 1)
  }
}

async function saveChanges() {
  if (!store.selected?.id) return
  await store.updateFamily(store.selected.id, workingFamily)
}

function cancelEdit() {
  store.select(null)
}
</script>

<style scoped>
.mixed-material-editor {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
}

.editor-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.subtitle {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: #666;
}

.error-banner {
  padding: 0.75rem;
  background: #fee;
  border-left: 4px solid #c33;
  color: #c33;
  font-weight: 500;
}

.loading-overlay {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #e3f2fd;
  border-radius: 4px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #1976d2;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.editor-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.template-library,
.family-editor {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.template-library h3,
.family-editor h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  color: #2c3e50;
}

.library-hint {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 1rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
}

.template-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.template-card {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.75rem;
  background: #fafafa;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.template-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #2c3e50;
}

.template-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 12px;
}

.template-materials {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.material-preview {
  flex: 1;
  height: 40px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: white;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.template-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.btn-apply {
  width: 100%;
  padding: 0.5rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-apply:hover:not(:disabled) {
  background: #1565c0;
}

.btn-apply:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.editor-placeholder {
  padding: 4rem 2rem;
  text-align: center;
  color: #999;
}

.editor-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.editor-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #2c3e50;
}

label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #555;
}

.input-text,
.input-select,
.input-textarea {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
}

.input-color {
  width: 60px;
  height: 36px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.material-editor {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.75rem;
  background: #fafafa;
}

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.material-index {
  font-weight: 600;
  color: #1976d2;
}

.btn-remove {
  width: 24px;
  height: 24px;
  padding: 0;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
}

.material-fields {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.visual-details summary {
  cursor: pointer;
  font-weight: 500;
  color: #1976d2;
  margin-bottom: 0.5rem;
}

.editor-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: #1976d2;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1565c0;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e0e0e0;
  color: #555;
}

.btn-secondary:hover {
  background: #d0d0d0;
}

.existing-families {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.existing-families h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1.125rem;
  color: #2c3e50;
}

.families-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.family-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.family-item:hover {
  background: #e3f2fd;
  border-color: #1976d2;
}

.family-item.selected {
  background: #1976d2;
  color: white;
  border-color: #1565c0;
}

.family-badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
  background: #e0e0e0;
  border-radius: 8px;
}

.family-item.selected .family-badge {
  background: rgba(255,255,255,0.3);
}

.family-lane {
  font-size: 0.75rem;
  font-style: italic;
  color: #666;
}

.family-item.selected .family-lane {
  color: rgba(255,255,255,0.9);
}
</style>
