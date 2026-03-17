<script setup lang="ts">
/**
 * InlayWorkspaceShell — Unified inlay workspace (INLAY-06)
 *
 * Five stages:
 *   Stage 0: Headstock Design (template + wood + import)
 *   Stage 1: Pattern library (InlayPatternView)
 *   Stage 2: Fretboard placement (ArtStudioInlay)
 *   Stage 3: Headstock placement (HeadstockDesignerView)
 *   Stage 4: BOM & export aggregator
 */
import { ref, defineAsyncComponent, provide } from "vue";
import { useWoodGrain, WOOD_SPECIES } from "@/composables/useWoodGrain";
import { useDxfImport } from "@/composables/useDxfImport";

type StageId = "headstock-design" | "pattern" | "fretboard" | "headstock" | "bom";

const stages: { id: StageId; label: string; icon: string }[] = [
  { id: "headstock-design", label: "Headstock Design", icon: "🎸" },
  { id: "pattern", label: "Pattern Library", icon: "◇" },
  { id: "fretboard", label: "Fretboard", icon: "▬" },
  { id: "headstock", label: "Headstock", icon: "🎸" },
  { id: "bom", label: "BOM & Export", icon: "📋" },
];

const activeStage = ref<StageId>("headstock-design");

function setStage(id: StageId) {
  activeStage.value = id;
}

// Stage 0 state: template + wood species
const HEADSTOCK_TEMPLATES = ["Les Paul", "Stratocaster", "Telecaster", "Flying V", "Explorer", "Custom"] as const;
type TemplateName = (typeof HEADSTOCK_TEMPLATES)[number];
const selectedTemplate = ref<TemplateName | null>(null);
const selectedSpecies = ref<string>("Mahogany");

const grain = useWoodGrain();
provide("grain", grain);

const dxfImport = useDxfImport();
const fileInputRef = ref<HTMLInputElement | null>(null);

function onTemplateSelect(name: TemplateName) {
  selectedTemplate.value = name;
}

function onSpeciesSelect(name: string) {
  if (WOOD_SPECIES[name]) {
    selectedSpecies.value = name;
    grain.setSpecies(name);
  }
}

function triggerFileInput() {
  fileInputRef.value?.click();
}

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    await dxfImport.loadFile(file);
    selectedTemplate.value = "Custom";
  } finally {
    input.value = "";
  }
}

function goToStage1() {
  setStage("pattern");
}

const speciesNames = Object.keys(WOOD_SPECIES);

// Lazy-loaded stage content to avoid pulling all views at once
const PatternStage = defineAsyncComponent(() =>
  import("@/views/art-studio/InlayPatternView.vue")
);
const FretboardStage = defineAsyncComponent(() =>
  import("@/components/art/art_studio_inlay/ArtStudioInlay.vue")
);
const HeadstockStage = defineAsyncComponent(() =>
  import("@/views/art-studio/HeadstockDesignerView.vue")
);
</script>

<template>
  <div class="inlay-workspace-shell">
    <header class="shell-header">
      <h1 class="shell-title">Inlay Workspace</h1>
      <p class="shell-subtitle">
        Headstock design · Pattern library · Fretboard · Headstock · BOM & export
      </p>
    </header>

    <nav class="stage-tabs" role="tablist">
      <button
        v-for="(stage, idx) in stages"
        :key="stage.id"
        type="button"
        role="tab"
        :aria-selected="activeStage === stage.id"
        :aria-controls="`stage-${stage.id}`"
        :id="`tab-${stage.id}`"
        class="stage-tab"
        :class="{ active: activeStage === stage.id }"
        @click="setStage(stage.id)"
      >
        <span class="stage-icon">{{ stage.icon }}</span>
        <span class="stage-label">{{ stage.label }}</span>
      </button>
    </nav>

    <input
      ref="fileInputRef"
      type="file"
      accept=".dxf,.svg,application/dxf,image/svg+xml"
      class="hidden-file-input"
      aria-hidden="true"
      @change="onFileSelected"
    />

    <div class="stage-content" role="tabpanel" :id="`stage-${activeStage}`" :aria-labelledby="`tab-${activeStage}`">
      <!-- Stage 0: Headstock Design -->
      <div v-show="activeStage === 'headstock-design'" class="stage-panel stage-panel-headstock-design" data-stage="headstock-design">
        <div class="headstock-design-stage">
          <section class="hd-section">
            <h2 class="hd-section-title">1. Headstock template</h2>
            <div class="template-cards">
              <button
                v-for="name in HEADSTOCK_TEMPLATES"
                :key="name"
                type="button"
                class="template-card"
                :class="{ selected: selectedTemplate === name }"
                @click="onTemplateSelect(name)"
              >
                {{ name }}
              </button>
            </div>
          </section>
          <section class="hd-section">
            <h2 class="hd-section-title">2. Wood species</h2>
            <div class="species-buttons">
              <button
                v-for="name in speciesNames"
                :key="name"
                type="button"
                class="species-btn"
                :class="{ selected: selectedSpecies === name }"
                @click="onSpeciesSelect(name)"
              >
                {{ name }}
              </button>
            </div>
          </section>
          <section class="hd-section">
            <h2 class="hd-section-title">3. Import DXF/SVG</h2>
            <button type="button" class="import-btn" @click="triggerFileInput">
              Import DXF/SVG
            </button>
            <p v-if="dxfImport.importedFile" class="import-filename">{{ dxfImport.importedFile.name }}</p>
            <p v-if="dxfImport.error" class="import-error">{{ dxfImport.error }}</p>
          </section>
          <section class="hd-section">
            <h2 class="hd-section-title">4. Preview</h2>
            <div class="canvas-preview">
              <p v-if="selectedTemplate" class="preview-line">Headstock: <strong>{{ selectedTemplate }}</strong></p>
              <p class="preview-line">Wood: <strong>{{ selectedSpecies }}</strong></p>
              <p class="preview-note">Full grain preview coming soon</p>
            </div>
          </section>
          <section class="hd-section hd-actions">
            <button
              type="button"
              class="next-btn"
              :disabled="!selectedTemplate"
              @click="goToStage1"
            >
              Next →
            </button>
          </section>
        </div>
      </div>

      <!-- Stage 1: Pattern library -->
      <div v-show="activeStage === 'pattern'" class="stage-panel" data-stage="pattern">
        <Suspense>
          <component :is="PatternStage" />
          <template #fallback>
            <div class="stage-loading">Loading pattern library…</div>
          </template>
        </Suspense>
      </div>

      <!-- Stage 2: Fretboard (ArtStudioInlay with composables) -->
      <div v-show="activeStage === 'fretboard'" class="stage-panel" data-stage="fretboard">
        <Suspense>
          <component :is="FretboardStage" />
          <template #fallback>
            <div class="stage-loading">Loading fretboard designer…</div>
          </template>
        </Suspense>
      </div>

      <!-- Stage 3: Headstock -->
      <div v-show="activeStage === 'headstock'" class="stage-panel" data-stage="headstock">
        <Suspense>
          <component :is="HeadstockStage" />
          <template #fallback>
            <div class="stage-loading">Loading headstock designer…</div>
          </template>
        </Suspense>
      </div>

      <!-- Stage 4: BOM & export aggregator -->
      <div v-show="activeStage === 'bom'" class="stage-panel stage-panel-bom" data-stage="bom">
        <div class="bom-aggregator">
          <h2 class="bom-title">BOM & Export</h2>
          <p class="bom-desc">
            Export from each stage, or use the tabs above to work in Pattern Library, Fretboard, or Headstock.
          </p>
          <div class="bom-cards">
            <div class="bom-card">
              <h3>◇ Pattern Library</h3>
              <p>Generate marquetry patterns, then use the <strong>Pattern Library</strong> tab to export SVG/DXF and view BOM.</p>
              <button type="button" class="bom-link" @click="setStage('pattern')">
                Open Pattern Library →
              </button>
            </div>
            <div class="bom-card">
              <h3>▬ Fretboard</h3>
              <p>Design fretboard inlays and export DXF from the <strong>Fretboard</strong> tab.</p>
              <button type="button" class="bom-link" @click="setStage('fretboard')">
                Open Fretboard →
              </button>
            </div>
            <div class="bom-card">
              <h3>🎸 Headstock</h3>
              <p>Choose headstock templates and copy the generated prompt from the <strong>Headstock</strong> tab.</p>
              <button type="button" class="bom-link" @click="setStage('headstock')">
                Open Headstock →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inlay-workspace-shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 1rem;
  max-width: 1600px;
  margin: 0 auto;
}

.shell-header {
  margin-bottom: 1rem;
}

.shell-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
  color: var(--color-text-primary, #1e293b);
}

.shell-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #64748b);
}

.stage-tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem;
  background: var(--color-bg-secondary, #f1f5f9);
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  flex-shrink: 0;
}

.stage-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 0.375rem;
  background: transparent;
  color: var(--color-text-secondary, #64748b);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.stage-tab:hover {
  background: var(--color-bg-tertiary, #e2e8f0);
  color: var(--color-text-primary, #334155);
}

.stage-tab.active {
  background: var(--color-accent-bg, #2563eb);
  color: white;
}

.stage-icon {
  font-size: 1.1rem;
}

.stage-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.stage-panel {
  flex: 1;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.stage-panel-bom {
  min-height: 300px;
}

.stage-loading {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-secondary, #64748b);
  font-size: 0.9rem;
}

/* BOM aggregator */
.bom-aggregator {
  padding: 1rem;
  max-width: 800px;
}

.bom-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
  color: var(--color-text-primary, #1e293b);
}

.bom-desc {
  margin: 0 0 1.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #64748b);
}

.bom-cards {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bom-card {
  padding: 1rem 1.25rem;
  background: var(--color-bg-secondary, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.5rem;
}

.bom-card h3 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary, #1e293b);
}

.bom-card p {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #475569);
  line-height: 1.4;
}

.bom-link {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-accent, #2563eb);
  text-decoration: none;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.bom-link:hover {
  text-decoration: underline;
}

/* Stage 0: Headstock Design */
.hidden-file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.stage-panel-headstock-design {
  min-height: 400px;
}

.headstock-design-stage {
  padding: 1rem;
  max-width: 720px;
}

.hd-section {
  margin-bottom: 1.5rem;
}

.hd-section-title {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
  color: var(--color-text-primary, #1e293b);
}

.template-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.template-card {
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.5rem;
  background: var(--color-bg-secondary, #f8fafc);
  color: var(--color-text-primary, #334155);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.template-card:hover {
  border-color: var(--color-accent, #2563eb);
  background: var(--color-bg-tertiary, #eff6ff);
}

.template-card.selected {
  border-color: var(--color-accent, #2563eb);
  background: var(--color-accent-bg, #2563eb);
  color: white;
}

.species-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.species-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.375rem;
  background: var(--color-bg-secondary, #f8fafc);
  color: var(--color-text-primary, #334155);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.species-btn:hover {
  border-color: var(--color-accent, #2563eb);
  background: var(--color-bg-tertiary, #eff6ff);
}

.species-btn.selected {
  border-color: var(--color-accent, #2563eb);
  background: var(--color-accent-bg, #2563eb);
  color: white;
}

.import-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.375rem;
  background: var(--color-bg-secondary, #f8fafc);
  color: var(--color-text-primary, #334155);
  font-size: 0.875rem;
  cursor: pointer;
}

.import-btn:hover {
  border-color: var(--color-accent, #2563eb);
  color: var(--color-accent, #2563eb);
}

.import-filename {
  margin: 0.5rem 0 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary, #64748b);
}

.import-error {
  margin: 0.5rem 0 0;
  font-size: 0.8125rem;
  color: var(--color-error, #dc2626);
}

.canvas-preview {
  padding: 1rem;
  background: var(--color-bg-secondary, #f1f5f9);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.5rem;
}

.preview-line {
  margin: 0 0 0.25rem;
  font-size: 0.875rem;
  color: var(--color-text-primary, #334155);
}

.preview-note {
  margin: 0.75rem 0 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary, #64748b);
  font-style: italic;
}

.hd-actions {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #e2e8f0);
}

.next-btn {
  padding: 0.6rem 1.25rem;
  border: none;
  border-radius: 0.375rem;
  background: var(--color-accent, #2563eb);
  color: white;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.next-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
