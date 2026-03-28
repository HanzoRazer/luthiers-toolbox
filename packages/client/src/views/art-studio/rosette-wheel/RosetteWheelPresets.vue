<script setup lang="ts">
/**
 * RosetteWheelPresets — Library tab with recipes and saved designs
 * Extracted from RosetteWheelView for decomposition
 */
import { ref } from "vue";
import { useRosetteWheelStore } from "@/stores/useRosetteWheelStore";

const store = useRosetteWheelStore();

// ── Import file input ref ──────────────────────────────────────────────
const importFileInput = ref<HTMLInputElement | null>(null);

// ── Import handler ─────────────────────────────────────────────────────
function triggerImport() {
  importFileInput.value?.click();
}

function onImportFile(ev: Event) {
  const target = ev.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    store.importJSON(file);
    target.value = "";
  }
}
</script>

<template>
  <div class="rd-tab-content">
    <h3 class="rd-section-title">Recipe Presets</h3>
    <div class="rd-recipe-list">
      <div
        v-for="recipe in store.recipes"
        :key="recipe.id"
        class="rd-recipe-card"
        :class="{ active: store.activeRecipeId === recipe.id }"
        @click="store.loadRecipe(recipe)"
      >
        <div class="rd-recipe-header">
          <strong>{{ recipe.name }}</strong>
          <span class="rd-recipe-segs">{{ recipe.num_segs }} seg</span>
        </div>
        <p class="rd-recipe-desc">{{ recipe.desc }}</p>
        <div class="rd-recipe-tags">
          <span v-for="tag in recipe.tags" :key="tag" class="rd-tag">{{ tag }}</span>
        </div>
      </div>
    </div>

    <h3 class="rd-section-title" style="margin-top: 1rem">Saved Designs</h3>
    <div v-if="Object.keys(store.savedDesigns).length === 0" class="rd-empty">
      No saved designs yet
    </div>
    <div v-else class="rd-saved-list">
      <div
        v-for="(state, name) in store.savedDesigns"
        :key="name"
        class="rd-saved-card"
      >
        <span class="rd-saved-name" @click="store.loadDesign(state)">{{ name }}</span>
        <button class="rd-btn-xs rd-btn-danger" @click="store.deleteSavedDesign(String(name))">✕</button>
      </div>
    </div>

    <div class="rd-import-section">
      <button class="rd-btn" @click="triggerImport">📂 Import .rsd</button>
      <input
        ref="importFileInput"
        type="file"
        accept=".rsd,.json"
        style="display: none"
        @change="onImportFile"
      />
    </div>
  </div>
</template>

<style scoped>
.rd-tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.rd-section-title { font-size: 0.8rem; color: #c89a2a; margin: 0 0 0.5rem; }
.rd-recipe-list { display: flex; flex-direction: column; gap: 0.5rem; }
.rd-recipe-card {
  background: rgba(200, 146, 42, 0.06);
  border: 1px solid rgba(200, 146, 42, 0.12);
  border-radius: 6px;
  padding: 0.5rem;
  cursor: pointer;
  transition: border-color 0.15s;
}
.rd-recipe-card:hover { border-color: rgba(200, 146, 42, 0.35); }
.rd-recipe-card.active { border-color: #c89a2a; }
.rd-recipe-header { display: flex; justify-content: space-between; align-items: center; }
.rd-recipe-segs { font-size: 0.65rem; color: #887a66; }
.rd-recipe-desc { font-size: 0.7rem; color: #a09888; margin: 0.25rem 0; }
.rd-recipe-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.rd-tag { font-size: 0.6rem; padding: 1px 6px; background: rgba(200, 146, 42, 0.12); border-radius: 8px; color: #c89a2a; }

.rd-saved-list { display: flex; flex-direction: column; gap: 4px; }
.rd-saved-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px;
  background: rgba(200, 146, 42, 0.06);
  border-radius: 4px;
}
.rd-saved-name { cursor: pointer; font-size: 0.75rem; }
.rd-saved-name:hover { color: #c89a2a; }
.rd-import-section { margin-top: 0.75rem; }

.rd-empty { font-size: 0.75rem; color: #887a66; text-align: center; padding: 1rem; }

.rd-btn {
  padding: 5px 12px;
  font-size: 0.7rem;
  border: 1px solid rgba(200, 146, 42, 0.3);
  border-radius: 4px;
  background: rgba(200, 146, 42, 0.08);
  color: #c89a2a;
  cursor: pointer;
  transition: background 0.15s;
}
.rd-btn:hover { background: rgba(200, 146, 42, 0.18); }

.rd-btn-xs { padding: 1px 6px; font-size: 0.65rem; border: none; background: none; color: #887a66; cursor: pointer; }
.rd-btn-danger { color: #ff6060; }
.rd-btn-danger:hover { color: #ff3030; }
</style>
