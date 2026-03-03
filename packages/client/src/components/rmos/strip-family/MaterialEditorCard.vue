<script setup lang="ts">
/* eslint-disable vue/no-mutating-props -- Form editor with v-model on object prop is intentional */
/**
 * MaterialEditorCard - Single material editor for strip family
 * Extracted from MixedMaterialStripFamilyEditor.vue
 */
import type { MaterialSpec } from '@/models/strip_family'

defineProps<{
  material: MaterialSpec
  index: number
  styles: Record<string, string>
}>()

const emit = defineEmits<{
  'remove': []
}>()
</script>

<template>
  <div :class="styles.materialEditor">
    <div :class="styles.materialHeader">
      <span :class="styles.materialIndex">#{{ index + 1 }}</span>
      <button
        :class="styles.btnRemove"
        @click="emit('remove')"
      >
        ×
      </button>
    </div>

    <div :class="styles.materialFields">
      <label>Material Type</label>
      <select
        v-model="material.type"
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
        v-model="material.species"
        type="text"
        :class="styles.inputText"
        placeholder="e.g. Rosewood, Abalone, Copper"
      >

      <label>Thickness (mm)</label>
      <input
        v-model.number="material.thickness_mm"
        type="number"
        step="0.01"
        :class="styles.inputText"
      >

      <label>Finish</label>
      <input
        v-model="material.finish"
        type="text"
        :class="styles.inputText"
        placeholder="e.g. polished, matte, oxidized"
      >

      <label>CAM Profile (optional)</label>
      <input
        v-model="material.cam_profile"
        type="text"
        :class="styles.inputText"
        placeholder="e.g. hardwood_fast, metal_slow"
      >

      <!-- Visual Properties -->
      <details
        v-if="material.visual"
        :class="styles.visualDetails"
      >
        <summary>Visual Properties</summary>
        <label>Base Color</label>
        <input
          v-model="material.visual.base_color"
          type="color"
          :class="styles.inputColor"
        >

        <label>Reflectivity (0-1)</label>
        <input
          v-model.number="material.visual.reflectivity"
          type="number"
          step="0.1"
          min="0"
          max="1"
          :class="styles.inputText"
        >

        <label>Iridescence (0-1)</label>
        <input
          v-model.number="material.visual.iridescence"
          type="number"
          step="0.1"
          min="0"
          max="1"
          :class="styles.inputText"
        >

        <label>Texture Map URL</label>
        <input
          v-model="material.visual.texture_map"
          type="text"
          :class="styles.inputText"
          placeholder="Optional texture URL"
        >

        <label>Burn Gradient (optional JSON)</label>
        <textarea
          v-model="(material.visual as any).burn_gradient"
          :class="styles.inputTextarea"
          rows="2"
          placeholder="{&quot;start&quot;:&quot;#000&quot;,&quot;end&quot;:&quot;#8b4513&quot;}"
        />
      </details>
    </div>
  </div>
</template>
