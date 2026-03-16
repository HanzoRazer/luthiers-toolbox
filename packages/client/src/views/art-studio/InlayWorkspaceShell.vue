<script setup lang="ts">
/**
 * InlayWorkspaceShell — Unified inlay workspace (INLAY-06)
 *
 * Four stages:
 *   Stage 1: Pattern library (InlayPatternView)
 *   Stage 2: Fretboard placement (ArtStudioInlay)
 *   Stage 3: Headstock placement (HeadstockDesignerView)
 *   Stage 4: BOM & export aggregator
 */
import { ref, defineAsyncComponent } from "vue";

type StageId = "pattern" | "fretboard" | "headstock" | "bom";

const stages: { id: StageId; label: string; icon: string }[] = [
  { id: "pattern", label: "Pattern Library", icon: "◇" },
  { id: "fretboard", label: "Fretboard", icon: "▬" },
  { id: "headstock", label: "Headstock", icon: "🎸" },
  { id: "bom", label: "BOM & Export", icon: "📋" },
];

const activeStage = ref<StageId>("pattern");

function setStage(id: StageId) {
  activeStage.value = id;
}

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
        Pattern library · Fretboard placement · Headstock · BOM & export
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

    <div class="stage-content" role="tabpanel" :id="`stage-${activeStage}`" :aria-labelledby="`tab-${activeStage}`">
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
</style>
