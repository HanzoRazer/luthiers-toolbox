<template>
  <div :class="styles.mixedMaterialEditor">
    <!-- Header -->
    <div :class="styles.editorHeader">
      <h2>Mixed-Material Strip Family Lab</h2>
      <p :class="styles.subtitle">
        Create rosette strip families from curated templates or design custom combinations
      </p>
    </div>

    <!-- Error Display -->
    <div
      v-if="store.error"
      :class="styles.errorBanner"
    >
      {{ store.error }}
    </div>

    <!-- Loading Overlay -->
    <div
      v-if="store.loading"
      :class="styles.loadingOverlay"
    >
      <div :class="styles.spinner" />
      <span>Loading...</span>
    </div>

    <div :class="styles.editorLayout">
      <!-- Left Panel: Template Library -->
      <div :class="styles.templateLibrary">
        <h3>Template Library</h3>
        <p :class="styles.libraryHint">
          Click "Apply" to instantiate a template into your workspace
        </p>

        <div
          v-if="store.templates.length === 0 && !store.loading"
          :class="styles.emptyState"
        >
          <button
            :class="styles.btnPrimary"
            @click="store.fetchTemplates()"
          >
            Load Templates
          </button>
        </div>

        <div :class="styles.templateGrid">
          <div
            v-for="tpl in store.templates"
            :key="tpl.id"
            :class="styles.templateCard"
          >
            <div :class="styles.templateHeader">
              <h4>{{ tpl.name }}</h4>
              <span :class="styles.templateBadge">{{ tpl.materials?.length || 0 }} materials</span>
            </div>

            <div :class="styles.templateMaterials">
              <div
                v-for="(mat, idx) in tpl.materials?.slice(0, 3)"
                :key="idx"
                :class="styles.materialPreview"
                :style="{ backgroundColor: mat.visual?.base_color || '#ccc' }"
              >
                <span :class="styles.materialLabel">{{ mat.species || mat.type }}</span>
              </div>
            </div>

            <div :class="styles.templateMeta">
              <span>Width: {{ tpl.default_width_mm || 0 }}mm</span>
              <span>Seq: {{ tpl.sequence || 0 }}</span>
              <span>Lane: {{ tpl.lane || 'experimental' }}</span>
            </div>

            <button
              :class="styles.btnApply"
              :disabled="store.loading"
              @click="applyTemplate(tpl.id)"
            >
              Apply Template
            </button>
          </div>
        </div>
      </div>

      <!-- Right Panel: Selected Family Editor -->
      <div :class="styles.familyEditor">
        <div
          v-if="!store.selected"
          :class="styles.editorPlaceholder"
        >
          <p>Select a template to begin editing</p>
        </div>

        <div
          v-else
          :class="styles.editorContent"
        >
          <h3>Editing: {{ workingFamily.name }}</h3>

          <!-- Basic Properties -->
          <div :class="styles.editorSection">
            <label>Name</label>
            <input
              v-model="workingFamily.name"
              type="text"
              :class="styles.inputText"
            >

            <label>Default Width (mm)</label>
            <input
              v-model.number="workingFamily.default_width_mm"
              type="number"
              step="0.1"
              :class="styles.inputText"
            >

            <label>Sequence</label>
            <input
              v-model.number="workingFamily.sequence"
              type="number"
              :class="styles.inputText"
            >

            <label>Quality Lane</label>
            <select
              v-model="workingFamily.lane"
              :class="styles.inputSelect"
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
              :class="styles.inputTextarea"
              rows="3"
            />
          </div>

          <!-- Materials Editor -->
          <div :class="styles.editorSection">
            <div :class="styles.sectionHeader">
              <h4>Materials ({{ workingFamily.materials?.length || 0 }})</h4>
              <button
                :class="styles.btnSecondary"
                @click="addMaterial"
              >
                + Add Material
              </button>
            </div>

            <div
              v-for="(mat, idx) in workingFamily.materials"
              :key="idx"
              :class="styles.materialEditor"
            >
              <div :class="styles.materialHeader">
                <span :class="styles.materialIndex">#{{ idx + 1 }}</span>
                <button
                  :class="styles.btnRemove"
                  @click="removeMaterial(idx)"
                >
                  ×
                </button>
              </div>

              <div :class="styles.materialFields">
                <label>Material Type</label>
                <select
                  v-model="mat.type"
                  :class="styles.inputSelect"
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
                  :class="styles.inputText"
                  placeholder="e.g. Rosewood, Abalone, Copper"
                >

                <label>Thickness (mm)</label>
                <input
                  v-model.number="mat.thickness_mm"
                  type="number"
                  step="0.01"
                  :class="styles.inputText"
                >

                <label>Finish</label>
                <input
                  v-model="mat.finish"
                  type="text"
                  :class="styles.inputText"
                  placeholder="e.g. polished, matte, oxidized"
                >

                <label>CAM Profile (optional)</label>
                <input
                  v-model="mat.cam_profile"
                  type="text"
                  :class="styles.inputText"
                  placeholder="e.g. hardwood_fast, metal_slow"
                >

                <!-- Visual Properties -->
                <details
                  v-if="mat.visual"
                  :class="styles.visualDetails"
                >
                  <summary>Visual Properties</summary>
                  <label>Base Color</label>
                  <input
                    v-model="mat.visual.base_color"
                    type="color"
                    :class="styles.inputColor"
                  >

                  <label>Reflectivity (0-1)</label>
                  <input
                    v-model.number="mat.visual.reflectivity"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    :class="styles.inputText"
                  >

                  <label>Iridescence (0-1)</label>
                  <input
                    v-model.number="mat.visual.iridescence"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    :class="styles.inputText"
                  >

                  <label>Texture Map URL</label>
                  <input
                    v-model="mat.visual.texture_map"
                    type="text"
                    :class="styles.inputText"
                    placeholder="Optional texture URL"
                  >

                  <label>Burn Gradient (optional JSON)</label>
                  <textarea
                    v-model="(mat.visual as any).burn_gradient"
                    :class="styles.inputTextarea"
                    rows="2"
                    placeholder="{&quot;start&quot;:&quot;#000&quot;,&quot;end&quot;:&quot;#8b4513&quot;}"
                  />
                </details>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div :class="styles.editorActions">
            <button
              :class="styles.btnPrimary"
              :disabled="store.loading"
              @click="saveChanges"
            >
              Save Changes
            </button>
            <button
              :class="styles.btnSecondary"
              @click="cancelEdit"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Panel: Existing Families -->
    <div :class="styles.existingFamilies">
      <h3>Existing Strip Families ({{ store.families.length }})</h3>
      <div :class="styles.familiesList">
        <div
          v-for="family in store.families"
          :key="family.id"
          :class="[styles.familyItem, { [styles.familyItemSelected]: store.selected?.id === family.id }]"
          @click="selectFamily(family)"
        >
          <span :class="styles.familyName">{{ family.name }}</span>
          <span :class="styles.familyBadge">{{ family.materials?.length || 0 }} mats</span>
          <span :class="styles.familyLane">{{ family.lane }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { useStripFamilyStore } from '@/stores/useStripFamilyStore'
import styles from './MixedMaterialStripFamilyEditor.module.css'
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
